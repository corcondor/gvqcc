#!/usr/bin/env python3
"""Identify adjacent GF kernels that can be co-synthesized as bilinear tensor blocks.

Tracks products from a first 42-CCX motif as independent formal atoms,
propagating them exactly through linear CX gates up to controls of the next
42-CCX motif. This is a structural dependency test, not a proof of savings.
"""
from __future__ import annotations
import argparse, hashlib, json
from collections import Counter
from pathlib import Path
import numpy as np
from dqi_kernel_motif_audit import arrays_from_kmb, canonical_ccx

def scan(path, limit=None):
 h,a=arrays_from_kmb(path)
 op,q30,q31,q32,q20,q21,*_=a
 p3=np.flatnonzero((op & 0x30)==0x30)
 mm=op[p3]==0x31;pc=p3[mm]
 c0,c1,t=q30[mm],q31[mm],q32[mm]
 cand=np.arange(len(pc)-41,dtype=np.int32)
 cand=cand[(t[cand]==t[cand+1])&(c0[cand]==c0[cand+3])&(c1[cand]==c1[cand+3])&(c0[cand]==c0[cand+4])&(c1[cand]==c1[cand+4])]
 ref=canonical_ccx(0,c0,c1,t)
 hits=np.array([i for i in cand if canonical_ccx(int(i),c0,c1,t)==ref],dtype=np.int32)
 p2=np.flatnonzero((op&0x30)==0x20)
 ix=np.flatnonzero(np.diff(hits)==42)
 pairs=[(int(pc[hits[k]]),int(pc[hits[k+1]])) for k in ix
     if np.all(op[int(pc[hits[k]]+1293):int(pc[hits[k+1]])]==0x21)]
 if limit is not None:pairs=pairs[:limit]
 counts=Counter();examples=[]
 for start,end in pairs:
  dep=[0]*h['qubits']
  ii2=int(np.searchsorted(p2,start));ii3=int(np.searchsorted(p3,start)); cc=0
  affected=0
  for i in range(start,end+1293):
   v=int(op[i])
   if v==0x21:
    a1,b1=int(q20[ii2]),int(q21[ii2]);ii2+=1
    dep[b1]^=dep[a1]
   elif v==0x31:
    a1,b1,z=map(int,(q30[ii3],q31[ii3],q32[ii3]));ii3+=1
    if i<start+1293:
     if dep[a1] or dep[b1]:raise RuntimeError('First motif internally uses earlier CCX value')
     dep[z]^=1<<cc
     cc+=1
    else:
     if dep[a1] or dep[b1]:affected+=1
     dep[z]^=1 << cc
     cc+=1
   else:raise RuntimeError(f'Unexpected opcode {v:#x} inside pair')
  if cc!=84:raise RuntimeError('bad motif pair')
  key='bilinear_pair' if affected==0 else 'nonlinear_dependency_pair'
  counts[key]+=1
  counts['second_ccx_controls_dependent_on_first_products']+=affected
  if len(examples)<15 and (affected and len([x for x in examples if x['dependent_ccx']])<5 or not affected and len([x for x in examples if not x['dependent_ccx']])<5):
   examples.append({'first_start':start,'second_start':end,'dependent_ccx':affected,'gap_length':end-start-1293})
 return {'motif_total':len(hits),'cx_only_pairs_scanned':len(pairs),'counts':dict(counts),'examples':examples,
         'method':'Exact symbolic XOR propagation of formal CCX product tokens from first motif; second input CCX controls dependent on any first product token imply pair cannot be naively represented as a bilinear map of initial wires.',
         'caution':'A zero dependency is necessary but not sufficient for cost improvement, entry contracts, all scratch restoration or quantum phase equivalence.'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('kmb',type=Path);p.add_argument('--limit',type=int);p.add_argument('-o','--output',type=Path);x=p.parse_args()
 r=scan(x.kmb,x.limit);s=json.dumps(r,indent=2,sort_keys=True)+'\n'
 if x.output:x.output.write_text(s)
 print(s)
