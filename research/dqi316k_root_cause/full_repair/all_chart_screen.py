"""Classical all-finite-chart screen used for native branch replay.
Do not count this host selector as a coherent circuit or its cost as zero.
Inputs are 70 moments and a legal-domain weight; weight selection in replay is
host-side and is NOT the native guard52 implementation.
"""
import direct_codec as D
from functools import reduce
xor=lambda vals:reduce(int.__xor__,vals,0)
def rational_from_moments(s,w):
 s=list(map(int,s));c,piv,_=D.solve([s[i:i+w] for i in range(70-w)],s[w:],range(w-1,-1,-1));assert len(piv)==w
 d=c+[1];p=D.trim([xor(D.mul(d[j],s[j-i-1]) for j in range(i+1,w+1)) for i in range(w)])
 return D.divrem(D.pmul(D.U,p),d)[1],d
def safe(s,w):
 n,d=rational_from_moments(s,w)
 for k in D.SLOTS:
  if not n:return len(d)==1
  nr,dr=D.rem(n,k),D.rem(d,k)
  if not nr:return False
  a,b=(nr+[0,0])[:2];norm=D.mul(a,a)^D.mul(a,b)^D.mul(k,D.mul(b,b));assert norm
  h=D.rem(D.pmul(dr,[D.div(a^b,norm),D.div(b,norm)]),k)
  q,r=D.divrem(D.add(d,D.pmul(h,n)),D.g(k));assert not r;n,d=q,n
 return len(n)<=1 and len(d)<=2
def rotate(s,t):
 p=t;r=[]
 for a in s:r.append(D.mul(int(a),p));p=D.mul(p,t)
 return r
def select(s,w,pad):
 for t in (range(1,136) if w<=17 else [D.EXP[i] for i in range(136)]):
  if w<=17:
   if safe([int(a)^D.mul(t,int(b)) for a,b in zip(s,pad)],w+18):return t
  elif safe(rotate(s,t),w):return t
 return None
