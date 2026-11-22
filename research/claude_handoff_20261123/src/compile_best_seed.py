#!/usr/bin/env python3
"""Real KMB synthesis: five-output signed6 XOR, exact high-bit residual, randomized XAG seed search.
Every output bit is preserved on the full valid address domain, including dirty-word semantics.
"""
import json,sys,time,hashlib,argparse,types
from pathlib import Path
import numpy as np
root=Path(__file__).parent
sys.path.insert(0,str(root/'axis_old/src'))
sys.modules.setdefault('kickmix',types.ModuleType('kickmix'))
import tensorqrom as tq
from chemistry_j_scheduler import delta_for
from angle_full_truth import anf_full7
from compile_angle_signed_core import compile_oracle
ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--out',required=True);ap.add_argument('--offsets',type=int,nargs='+',default=[20,42,160]);args=ap.parse_args()
with np.load(args.source) as z:w=z['angle_words'].astype(np.uint8)
out=Path(args.out);out.mkdir(exist_ok=True,parents=True)
report=[]
for k in range(15):
 t0=time.time();d=delta_for(list(range(75)),w,5,k);C=anf_full7(d,4)
 C6=C[:,:,[7*j+b for j in range(5) for b in range(6)]]
 cr=anf_full7((((d>>6)^(d>>5))&1).astype(np.uint8),4)[:,:,[7*j for j in range(5)]]
 rest=tq.per_output(cr)
 choices=[];best=None
 for base in args.offsets:
  terms6=tq.shared(C6,[6]*5,trials=1,seed=base+k,margin=1,transpose=True)
  terms=[]
  for a,b,c,e,mask in terms6:
   dest=0
   for j in range(5):
    for bit in range(6):
     if (mask>>(6*j+bit))&1:
      dest|=1<<(7*j+bit)
      if bit==5:dest|=1<<(7*j+6)
   terms.append((a,b,c,e,dest))
  for a,b,c,e,mask in rest:
   terms.append((a,b,c,e,sum((1<<(7*j+6)) for j in range(5) if mask>>j&1)))
  assert np.array_equal(tq.mixed_of(terms,C.shape[0]-1,C.shape[1]-1,C.shape[2]),C[1:,1:])
  choices.append(dict(seed=base+k,base6=len(terms6),residual=len(rest),total_terms=len(terms)))
  if best is None or len(terms)<len(best[1]):best=(base+k,terms)
 gate=compile_oracle(d,best[1],out/f'angle_k_{k}.kmb')
 gate.update(k=k,seed=best[0],choices=choices,seconds=round(time.time()-t0,3))
 report.append(gate)
 print('BANK',k,'T',gate['CCX'],'Q',gate['Q'],'seed',best[0],'choices',choices,'time',gate['seconds'],flush=True)
rec=dict(source=str(args.source),source_sha256=hashlib.sha256(Path(args.source).read_bytes()).hexdigest(),scheme='signed6_exact_residual_shared_XAG_seed_beam',banks=report,total_T=sum(x['CCX'] for x in report),maxQ=max(x['Q'] for x in report),native_official_pass=False)
(out/'build_report.json').write_text(json.dumps(rec,indent=2)+'\n')
print('TOTAL',rec['total_T'],'Q',rec['maxQ'],flush=True)