#!/usr/bin/env python3
"""Screen global 20-high-state GF(2) basis changes with selector matrix-rank pricing.

This is a STRUCTURAL SCREEN only. A basis of high cofactors G=M F costs paid
low ANDs; the high selectors are columns of M^{-1}. Any resulting selector
is an 8x3 GF(2) matrix and requires rank(E) nonlinear products of one-hot
high A/B factors. Unlike fixed-upper group bases, this selector pricing
is coupled across basis choices, so weighted greedy is NOT globally optimal.
"""
import argparse, hashlib, itertools, json, math, sys,time
from pathlib import Path
from collections import Counter
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from high_group_basis import (inverse_rows,cf_cost,group_candidates,group_candidates as can, xor_coeff)
ROOT=Path(__file__).resolve().parents[1]
for local,hosted in [('gvqcc_multiform','gvqcc_multiform'),('gvqcc_multiform_v3','multiangle_v3'),('gvqcc_multiform_v4','multiangle_v4')]:
 d=ROOT/(local if (ROOT/local).exists() else hosted)
 sys.path.insert(0,str(d))
from multi_angle_synthesis import delta_table,word_masks,rank_output_basis
from partition_patterns import mobius
from global_cofactor import discover_global

def high_selector_rank(mask:int)->int:
 """GF(2) rank of 8x3 high-selector truth matrix: minimal number
 of products (A-selector linear form)*(B-selector linear form)."""
 cols=[]
 for j in range(3):
  v=(mask>>(8*j))&255
  if v:cols.append(v)
 pivots={}
 for col in cols:
  v=col
  while v:
   p=v.bit_length()-1
   if p in pivots:v^=pivots[p]
   else:pivots[p]=v;break
 return len(pivots)


def greedy_basis(rows,global_mode='canonical',max_support=3,criterion='pure'):
 low,_=discover_global(rows,6,global_mode) if global_mode else ([0]*64,{})
 H=math.ceil(len(rows)/64)
 groups=[[int(v)^low[j] for j,v in enumerate(rows[i*64:(i+1)*64])]+[0]*(64-len(rows[i*64:(i+1)*64])) for i in range(H)]
 coeff=[tuple(mobius(x,6)) for x in groups]
 cand=[]
 for cnt in range(1,max_support+1):
  for inds in itertools.combinations(range(H),cnt):
   merged=(0,)*64
   mask=0
   for i in inds:
    merged=xor_coeff(merged,coeff[i]);mask|=1<<i
   cost,paid,_=cf_cost(merged)
   # Heuristic sort: local output cost plus support penalty.
   score=(cost+(max(0,cnt-1)*(.0 if criterion=='pure' else .25)))
   cand.append((score,cost,paid,cnt,mask,merged))
 cand.sort(key=lambda x:(x[0],x[3],x[4]))
 pivots={};selected=[]
 for x in cand:
  v=x[4]
  while v:
   p=v.bit_length()-1
   if p in pivots:v^=pivots[p]
   else:pivots[p]=v;selected.append(x);break
  if len(selected)==H:break
 assert len(selected)==H
 inv=inverse_rows([x[4] for x in selected],H)
 selectors=[sum(((inv[i]>>j)&1)<<i for i in range(H)) for j in range(H)]
 ranks=[high_selector_rank(s) for s in selectors]
 paid=sum(x[2] for x in selected)
 base_paid=sum(cf_cost(c)[1] for c in coeff)
 base_nonzero=sum(bool(cf_cost(c)[0]) for c in coeff)
 cost_est_relaxed=paid+sum(ranks)
 cost_est_conservative=paid+sum(r if r==1 else 2*r for r in ranks)
 base_cost=base_paid+base_nonzero
 return dict(H=H,weighted_candidate_count=len(cand),base_cost=base_cost,
             new_low_products=paid,base_low_products=base_paid,
             high_selector_rank_total=sum(ranks),
             high_selector_rank_hist=dict(Counter(ranks)),
             predicted_relaxed_gain=base_cost-cost_est_relaxed,
             predicted_conservative_gain=base_cost-cost_est_conservative,
             cost_est_relaxed=cost_est_relaxed,cost_est_conservative=cost_est_conservative,
             chosen_high_cofactor_masks=[hex(x[4]) for x in selected],
             inverse_selector_masks=[hex(x) for x in selectors],
             chosen_support_hist=dict(Counter(x[3] for x in selected)))

def main():
 p=argparse.ArgumentParser()
 p.add_argument('--seeds',type=Path,nargs='+',required=True)
 p.add_argument('--out',type=Path,required=True)
 p.add_argument('--slots',default='all')
 a=p.parse_args();a.out.parent.mkdir(parents=True,exist_ok=True)
 res=[]
 for fp in a.seeds:
  with np.load(fp,allow_pickle=False) as z:words=np.array(z['angle_words'],dtype=np.int64)
  sha=hashlib.sha256(fp.read_bytes()).hexdigest()
  for k in (list(range(15)) if a.slots=='all' else [int(x) for x in a.slots.split(',')]):
   rows=word_masks(delta_table(words,k))
   for maxs in (2,3):
    for method in ('pure','support'):
     start=time.monotonic()
     r=greedy_basis(rows,'canonical',maxs,method)
     r.update(seed=fp.name,seed_sha256=sha,slot=k,max_support=maxs,heuristic=method,
              seconds=round(time.monotonic()-start,4),
              caveat='greedy basis ignores coupled selector rank until after choice; screen only')
     res.append(r)
     print(fp.name,k,maxs,method,'baseline',r['base_cost'],'new',r['cost_est_conservative'],
           'rankHist',r['high_selector_rank_hist'],flush=True)
  print('SEED_COMPLETE',fp.name,flush=True)
 with a.out.open('w') as f:
  for r in res:f.write(json.dumps(r,sort_keys=True)+'\n')
 print('WROTE',a.out,len(res),flush=True)
if __name__=='__main__':main()
