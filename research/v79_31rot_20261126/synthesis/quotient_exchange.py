"""Exact quotient-kernel optimization by one-dimensional subspace exchange.
Distinct from reordering batches: basis vectors may be new pair differences.
"""
from collections import Counter,defaultdict
from functools import lru_cache
from conditional_basis_prefix import pivot_basis,reduce
from global_transport import independent,plan_rank_cost
from quotient_hubs_v1 import quotient_plan as old_quotient_plan

COUNTERS=Counter()

def classes(vectors,B):
 T=pivot_basis(B)
 return sorted(set(reduce(v,T)[0] for v in vectors))

def next_direction(rs):
 score=Counter()
 for i,r in enumerate(rs):
  for s in rs[i+1:]:score[r^s]+=1
 if 0 not in rs:
  for r in rs:
   if r:score[r]+=1
 # objective = nonzero cosets after insertion, counting zero exactly.
 if not score:return None
 return max(score,key=lambda d:(score[d],-d.bit_count(),-d))

def make_plan(keys,B):
 T=pivot_basis(B);G=defaultdict(list)
 for v,h in keys:G[reduce(v,T)[0]].append((v,h))
 out=[]
 if 0 in G:out.append((B[:],[(v,h,reduce(v,T)[1]) for v,h in G[0]]))
 for r,ks in sorted(G.items()):
  if not r:continue
  d=min([r]+[v for v,h in ks],key=lambda v:(v.bit_count(),v));C=B+[d];U=pivot_basis(C)
  out.append((C,[(v,h,reduce(v,U)[1]) for v,h in ks]))
 return out

@lru_cache(None)
def kernel_search(vectors,cap):
 n=len(independent(vectors))
 if n<=cap:return tuple(independent(vectors)), True
 B=[]
 for step in range(cap-1):
  rs=classes(vectors,B);d=next_direction(rs)
  if d is None:break
  B.append(d)
 best=sum(bool(r) for r in classes(vectors,B));initial=best
 for sweep in range(10):
  winner=None
  for i in range(len(B)):
   C=B[:i]+B[i+1:];rs=classes(vectors,C);d=next_direction(rs)
   if d is None:continue
   D=C+[d];score=sum(bool(r) for r in classes(vectors,D))
   if score<best and (winner is None or (score,sum(v.bit_count() for v in D))<winner[:2]):winner=(score,sum(v.bit_count() for v in D),D)
  if winner is None:break
  best=winner[0];B=winner[2]
 COUNTERS['kernels']+=1;COUNTERS['exchange_saved_quotient_classes']+=initial-best
 return tuple(B),False

def quotient_plan(keys,cap,seed=0):
 old=old_quotient_plan(keys,cap,seed)
 if not keys:return old
 vectors=tuple(sorted(set(v for v,h in keys)))
 B,full=kernel_search(vectors,cap)
 if full:
  T=pivot_basis(B);new=[(list(B),[(v,h,reduce(v,T)[1]) for v,h in keys])]
 else:new=make_plan(keys,list(B))
 return min([old,new],key=lambda p:(plan_rank_cost(p),sum(v.bit_count() for B,K in p for v in B)))
