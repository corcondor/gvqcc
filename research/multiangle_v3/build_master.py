#!/usr/bin/env python3
"""Aggregate immutable experiment folders and write global machine-readable index."""
from pathlib import Path
import json,csv,hashlib,sys,shutil,os
root=Path(__file__).resolve().parent
folders=[root/x for x in ('results_v3_c46','results_v3_c45b129','results_v3_c45b130','results_v3_c45b130_edited',
'partition_c46','partition_c45b129','partition_c45b130','partition_c45b130_edited','permutation_selected_complete')]
summ=[];totals=0;uids=set();listing=[]
for folder in folders:
 lines=(folder/'experiments.jsonl').read_text().splitlines()
 records=[json.loads(s) for s in lines if s.strip()]
 print(folder.name,len(records));totals+=len(records)
 for r in records:
  ex=r['experiment_id'];assert ex not in uids;uids.add(ex)
  name=r.get('kmx_path')
  if name:
   fp=folder/name
   actual=hashlib.sha256(fp.read_bytes()).hexdigest()
   assert actual == r['kmx_sha256'],(name,actual,r['kmx_sha256'])
   listing.append(dict(folder=folder.name,source=r['source'],method=r['method'],slot=r['slot'],file=name,
                       sha256=actual,bytes=fp.stat().st_size))
 info=json.load((folder/'summary.json').open())
 summ+=info['groups']
assert totals==2100 and len(listing)==2100
master=dict(schema='gvqcc.multiform.v3.master',num_circuits=totals,sha_records=len(listing),
    num_physical_seeds=4,method_classes=35,method_settings=list(sorted(set(x['method'] for x in summ))),
    group_summaries=summ,source_folders=[p.name for p in folders],
    c46_permutation_candidates=462,c46_permutation_screen_file='screen_c46_462.jsonl',
    value_proof='All valid legal addresses for each NPZ, two independent dirty target seeds',
    phase_proof='For HMR variants all measurement symbols canceled exactly',
    native_KickMix_full_verifier=False,official_score=None,
    previous_four_baseline_methods_not_counted_in_2100=True)
(root/'MASTER_SUMMARY.json').write_text(json.dumps(master,indent=2,ensure_ascii=False)+'\n')
with (root/'ALL_KMX_SHA256.jsonl').open('w') as f:
 for rec in listing:f.write(json.dumps(rec,sort_keys=True)+'\n')
with (root/'GROUP_COMPARISONS.csv').open('w',newline='') as f:
 fields=['source','method','Q_peak','CCX','CX','X','HMR','conditional_CZ','Q_times_CCX_proxy']
 w=csv.DictWriter(f,fields,extrasaction='ignore');w.writeheader()
 for rec in summ:
  w.writerow({key:rec.get(key,'') for key in fields})
# Raw 462 subset-cost screen has a corresponding exact emitted CCX formula.
with (root/'FILE_INDEX_SHA256').open('w') as f:
 for p in sorted([root/'REPORT_JA.md',root/'MASTER_SUMMARY.json',root/'GROUP_COMPARISONS.csv',root/'ALL_KMX_SHA256.jsonl',root/'screen_c46_462.jsonl',
                  *[root/x for x in ('hmr_patterns.py','affine_patterns.py','partition_patterns.py','permutation_patterns.py','run_patterns.py','run_partitions.py','run_perm_selected.py','scan_permutations.py','consolidate.py','test_new_patterns.py','test_partition_and_permutation.py')]]):
  f.write(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n')
print('MASTER',totals,'KMX HASHES',len(listing),'groups',len(summ),'methods',len(master['method_settings']))
