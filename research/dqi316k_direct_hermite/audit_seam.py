import json, random, struct, hashlib
from pathlib import Path
import numpy as np,kickmix as km
import crt882 as C
U=C.mul(C.G,C.G)
ORDER=[3169,3169,3257,3257,3134,3134,3302,3302,3727,3727,3671,3671,3792,3792,3592,3592]
NODES=[3169,3257,3134,3302,3384,3431,3519,3552,3592,3633,3671,3727,3792,3854,3921,3977,4054]
def pmul(a,b):return C.mul(a,b)
def g(k):return [k,1,1]
def rem(p,k):return C.div(p,g(k))[1]
def prod(a,b,k):
 x,y=a;z,t=b;u=C.m(y,t)
 return (C.m(x,z)^C.m(k,u),C.m(x,t)^C.m(y,z)^u)
def inverse(a,k):
 x,y=a;n=C.m(x,x)^C.m(x,y)^C.m(k,C.m(y,y))
 return (C.m(x^y,C.inv(n)),C.m(y,C.inv(n))) if n else (0,0)
def ev(p,k):return tuple((rem(p,k)+[0,0])[:2])
def head(n,d,k):
 a,b=ev(n,k),ev(d,k)
 if not any(a):
  q,r=C.div(n,g(k));assert not r
  return (0,0),(q,d)
 h=prod(b,inverse(a,k),k)
 q,r=C.div(C.add(d,pmul(list(h),n)),g(k));assert not r
 return h,(q,n)
def deriv(a):return [a[i] if i%2 else 0 for i in range(1,len(a))]
def jet(n,d,k):
 a,b=ev(n,k),ev(d,k);i=inverse(a,k)
 h=prod(b,i,k);x=prod(ev(deriv(d),k),a,k);y=prod(b,ev(deriv(n),k),k)
 v=prod((x[0]^y[0],x[1]^y[1]),prod(i,i,k),k)
 return (*h,*v)
def rational(E):
 d=[1]
 for x in E:d=pmul(d,[x,1])
 n=[]
 for x,e in E.items():n=C.add(n,pmul(C.div(d,[x,1])[0],[C.m(C.m(x,e),C.evalp(U,x))]))
 return n,d
def calc(E):
 n,d=rational(E);res=[];labels=[]
 for j,k in enumerate(ORDER):
  h,(n,d)=head(n,d,k);res.extend(h);labels.extend([(j+1,k,'h',0),(j+1,k,'h',1)])
  if j+1 in (2,4,6,8,10,12,14,16):
   for l in NODES:
    if l not in ORDER[:j+1]:
     res.extend(jet(n,d,l));labels.extend((j+1,l,'jet',t) for t in range(4))
 return res,labels
rng=random.Random(164839)
high=[{x:rng.randrange(1,4096)for x in rng.sample(range(1,4096),35)} for i in range(128)]
mixed=[{x:rng.randrange(1,4096)for x in rng.sample(range(1,4096),i%36)}for i in range(64)]
es=high+mixed
ys=[calc(e)[0] for e in es];labels=calc(es[0])[1]
# Use independent 128 lanes for matching each exact word form.
Y=np.asarray(ys,np.uint16)
Q=km.Circuit.from_file('donor.kmb').register_data
qids=[int(str(q)[1:]) for j in range(70) for q in Q[f'S{j}']]
S=np.asarray([C.moment(list(e),list(e.values())) for e in es],np.uint16)
for i in range(3):
 x=((S[64*i:64*(i+1),:,None]>>np.arange(12))&1).reshape(64,840).T.astype(np.uint8)
 w=np.zeros((900,64),np.uint8);w[qids]=x
 np.packbits(w,axis=1,bitorder='little').tofile(f'in{i}.bin')
# All nonzero bit forms of each word. Matching a single form is not proof.
with open('forms.bin','wb') as f:
 for i in range(Y.shape[1]):
  a=np.packbits(((Y[:,i,None]>>np.arange(12))&1).T,axis=1,bitorder='little').copy().view('<u8').reshape(12,3)
  v=np.zeros((4096,3),np.uint64)
  for k in range(12):v[1<<k:1<<(k+1)]=v[:1<<k]^a[k]
  for m,row in enumerate(v[1:],1):f.write(struct.pack('<QQQII',*(int(z) for z in row),i,m))
Path('labels.json').write_text(json.dumps(labels));Path('seam_inputs.json').write_text(json.dumps(es))
print('forms',len(labels)*4095,'labels',len(labels),'inputs',len(es),flush=True)

