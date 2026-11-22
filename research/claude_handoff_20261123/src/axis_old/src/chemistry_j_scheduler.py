#!/usr/bin/env python3
"""Exact-word chemistry ANGLE rescheduling for J=3/4/5 with topological legality.
Uses GF(2) matrix ranks of actual 1219-row, 7-bit XOR-delta truth tables as a fast prefilter.
These ranks are *not* full Toffoli synthesis; reports never call them scores.
"""
import argparse, math, json, time, hashlib, heapq
from pathlib import Path
import numpy as np

NADDR=1219

def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def mobius(x,axis):
 x=np.moveaxis(x,axis,0).copy();n=x.shape[0];s=1
 while s<n:
  lo=np.arange(n,dtype=np.int32)
  ix=lo[(lo&s)>0];x[ix]^=x[ix^s];s*=2
 return np.moveaxis(x,0,axis)

def multiout_perbit_ranks(w, low=4):
 # w: (rows, J) uint8 bytes (0..127). For correct 7-bit words, no signed-bit assumptions.
 A,J=w.shape;L=1<<low;H=(A+L-1)//L;hbits=max(1,(H-1).bit_length());
 truth=np.zeros((1<<hbits,L,J*7),dtype=np.uint8)
 for j in range(J):
  for b in range(7):truth.reshape(-1,J*7)[:A,j*7+b]=(w[:,j]>>b)&1
 C=mobius(mobius(truth,0),1)[:H]
 # Need matrices of shape (L-1,H-1) for each output; rank is a provable lower bound on bilinear products for one output
 X=C[1:,1:];ranks=[];nfeatures=0
 for o in range(J*7):
  rows=[]
  for a in range(L-1):
   v=0
   for b in range(H-1):
    if X[b,a,o]:v|=1<<b
   rows.append(v)
  piv={}; rank=0
  for v in rows:
   while v:
    lead=v.bit_length()-1
    if lead in piv:v^=piv[lead]
    else:piv[lead]=v;rank+=1;break
  ranks.append(rank)
 return ranks

def delta_for(schedule,W,J,k):
 A=len(W);total=len(schedule);curr=np.zeros((A,J),dtype=np.uint8)
 for j in range(J):
  i=k*J+j
  if i<total:curr[:,j]=W[:,schedule[i]]
  if k>0:
   prev=(k-1)*J+j
   if prev<total:curr[:,j]^=W[:,schedule[prev]]
 return curr

def register_profile(schedule,W,J):
 costs=[]; nr=(len(schedule)+J-1)//J
 for k in range(nr):
  r=multiout_perbit_ranks(delta_for(schedule,W,J,k))
  # Lower bound for isolated bit-plane synth; not an achievable joint total nor a bound on multi-output schemes.
  costs.append(sum(r))
 return costs

def score(sched,W,J):return sum(register_profile(sched,W,J))

def decode(W,E):
 v=np.zeros((W.shape[0],76),dtype=np.float64);v[:,0]=1
 for t,(a,b) in enumerate(E):
  th=np.pi*W[:,t]/64;co=np.cos(th);si=np.sin(th);aa=v[:,a].copy();bb=v[:,b].copy();v[:,a]=co*aa-si*bb;v[:,b]=si*aa+co*bb
 return v

def run(p):
 src=Path(p.source);out=Path(p.out);out.mkdir(parents=True,exist_ok=True)
 with np.load(src,allow_pickle=False) as z:d={k:z[k].copy() for k in z.files}
 W=np.asarray(d['angle_words'],dtype=np.uint8);E=np.asarray(d['tree_edges'],dtype=np.int64);assert W.shape[1]==75 and E.shape==(75,2)
 direct={J:register_profile(list(range(75)),W,J) for J in (3,4,5)}
 # Optimize scheduled J=4 and J=5 with pairwise valid swaps, exact touched bank recompute only.
 pred=np.zeros(75,dtype=object)
 for j in range(75):
  pred[j]=sum(1<<i for i in range(j) if E[i,0] in E[j] or E[i,1] in E[j])
 rng=np.random.default_rng(p.seed)
 solutions={}
 for J in (4,5):
  best=list(range(75));costs=direct[J].copy();bv=sum(costs);history=[]
  for it in range(p.iterations):
   x=best.copy() if it<20 or rng.random()<.65 else list(range(75))
   r=int(rng.integers(0,75));j=int(np.clip(r+int(rng.integers(-14,15)),0,74))
   if r==j:continue
   elem=x.pop(r);x.insert(j,elem)
   # Verify topological order by all predecessor masks.
   done=0;legal=True
   for q in x:
    if pred[q]&~done:legal=False;break
    done |= 1<<q
   if not legal:continue
   affected={k for pos in range(min(r,j),max(r,j)+1) for k in (pos//J,(pos+J)//J) if k<len(costs)}
   newcosts=costs.copy()
   for k in affected:newcosts[k]=sum(multiout_perbit_ranks(delta_for(x,W,J,k)))
   v=sum(newcosts)
   if v<bv:
    best=x;bv=v;costs=newcosts
    history.append(dict(iteration=it,new_rank_sum=bv,changed_positions=sum(i!=q for i,q in enumerate(best))))
  # commuting rotations: decoded output must match exactly regardless of order
  base=decode(W,E);chg=decode(W[:,best],E[best])
  err=float(np.max(np.abs(chg-base)))
  assert err<1e-12
  solutions[J]={'baseline_rank_sum':sum(direct[J]),'best_rank_sum':bv,'baseline_bank_sums':direct[J], 'best_bank_sums':costs, 'changed_positions':sum(i!=q for i,q in enumerate(best)),'permutation':best,'max_abs_vector_diff':err,'history':history}
  dd=dict(d);dd['angle_words']=d['angle_words'][:,best].copy();dd['tree_edges']=E[best].copy()
  np.savez_compressed(out/f'chem_schedule_J{J}_SAME_SHAPE_RESEARCH.npz',**dd)
  print('CHEM J',J,'base ranks',sum(direct[J]),'best ranks',bv,'changes',len(history),'Uerr',err,flush=True)
 rec={'kind':'REAL_TRUTH_TABLE_RANK_AND_COMMUTING_TREE_SCHEDULE_SEARCH','source_sha256':sha(src),'RBC':list(d['W'].shape),'rows':W.shape[0],'input_words':75,'baseline':{str(j):direct[j] for j in direct},'search':{str(j):sol for j,sol in solutions.items()},'limitations':['Sum of individual-bit bilinear ranks is a proxy, not exact multi-output XAG cost or Toffoli count','No 19 native ANGLE KMBs compiled','Physics invariant for commuting edge reorder only','All candidates require official end-to-end verification']}
 (out/'chemistry_schedule_receipt.json').write_text(json.dumps(rec,indent=2)+'\n')
 print('wrote',out/'chemistry_schedule_receipt.json',flush=True)

if __name__=='__main__':
 pa=argparse.ArgumentParser();pa.add_argument('--source',default='/mnt/data/gvqcc_work/chemistry_baseline/submission.npz');pa.add_argument('--out',default='/mnt/data/GVQCC_MULTIAXIS_20261122');pa.add_argument('--iterations',type=int,default=160);pa.add_argument('--seed',type=int,default=113);run(pa.parse_args())