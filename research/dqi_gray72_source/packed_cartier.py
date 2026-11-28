"""Reversible tagged Cartier chart over GF4096. Reference only.
Arbitrary Q, arbitrary dirty numerator, all degrees 1..35. No full DQI splice.
"""
from random import Random
import json
MOD=0x1053; F=4096; EXP=[];LOG=[-1]*F;x=1
for i in range(F-1):
 assert LOG[x]==-1; LOG[x]=i;EXP.append(x);x<<=1
 if x&F:x^=MOD
assert x==1;EXP*=2
def m(a,b):return EXP[LOG[a]+LOG[b]] if a and b else 0
def inv(a):assert a;return EXP[4095-LOG[a]]
def sq(a):return m(a,a)
def sqrt(a):return EXP[(LOG[a]*2048)%4095] if a else 0
def tr(a):
 t=0
 for _ in range(12):t^=a;a=sq(a)
 assert t in (0,1);return t
def trim(a):
 a=list(a)
 while a and not a[-1]:a.pop()
 return a
def add(a,b):
 z=[0]*max(len(a),len(b))
 for i,v in enumerate(a):z[i]^=v
 for i,v in enumerate(b):z[i]^=v
 return trim(z)
def scale(a,c):return trim([m(x,c) for x in a])
def mul(a,b):
 if not a or not b:return []
 z=[0]*(len(a)+len(b)-1)
 for i,u in enumerate(a):
  if u:
   for j,v in enumerate(b):z[i+j]^=m(u,v)
 return trim(z)
def divrem(a,b):
 a=trim(a);b=trim(b);assert b
 z=[0]*max(0,len(a)-len(b)+1);iv=inv(b[-1])
 while len(a)>=len(b):
  k=len(a)-len(b);v=m(a[-1],iv);z[k]=v
  for i,u in enumerate(b):a[k+i]^=m(v,u)
  a=trim(a)
 return trim(z),a
def exact(a,b):
 q,r=divrem(a,b);assert not r;return q
def gcd(a,b):
 while b:a,b=b,divrem(a,b)[1]
 return scale(a,inv(a[-1])) if a else []
def inverse_mod(a,b):
 if len(b)==1:return []
 a=divrem(a,b)[1];r,s=b,a;u,v=[],[1]
 while s:
  q,t=divrem(r,s);r,s=s,t;u,v=v,add(u,mul(q,v))
 assert len(r)==1
 z=divrem(scale(u,inv(r[0])),b)[1]
 assert divrem(mul(a,z),b)[1]==[1];return z
