"""Reference-only homogeneous continuant reconstruction for the captured #262 pole."""
import json
import crt882 as F
from pathlib import Path
inp=json.load(open('captured_input.json'))
obs=json.load(open('extract_witness.json'))['words'][-1]
xs=[F.exp[i] for i in inp['support']]
es=inp['magnitudes']
ks=[F.m(c,c)^c^2048 for c in [2*i for i in range(17) for _ in range(2)]]
qs=[[k,1,1] for k in ks]
P=[0,0,1]
for q in qs:P=F.mul(P,q)
D=[1]
for x in xs:D=F.mul(D,[x,1])
N=[]
for x,e in zip(xs,es):
 d,r=F.div(D,[x,1]);assert not r
 N=F.add(N,[F.m(F.m(F.m(x,e),F.evalp(P,x)),v) for v in d])
N0,D0=N[:],D[:]
heads=[];poles=[]
for i,q in enumerate(qs):
 n=F.div(N,q)[1];d=F.div(D,q)[1]
 if not d:
  assert n and D
  h=[];poles.append(i)
  N,D=F.mul(q,D),N
 else:
  h=F.div(F.mul(n,F.inversemod(d,q)),q)[1]
  R,r=F.div(F.add(N,F.mul(h,D)),q);assert not r
  N,D=D,R
 heads.extend((h+[0,0])[:2])
assert heads==obs[:68]
assert len(D)==1 and len(N)<=2
tail=[F.m(x,F.inv(D[0])) for x in N]
assert (tail+[0,0])[:2]==obs[68:]
for i in reversed(range(34)):
 h=F.trim(heads[2*i:2*i+2])
 N,D=F.add(F.mul(h,N),F.mul(qs[i],D)),N
assert F.mul(N,D0)==F.mul(D,N0)
assert F.div(D,D0)[1]==[]
g=F.div(D,D0)[0]
roots=[x for x in range(1,4096) if F.evalp(D,x)==0]
assert set(roots)==set(xs)
der=[D[i] if i%2 else 0 for i in range(1,len(D))]
out={}
for x in roots:
 den=F.m(F.m(x,F.evalp(P,x)),F.evalp(der,x))
 assert den
 out[x]=F.m(F.evalp(N,x),F.inv(den))
assert out==dict(zip(xs,es))
receipt=dict(poles=poles,heads_equal=34,tail_equal=2,root_count=len(roots),root_magnitude_equal=True,all_field_points=4095,common_factor=g,weighted_numerator=N,locator=D,native_repair=False)
Path('homogeneous_receipt.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps(receipt))

