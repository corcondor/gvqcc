"""Fraction-free, gap-independent, nonmonic half-Bezout reference.

This is a word-level algebraic oracle, not a native KMB. It consumes actual
#261 D,N coordinates captured from the physical guarded prefix. No support
or magnitudes are used by the transform; they are used only for validation.
"""
import json,collections,random
from pathlib import Path
import crt882 as C
import numpy as np
def sm(a,c):return C.trim([C.m(v,c) for v in a])
def shifted(a,s):return [0]*s+a if a else []
def bezout(A,B):
 assert B and A
 f,g=B[:],A[:];u,v=[],[1];steps=0;mulcount=0;maxgap=0
 while g:
  if len(f)<len(g):f,g=g,f;u,v=v,u
  d=len(f)-len(g);a,b=f[-1],g[-1];maxgap=max(maxgap,d)
  # no inverse in this leading cancellation
  f=C.add(sm(f,b),shifted(sm(g,a),d))
  u=C.add(sm(u,b),shifted(sm(v,a),d))
  mulcount+=len(f)+len(g)+len(u)+len(v) # diagnostic proxy only
  assert len(f)<=len(g)+d-1
  steps+=1;assert steps<=35
  if not f:f,g=g,f;u,v=v,u
 assert len(f)==1 and f[0]
 # The Bezout coefficient u satisfies A*u = f mod B.
 I=C.div(sm(u,C.inv(f[0])),B)[1]
 assert C.div(C.mul(A,I),B)[1]==[1]
 return I,steps,maxgap
def transform(D,N):
 A=C.trim([C.gf_pow(v,2048,12,C.MOD) for v in D[::2]])
 B=C.trim([C.gf_pow(v,2048,12,C.MOD) for v in D[1::2]])
 P=C.trim([C.gf_pow(v,2048,12,C.MOD) for v in N[::2]])
 Q=C.trim([C.gf_pow(v,2048,12,C.MOD) for v in N[1::2]])
 I,steps,gap=bezout(A,B)
 U=C.div(C.mul(I,P),B)[1]
 T=C.div(C.mul(I,Q),B)[1]
 Z,r=C.div(C.add(P,C.mul(A,U)),B);assert not r
 W,r=C.div(C.add(Q,C.mul(A,T)),B);assert not r
 F=C.add(Z,shifted(T,1));G=C.add(W,U)
 V=C.add(C.mul(F,F),shifted(C.mul(G,G),1))
 # Polynomial identity, not merely sampled points.
 H=C.add(C.mul(U,U),shifted(C.mul(T,T),1))
 assert C.mul(C.mul(B,B),V)==C.add(C.trim(N[:]),C.mul(C.trim(D[:]),H))
 return V,steps,gap
def vm(a,b):
 return np.where((a!=0)&(b!=0),EXP[LOG[a]+LOG[b]],0)
EXP=np.asarray(C.exp,np.int64);LOG=np.asarray(C.log,np.int64)
XS=np.arange(1,4096,dtype=np.int64)
def evs(p):
 y=np.zeros(4095,dtype=np.int64)
 for v in p[::-1]:y=vm(y,XS)^v
 return y
def main():
 U0=None
 # Actual weighting polynomial is recovered from the pinned public geometry,
 # not estimated from a syndrome. The prefix probe stores expected root values.
 rows=json.load(open('gcd_probe.json'))
 g=collections.Counter();steps=[];gaps=[]
 for p in rows:
  V,n,gap=transform(p['D'],p['N']);steps.append(n);gaps.append(gap)
  D=p['D'];N=p['N'];Dval=evs(D);Vval=evs(V)
  root=np.flatnonzero(Dval==0)+1
  assert set(root)==set(p['roots'])
  for x in root:
   d=C.xor_word(C.m(D[j],C.gf_pow(int(x),j-1,12,C.MOD)) for j in range(1,len(D),2))
   assert d and C.m(int(Vval[x-1]),d)==C.evalp(N,int(x))
  g[p['w']]+=1
 rng=random.Random(261263);synth=0
 # Arbitrary half pairs of degree<=17, including deliberately large gaps.
 for k in range(512):
  d=rng.randrange(0,18);A=[rng.randrange(4096) for i in range(d)]+[rng.randrange(1,4096)]
  B=[rng.randrange(4096) for i in range(17)]+[rng.randrange(1,4096)]
  f,g0=A[:],B[:]
  while g0:f,g0=g0,C.div(f,g0)[1]
  if len(f)!=1:continue
  P=[rng.randrange(4096) for i in range(18)];Q=[rng.randrange(4096) for i in range(17)]
  D=[0]*36;N=[0]*35
  for i,a in enumerate(A):D[2*i]=C.m(a,a)
  for i,a in enumerate(B):D[2*i+1]=C.m(a,a)
  for i,a in enumerate(P):N[2*i]=C.m(a,a)
  for i,a in enumerate(Q):N[2*i+1]=C.m(a,a)
  transform(D,N);synth+=1
 r=dict(scope='word-level nonmonic half-Bezout reference; no native converter or paid-gate claim',native_prefix_coordinate_cases=len(rows),arbitrary_coprime_cases=synth,max_fraction_free_steps=max(steps),max_degree_gap=max(gaps),all_polynomial_identities_pass=True,weights=list(range(36)))
 print(json.dumps(r),flush=True);Path('fraction_free_receipt.json').write_text(json.dumps(r,indent=2)+'\n')
if __name__=='__main__':main()

