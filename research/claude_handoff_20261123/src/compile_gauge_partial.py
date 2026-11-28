#!/usr/bin/env python3
"""Generate REAL KMBs of C45 B129 and C46 V8 with full 7-bit tensorqrom XAG.
No offset hacks, no claim of an official scored submission.
"""
import os,sys,hashlib,time,json,argparse,types
from pathlib import Path
import numpy as np
root=Path(__file__).parent
sys.path.insert(0,str(root/'axis_old/src'))
sys.modules.setdefault('kickmix',types.ModuleType('kickmix'))
from chemistry_j_scheduler import delta_for
from angle_full_truth import anf_full7
import compile_angle_signed_core as core
from compile_angle_signed_core import compile_oracle
import tensorqrom as tq

p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);p.add_argument('--mode',choices=['per_output','shared','signed6resid'],default='per_output');p.add_argument('--J',type=int,default=5);p.add_argument('--banks',type=int,default=15);p.add_argument('--start',type=int,default=0);p.add_argument('--seed',type=int,default=20);p.add_argument('--trials',type=int,default=1);p.add_argument('--lowbits',type=int,default=4);a=p.parse_args()
out=Path(a.out);out.mkdir(exist_ok=True,parents=True)
with np.load(a.source) as z:w=z['angle_words'].astype(np.uint8)
records=[]
for k in range(a.start,a.banks):
 t=time.time();delta=delta_for(list(range(75)),w,a.J,k);C=anf_full7(delta,a.lowbits);core.L=1<<a.lowbits
 if a.mode=='per_output':terms=tq.per_output(C)
 elif a.mode=='shared':terms=tq.shared(C,[7]*a.J,trials=a.trials,seed=a.seed+k,margin=1,transpose=True)
 elif a.mode=='signed6resid':
  C6=C[:,:,[7*j+b for j in range(a.J) for b in range(6)]]
  residue=((delta>>6)^(delta>>5))&1
  Cr=anf_full7(residue.astype(np.uint8),a.lowbits)[:,:,[7*j for j in range(a.J)]]
  six=tq.shared(C6,[6]*a.J,trials=a.trials,seed=a.seed+k,margin=1,transpose=True)
  remain=tq.per_output(Cr)
  terms=[]
  for A,B,D,E,mask in six:
   outmask=0
   for j in range(a.J):
    for b in range(6):
     if mask>>(6*j+b)&1:
      outmask|=1<<(7*j+b)
      if b==5:outmask|=1<<(7*j+6)
   terms.append((A,B,D,E,outmask))
  for A,B,D,E,mask in remain:
   outmask=sum((1<<(7*j+6)) for j in range(a.J) if mask>>j&1)
   terms.append((A,B,D,E,outmask))

 assert np.array_equal(tq.mixed_of(terms,C.shape[0]-1,C.shape[1]-1,C.shape[2]),C[1:,1:])
 path=out/f'angle_k_{k}.kmb';rec=compile_oracle(delta,terms,path)
 rec.update(bank=k,lowbits=a.lowbits,synthesis=a.mode,nterms=len(terms),time=round(time.time()-t,3),h=(len(w)+15)//16,valid_rows=len(w))
 records.append(rec)
 print(f'bank={k} T={rec["CCX"]} Q={rec["Q"]} ops={rec["operations"]} time={rec["time"]}',flush=True)
with open(out/'build_report.json','w') as f:json.dump(dict(source=a.source,source_sha256=hashlib.sha256(Path(a.source).read_bytes()).hexdigest(),mode=a.mode,J=a.J,records=records,T=sum(x['CCX'] for x in records),maxQ=max(x['Q'] for x in records),official_verified=False),f,indent=2)
print('TOTAL',sum(x['CCX'] for x in records),'maxQ',max(x['Q'] for x in records),flush=True)