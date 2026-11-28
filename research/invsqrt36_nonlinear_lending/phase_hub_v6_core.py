"""V6 compiler core excerpt from v6_phase_blocks.py and v6_guard_pool.py.
Run inside the supplied V6 bundle central/global_chart, not standalone.
The actual complete search, BDD verifier, serializer and receipts are in the bundle.
"""
from v5_fresh_charts import *
from functools import lru_cache
from itertools import combinations

def anf(form):
 return {1<<q for q in range(37) if form>>q&1}|({0} if form&ONE else set())

def affine_step(x,o):
 w=o.wires;g=o.raw&127
 if g==17:x[w[0]]^=ONE
 elif g==33:x[w[1]]^=x[w[0]]
 elif g==34:x[w[0]],x[w[1]]=x[w[1]],x[w[0]]
 else:raise ValueError(g)

@lru_cache(None)
def collect_block(i,j):
 x=[1<<q for q in range(37)];stack=[];phases=defaultdict(set);guards=[]
 for o in OPS[i:j]:
  g=o.raw&127
  if o.raw==129:stack.append(x.copy());guards.append(o.condition);continue
  if o.raw==1:
   if not stack or x!=stack.pop():return None
   guards.pop();continue
  if g in (17,33,34) and not o.raw&128:affine_step(x,o);continue
  if g not in (0,16,32,48):return None
  p={0}
  for q in o.wires:p=mul(p,anf(x[q]))
  k=tuple(guards)+((o.condition,)if o.raw&128 else ())
  phases[k].symmetric_difference_update(p)
 if stack or x!=[1<<q for q in range(37)]:return None
 return tuple((k,frozenset(v))for k,v in phases.items() if v)

def lower_phase(poly,d):
 p=set(mons(poly,d));out=[]
 while True:
  triples=[t for t in p if len(t)==3]
  if not triples:break
  counts=Counter(pair for t in triples for pair in combinations(t,2))
  a,b=max(counts,key=lambda k:(counts[k],k))
  L=sorted(next(q for q in t if q not in (a,b))for t in triples if a in t and b in t);u=L[0]
  g=[Op(33,(v,u))for v in L[1:]];out+=g+[Op(48,(a,b,u))]+g[::-1]
  for v in L:p.remove(tuple(sorted((a,b,v))))
 for m in sorted(p,key=lambda m:(len(m),m)):
  if len(m)<=2:out.append(Op((0,16,32)[len(m)],m))
  elif len(m)==4:
   a,b,c,e=m;t=next(q for q in range(36)if q not in m)
   u=Op(49,(a,b,t));v=Op(48,(t,c,e));out += [u,v,u,v]
  else:return None
 return out

def lower_block(block,d,ps):
 best=None
 for rel in ps:
  if not eligible(rel)>>d&1:continue
  expr=rel^{1<<d};out=[]
  for guard,poly in block:
   p=subst(poly,{1<<d:expr});g=lower_phase(p,d)
   if g is None:break
   out += [Op(129,(),condition=c)for c in guard]+g+[Op(1,())for c in guard]
  else:
   v=(stats(out)['paid'],len(out))
   if best is None or v<best[0]:best=(v,out)
 return None if best is None else best[1]

def block_key(body):
 x=[{1<<q}for q in range(37)];p=set()
 for o in body:
  if o.raw&128:return None
  g=o.raw;w=o.wires
  if g==17:x[w[0]]^={0}
  elif g==33:x[w[1]]^=x[w[0]]
  elif g==34:x[w[0]],x[w[1]]=x[w[1]],x[w[0]]
  elif g==49:x[w[2]]^=mul(x[w[0]],x[w[1]])
  elif g==50:
   d=mul(x[w[0]],x[w[1]]^x[w[2]]);x[w[1]]^=d;x[w[2]]^=d
  elif g in(0,16,32,48):
   v={0}
   for q in w:v=mul(v,x[q])
   p^=v
  else:return None
  if len(p)>5000 or any(len(v)>500 for v in x):return None
 return frozenset(p) if all(x[q]=={1<<q}for q in range(37))else None
