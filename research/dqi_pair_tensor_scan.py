#!/usr/bin/env python3
"""Materialize quadratic tensor factors and shared exit directions in 42T+42T pairs.

Reports syntactic identities/collisions, not an executable rewrite, semantic
admissibility in the enclosing circuit, or any score improvement.
"""
from __future__ import annotations
import argparse, json
from collections import Counter
from pathlib import Path
import numpy as np
from dqi_kernel_motif_audit import arrays_from_kmb,canonical_ccx

def scan(path,limit=None):
 h,v=arrays_from_kmb(path);op,q30,q31,q32,q20,q21,*_=v
 p3=np.flatnonzero((op&48)==48);m=op[p3]==49;pc=p3[m];a,b,t=q30[m],q31[m],q32[m]
 cand=np.arange(len(pc)-41,dtype=np.int32);cand=cand[(t[cand]==t[cand+1])&(a[cand]==a[cand+3])&(b[cand]==b[cand+3])&(a[cand]==a[cand+4])&(b[cand]==b[cand+4])]
 ref=canonical_ccx(0,a,b,t)
 hits=np.array([i for i in cand if canonical_ccx(int(i),a,b,t)==ref],dtype=np.int32)
 ix=np.flatnonzero(np.diff(hits)==42)
 pairs=[(int(pc[hits[k]]),int(pc[hits[k+1]])) for k in ix if np.all(op[int(pc[hits[k]]+1293):int(pc[hits[k+1]])]==33)]
 if limit is not None:pairs=pairs[:limit]
 p2=np.flatnonzero((op&48)==32);cnt=Counter();evidence=[]
 for start,end in pairs:
  aff=[1<<w for w in range(h['qubits'])];dep=[0]*h['qubits'];terms=[];nonlinear=False
  i2=int(np.searchsorted(p2,start));i3=int(np.searchsorted(p3,start))
  for i in range(start,end+1293):
   if op[i]==33:
    x,y=int(q20[i2]),int(q21[i2]);i2+=1;aff[y]^=aff[x];dep[y]^=dep[x]
   elif op[i]==49:
    x,y,z=int(q30[i3]),int(q31[i3]),int(q32[i3]);i3+=1
    if dep[x] or dep[y]:nonlinear=True
    terms.append((aff[x],aff[y]));dep[z]^=1<<(len(terms)-1)
   else:raise RuntimeError((i,int(op[i])))
  assert len(terms)==84
  if nonlinear:
   cnt['nonlinear_pairs']+=1;continue
  cnt['bilinear_pairs']+=1
  dirs=[0]*84
  for w,mask in enumerate(dep):
   while mask:
    bit=mask&-mask;j=bit.bit_length()-1;dirs[j]|=1<<w;mask^=bit
  triples=list(zip(terms,dirs))
  count_directions=len(set(dirs));cnt['direction_uniques_total']+=count_directions
  basis={}
  for vector in dirs:
   while vector:
    hi=vector.bit_length()-1
    if hi in basis:vector^=basis[hi]
    else:
     basis[hi]=vector
     break
  rank=len(basis)
  cnt[f'output_linear_rank_{rank}']+=1
  cnt[f'outputs_{count_directions}_rank_{rank}']+=1
  if count_directions<84:cnt['repeated_direction_pairs']+=1
  same_full=0;factor_same_output=0;product_shared_diff_out=0
  for j,(pr,d) in enumerate(triples):
   x,y=pr
   for pr2,d2 in triples[:j]:
    x2,y2=pr2
    fs={x,y}&{x2,y2};sameProduct=(x==x2 and y==y2) or (x==y2 and y==x2)
    if d==d2 and sameProduct:same_full+=1
    elif d==d2 and fs:factor_same_output+=1
    if d!=d2 and sameProduct:product_shared_diff_out+=1
  cnt['duplicate_identical_terms']+=same_full
  cnt['shared_factor_same_direction_pairs']+=factor_same_output
  cnt['shared_product_different_direction_pairs']+=product_shared_diff_out
  if (same_full or factor_same_output or product_shared_diff_out or count_directions<84) and len(evidence)<30:
   evidence.append(dict(first_start=start,second_start=end,distinct_exit_directions=count_directions,exact_duplicates=same_full,same_direction_factor_shares=factor_same_output,same_product_different_direction=product_shared_diff_out))
 return {'pairs_scanned':len(pairs),'counts':dict(cnt),'evidence':evidence,
         'note':'Affine masks are complete in 890 independent entry variables. All quadratic product atoms are propagated to an exit common GF(2) direction. No optimization proven by equal source wire numbers alone.'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('kmb',type=Path);p.add_argument('--limit',type=int);p.add_argument('-o','--output',type=Path);x=p.parse_args()
 r=scan(x.kmb,x.limit);s=json.dumps(r,indent=2,sort_keys=True)+'\n'
 if x.output:x.output.write_text(s)
 print(s)
