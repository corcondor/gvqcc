import capture262 as C
import numpy as np,kickmix as km,json
import crt882 as F
S,M,P,seed=C.gen(157); j=244
for path in ['joint_alias.kmb','full_fft.kmb','alias_direct.kmb','alias_scope.kmb','joint_monotone.kmb']:
 c=km.Circuit.from_file(path);E,T=C.run(c,S,M,P,seed);print(path,E[:,j].astype(int).tolist(),np.flatnonzero(E.any(0)).tolist(),flush=True)
 del c
# Same input in different lanes/seeds, dense mask and zero mask, plus
# independent one-hot masks at every nonzero physical root.
# recover sparse support by standard BM and magnitudes independently.
def bm(s):
 c=[1];b=[1];l=0;sh=1;last=1
 for i,v in enumerate(s):
  d=int(v)
  for k in range(1,min(l+1,len(c))):d^=F.m(c[k],int(s[i-k]))
  if not d:sh+=1;continue
  old=c[:];c=F.add(c,[0]*sh+[F.m(F.m(d,F.inv(last)),x) for x in b])
  if 2*l<=i:l=i+1-l;b=old;last=d;sh=1
  else:sh+=1
 return c+[0]*(l+1-len(c))
d=bm(S[j])[::-1];w=len(d)-1;xs=[x for x in range(1,4096) if F.evalp(d,x)==0];assert len(xs)==w
n=[0]*w
for k in range(w):
 for a in range(k+1,w+1):n[k]^=F.m(d[a],int(S[j,a-k-1]))
dd=[d[a] if a%2 else 0 for a in range(1,w+1)]
es=[F.m(F.evalp(n,x),F.inv(F.m(x,F.evalp(dd,x)))) for x in xs];assert F.moment(xs,es)==S[j].tolist()
out=dict(batch=157,lane=j,seed=str(seed),weight=w,support=[F.log[x] for x in xs],magnitudes=es,syndrome=S[j].tolist(),expected_phase=bool(P[j]))
print('INPUT',json.dumps(out),flush=True)
open('captured_input.json','w').write(json.dumps(out,indent=2))
A=np.repeat(S[j:j+1],256,axis=0);mask=np.repeat(M[j:j+1],256,axis=0);mask[:64]=0
for k in range(64,128):
 mask[k]=0;mask[k,F.log[xs[(k-64)%w]]]=1<<((k-64)%12)
r=np.random.default_rng(260259);mask[192:]=r.integers(0,4096,(64,4095))
expect=np.array([sum((int(v[F.log[x]])&e).bit_count() for x,e in zip(xs,es))%2 for v in mask],bool)
for path in ('joint_alias.kmb','full_fft.kmb','joint_monotone.kmb'):
 c=km.Circuit.from_file(path)
 for ss in (1,2,seed):
  E,T=C.run(c,A,mask,expect,ss)
  print('REPEAT',path,str(ss),[E[:,k:k+64].sum(1).tolist() for k in range(0,256,64)],flush=True)
 del c

