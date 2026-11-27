from functools import lru_cache
from collections import defaultdict
from grouped_guard247 import one_block,optimal
@lru_cache(None)
def residue_plan(lo,hi,d,r):
 h0=(lo-r+d-1)//d;h1=(hi-r)//d
 ulo=(1-r+d-1)//d;uhi=(lo-1-r)//d
 j0=max(1,h0-uhi);j1=min(lo-1,h1-ulo)
 if h0>h1 or ulo>uhi or j0>j1:return 0,()
 dp={j0-1:(0,())}
 for k in range(j0,j1+1):
  opts=[]
  for j in range(j0,k+1):
   u0=max(ulo,h0-k);u1=min(uhi,h1-j)
   if u0>u1:continue
   num=sum(max(0,min(u1,h1-l)-max(u0,h0-l)+1) for l in range(j,k+1))
   na=42*num+12*(k-j+1)
   ev=54*(u1-u0+k-j+1)
   old,p=dp[j-1]
   if ev<na:opts.append((old+ev,p+((1,r,h0,h1,j,k,u0,u1),)))
   else:opts.append((old+na,p+((0,r,h0,h1,j,k,u0,u1),)))
  dp[k]=min(opts)
 return dp[j1]
@lru_cache(None)
def block_cost(lo,hi,d):
 singles,groups=one_block(lo,hi,d)
 base=sum(12 if t==0 else 54 for i,j,t in singles)
 cg=sum(42*len(v)+12 for v in groups.values())
 rr=[residue_plan(lo,hi,d,r) for r in range(d)]
 ev=sum(x[0] for x in rr)
 if ev<cg:
  return base+ev,tuple(v for x in rr for v in x[1])
 return base+cg,None
@lru_cache(None)
def plan(n,d):
 dp={d-1:(0,())}
 for hi in range(d,n):
  vals=[]
  for lo in range(d,hi+1):
   c,_=block_cost(lo,hi,d)
   v,p=dp[lo-1];vals.append((v+c,((lo,hi),)+p))
  dp[hi]=min(vals)
 return dp[n-1] if n>d else (0,())
if __name__=='__main__':
 total0=total1=blocks=evals=0
 for n in range(20,53):
  for d in (2,4,16):
   cost=0
   for lo,hi in optimal(n,d):
    s,g=one_block(lo,hi,d)
    cost+=sum(12 if t==0 else 54 for i,j,t in s)+sum(42*len(v)+12 for v in g.values())
   z,p=plan(n,d)
   total0+=cost;total1+=z
   for lo,hi in p:
    _,rr=block_cost(lo,hi,d)
    if rr is not None:
     blocks+=1;evals+=sum(t[0] for t in rr)
 print(total0,total1,'full savings',4*(total0-total1),'blocks',blocks,'eval chunks',evals)
