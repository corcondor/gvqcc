"""Exact frozen selector residual interpolation, no quantum gates."""
import sys,itertools,collections,runpy
from pathlib import Path
SRC=Path('/tmp/source/dqi');sys.path.insert(0,str(SRC))
import selector
E=[1]
for _ in range(4094):
 x=E[-1]<<1;E.append(x^0x1053 if x&4096 else x)
L={x:i for i,x in enumerate(E)};E*=2
def m(a,b):return E[L[a]+L[b]] if a and b else 0
def inv(a):return E[4095-L[a]]
def add(a,b):
 c=[0]*max(len(a),len(b))
 for i,x in enumerate(a):c[i]^=x
 for i,x in enumerate(b):c[i]^=x
 return c
def prod(a,b):
 c=[0]*(len(a)+len(b)-1)
 for i,x in enumerate(a):
  for j,y in enumerate(b):c[i+j]^=m(x,y)
 return c
def ev(p,x):
 v=0
 for c in p[::-1]:v=m(v,x)^c
 return v
def prepare(em):
 rows=collections.defaultdict(dict)
 for i,j,a in selector.matrix_rows():
  assert a==[m(a[0],1<<k) for k in range(12)]
  rows[i][j]=a[0]
 assert list(rows)==list(range(4024)) and all(len(r)==72 for r in rows.values())
 anchor=sorted(set.intersection(*(set(r) for r in rows.values())));assert len(anchor)==71
 xs=[E[j] for j in anchor];LP=[]
 for i,x in enumerate(xs):
  p=[1]
  for j,y in enumerate(xs):
   if i!=j:p=prod(p,[y,1])
  LP.append([m(c,inv(m(x,ev(p,x)))) for c in p])
 for i,r in rows.items():
  j,=set(r)-set(anchor);x=E[j]
  for a,p in zip(anchor,LP):assert r[a]==m(r[j],m(x,ev(p,x)))
 T=[];P=[0,1];NB=[[1]]
 for k in range(12):
  v=ev(P,1<<k);T.append([m(c,inv(v)) for c in P]);P=add(prod(P,P),[m(v,c) for c in P])
 for i in range(1,72):
  k=(i&-i).bit_length()-1;NB.append(prod(NB[i^(1<<k)],T[k]))
 C=[]
 for p in LP:
  p=[0]+p;cs=[0]*72
  for j in range(71,-1,-1):
   v=m(p[j],inv(NB[j][-1]));cs[j]=v
   for k,z in enumerate(NB[j]):p[k]^=m(v,z)
  assert not any(p);C.append(cs)
 # Original KMB uses classical bits 0..691865. New private scratch is cleared.
 base=691866
 def coef(j):return base+12*j
 def zero(a):
  for j in range(12):em.zero(a+j)
 def acc(a,b,c):
  if not c:return
  for j in range(12):
   z=m(c,1<<j)
   while z:
    k=(z&-z).bit_length()-1;z^=1<<k;em.xor(a+k,b+j)
 for j in range(72):zero(coef(j))
 for i,j in enumerate(anchor):
  for k,c in enumerate(C[i]):acc(12*j,coef(k),c)
 lookup={E[next(iter(set(r)-set(anchor)))]:i for i,r in rows.items()};assert len(lookup)==4024
 seen=[]
 def scan(k,x,deg):
  if not k:
   if x not in lookup:return
   i=lookup[x];j=L[x];rho=rows[i][j];t=selector.NORMAL+12*i
   zero(t);acc(12*j,t,rho);acc(coef(0),t,rho);seen.append(i);return
  h=1<<(k-1)
  if deg<h:scan(k-1,x,deg);scan(k-1,x^h,deg);return
  c=ev(T[k-1],x)
  for j in range(h,deg+1):acc(coef(j),coef(j-h),c)
  scan(k-1,x,h-1)
  for j in range(h,deg+1):acc(coef(j),coef(j-h),1)
  scan(k-1,x^h,h-1)
  for j in range(h,deg+1):acc(coef(j),coef(j-h),c^1)
 scan(12,0,71);assert sorted(seen)==list(range(4024))
 for j in range(72):zero(coef(j))
 print('exact 289728 scalar maps and 3476736 binary rows verified',flush=True)
if __name__=='__main__':
 target=sys.argv[1];selector.prepare_residuals=prepare
 p=Path(__file__).resolve().parents[1]/'dqi316k_joint_crt/d16_shared_frame.py'
 sys.argv=[str(p),target];runpy.run_path(str(p),run_name='__main__')
