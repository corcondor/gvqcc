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

if __name__=="__main__":
    import sys
    root=Path(sys.argv[1])
    import json
    ledger=[]
    for p in sorted(root.glob("field_*_wiring_*.json")):
        w=json.loads(p.read_text())
        ins=list(masks(root/w["input_forms"]))
        outs=[v for v, in masks(root/w["output_forms"])]
        assert len(ins)==len(outs) and len(ins) in (70,84)
        n=len(ins)//14
        pair_ranks=Counter()
        g=[[v for a in ins[k:k+n] for v in a] for k in range(0,len(ins),n)]
        for a,b in combinations(g,2):pair_ranks[rank(a+b)]+=1
        triples12=[]
        for a,b,c in combinations(range(14),3):
            r=rank(g[a]+g[b]+g[c])
            assert r in (12,18)
            if r==12:triples12.append([a,b,c])
        for k, group in enumerate(g):
            ids=list(range(k*n,(k+1)*n))
            ib=list(basis(group).values())
            assert len(ib)==6
            co=coords(ib)
            ij=list(combinations(range(6),2))
            links=[[(j if i==s else i,1<<k) for k,(i,j) in enumerate(ij) if s in (i,j)] for s in range(6)]
            polar=[wedge(co(ins[k][0]),co(ins[k][1]),ij) for k in ids]
            rows=list(basis(reduce(xor,(x for x,j in zip(polar,ids) if outs[j]>>b&1),0)
                        for b in range(max(outs).bit_length())).values())
            assert len(rows)==n-1 and not any(decomposable(x,ij,links) for x in span(rows))
        ledger.append(dict(block=p.name,local_groups=len(g),products=len(ins),lower_per_group=n,
                           pair_input_rank=dict(pair_ranks),rank12_triples_zero_based=triples12))
    print(json.dumps(ledger,indent=2))