def pad(a,n):assert len(a)<=n;return list(a)+[0]*(n-len(a))
def join(c,d,n):
 c=pad(c,(n+1)//2);d=pad(d,n//2);z=[0]*n;z[::2]=c;z[1::2]=d;return trim(z)
def section(Q,P,bit):return trim([sqrt(v) for v in mul(Q,P)[bit::2]])
def chart(Q,bit):
 d=len(Q)-1;assert d>=1 and Q[0]==1 and Q[-1]
 A,B=trim(Q[::2]),trim(Q[1::2]);H=gcd(A,B);g=len(H)-1;a,b=exact(A,H),exact(B,H)
 l,r=(a,[0]+b if b else []) if bit==0 else (b,a)
 tag_c=bool((d%2) != bit)
 nC,nD=(d+1)//2,d//2
 assert gcd(l,r)==[1]
 assert len(r if tag_c else l)-1==(nC if tag_c else nD)-g
 return d,g,H,l,r,tag_c
def encode(Q,P,bit):
 d,g,H,l,r,tag_c=chart(Q,bit);P=pad(P,d);C,D=trim(P[::2]),trim(P[1::2]);W=add(mul(l,C),mul(r,D))
 J,_=divrem(C,r) if tag_c else divrem(D,l)
 packed=pad(W,d-g)+pad(J,g)
 assert section(Q,P,bit)==trim([sqrt(x) for x in mul(H,W)])
 return packed
def decode(Q,z,bit):
 d,g,H,l,r,tag_c=chart(Q,bit);assert len(z)==d
 W,J=trim(z[:d-g]),trim(z[d-g:])
 if tag_c:
  C0=divrem(mul(W,inverse_mod(l,r)),r)[1];D0=exact(add(W,mul(l,C0)),r)
 else:
  D0=divrem(mul(W,inverse_mod(r,l)),l)[1];C0=exact(add(W,mul(r,D0)),l)
 C=add(C0,mul(r,J));D=add(D0,mul(l,J));return join(C,D,d)
def locator(xs):
 p=[1]
 for x in xs:p=mul(p,[1,x])
 return p
def moments(xs,amps,n):
 S=[0]*n
 for x,a in zip(xs,amps):
  u=m(a,x)
  for j in range(n):S[j]^=u;u=m(u,x)
 return S
def seq(Q,P,n):
 out=[]
 for j in range(n):
  v=P[j] if j<len(P) else 0
  for k in range(1,min(j+1,len(Q))):v^=m(Q[k],out[j-k])
  out.append(v)
 return out
def test():
 rng=Random(34172);out=dict(arbitrary_q_roundtrips=0,singular_charts=0,zero_odd_q=0,valid_rational=0,period=0,branch_relation=0,high_moment_checks=0,phase_basis=0,weighted_cases=0,degree_profiles=35)
 for d in range(1,36):
  for it in range(24):
   g=rng.randrange(d//2+1) if it<20 else d//2
   h=[1]+[rng.randrange(F) for _ in range(max(0,g-1))]+([rng.randrange(1,F)] if g else [])
   k=d-2*g; q=[1]+[rng.randrange(F) for _ in range(max(0,k-1))]+([rng.randrange(1,F)] if k else [])
   Q=mul(mul(h,h),q);assert len(Q)==d+1
   P=trim([rng.randrange(F) for _ in range(d)])
   for b in (0,1):
    z=encode(Q,P,b);assert decode(Q,z,b)==P
    assert encode(Q,decode(Q,z,b),b)==z
    out['arbitrary_q_roundtrips']+=1;out['singular_charts']+=chart(Q,b)[1]>0;out['zero_odd_q']+=not any(Q[1::2])
 for w in range(36):
  for it in range(12):
   xs=rng.sample(range(1,F),w);amps=[rng.randrange(1,F) for _ in xs];S=moments(xs,amps,142)
   ghost=rng.randrange(36-w);q=[1]+[rng.randrange(F) for _ in range(max(0,ghost-1))]+([rng.randrange(1,F)] if ghost else [])
   Q=mul(locator(xs),q);d=len(Q)-1;P=trim(mul(Q,S[:70])[:d]);assert seq(Q,P,142)==S
   out['valid_rational']+=1;out['weighted_cases']+=1
   if d:
    a=section(Q,P,0);b=section(Q,P,1)
    assert seq(Q,a,71)==[sqrt(x) for x in S[::2]]
    assert seq(Q,b,71)==[sqrt(x) for x in S[1::2]]
    def powmod(a,n):
     z=[1]
     while n:
      if n&1:z=divrem(mul(z,a),Q)[1]
      n//=2
      if n:a=divrem(mul(a,a),Q)[1]
     return z
    assert divrem(mul(powmod([0,1],2047),a),Q)[1]==b
    out['branch_relation']+=1
    for bit in (0,1):
     z=P
     for _ in range(12):z=section(Q,z,bit)
     assert z==P;out['period']+=1
   p=([0]*(35-d)+list(reversed(Q)))[:-1]
   assert len(p)==35
   for n in (1,2):
    v=0
    for i,c in enumerate(p):v^=m(sq(c),S[2*i+n-1])
    assert v==S[70+n-1];out['high_moment_checks']+=1
 forms=[sum(tr(m(EXP[h],1<<k))<<k for k in range(12)) for h in range(34)]
 for i in range(12):
  for j in range(12):
   for k in range(12):
    assert (forms[2*i+j]>>k)&1==tr(m(m(sq(1<<i),1<<j),1<<k));out['phase_basis']+=1
 print(json.dumps(out,indent=2));return out
if __name__=='__main__':test()
