"""Choose a resident subspace from pair differences, rather than requested masks.
Every nonzero quotient coset needs one additional conditional product; all its
requests are served by CNOT combinations with the retained kernel basis.
"""
from collections import Counter,defaultdict
from global_transport import independent, plan_rank_cost
from conditional_basis_prefix import pivot_basis,reduce

def quotient_plan(keys,cap,seed=0):
 if not keys or cap<1:return []
 vectors=sorted(set(v for v,h in keys));B=[];cands=[]
 for step in range(cap):
  T=pivot_basis(B)
  groups=defaultdict(list)
  for v,h in keys:groups[reduce(v,T)[0]].append((v,h))
  plan=[]
  if 0 in groups:plan.append((B[:],[(v,h,reduce(v,T)[1]) for v,h in groups[0]]))
  for r,ks in sorted(groups.items()):
   if not r:continue
   C=B+[min([v for v,h in ks]+[r],key=lambda v:(v.bit_count(),v))];U=pivot_basis(C)
   plan.append((C,[(v,h,reduce(v,U)[1]) for v,h in ks]))
  if plan and max(len(a) for a,k in plan)<=cap:cands.append(plan)
  if len(B)==cap-1 or len(groups)<=1:break
  rs=sorted(groups);scores=Counter()
  for i,r in enumerate(rs):
   for s in rs[i+1:]:scores[r^s]+=1
  # Quotient zero can be absorbed without needing a separate varying direction.
  for r in rs:
   if r:scores[r]+=1
  if not scores:break
  best=max(scores,key=lambda v:(scores[v],-v.bit_count(),-v))
  B.append(best)
 return min(cands,key=lambda p:(plan_rank_cost(p),sum(v.bit_count() for B,K in p for v in B)))
