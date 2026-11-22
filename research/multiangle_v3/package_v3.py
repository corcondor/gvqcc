#!/usr/bin/env python3
"""Package source + ledgers, optionally all 2100 concrete KMX, reproducibly."""
from __future__ import annotations
import argparse,hashlib,zipfile,json,sys
from pathlib import Path
root=Path(__file__).resolve().parent
folders=['results_v3_c46','results_v3_c45b129','results_v3_c45b130','results_v3_c45b130_edited',
'partition_c46','partition_c45b129','partition_c45b130','partition_c45b130_edited','permutation_selected_complete']
code=['hmr_patterns.py','affine_patterns.py','partition_patterns.py','permutation_patterns.py',
'run_patterns.py','run_partitions.py','run_perm_selected.py','scan_permutations.py',
'consolidate.py','build_master.py','package_v3.py','test_new_patterns.py','test_partition_and_permutation.py']
header=['REPORT_JA.md','MASTER_SUMMARY.json','GROUP_COMPARISONS.csv','ALL_KMX_SHA256.jsonl','screen_c46_462.jsonl','FILE_INDEX_SHA256']
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--full',action='store_true');a=p.parse_args()
items=[]
for f in code+header:items.append((root/f,'gvqcc_multiform_v3/'+f))
base=root.parent/'gvqcc_multiform'/'multi_angle_synthesis.py'
items.append((base,'gvqcc_multiform/multi_angle_synthesis.py'))
for fp in sorted((root.parent/'gvqcc_multiform'/'seeds').glob('*.npz')):items.append((fp,'seeds/'+fp.name))
for folder in folders:
 for fname in ('experiments.jsonl','summary.json','comparisons.csv','SHA256SUMS'):
  pth=root/folder/fname
  if pth.exists():items.append((pth,'gvqcc_multiform_v3/'+folder+'/'+fname))
 if a.full:
  for fp in sorted((root/folder/'kmx').rglob('*.kmx')):
   items.append((fp,'gvqcc_multiform_v3/'+folder+'/'+str(fp.relative_to(root/folder))))
 else:
  # preserve genuine KMX examples of the strongest partition and the most
  # algebraically different variants for every physical input.
  for fp in sorted((root/folder/'kmx').rglob('*.kmx')):
   if fp.stem not in ('angle_k_0','angle_k_7','angle_k_14'):continue
   if folder.startswith('results_v3_') and not any(x in str(fp) for x in ('--hmr-all-clean','affine-mix')):continue
   if folder.startswith('partition_') and not any(x in str(fp) for x in ('partition6-basis','partition5-basis')):continue
   if folder=='permutation_selected_complete' and not any(x in str(fp) for x in ('perm6-012345','perm6-012347')):continue
   items.append((fp,'gvqcc_multiform_v3/'+folder+'/'+str(fp.relative_to(root/folder))))
assert len({x[1] for x in items})==len(items)
with zipfile.ZipFile(a.output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=4,allowZip64=True) as z:
 for i,(fp,arcname) in enumerate(items):
  z.write(fp,arcname)
  if i%250==0:print('packed',i,'/',len(items),flush=True)
with zipfile.ZipFile(a.output) as z:
 names=set(z.namelist())
 assert len(names)==len(items)
 assert 'gvqcc_multiform_v3/REPORT_JA.md' in names
 assert len([x for x in names if x.endswith('.kmx')])==(2100 if a.full else len([x for x in names if x.endswith('.kmx')]))
 digest=hashlib.sha256(a.output.read_bytes()).hexdigest()
 print(json.dumps(dict(path=str(a.output),entries=len(names),kmx=sum(x.endswith('.kmx') for x in names),bytes=a.output.stat().st_size,sha256=digest),indent=2))
