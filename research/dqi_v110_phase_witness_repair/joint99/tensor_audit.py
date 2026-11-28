from collections import Counter,defaultdict
from itertools import combinations
from hashlib import sha256
import json
Q=900
CC=1<<Q
M=CC-1

def ids(x):
 while x:
  b=x&-x
  yield b.bit_length()-1
  x^=b
def rank(xs):
 bas={}
 for x in xs:
  while x:
   k=x.bit_length()
   if k in bas:x^=bas[k]
   else:bas[k]=x;break
 return len(bas)
def decomp(pairs):
 # For p(x)=sum a_i b_i, decompose its alternating polar into
 # one product per 2x2 pivot, and recover the exact affine residual.
 poly={}
 def flip(a,b):
  for i in ids(a):
   poly[i]=poly.get(i,0)^b
  for i in ids(b):
   poly[i]=poly.get(i,0)^a
 lin=0
 for a,b in pairs:
  x,y=a&M,b&M
  flip(x,y)
  lin^=(x&y)^(x if b&CC else 0)^(y if a&CC else 0)^(CC if a&b&CC else 0)
 out=[]
 while True:
  i=next((i for i,r in poly.items() if r),None)
  if i is None:break
  row=poly[i]; j=(row&-row).bit_length()-1
  a,b=row,poly[j]
  flip(a,b); lin^=a&b;out.append((a,b))
 return out,lin

def parse(path):
 meta=None; gates=[]
 for l in open(path):
  if l.startswith('#'):
   if meta is not None:yield meta,gates
   meta=list(map(int,l[1:].split()));gates=[]
  else:gates.append(tuple(map(int,l.split())))
 if meta is not None:yield meta,gates

def analyze(gates):
 aff=[1<<i for i in range(Q)]
 ds=[0]*Q; terms=[]; keys={}
 canon=[]
 nonlinear=0
 for op,a,b,t in gates:
  k=[]
  for q in ([a] if op==16 else [a,b] if op==33 else [a,b,t]):
   if q not in keys:keys[q]=len(keys)
   k.append(keys[q])
  canon.append((op,*k))
  if op==16:aff[a]^=CC
  elif op==33:aff[b]^=aff[a];ds[b]^=ds[a]
  elif op==49:
   nonlinear+=bool(ds[a]|ds[b]);ds[t]^=1<<len(terms);terms.append((aff[a],aff[b]))
  else:raise ValueError(op)
 sig=sha256(str(canon).encode()).hexdigest()
 if nonlinear:return dict(shape=sig,nonlinear=nonlinear,ops=len(gates))
 dirs=[0]*len(terms)
 for q,dd in enumerate(ds):
  for i in ids(dd):dirs[i]|=1<<q
 groups=defaultdict(list)
 for term,d in zip(terms,dirs):groups[d].append(term)
 sameout=sum(len(decomp(g)[0]) for d,g in groups.items() if d)
 sameprod=defaultdict(int)
 for (a,b),d in zip(terms,dirs):
  if a&b&M or a&CC or b&CC:pass # polar equivalence carries explicit affine debt
  reduced=tuple(sorted((a&M,b&M,(a^b)&M)))
  sameprod[reduced]^=d
 prod=sum(bool(d) and bool(p[0]) for p,d in sameprod.items())
 supports=set(i for a,b in terms for i in ids((a|b)&M))
 return dict(shape=sig,ops=len(gates),nonlinear=0,input_rank=rank(v&M for p in terms for v in p),n_input=len(supports),
             output_rank=rank(dirs),dirs=len(groups),after_same_output=sameout,after_same_polar=prod)

if __name__=='__main__':
 import sys
 for meta,g in parse(sys.argv[1]):print(json.dumps(dict(start=meta[0],end=meta[1],depth=meta[2],**analyze(g))))
