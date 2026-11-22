#!/usr/bin/env python3
"""Query an append-only GVQCC pattern JSONL without rerunning costly physics.

Example: python query_pattern_ledger.py ledger_20261123.jsonl --family within_rank_row_permutation --rank-le 0 --top 10
"""
import argparse,csv,json,sys
from pathlib import Path


def read_records(path):
    with Path(path).open(encoding='utf-8') as f:
        for line_no,line in enumerate(f,1):
            if not line.strip(): continue
            try:r=json.loads(line)
            except ValueError as e:raise ValueError(f'{path}:{line_no}: {e}') from e
            if 'experiment_id' not in r:raise ValueError(f'{path}:{line_no}: missing experiment_id')
            yield r


def flatten(r):
    m=r.get('physics') or r.get('base_physical') or {}
    return dict(experiment_id=r['experiment_id'],pattern=r.get('pattern',''),
      seed_sha256=r.get('seed_sha256',''),
      rank_delta=r.get('GF2_bit0_rank_delta',''),
      rank_before=r.get('GF2_bit0_rank_before',''),
      rank_after=r.get('GF2_bit0_rank_after',''),
      evidence=r.get('evidence',''),
      independent_physics_pass=m.get('pass',''),
      error_1=m.get('error_1',''),error_2=m.get('error_2',''),
      E_gap=m.get('E_gap',''),lambda_eff=m.get('lambda_eff',''),
      classification=r.get('classification',''),
      action_json=json.dumps(r.get('action',{}),sort_keys=True,separators=(',',':')))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('ledger',type=Path)
    p.add_argument('--family',default='')
    p.add_argument('--seed-prefix',default='')
    p.add_argument('--rank-le',type=int)
    p.add_argument('--top',type=int,default=15)
    p.add_argument('--csv',type=Path)
    args=p.parse_args()
    rows=[]
    for rec in read_records(args.ledger):
        row=flatten(rec)
        if args.family and row['pattern']!=args.family:continue
        if args.seed_prefix and not row['seed_sha256'].startswith(args.seed_prefix):continue
        if args.rank_le is not None and (row['rank_delta']=='' or row['rank_delta']>args.rank_le):continue
        rows.append(row)
    rows.sort(key=lambda x:(float(x['rank_delta']) if x['rank_delta']!='' else float('inf'),x['experiment_id']))
    if args.csv:
        args.csv.parent.mkdir(parents=True,exist_ok=True)
        with args.csv.open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(flatten({'experiment_id':'','pattern':''}).keys()))
            w.writeheader();w.writerows(rows)
        print(f'exported={len(rows)} to {args.csv}')
    else:
        for row in rows[:args.top]:
            print(row['pattern'],str(row['rank_delta']).rjust(4),str(row['independent_physics_pass']).rjust(5),row['seed_sha256'][:8],row['experiment_id'][:10],row['action_json'])
        print(f'count={len(rows)} (showing first {min(args.top,len(rows))})')

if __name__=='__main__':main()
