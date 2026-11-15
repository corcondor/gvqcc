#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Exactly factor same-target CCX pairs across commuting quantum instruments.

CCX(a,b,t); CCX(a,c,t) = CX(b,c); CCX(a,c,t); CX(b,c).
All four wires may be dirty. Both endpoints are unconditional. A discovery
signature is never accepted as proof: all crossed operations are checked.
"""
import argparse
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path
import time
import dqi_ccx_peephole as p
import kmb_profile as kp
from score4_measurement_fanout import commute, op_record
from score4_dqi_guard_review import text as circuit_text

SOURCE_SHA = '98ad7b39a630a4152c54b39fbb14dece22fcaf34b00410ab8a45629db87e0b6f'

def identity():
    for a,b,c,t in itertools.product((0,1),repeat=4):
        old=(a,b,c,t^(a&b)^(a&c))
        d=c^b;u=t^(a&d);d^=b
        assert old==(a,b,d,u)
    return {'all_basis_columns':16,'phase':'identical permutation matrices, with +1 phases'}

def native(before,after,seed):
    import kickmix as km
    import numpy as np
    qs=sorted({q for op in before for q in op.qubits})
    bs=sorted({b for op in before for b in (op.bit,op.condition) if b is not None})
    qreg=km.array([km.q(q) for q in qs]);breg=km.array([km.b(b) for b in bs])
    rng=np.random.default_rng(seed)
    values=rng.integers(0,2,(len(qs),256),dtype=np.uint8).astype(bool)
    bits=rng.integers(0,2,(len(bs),256),dtype=np.uint8).astype(bool)
    results=[]
    for ops in (before,after):
        sim=km.Simulator(batch_size=256,seed=2026111550,debug_print=False)
        sim.write_across_shots(qreg,values)
        if bs:sim.write_across_shots(breg,bits)
        sim.do(km.Circuit(circuit_text(ops)))
        results.append((sim.read_across_shots(qreg),sim.read_across_shots(breg) if bs else np.zeros(0),sim.read_phase_flipped_across_shots()))
    assert all(np.array_equal(a,b) for a,b in zip(*results))
    return {'basis_inputs':256,'quantum_errors':0,'classical_errors':0,'phase_errors':0}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('source',type=Path);ap.add_argument('discovery',type=Path)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    begun=time.monotonic();profile=kp.profile(args.source,max_register_summaries=0)
    assert profile['raw_kmb_sha256']==SOURCE_SHA
    discovered=json.loads(args.discovery.read_text());assert discovered['num_ops']==profile['header']['num_ops']
    rows=sorted(discovered['opportunities'],key=lambda r:r['first'])
    endpoints=[r[k] for r in rows for k in ('first','second')];assert len(endpoints)==len(set(endpoints))
    ranges=[]
    for row in rows:
        assert row['first_depth']==row['second_depth']==0
        assert row['first_condition']==row['second_condition']==-1
        if ranges and row['first']<ranges[-1][1]:ranges[-1][1]=max(ranges[-1][1],row['second']+1)
        else:ranges.append([row['first'],row['second']+1])
    circuit=p.BinaryCircuit(args.source,profile);certificates=[];splices=[]
    try:
        for start,end in ranges:
            assert circuit.opcodes[:start].count(0x81)==circuit.opcodes[:start].count(0x01)
            original=list(circuit.operations(start,end));current=original[:];edits={};steps=[]
            selected=[r for r in rows if start<=r['first'] and r['second']<end]
            for row in selected:
                fi=next(i for i,o in enumerate(current) if o.source_index==row['first'])
                si=next(i for i,o in enumerate(current) if o.source_index==row['second'])
                first,second=current[fi],current[si];a=row['common_control'];b,c=row['other_controls'];t=row['target']
                assert fi<si and len({a,b,c,t})==4
                assert first.opcode==second.opcode==0x31 and first.condition is second.condition is None
                assert set(first.qubits[:2])=={a,b} and set(second.qubits[:2])=={a,c}
                assert first.qubits[2]==second.qubits[2]==t
                depth=0
                for i,op in enumerate(current[:si+1]):
                    if i in (fi,si):assert depth==0
                    if op.opcode==0x81:depth+=1
                    elif op.opcode==0x01:depth-=1;assert depth>=0
                assert depth==0
                middle=current[fi+1:si];assert all(commute(first,op) for op in middle)
                cx=p.Operation(0x21,(b,c));replacement=[cx,p.Operation(0x31,(a,c,t)),cx]
                current[fi:si+1]=middle+replacement
                edits[row['first']]=[];edits[row['second']]=replacement
                steps.append(dict(first=row['first'],second=row['second'],common_control=a,other_controls=[b,c],target=t,
                    every_crossed_instrument_commutes=True,crossed_families=dict(Counter(kp.OPCODES[op.opcode] for op in middle))))
            expected=[new for op in original for new in edits.get(op.source_index,[op])];assert current==expected
            original_by_id={o.source_index:o for o in original}
            for index,after in sorted(edits.items()):splices.append((index,index+1,[original_by_id[index]],after))
            certificates.append(dict(start=start,end=end,steps=steps,before=[op_record(o) for o in original],
                after=[op_record(o) for o in current],native=native(original,current,2026111551+len(certificates))))
        candidate=args.out/'dqi.kmb';p.write_rewritten(circuit,candidate,sorted(splices,key=lambda row:row[0]))
    finally:circuit.close()
    after=kp.profile(candidate,max_register_summaries=0);count=len(rows)
    assert count>0
    assert profile['raw_gate_families']['CCX']['total']-after['raw_gate_families']['CCX']['total']==count
    assert after['raw_gate_families']['CX']['total']-profile['raw_gate_families']['CX']['total']==2*count
    assert all(profile['header'][k]==after['header'][k] for k in ('num_qubits','num_bits','num_registers'))
    report=dict(status='EXACT_INSTRUMENT_FANIN_REWRITE_PASS',source_sha256=SOURCE_SHA,
        candidate_sha256=after['raw_kmb_sha256'],additional_unconditional_ccx_reduction=count,added_cx=2*count,
        qubits=after['header']['num_qubits'],classical_bits=after['header']['num_bits'],identity=identity(),
        blocks=certificates,official_verification='NOT_RUN',elapsed_seconds=time.monotonic()-begun)
    (args.out/'rewrite_certificate.json').write_text(json.dumps(report,indent=2)+'\n')
    (args.out/'profile.json').write_text(json.dumps(after,indent=2)+'\n')
    recipe=dict(source_sha256=SOURCE_SHA,candidate_sha256=after['raw_kmb_sha256'],
        edits=[dict(index=s,old=op_record(old[0]),new=[op_record(o) for o in new]) for s,e,old,new in sorted(splices,key=lambda r:r[0])])
    (args.out/'patch.json').write_text(json.dumps(recipe,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='blocks'},indent=2),flush=True)

if __name__=='__main__':main()
