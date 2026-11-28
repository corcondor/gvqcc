#!/usr/bin/env python3
"""Compile exact selected low6 wire subsets after 462-choice cost screen."""
import argparse,hashlib,json,csv,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'gvqcc_multiform'))
from permutation_patterns import compile_perm,estimate
from partition_patterns import convert_hmr
from hmr_patterns import prove
from multi_angle_synthesis import delta_table,sha256
CHOSEN=((0,1,2,3,4,5),(0,1,2,3,4,7),(0,1,2,3,4,6),
        (2,3,4,5,6,7),(0,2,4,6,8,10),(1,3,7,8,9,10))
p=argparse.ArgumentParser();p.add_argument('--seeds',nargs='+',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
a.out.mkdir(parents=True,exist_ok=False);(a.out/'kmx').mkdir()
source_scripts={x.name:sha256(x) for x in [Path(__file__),Path(__file__).parent/'permutation_patterns.py',Path(__file__).parent/'partition_patterns.py']}
records=0;groups=[]
with (a.out/'experiments.jsonl').open('w') as f:
 for path in a.seeds:
  words=np.load(path,allow_pickle=False)['angle_words']
  origsha=sha256(path)
  for low in CHOSEN:
   name='perm6-'+''.join(map(str,low));group=dict(source=path.name,method=name,low_wires=list(low),slots=0,Q_peak=0,CCX=0,CX=0,X=0,HMR=0)
   for slot in range(15):
    c,s=compile_perm(words,slot,low)
    m,ms=convert_hmr(c,s)
    for dirty in (7,314):
     cert=prove(m,delta_table(words,slot),dirty)
     assert cert['scratch_clean'] and cert['all_HMR_phase_symbols_cancel']
    assert ms['CCX']==estimate(words,slot,low)['total_ccx_after_hmr']
    target=a.out/'kmx'/path.stem/name/f'angle_k_{slot}.kmx';target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('w') as fw:
     for line in m.kmx_lines():fw.write(line+'\n')
    rec=dict(schema='gvqcc.perm6.selected.v1',source=path.name,source_sha256=origsha,
       script_sha256=source_scripts,method=name,slot=slot,low_wires=list(low),
       Q=ms['qubits'],CCX=ms['CCX'],CX=ms['CX'],X=ms['X'],HMR=ms['HMR'],
       kmx_path=str(target.relative_to(a.out)),kmx_sha256=sha256(target),
       proof_all_legal_addresses=True,scratch_and_tags_clean=True,all_HMR_phases_cancel=True,
       official_KickMix_verified=False,new_score=None)
    rec['experiment_id']=hashlib.sha256(f'{origsha}|{name}|{slot}|{json.dumps(source_scripts,sort_keys=True)}'.encode()).hexdigest()
    f.write(json.dumps(rec,sort_keys=True)+'\n');f.flush()
    records+=1;group['slots']+=1;group['Q_peak']=max(group['Q_peak'],ms['qubits'])
    for k in ('CCX','CX','X','HMR'):group[k]+=ms[k]
   group['Q_times_CCX_proxy']=group['Q_peak']*group['CCX']
   groups.append(group)
   print(path.name,name,'CCX',group['CCX'],'Q',group['Q_peak'],flush=True)
groups.sort(key=lambda x:(x['source'],x['CCX']))
(a.out/'summary.json').write_text(json.dumps(dict(schema='gvqcc.perm6.selected.summary.v1',records=records,groups=groups,scripts=source_scripts,proof='all valid addresses; both dirty target seeds; every HMR phase symbol 0',official_score=None),indent=2)+'\n')
with (a.out/'comparisons.csv').open('w',newline='') as f:
 cols=list(groups[0]);w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(groups)
with (a.out/'SHA256SUMS').open('w') as f:
 for path in sorted(a.out.rglob('*')):
  if path.is_file() and path.name!='SHA256SUMS':f.write(f'{sha256(path)}  {path.relative_to(a.out)}\n')
print('COMPLETE',records,'ALL_CHECKS_PASS')
