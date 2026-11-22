#!/usr/bin/env python3
"""Build immutable v3 canonical ledgers and SHA manifest, ignoring interrupted run tail."""
from __future__ import annotations
import json,os,shutil,csv,glob,itertools,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'gvqcc_multiform'))
from multi_angle_synthesis import sha256
ROOT=Path(__file__).parent
DEST=ROOT/'permutation_selected_complete'
DEST.mkdir(exist_ok=False)
first=(ROOT/'permutation_selected')
second=(ROOT/'permutation_selected_b130')
third=(ROOT/'permutation_selected_b130_edited')
keep_two={'c46_public_v8.npz','C45_B129_JACOBI_OPTIMIZED.npz'}
records=[]
for loc in (first,second,third):
  for line in (loc/'experiments.jsonl').read_text().splitlines():
    if not line.strip():continue
    row=json.loads(line)
    if loc==first and row['source'] not in keep_two:continue
    src=loc/row['kmx_path']; assert sha256(src)==row['kmx_sha256']
    dst=DEST/row['kmx_path'];dst.parent.mkdir(parents=True,exist_ok=True)
    os.link(src,dst)
    assert sha256(dst)==row['kmx_sha256']
    records.append(row)
keys=[(r['source'],tuple(r['low_wires']),r['slot']) for r in records]
assert len(records)==360 and len(set(keys))==360,(len(records),len(set(keys)))
with (DEST/'experiments.jsonl').open('w') as f:
  for x in records:f.write(json.dumps(x,sort_keys=True)+'\n')
groups={}
for r in records:
  key=(r['source'],r['method'])
  agg=groups.setdefault(key,dict(source=r['source'],method=r['method'],low_wires=r['low_wires'],Q_peak=0,CCX=0,CX=0,X=0,HMR=0,slots=0))
  for k in ('CCX','CX','X','HMR'):agg[k]+=r[k]
  agg['Q_peak']=max(agg['Q_peak'],r['Q']);agg['slots']+=1
summ=sorted(groups.values(),key=lambda a:(a['source'],a['CCX']))
assert len(summ)==24 and all(g['slots']==15 for g in summ)
for g in summ:g['Q_times_CCX_proxy']=g['Q_peak']*g['CCX']
(DEST/'summary.json').write_text(json.dumps(dict(schema='gvqcc.perm6.complete.v1',records=360,groups=summ,official_verifier_executed=False,first_half_from_interrupted_run='only 180 complete entries, 4 incomplete-tail entries excluded'),indent=2)+'\n')
with (DEST/'comparisons.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(summ[0]));w.writeheader();w.writerows(summ)
SCREEN=ROOT/'screen_c46_462.jsonl'
perms=[]
for file in sorted(ROOT.glob('permutation_screen_c46_*.jsonl')):
 for line in file.read_text().splitlines():
  if line.strip():perms.append(json.loads(line))
assert len(perms)==462 and set(a['subset_index'] for a in perms)==set(range(462))
perms.sort(key=lambda a:a['subset_index'])
with SCREEN.open('w') as f:
 for r in perms:f.write(json.dumps(r,sort_keys=True)+'\n')
print('EXHAUSTIVE462',len(perms),'BEST', sorted((x['CCX_per_pass'],x['low_wires']) for x in perms)[:5])
with (DEST/'SHA256SUMS').open('w') as f:
 for p in sorted(DEST.rglob('*')):
  if p.is_file() and p.name!='SHA256SUMS':f.write(f'{sha256(p)}  {p.relative_to(DEST)}\n')
print('COMPLETE',len(records),'KMX exact hashes pass','GROUPS',len(summ))
