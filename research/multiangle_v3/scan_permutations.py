#!/usr/bin/env python3
"""Complete 462-choice C(11,6) screen with exact executable-compiler CCX count.

This is not a global quantum optimality certificate; only an exhaustive search
of six-wire low-subset choices within a fixed multi-output-basis compiler.
"""
import argparse,itertools,json,sys,hashlib
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from permutation_patterns import estimate
from multi_angle_synthesis import sha256
p=argparse.ArgumentParser()
p.add_argument('--npz',required=True,type=Path)
p.add_argument('--out',required=True,type=Path)
p.add_argument('--start',type=int,default=0)
p.add_argument('--stop',type=int,default=462)
a=p.parse_args()
subs=list(itertools.combinations(range(11),6))
assert len(subs)==462 and 0<=a.start<a.stop<=462
with np.load(a.npz,allow_pickle=False) as z:words=z['angle_words'].astype(np.int64)
a.out.parent.mkdir(parents=True,exist_ok=True)
with a.out.open('w') as file:
 for ii in range(a.start,a.stop):
  low=subs[ii]
  scores=[estimate(words,k,low) for k in range(15)]
  total=sum(row['total_ccx_after_hmr'] for row in scores)
  rec=dict(schema='gvqcc.permute6.v1',source=a.npz.name,source_sha256=sha256(a.npz),
      subset_index=ii,low_wires=list(low),CCX_per_pass=total,Q=127,
      per_slot_CCX=[r['total_ccx_after_hmr'] for r in scores],
      theoretical_constructive=True,native_verification=False,
      limitation='exact formula for this compiler; not competitive lower bound')
  file.write(json.dumps(rec,sort_keys=True)+'\n')
 print(a.npz.name,a.start,a.stop,'records',a.stop-a.start)
