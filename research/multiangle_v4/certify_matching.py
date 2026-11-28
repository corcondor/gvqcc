#!/usr/bin/env python3
"""Independent finite-class optimality certificate for disjoint high selector pairs.

Uses direct ANF nonconstant output-rank for each 64x35 cofactor block, NOT
compiler's emitted product list. Then performs exact subset DP, independently
of NetworkX maximum weight matching. This certifies only the chosen restricted
selector-pair class; it does NOT lower-bound unrestricted XAG complexity.
"""
from __future__ import annotations
import argparse, functools, json, sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
BASE=ROOT/'gvqcc_multiform' if (ROOT/'gvqcc_multiform').exists() else ROOT
V3=ROOT/'gvqcc_multiform_v3' if (ROOT/'gvqcc_multiform_v3').exists() else ROOT/'multiangle_v3'
sys.path[:0]=[str(BASE),str(V3),str(HERE)]
from multi_angle_synthesis import delta_table,word_masks
from global_cofactor import discover_global


def rank(vals):
 piv={}
 for item in vals:
  x=int(item)
  while x:
   p=x.bit_length()-1
   if p in piv:x^=piv[p]
   else:piv[p]=x;break
 return len(piv)


def mobius64(vec):
 x=list(vec)
 for bit in range(6):
  for j in range(64):
   if j>>bit&1:x[j]^=x[j^(1<<bit)]
 return x


def nonconstant_rank(rows):
 return rank(mobius64(rows)[1:])


def independent_matching_limit(w:np.ndarray,slot:int):
 data=word_masks(delta_table(w,slot))
 low,cert=discover_global(data,6,'canonical')
 n=(len(data)+63)//64
 groups=[[int(x)^low[j] for j,x in enumerate(data[h*64:h*64+64])]+[0]*max(0,64-len(data[h*64:h*64+64])) for h in range(n)]
 r=[nonconstant_rank(x) for x in groups]
 weights={}
 for i in range(n):
  for j in range(i+1,n):
   if (i&7)!=(j&7) and (i>>3)!=(j>>3):continue
   diff=[a^b for a,b in zip(groups[i],groups[j])]
   gain=max(r[i],r[j])-nonconstant_rank(diff)
   if gain>0:weights[i,j]=gain
 @functools.lru_cache(None)
 def rec(mask):
  if mask==0:return 0
  pivot=(mask&-mask).bit_length()-1
  rem=mask ^ (1<<pivot)
  best=rec(rem)
  for j in range(pivot+1,n):
   if (rem>>j)&1 and (pivot,j) in weights:
    best=max(best,weights[pivot,j]+rec(rem^(1<<j)))
  return best
 return dict(max_matching_gain=rec((1<<n)-1),candidate_edges=len(weights),
             independent_base_paid=sum(r),high_blocks=n,
             active_global_parities=cert['active_global_parities'])


def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--seeds',nargs='+',type=Path,required=True)
 p.add_argument('--out',type=Path,required=True)
 p.add_argument('--data-root',type=Path,default=HERE)
 args=p.parse_args();records=[]
 for seed in args.seeds:
  with np.load(seed,allow_pickle=False) as z:w=np.asarray(z['angle_words'],np.int64)
  stem=seed.stem
  repo=args.data_root/f'pair_{stem}'/'experiments.jsonl'
  source=[json.loads(x) for x in repo.read_text().splitlines()]
  selected={int(x['slot']):x for x in source if x['method']=='pair6-exact-paid--hmr-all-clean'}
  assert len(selected)==15
  for k in range(15):
   r=independent_matching_limit(w,k)
   claimed=selected[k]['predicted_rank_gain']
   if r['max_matching_gain']!=claimed:
    raise AssertionError((seed.name,k,r['max_matching_gain'],claimed))
   records.append(dict(source=seed.name,slot=k,**r,chosen_matching_gain=claimed,independent_certificate='PASS'))
  print(seed.name,sum(x['max_matching_gain'] for x in records if x['source']==seed.name),flush=True)
 args.out.write_text(json.dumps(dict(schema='gvqcc.cheap_highpair_dp.v1',
             theorem_scope='exact optimum within disjoint cheap high-pair basis class; NOT global circuit optimum',
             matches_networkx_all=True,results=records),indent=2)+'\n')
if __name__=='__main__':main()
