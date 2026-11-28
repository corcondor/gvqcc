"""Exact #316k -> #246/#259 residue chart on the legal padded-pair domain.
Not a native syndrome-to-coefficient compiler. All field arithmetic reused
from the pinned #237 CRT implementation. No external choice in a native oracle
is claimed by this reference.
"""
import crt882 as C
import random,json,hashlib,time
from pathlib import Path
from collections import Counter
from functools import reduce
m=C.m
def gcd(a,b):
 a=C.trim(a[:]);b=C.trim(b[:])
 while b:a,b=b,C.div(a,b)[1]
 return [m(v,C.inv(a[-1])) for v in a] if a else []
def exact(a,b):
 q,r=C.div(C.trim(a[:]),C.trim(b[:]));assert not r
 return q
def derivative(a):return C.trim([a[i] if i&1 else 0 for i in range(1,len(a))])
def sqrt(x):return C.gf_pow(x,2048,12,C.MOD)
def halves(a):return C.trim([sqrt(x) for x in a[::2]]),C.trim([sqrt(x) for x in a[1::2]])
def square(a):return C.mul(a,a)
def join(a,b):return C.add(square(a),[0]+square(b))
def residue_chart(D,N):
 A,B=halves(D);P,Q=halves(N)
 H=gcd(A,B);assert H and B
 # Do not divide away non-squarefree padding as an irreversible step:
 # D itself is retained. The new coordinate is canonical in F[X]/(D/H^2).
 a,b,p,q=[exact(t,H) for t in (A,B,P,Q)]
 d=join(a,b);n=join(p,q);h2=square(H)
 assert C.mul(d,h2)==D and C.mul(n,h2)==N
 assert gcd(a,b)==[1] and gcd(d,derivative(d))==[1]
 if len(b)==1:
  u=t=[]
 else:
  j=C.inversemod(C.div(a,b)[1],b)
  u=C.div(C.mul(j,p),b)[1];t=C.div(C.mul(j,q),b)[1]
 z=exact(C.add(p,C.mul(a,u)),b);w=exact(C.add(q,C.mul(a,t)),b)
 V=join(C.add(z,[0]+t),C.add(w,u))
 V=C.div(V,d)[1]
 assert C.div(C.mul(derivative(D),V),D)[1]==N
 assert gcd(D,derivative(D))==h2
 return V,H
def rational(xs,es,U):
 d=[1]
 for x in xs:d=C.mul(d,[x,1])
 n=[]
 for x,e in zip(xs,es):
  n=C.add(n,[m(m(m(x,e),C.evalp(U,x)),v) for v in exact(d,[x,1])])
 return n,d
def main():
 rng=random.Random(259316); U=square(C.G); counts=Counter();roots=0;maxh=0;start=time.time()
 assert all(C.evalp(U,x) for x in range(4096))
 for weight in range(36):
  for rep in range(12):
   X=rng.sample(range(1,4096),weight)
   d=[1]
   for x in X:d=C.mul(d,[x,1])
   if rep<6: E=[rng.randrange(1,4096) for x in X]
   else:
    # Explicit single and double divisibility by the original CRT nodes
    # in the weighted numerator when degree permits. All legal e remain nonzero.
    k=C.ks[(weight+rep)%len(C.ks)]
    f=[1] if weight<3 else [k,1,1] if weight<5 or rep<9 else square([k,1,1])
    E=[m(C.evalp(f,x),C.inv(m(m(x,C.evalp(U,x)),C.evalp(derivative(d),x)))) for x in X]
    assert all(E)
   n,d=rational(X,E,U)
   pad=[0,1] if (35-weight)%2 else [1]
   for j in range((35-weight)//2):
    # Distinct, duplicated, and arbitrary multiplicity irreducible quadratics.
    k=C.ks[j] if rep%3==0 else C.ks[j//2] if rep%3==1 else C.ks[rng.randrange(3)]
    pad=C.mul(pad,[k,1,1])
   D,N=C.mul(pad,d),C.mul(pad,n)
   V,H=residue_chart(D,N);maxh=max(maxh,len(H)-1)
   assert len(D)==36 and len(V)<len(exact(D,square(H)))
   if len(H)>1:counts['nontrivial_square_factor']+=1
   for x,e in zip(X,E):
    assert C.evalp(D,x)==0 and C.evalp(H,x)
    assert C.evalp(V,x)==m(m(x,e),C.evalp(U,x))
    roots+=1
   assert C.moment(X,[m(C.evalp(V,x),C.inv(m(x,C.evalp(U,x)))) for x in X])==C.moment(X,E)
   counts['cases']+=1
   if rep>=9 and weight>=5:counts['forced_double_node']+=1
 out=dict(scope='word-level canonical residue chart, not native decoder',counts=dict(counts),root_values=roots,max_half_gcd_degree=maxh,errors=0,seconds=time.time()-start)
 print(json.dumps(out),flush=True);Path('quotient_chart_receipt.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()

