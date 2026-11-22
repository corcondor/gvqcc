#!/usr/bin/env python3
"""Independent parser on real generated KMX: all legal addresses, dirty targets, HMR phase."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from collections import Counter
import hashlib,json,sys
import numpy as np
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'gvqcc_multiform_v4'))
from independent_kmx_verifier import verify
CASES=[
('c46_public_v8.npz','run_c46_upper8'),
('C45_B129_JACOBI_OPTIMIZED.npz','run_c45b129_upper8'),
('c45_B130_postangle_PSD_physical_pass.npz','run_c45b130_upper8'),
('c45_B130_postangle_PSD_physical_pass_coupled_numeric_only.npz','run_c45b130_edited_upper8')]

def one(seed:str, folder:str, k:int):
 path=HERE/folder/f'angle_k_{k}.kmx'
 with np.load(ROOT/'gvqcc_multiform'/'seeds'/seed,allow_pickle=False) as z: words=np.array(z['angle_words'],np.int64)
 rec=verify(path,words,k,dirty_seed=942)
 rec.update(seed=seed,slot=k,bytes=path.stat().st_size,relative_kmx_path=str(path.relative_to(HERE)))
 return rec

records=[]
with ThreadPoolExecutor(max_workers=3) as pool:
 jobs=[pool.submit(one,seed,folder,k) for seed,folder in CASES for k in range(15)]
 for j in jobs:records.append(j.result())
records.sort(key=lambda x:(x['seed'],x['slot']))
with (HERE/'independent_60_verified.jsonl').open('w') as f:
 for r in records:f.write(json.dumps(r,sort_keys=True)+'\n')
aggregate={}
for seed,folder in CASES:
 sample=[r for r in records if r['seed']==seed]
 aggregate[seed]=dict(circuits=len(sample),CCX=sum(x['CCX'] for x in sample),
   CX=sum(x['CX'] for x in sample),HMR=sum(x['HMR'] for x in sample),CZ=sum(x['CZ'] for x in sample),
   Q=max(x['Q'] for x in sample),bytes=sum(x['bytes'] for x in sample),
   addresses=sample[0]['all_legal_addresses_verified'],
   source_sha256=hashlib.sha256((ROOT/'gvqcc_multiform'/'seeds'/seed).read_bytes()).hexdigest())
out=dict(scope='INDEPENDENT_SERIALIZED_KMX_BITPARALLEL_ALL_VALID_ADDRESSES; NOT FULL KICKMIX',records=len(records),groups=aggregate)
(HERE/'independent_60_summary.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
