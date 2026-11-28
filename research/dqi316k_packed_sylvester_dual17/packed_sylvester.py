"""Exact packed inverse modular multiplication; word-level reference, not native gates."""
from collections import Counter
import crt882 as C
def trim(a):return C.trim(list(map(int,a)))
def deg(a):return len(trim(a))-1
def pad(a,n):return list(a)+[0]*(n-len(a))
def packed(A,B,p,counter):
 A=trim(A);B=trim(B);p=trim(p);a=deg(A);b=deg(B)
 assert 0<=a<b and deg(p)<b
 if a==0:return [C.m(x,C.inv(A[0])) for x in pad(p,b)]
 _,r=C.div(B,A);assert trim(r)
 h,rhs=C.div(p,A)
 v=packed(r,A,rhs,counter)
 g=b-a;w=pad(h,g)+pad(v,a);assert len(w)==b
 lead=C.m(B[-1],C.inv(A[-1]))
 for j in range(a):
  col,_=C.div([0]*j+B,A)
  x=w[g+j]
  assert len(col)==g+j+1 and col[-1]==lead
  for k in range(g+j):w[k]^=C.m(x,col[k])
  w[g+j]=C.m(x,lead)
 counter[g]+=1
 assert trim(C.div(C.mul(A,w),B)[1])==trim(p)
 return w
def magnitude(D,N,counter):
 D=list(map(int,D));N=list(map(int,N))
 A=[C.gf_pow(D[i],2048,12,C.MOD) for i in range(0,36,2)]
 B=[C.gf_pow(D[i],2048,12,C.MOD) for i in range(1,36,2)]
 P=[C.gf_pow(N[i],2048,12,C.MOD) for i in range(0,35,2)]
 Q=[C.gf_pow(N[i],2048,12,C.MOD) for i in range(1,35,2)]
 _,Ar=C.div(A,B);_,Pr=C.div(P,B)
 U=packed(Ar,B,Pr,counter);T=packed(Ar,B,Q,counter)
 Z,r=C.div(C.add(P,C.mul(A,U)),B);assert not trim(r) or trim(r)==[0]
 W,r=C.div(C.add(Q,C.mul(A,T)),B);assert not trim(r) or trim(r)==[0]
 V=[0]*35
 for j,x in enumerate(C.add(Z,[0]+T)):V[2*j]^=C.m(x,x)
 for j,x in enumerate(C.add(W,U)):V[2*j+1]^=C.m(x,x)
 return V,B
def validate(Ds,Ns):
 count=Counter();roots=0;n=0
 for D,N in zip(Ds,Ns):
  V,B=magnitude(D,N,count)
  for x in range(1,4096):
   if C.evalp(D,x)==0:
    bv=C.evalp(B,x);assert bv
    assert C.m(C.evalp(V,x),C.m(bv,bv))==C.evalp(N,x);roots+=1
  n+=1
 return dict(pairs=n,roots=roots,max_rhs_words=17,degree_gaps=dict(count))
if __name__=='__main__':
 import numpy as np,sys,json
 z=np.load(sys.argv[1]);print(json.dumps(validate(z['D'],z['N'])))

