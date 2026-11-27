"""Generate exact native joint configuration from the pinned 900Q donor KMB.
Python standard library only. All pad constants are public and input independent.
"""
import sys,struct,hashlib
from pathlib import Path
F=4096; MOD=0x1053; K=2048
ROOTS=[[[112,3363,15222677],[2908,2944,11341719],[3984,3100,11248864],[3915,3229,6975786],[2635,3762,7084381],[1192,3003,15626060],[2526,3289,10290620],[1452,3999,8498533],[2984,3963,6174292]],[[3944,2235,3704072],[3546,2770,2683185],[1663,3573,4578274],[931,3913,14291038],[1457,3795,11701816],[3150,3626,10296175],[3203,4009,7695258],[2227,3206,8707000],[3638,3538,12593991]]]
NODES=(3169,3257,3134,3302,3384,3431,3519,3552,3592,3633,3671,3727,3792,3854,3921,3977,4054)
E=[1]
for _ in range(4094):
 x=E[-1]<<1;E.append(x^MOD if x&F else x)
L=[-1]*F
for i,x in enumerate(E):L[x]=i
E*=2
def m(a,b):return E[L[a]+L[b]] if a and b else 0
def em(a,b):
 a0,a1=a&4095,a>>12;b0,b1=b&4095,b>>12;t=m(a1,b1)
 return (m(a0,b0)^m(K,t))|((m(a0,b1)^m(a1,b0)^t)<<12)
def pmul(a,b):
 c=[0]*(len(a)+len(b)-1)
 for i,x in enumerate(a):
  for j,y in enumerate(b):c[i+j]^=m(x,y)
 return c
U=[1]
for k in NODES:
 for _ in range(2):U=pmul(U,[k,1,1])
z=next(c|F for c in range(F) if m(c,c)^c^K==NODES[0]);qpoly=[0]*(len(U)-1);qpoly[-1]=1
for i in range(len(qpoly)-2,-1,-1):qpoly[i]=U[i+1]^em(z,qpoly[i+1])
assert U[0]==em(z,qpoly[0]);assert all(U[i]==qpoly[i-1]^em(z,qpoly[i]) for i in range(1,len(qpoly)))
def lin(s):
 v=0
 for c,a in zip(qpoly,s):v^=em(c,a)
 return v
def moments(rows):
 S=[0]*70
 for c,k,beta in rows:
  assert m(c,c)^c^K==k
  x=c|F;p=x
  for i in range(70):S[i]^=em(beta,p)>>12;p=em(p,x)
 return S
P=list(map(moments,ROOTS));v0,v1=map(lin,P);assert (v0,v1)==(6782394,8583949)
parent=Path(sys.argv[1]);assert hashlib.file_digest(parent.open('rb'),'sha256').hexdigest()=='4b5721411adc239f61fc11c773a2358b75dfe7cb15586efae4f0459c77d77e52'
regs={}
with parent.open('rb') as f:
 f.seek(104)
 while (h:=f.read(16)):
  kind,n=struct.unpack('<QQ',h)
  if kind!=0:break
  raw=f.read(n);a,b=struct.unpack_from('<II',raw);name=raw[8:8+a].decode()
  if name.startswith('S'):regs[int(name[1:])]=[x&0x7fffffff for x in struct.unpack_from('<'+'I'*b,raw,8+a)]
q=sum([regs[i] for i in range(70)],[]);assert len(set(q))==840
terms=[]
for j,a in enumerate(qpoly):
 for k in range(12):
  v=em(a,1<<k)
  for t in range(24):
   if v>>t&1:terms.append((q[12*j+k],t))
with open(sys.argv[2],'w') as f:
 f.write(str(v0)+'\n'+str(len(terms))+'\n');f.writelines(f'{a} {b}\n' for a,b in terms)
 for pad in P:
  ids=[q[12*j+k] for j,v in enumerate(pad) for k in range(12) if v>>k&1];f.write(str(len(ids))+'\n');f.writelines(str(i)+'\n' for i in ids)
