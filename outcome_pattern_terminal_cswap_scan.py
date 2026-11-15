#!/usr/bin/env python3
"""Bounded exact P16 match scan and conservative affine-cone feasibility scan.

No source circuits are modified. The strict matcher proves a CSWAP can be
commuted to two terminal X-measurements, permitting a Clifford-only rewrite
with explicit outcome relabeling. The affine-cone scan is discovery only.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import time

import dqi_ccx_peephole as shared
import kmb_profile as kp


def target_writes(op):
    b = op.opcode & 127
    if b in (0x11, 0x12, 0x50, 0x21, 0x31): return set(op.qubits[-1:])
    if b in (0x22, 0x32): return set(op.qubits[-2:])
    if b in (0, 0x10, 0x13, 0x20, 0x30): return set()
    return set(op.qubits)


def strict(circuit, first, window):
    ctrl, a, b = first.qubits
    first_measure = None
    for op in circuit.operations(first.source_index + 1,
                                 min(len(circuit.opcodes), first.source_index + window + 1)):
        base = op.opcode & 127
        if base in (1, 6, 7, 0x17, 0x47): return None, 'scope_or_unknown'
        if first_measure is not None:
            q1, bit1, pos1 = first_measure
            pending = b if q1 == a else a
            if op.condition == bit1 or op.bit == bit1:
                return None, 'first_record_used_before_second_measurement'
            if pending not in op.qubits: continue
            if op.opcode == 0x50 and op.qubits == (pending,):
                return dict(start=first.source_index, control=ctrl, targets=[a,b],
                            first_hmr=pos1, second_hmr=op.source_index,
                            measurement_order=[q1,pending], bits=[bit1,op.bit],
                            saving_static_toffoli=1), 'strict_match'
            return None, 'pending_target_touched'
        if not set((a,b)).intersection(op.qubits):
            if ctrl in target_writes(op): return None, 'control_written'
            continue
        if op.opcode == 0x50 and op.qubits[0] in (a,b):
            first_measure = op.qubits[0], op.bit, op.source_index
            continue
        # Diagonal gates symmetric in a,b commute with their swap.
        if base in (0x20,0x30) and {a,b}.issubset(op.qubits): continue
        return None, f'target_touched_by_{kp.OPCODES.get(op.opcode, str(op.opcode))}'
    return None, 'window_exhausted'


def affine_cone(circuit, first, window):
    """Track nonzero CSWAP difference through affine gates, stop at all barriers.

    If all differences disappear at HMRs before any nonlinear/phase use, a
    terminal readout cone exists; a phase/record construction is still needed.
    Unconditional SWAP relabels the dependency vector. CZ/CCZ touching the cone
    are barriers. This is not a license to remove the CSWAP by itself.
    """
    ctrl,a,b=first.qubits
    affected={a,b}; measured=[]; touched={a,b}; affine=0
    for op in circuit.operations(first.source_index + 1,
                                 min(len(circuit.opcodes), first.source_index + window + 1)):
        base=op.opcode & 127
        if base in (1,6,7,0x17,0x47): return None,'scope_or_unknown'
        hit=affected.intersection(op.qubits)
        if ctrl in target_writes(op):return None,'control_written'
        if not hit: continue
        if op.opcode==0x21:
            u,v=op.qubits
            if u in affected:
                if v in affected:affected.remove(v)
                else:affected.add(v)
            touched.update(op.qubits);affine+=1
        elif op.opcode==0x22:
            u,v=op.qubits
            if (u in affected)!=(v in affected):affected.symmetric_difference_update((u,v))
            touched.update(op.qubits);affine+=1
        elif op.opcode==0x11:
            affine+=1
        elif op.opcode==0x50:
            affected.remove(op.qubits[0]);measured.append([op.source_index,op.qubits[0],op.bit])
            if not affected:
                return dict(start=first.source_index,end=op.source_index+1,control=ctrl,
                            targets=[a,b],readouts=measured,affine_ops=affine,
                            touched_qubits=sorted(touched)), 'affine_cone'
        else:return None, f'cone_touched_by_{kp.OPCODES.get(op.opcode,str(op.opcode))}'
    return None,'window_exhausted'


def local_identity_check():
    # Exact signed basis check for every three-bit input and both HMR outcomes.
    cases=0
    for ctrl in (0,1):
        for a in (0,1):
            for b in (0,1):
                for u in (0,1):
                    for v in (0,1):
                        r,s=u^v,v
                        aa,bb=(b,a) if ctrl else (a,b)
                        before=(r*aa+s*bb)&1
                        after=(u*a+u*ctrl*(a^b)+v*(a^b))&1
                        assert before==after
                        cases+=1
    return dict(status='PASS',basis_and_record_cases=cases,
                before='CSWAP c a b; HMR a r; HMR b s',
                after='CX a b; HMR a u; CZ c b if u; HMR b v; r=u XOR v; s=v')


def matcher_fixtures():
    class Circuit:
        def __init__(self, specs):
            self.items=[shared.Operation(code,tuple(qs),bit,condition,source_index=i)
                        for i,(code,qs,bit,condition) in enumerate(specs)]
            self.opcodes=bytes(o.opcode for o in self.items)
        def operations(self,start,end):return iter(self.items[start:end])
    S=(0x32,(0,1,2),None,None)
    A=(0x50,(1,),5,None);B=(0x50,(2,),6,None)
    tests=[
        ('direct',[S,A,B],True,True),
        ('disjoint_and_control_read',[S,(0x21,(0,3),None,None),A,(0x11,(4,),None,None),B],True,True),
        ('shared_symmetric_phase',[S,(0x20,(1,2),None,None),A,B],True,False),
        ('affine_fanout',[S,(0x21,(1,3),None,None),A,B,(0x50,(3,),7,None)],False,True),
        ('control_overwritten',[S,(0x11,(0,),None,None),A,B],False,False),
        ('target_phase_read',[S,(0x20,(1,3),None,None),A,B],False,False),
        ('early_record_read',[S,A,(0x91,(4,),None,5),B],False,True),
        ('scope_change',[S,(0x81,(),None,9),A,B],False,False),
    ]
    results=[]
    for name,specs,strict_expected,cone_expected in tests:
        c=Circuit(specs)
        s,swhy=strict(c,c.items[0],64);a,awhy=affine_cone(c,c.items[0],64)
        assert bool(s)==strict_expected,(name,swhy)
        assert bool(a)==cone_expected,(name,awhy)
        results.append(dict(name=name,strict=bool(s),affine_candidate=bool(a)))
    return dict(status='PASS',tests=results,
                note='Affine hits intentionally require subsequent classical-record dependency audit.')


def main():
    p=argparse.ArgumentParser();p.add_argument('input',type=Path)
    p.add_argument('--profile',type=Path);p.add_argument('--window',type=int,default=4096)
    p.add_argument('--seconds',type=float,default=180);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--affine-only',action='store_true')
    args=p.parse_args();started=time.monotonic()
    profile=json.loads(args.profile.read_text()) if args.profile else kp.profile(args.input,max_register_summaries=0)
    c=shared.BinaryCircuit(args.input,profile)
    strict_hits=[];cones=[];strict_reasons=Counter();cone_reasons=Counter();seen=0;caps=[]
    total=c.opcodes.count(0x32)+c.opcodes.count(0xb2)
    try:
        for m in re.finditer(rb'[\x32\xb2]',c.opcodes):
            if time.monotonic()-started>args.seconds:break
            op=next(c.operations(m.start(),m.start()+1));seen+=1
            if op.condition is not None:
                strict_reasons['explicit_condition']+=1;cone_reasons['explicit_condition']+=1;continue
            if not args.affine_only:
                h,reason=strict(c,op,args.window);strict_reasons[reason]+=1
                if h:strict_hits.append(h)
            h,reason=affine_cone(c,op,args.window);cone_reasons[reason]+=1
            if h:cones.append(h)
            if reason=='window_exhausted':caps.append(m.start())
            if seen%2048==0:
                print(json.dumps(dict(progress=seen,total=total,affine_hits=len(cones),
                                      seconds=time.monotonic()-started)),flush=True)
        result=dict(status='COMPLETE' if seen==total else 'TIME_BOUNDED_PARTIAL',
                    input=str(args.input),input_sha256=profile['raw_kmb_sha256'],
                    local_identity=local_identity_check(),window=args.window,
                    strict_scan_performed=not args.affine_only,
                    total_cswaps=total,scanned_cswaps=seen,strict_matches=strict_hits,
                    strict_rejections=dict(strict_reasons),affine_terminal_cones=cones,
                    affine_window_exhausted_positions=caps,
                    affine_rejections=dict(cone_reasons),seconds=time.monotonic()-started,
                    caveat='Affine-cone hits are candidates only: phase/record dependencies still require proof. No circuit was changed.')
    finally:c.close()
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('strict_matches','affine_terminal_cones','affine_window_exhausted_positions')},indent=2))
    print('strict',len(strict_hits),'affine',len(cones),flush=True)

if __name__=='__main__':main()
