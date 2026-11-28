import json,functools,sys
F=4096;ex=[1]
for _ in range(4094):
 x=ex[-1]<<1;ex.append(x^0x1053 if x&4096 else x)
lg={x:i for i,x in enumerate(ex)}
ex*=2
m=lambda a,b:ex[lg[a]+lg[b]] if a and b else 0
xor=lambda a:functools.reduce(int.__xor__,a,0)
def pm(a,b):
 c=[0]*(len(a)+len(b)-1)
 for i,x in enumerate(a):
  for j,y in enumerate(b):c[i+j]^=m(x,y)
 return c
ks=[3169,3257,3134,3302,3384,3431,3519,3552,3592,3633,3671,3727,3792,3854,3921,3977,4054]
G=[1]
for k in ks:G=pm(G,[k,1,1])
U=pm(G,G)
def em(a,b):
 c,d=a&4095,a>>12;e,f=b&4095,b>>12;t=m(d,f)
 return (m(c,e)^m(2048,t))|((m(c,f)^m(d,e)^t)<<12)
def divide(p,z):
 q=[0]*(len(p)-1);q[-1]=p[-1]
 for i in range(len(q)-2,-1,-1):q[i]=p[i+1]^em(z,q[i+1])
 assert p[0]==em(z,q[0]);return q
def mat(q):
 r=[0]*24
 for j,c in enumerate(q):
  for b in range(12):
   v=em(c,1<<b)
   for i in range(24):
    if v>>i&1:r[i]^=1<<(12*j+b)
 return r
def basis(rows):
 a={}
 for r in rows:
  while r:
   k=r.bit_length()-1
   if k not in a:a[k]=r;break
   r^=a[k]
 return a
def member(r,p):
 while r:
  k=r.bit_length()-1
  if k not in p:return False
  r^=p[k]
 return True
data=open(sys.argv[1]).read().splitlines()
at,a,b,t=map(int,data[0].split());q=[int(x,2)&((1<<840)-1) for x in data[1:]]
res=[]
for k in ks:
 z=next(c|4096 for c in range(4096) if m(c,c)^c^2048==k)
 u=divide(U,z);v=divide(u,z)
 A=mat(u);B=mat(v)
 for name,R in [('value',A),('derivative',B),('both',A+B)]:
  P=basis(R);w=[i for i,x in enumerate(q) if x and member(x,P)]
  res.append(dict(k=k,jet=name,rank=len(P),physical=len(w),controls=[a in w,b in w],wires=w))
out=dict(first_op=at,controls=[a,b],target=t,linear_rank=len(basis(q)),zero_wires=sum(not x for x in q),matches=[r for r in res if r['physical'] or any(r['controls'])])
print(json.dumps(out,indent=2))
open('seam_matrix_receipt.json','w').write(json.dumps(out,indent=2))

