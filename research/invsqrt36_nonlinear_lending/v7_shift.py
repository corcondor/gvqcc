"""V7 affine gauge shift: actual compiler stage from the research archive.
Run with v7_compile_cubic.py and the pinned archive dependencies.
Exact formal ANF equality, not sampled fitting."""
from v7_compile_cubic import *
from functools import reduce as fold

def linear_form(qs):return xor([var(q)for q in qs])
def poly(ts):return frozenset(sum(1<<i for i in t)for t in ts)
def factorpoly(prods,aff):return xor([mul(linear_form(a),linear_form(b))for a,b in prods]+[poly(aff)])
def cubicpoly(cp):return xor([prod([var(q),linear_form(a),linear_form(b)])for q,a,b in cp])
def shift_plan(r,best):
 score,A,B,plans=best;active=sorted({q for m in r['phase']for q in bits(m)if q<37});P=[(k,factorpoly(prods,aff),xor([frozenset({x})for x in q])^cubicpoly(cp),prods,aff)for k,q,prods,aff,cp in plans];base=mul(A,B);winning=None
 for m in range(1<<len(active)):
  L=linear_form(active[i]for i in bits(m));paid=set();result=[]
  for k,F,C,prods,aff in P:
   C=C^mul(L,F);q={t for t in C if t.bit_count()<=2};cp,low=cubic_factor([bits(t)for t in C if t.bit_count()==3]);q.symmetric_difference_update(low)
   assert all(t.bit_count()<=3 for t in C)
   for a,b in prods:paid.add((-1,)+tuple(sorted((tuple(a),tuple(b)))))
   for p,a,b in cp:paid.add((p,)+tuple(sorted((tuple(a),tuple(b)))))
   result.append((k,list(q),prods,aff,cp))
  rank=(1+len(paid),sum(len(q)+len(p)+len(a)for _,q,p,a,c in result),len(L))
  if winning is None or rank<winning[0]:winning=(rank,A,B,L,result)
 rank,A,B,L,plans=winning
 actual={k:frozenset(q)^cubicpoly(cp)^mul(base^L,factorpoly(p,aff))for k,q,p,aff,cp in plans}
 expected=defaultdict(set)
 for m in r['phase']:expected[m>>37].add(m&((1<<37)-1))
 assert actual=={k:frozenset(v)for k,v in expected.items()}
 return winning,1<<len(active)

def emit_shift(r,best,m):
 score,A,B,L,plans=best;d=r['d'];t=slot(r['piv'][1],d);G=list(r['prep']);common=fold(int.__and__,[k for k,*_ in plans]);c0=guard(common,r)
 for o in OPS[r['a']:r['z']]:
  if o.raw in(129,1)or o.raw&127 in(64,65,66):G.append(o)
  elif o.raw&127==80:G.append(replace(o,wires=(t,)))
 writes={o.measurement for o in OPS[r['a']:r['z']]if o.raw&127 in(64,65,66,80)}
 assert all(not(set(guard(k,r))&writes)for k,*_ in plans)
 pre,(u,v)=affine_pair(A,B,d);lg=[Op(33,(slot(q,d),t))for q in bits(lm(L))];G+=scoped(pre+[Op(49,(u,v,t))]+pre[::-1]+lg,c0)
 paid=defaultdict(list)
 for k,q,prods,aff,cp in plans:
  c=guard(k,r);g=[pg([slot(j,d)for j in bits(x)])for x in q]+[pg([t]+[slot(j,d)for j in x])for x in aff];G+=scoped(g,c)
  for a,b in prods:paid[(-1,)+tuple(sorted((tuple(a),tuple(b))))].append(c)
  for pivot,a,b in cp:paid[(pivot,)+tuple(sorted((tuple(a),tuple(b))))].append(c)
 for (pivot,a,b),cs in paid.items():
  pp,(x,y)=affine_pair(linear_form(a),linear_form(b),d);body=pp+[Op(48,(x,y,t if pivot<0 else slot(pivot,d)))]+pp[::-1]
  for c in cs:G+=scoped(body,c)
 G+=scoped(lg[::-1]+pre+[Op(80,(t,),measurement=m),Op(160,(u,v),condition=m)]+pre[::-1],c0);m+=1;G+=decode(r)
 assert all(q<36 for o in G for q in o.wires);return G,m

def main():
 ps,_=pickle.load(open(P/'v7_cubic_proposals.pkl','rb'));out=[];m=REF.header[2]+N+200
 for r,G,b in ps:
  best,tests=shift_plan(r,b);G,m=emit_shift(r,best,m);print('shift',r['a'],tests,'old',r['oldpaid'],'new',stats(G),'L',bits(lm(best[3])),flush=True);out.append((r,G,best))
 pickle.dump((out,m),open(P/'v7_shift_proposals.pkl','wb'))
if __name__=='__main__':main()
