#!/usr/bin/env python3
"""Generate upstream 66/65-T inverse components and alpha-match exact KMB blocks.

Input circuits are read-only. Qubit and classical-bit names are independently
renamed injectively; every opcode and operand position must match.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import time
import dqi_ccx_peephole as shared
import kmb_profile as kp

ROOT=Path(__file__).resolve().parent
SOURCE_ROOT=ROOT.parent/'official_sources/Syed_v12/source/dqi_source/src/controller_work/work/round2/milestone152/source'


def match(template, actual):
    qmap={};qrev={};bmap={};brev={}
    def bind(x,y,m,r):
        if (x is None)!=(y is None):return False
        if x is None:return True
        if x in m and m[x]!=y or y in r and r[y]!=x:return False
        m[x]=y;r[y]=x;return True
    for old,new in zip(template,actual):
        if old.opcode!=new.opcode or old.angle!=new.angle:return None
        if len(old.qubits)!=len(new.qubits):return None
        for q,r in zip(old.qubits,new.qubits):
            if not bind(q,r,qmap,qrev):return None
        if not bind(old.bit,new.bit,bmap,brev):return None
        if not bind(old.condition,new.condition,bmap,brev):return None
    return qmap,bmap


def main():
    p=argparse.ArgumentParser();p.add_argument('input',type=Path)
    p.add_argument('--profile',type=Path);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();started=time.monotonic()
    sys.path.insert(0,str(SOURCE_ROOT))
    import compact_inverse as upstream
    import kickmix as km
    records=[];templates=[]
    for zero_flag in (False,True):
        for label,name in [('legacy66','legacy_compact_inverse_twelve'),('cubic65','compact_inverse_twelve')]:
            builder=km.CircuitBuilder();source=builder.create_quantum_register(12,'source')
            flag=builder.create_quantum_register(1,'flag') if zero_flag else None
            target=getattr(upstream,name)(builder,source,zero_flag=flag[0] if flag is not None else None)
            c=builder.finish_circuit();label+=('_flag' if zero_flag else '')
            dest=ROOT/f'outcome_inverse65_{label}.kmb';c.to_file(str(dest),format='kmb')
            c.to_file(str(dest.with_suffix('.kmx')),format='kmx')
            prof=kp.profile(dest,max_register_summaries=0);bc=shared.BinaryCircuit(dest,prof)
            try:ops=list(bc.operations(0,len(bc.opcodes)))
            finally:bc.close()
            rec=dict(name=label,source_function=name,zero_flag=zero_flag,template_sha256=prof['raw_kmb_sha256'],
                     num_ops=len(ops),num_qubits=c.num_qubits,num_bits=c.num_bits,
                     toffoli=c.operation_statistics().num_toffoli_like,
                     source=[int(str(q)[1:]) for q in source],target=[int(str(q)[1:]) for q in target],
                     flag=[int(str(q)[1:]) for q in flag] if flag is not None else [],
                     gate_counts=dict(Counter(kp.OPCODES[o.opcode] for o in ops)))
            records.append(rec);templates.append((rec,ops))
    profile=json.loads(args.profile.read_text()) if args.profile else kp.profile(args.input,max_register_summaries=0)
    c=shared.BinaryCircuit(args.input,profile)
    try:
        for rec,ops in templates:
            pattern=bytes(o.opcode for o in ops);pos=0;candidates=0;hits=[]
            while True:
                pos=c.opcodes.find(pattern,pos)
                if pos<0:break
                start=pos;pos+=1;candidates+=1
                actual=list(c.operations(start,start+len(ops)))
                maps=match(ops,actual)
                if maps is None:continue
                qm,bm=maps
                hits.append(dict(start=start,end=start+len(ops),qubit_map=qm,bit_map=bm,
                                 source=[qm[q] for q in rec['source']],target=[qm[q] for q in rec['target']],
                                 flag=[qm[q] for q in rec['flag']]))
            rec.update(opcode_candidates=candidates,exact_matches=len(hits),matches=hits)
            print(json.dumps({k:v for k,v in rec.items() if k!='matches'}),flush=True)
    finally:c.close()
    result=dict(status='EXACT_TEMPLATE_SCAN_COMPLETE',input=str(args.input),input_sha256=profile['raw_kmb_sha256'],
                source_files={n:hashlib.sha256((SOURCE_ROOT/n).read_bytes()).hexdigest() for n in
                              ['compact_inverse.py','cubic_inverse130.py','tower_inverse.py']},
                records=records,seconds=time.monotonic()-started,circuit_modified=False,
                note='Source templates only; no substitution, classical lifetime or full-circuit proof is implied by a match.')
    args.out.write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
