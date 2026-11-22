#!/usr/bin/env python3
"""Audit every new v4 KMX from disk with independent parser and SHA. Never modify originals."""
from __future__ import annotations
import argparse,csv,glob,hashlib,json,sys
from collections import Counter,defaultdict
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from independent_kmx_verifier import verify

DATA=Path(__file__).resolve().parent
SEEDROOT=DATA.parent/'gvqcc_multiform'/'seeds'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def entries():
    tasks=[]
    for seedfile in sorted(SEEDROOT.glob('*.npz')):
        stem=seedfile.stem
        for family in ('global','pair','general'):
            root=DATA/f'{family}_{stem}'
            if not (root/'summary.json').exists():raise FileNotFoundError(root)
            records={}
            for line in (root/'experiments.jsonl').read_text().splitlines():
                rec=json.loads(line)
                if family=='global':name=rec['algorithm']
                elif family=='pair':name=rec['method'].replace('pair6-','').replace('--hmr-all-clean','')
                else:name=rec['method'].replace('general6-','')
                key=(name,int(rec['slot']))
                if key in records:raise AssertionError(('duplicate',family,stem,key))
                records[key]=rec
            for name,slot in records:
                path=root/'kmx'/name/f'angle_k_{slot}.kmx'
                if not path.exists():raise FileNotFoundError(path)
                tasks.append(dict(seed=str(seedfile),family=family,name=name,slot=slot,path=str(path),expected=records[(name,slot)]))
    return tasks


def check(task):
    path=Path(task['path']); seed=Path(task['seed']);src=task['expected']
    with np.load(seed,allow_pickle=False) as z:words=np.asarray(z['angle_words'],dtype=np.uint8)
    report=verify(path,words,task['slot'],dirty_seed=23)
    for key,src_key in (('CCX','CCX'),('CX','CX'),('Q','qubits'),('HMR','HMR'),('CZ','conditional_CZ'),('kmx_sha256','kmx_sha256')):
        assert report[key]==src[src_key],(str(path),key,report[key],src[src_key])
    rec=dict(source=seed.name,source_sha256=sha(seed),family=task['family'],variant=task['name'],slot=task['slot'],
             **report,independent_verifier_sha256=sha(Path(__file__).with_name('independent_kmx_verifier.py')),
             actual_KMX_verified=True,native_KickMix_full_verifier=False,official_score=None)
    return rec


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--workers',type=int,default=4)
    p.add_argument('--seed-root',type=Path,default=None)
    p.add_argument('--data-root',type=Path,default=None)
    args=p.parse_args()
    global DATA,SEEDROOT
    if args.seed_root is not None:SEEDROOT=args.seed_root
    if args.data_root is not None:DATA=args.data_root
    args.out.mkdir(parents=True,exist_ok=True)
    if (args.out/'independent_verified.jsonl').exists():raise FileExistsError('append-only evidence')
    tasks=entries();print('Expected KMX',len(tasks),flush=True)
    assert len(tasks)==4*(8+3+2)*15, len(tasks)
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        rows=list(pool.map(check,tasks))
    rows.sort(key=lambda z:(z['source'],z['family'],z['variant'],z['slot']))
    with (args.out/'independent_verified.jsonl').open('w') as f:
        for row in rows:f.write(json.dumps(row,sort_keys=True)+'\n')
    group=defaultdict(list)
    for row in rows:group[(row['source'],row['family'],row['variant'])].append(row)
    grouped=[]
    for (source,family,variant),rr in sorted(group.items()):
        assert len(rr)==15
        grouped.append(dict(source=source,family=family,variant=variant,n=len(rr),
                            Q=max(r['Q'] for r in rr),CCX=sum(r['CCX'] for r in rr),
                            CX=sum(r['CX'] for r in rr),HMR=sum(r['HMR'] for r in rr),CZ=sum(r['CZ'] for r in rr),
                            multi_CZ=sum(r['measurements_with_multiple_CZ'] for r in rr),
                            valid_addresses=rr[0]['all_legal_addresses_verified']))
    distinct=len(set(row['kmx_sha256'] for row in rows))
    summary=dict(records=len(rows),group_count=len(grouped),unique_kmx_hashes=distinct,
                 exact_all_addresses=True,independent_serialized_KMX_verified=True,
                 native_KickMix_full_verifier=False,physical_verification_for_current_KMX=False,
                 full_seed_SHA={r['source']:r['source_sha256'] for r in rows},
                 observed_native_score=None,group_summaries=grouped)
    (args.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    with (args.out/'groups.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(grouped[0]));w.writeheader();w.writerows(grouped)
    with (args.out/'SHA256SUMS').open('w') as f:
        for r in rows:f.write(r['kmx_sha256']+'  '+f'{r["source"]}/{r["family"]}/{r["variant"]}/angle_k_{r["slot"]}.kmx'+'\n')
    for source in sorted({r['source'] for r in rows}):
        vals=[r for r in grouped if r['source']==source]
        print(source,'n=',len(vals),'best=',[(r['family'],r['variant'],r['CCX']) for r in sorted(vals,key=lambda r:r['CCX'])[:5]],flush=True)
    print('VALIDATED',len(rows),'KMX', 'unique',distinct,flush=True)

if __name__=='__main__':main()
