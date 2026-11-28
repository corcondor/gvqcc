from arithmetic import masks
from collections import Counter
from functools import reduce
from itertools import combinations
from pathlib import Path
from operator import xor

def basis(xs):
 d={}
 for x in xs:
  while x:
   p=x.bit_length()
   if p in d:x^=d[p]
   else:d[p]=x;break
 return d
def rank(xs):return len(basis(xs))
def span(xs):
 s=[0]
 for x in xs:s+= [y^x for y in s]
 return s
def wedge(a,b,ij):return sum((((a>>i&1)*(b>>j&1))^((a>>j&1)*(b>>i&1)))<<k for k,(i,j) in enumerate(ij))
def coords(xs):
 d={}
 for j,x in enumerate(xs):
  v=1<<j
  while x:
   p=x.bit_length()
   if p in d:
    y,w=d[p];x^=y;v^=w
   else:
    d[p]=(x,v);break
  else:raise ValueError('dependent')
 def c(x):
  v=0
  while x:
   p=x.bit_length()
   y,w=d[p];x^=y;v^=w
  return v
 return c
def decomposable(p,ij,links):
 if not p:return False
 k=(p&-p).bit_length()-1
 i,j=ij[k]
 a=sum(1<<s for s,m in links[j] if p&m)
 b=sum(1<<s for s,m in links[i] if p&m)
 return p==wedge(a,b,ij)

for n in [5,6]:
 ins=list(masks(Path(f'd16/inputs_{14*n}.tsv')))
 for trip in combinations(range(14),3):
  ids=[k*n+j for k in trip for j in range(n)]
  xx=[v for k in ids for v in ins[k]]
  ib=list(basis(xx).values())
  if len(ib)!=12:continue
  co=coords(ib)
  ij=list(combinations(range(12),2))
  links=[[(j if i==s else i,1<<k) for k,(i,j) in enumerate(ij) if s in (i,j)] for s in range(12)]
  polar=[wedge(co(ins[k][0]),co(ins[k][1]),ij) for k in ids]
  assert rank(polar)==len(polar)
  dec=[i for i,x in enumerate(span(polar)) if decomposable(x,ij,links)]
  for file in ([Path('d16/outputs_70.tsv')] if n==5 else sorted(Path('d16').glob('*outputs_84.tsv'))):
   outs=[m for m, in masks(file)]
   rows=list(basis(sum((outs[k]>>b&1)<<j for j,k in enumerate(ids)) for b in range(max(outs).bit_length())).values())
   w=set(span(rows))
   print(n,trip,file.name,'rank',len(rows),'decomps',len(dec),'local',sum(i.bit_count()==1 for i in dec),'decInW',sum(i in w for i in dec),flush=True)
   if len(dec)>3*n:
    print('extra',[hex(i) for i in dec if i.bit_count()>1],flush=True)
