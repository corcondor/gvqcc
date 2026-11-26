"""Joint signed-digit flag routing with genuinely clean high-word scratch.
5-bit truth-table care domain is exactly address8..31. All cubes are exact there.
"""
import split_carry as A
import itertools,functools
from collections import defaultdict

CUBES={}
for pat in itertools.product((-1,0,1),repeat=5):
 mask=sum(1<<a for a in range(24) if all(v<0 or (a+8)>>j&1==v for j,v in enumerate(pat)))
 if not mask:continue
 n=sum(v>=0 for v in pat);cost=max(0,n-1);score=(cost,n+2*sum(v==0 for v in pat))
 if mask not in CUBES or score<CUBES[mask][0]:CUBES[mask]=(score,[pat])
PAIRS={0:((0,0),[])}
for a,(sa,pa) in CUBES.items():
 for b,(sb,pb) in CUBES.items():
  z=a^b;s=(sa[0]+sb[0],sa[1]+sb[1])
  if z not in PAIRS or s<PAIRS[z][0]:PAIRS[z]=(s,pa+pb)
@functools.lru_cache(None)
def flag_plan(mask):
 if not mask:return (0,0),[]
 opts=[]
 if mask in CUBES:opts.append(CUBES[mask])
 if mask in PAIRS:opts.append(PAIRS[mask])
 for a,(sa,pa) in CUBES.items():
  if mask^a in PAIRS:
   sb,pb=PAIRS[mask^a];opts.append(((sa[0]+sb[0],sa[1]+sb[1]),pa+pb))
 if not opts:
  ans=[CUBES[1<<a]for a in range(24)if mask>>a&1];opts.append(((sum(x[0][0]for x in ans),sum(x[0][1]for x in ans)),sum((x[1]for x in ans),[])))
 return min(opts,key=lambda x:x[0])

def flag(b,mask,free):
 for pat in flag_plan(mask)[1]:
  cs=[17+j for j,v in enumerate(pat)if v>=0];neg=[17+j for j,v in enumerate(pat)if v==0]
  for q in neg:b.X(q)
  if len(cs)==0:b.X(A.FLAG)
  elif len(cs)==1:b.CX(cs[0],A.FLAG)
  elif len(cs)==2:b.CCX(*cs,A.FLAG)
  else:
   chain=[]
   for i in range(len(cs)-2):
    a,c=(cs[0],cs[1])if i==0 else(free[i-1],cs[i+1]);q=free[i];b.CCX(a,c,q);chain.append((q,a,c))
   b.CCX(free[len(cs)-3],cs[-1],A.FLAG)
   for q,a,c in reversed(chain):b.erase(q,[a,c])
  for q in reversed(neg):b.X(q)

def route(masks):
 rem=list(masks);out=[0]
 while rem:
  q=min(rem,key=lambda q:(flag_plan(out[-1]^q)[0],q));out.append(q);rem.remove(q)
 out.append(0)
 def score(p):return tuple(sum(flag_plan(a^b)[0][j]for a,b in zip(p,p[1:])) for j in range(2))
 cur=score(out)
 while True:
  best=cur;bp=None
  for i in range(1,len(out)-2):
   for j in range(i+1,len(out)-1):
    p=out[:i]+out[i:j+1][::-1]+out[j+1:];s=score(p)
    if s<best:best,bp=s,p
  if bp is None:return out[1:-1]
  cur,out=best,bp


def add_low(b,negative=False):
 groups=defaultdict(list);by={}
 for a,k in enumerate(A.H.CONSTANT):
  for j,d in A.H.naf(int(k)):
   if j<16:by[j,d]=by.get((j,d),0)|(1<<a)
 for (j,d),mask in by.items():groups[mask].append((j,d))
 order=route(list(groups));old=0
 if negative:order.reverse()
 for mask in order:
  flag(b,old^mask,A.HIGH);old=mask
  for j,d in groups[mask]:A.conditional_increment(b,A.LOW[j:],A.FLAG,A.HIGH,-d if negative else d)
 flag(b,old,A.HIGH)


def carry(b):
 ks={1<<a:int(k)&65535 for a,k in enumerate(A.H.CONSTANT)if int(k)&65535};old=0
 for mask in route(list(ks)):
  flag(b,old^mask,A.HIGH[1:]);old=mask
  A.compare_constant(b,ks[mask],A.HIGH[0],A.FLAG,A.HIGH[1:])
 flag(b,old,A.HIGH[1:])

if __name__=='__main__':
 A.add_low=add_low;A.carry=carry;A.main('_clean_lookup')
