"""Finite GF(2) rank-one tensor identity: merge equal pairs and reorient
three symmetric factors across all selector groups. No new clean wire.
All chosen factor sets are checked by exact symbolic Boolean ANF expansion.
Run beside V47 companion archive's v47_group.py and joint_quotient.py.
"""
from v47_group import *
from itertools import combinations
import random

def expand_linear_forms(forms):
 z={()}
 for f in forms:
  n=set()
  for t in z:
   for i in bits(f):n.symmetric_difference_update({tuple(sorted(set(t)|{i}))})
  z=n
 return z

def canon(ts):
 return tuple(sorted(set(ts)))

def merge(triples,low):
 ts=set();lo=set(low)
 def add(t):
  z=canon(t)
  if not all(t):return
  if len(z)<3:lo.symmetric_difference_update(expand_linear_forms(z))
  else:ts.symmetric_difference_update({z})
 for t in triples:add(t)
 merges=[]
 while 1:
  pairs=defaultdict(list)
  for t in ts:
   for p in combinations(t,2):pairs[p].append(t)
  if not pairs:break
  p,ls=max(pairs.items(),key=lambda x:(len(x[1]),-sum(a.bit_count() for a in x[0])))
  if len(ls)<2:break
  a=0
  for t in ls:
   ts.remove(t);a^=next(x for x in t if x not in p)
  add((*p,a));merges.append(dict(pair=list(p),merged=len(ls),third=a))
 return sorted(ts),sorted(lo,key=lambda x:(len(x),x)),merges

def oriented(triples,seed=47):
 rng=random.Random(seed);best=None
 for it in range(400):
  left=list(triples);d=defaultdict(list)
  while left:
   c=Counter(x for t in left for x in t)
   s=max(c,key=lambda x:(c[x]+(0 if it==0 else rng.random()*1.2),-x.bit_count()))
   hit=[t for t in left if s in t];d[s].extend(tuple(x for x in t if x!=s) for t in hit);left=[t for t in left if s not in t]
  cost=sum(min(4*len(v),2*len(v)+2)for v in d.values());metric=(cost,sum(s.bit_count() for s in d))
  if best is None or metric<best[0]:best=(metric,d)
 return best[1]

def compile_dense(s,fs,n,t):
 best=None
 for p in bits(s):
  assert p!=t
  pre=[Op(33,(i,p))for i in bits(s) if i!=p];fac=[];low=set()
  def change(m):return m^(s^(1<<p)) if m>>p&1 else m
  for a,b in fs:
   aa,bb=change(a),change(b);alpha=aa>>p&1;beta=bb>>p&1;aa&=~(1<<p);bb&=~(1<<p)
   if aa and bb:
    if aa==bb:low.symmetric_difference_update(expand_linear_forms((1<<p,aa)))
    else:fac.append((aa,bb))
   if alpha:low.symmetric_difference_update(expand_linear_forms((1<<p,bb)))
   if beta:low.symmetric_difference_update(expand_linear_forms((1<<p,aa)))
   if alpha and beta:low.symmetric_difference_update({(p,)})
  body,info=compile_group(p,fac,n,t) if fac else ([],{})
  lo,_=emit_poly(list(low),n,t);gs=pre+body+lo+pre[::-1]
  if best is None or (paid(gs),len(gs))<(paid(best[0]),len(best[0])):best=(gs,dict(selector=s,pivot=p,factors=len(fs),new=paid(gs),ops=len(gs),group=info))
 return best

def compile_shared(f,n,t):
 orig=[(1<<s,a,b) for s,a,b in f['cubic_factors']];lo=list(map(tuple,f['low']));ts,low,merges=merge(orig,lo)
 P=set(lo)
 for x in orig:P.symmetric_difference_update(expand_linear_forms(x))
 Q=set(low)
 for x in ts:Q.symmetric_difference_update(expand_linear_forms(x))
 assert P==Q
 g=oriented(ts);ops,_=emit_poly(low,n,t);rec=[]
 for s,fs in g.items():
  gs,info=compile_dense(s,fs,n,t);ops+=gs;rec.append(info)
 return ops,dict(initial_factors=len(orig),merged_factors=len(ts),merges=merges,groups=rec,paid=paid(ops),ops=len(ops),anf_exact='PASS')

if __name__=='__main__':
 f=json.load(open('v47_direct_factor.json'));ops,r=compile_shared(f,36,29);print(r,flush=True);Path('v47_shared_receipt.json').write_text(json.dumps(r,indent=2))
