"""Direct D16 generator replacement: retain shared affine frames across products.
No extra quantum wires, no assumption about dirty targets or input weight.
"""
import sys,random,json,hashlib,io,tempfile
from pathlib import Path
from functools import reduce
from operator import xor
sys.path.insert(0,'/tmp/source/dqi')
import build,arithmetic,kickmix as km
def bits(v):
 while v:
  j=(v&-v).bit_length()-1;yield j;v^=1<<j
def parity(v):return v.bit_count()&1
class Frame:
 def __init__(self,wires):
  self.wires=wires;self.n=len(wires);self.rows=[1<<i for i in range(self.n)]
  self.inv=self.rows.copy()
 def cx(self,i,j,ops):
  assert i!=j
  self.rows[j]^=self.rows[i]
  # Each original coordinate's expression changes by substituting
  # old current j = new current j + new current i.
  for k in range(self.n):
   if self.inv[k]>>j&1:self.inv[k]^=1<<i
  ops.append(('CX',self.wires[i],self.wires[j]))
 def coordinates(self,mask):return reduce(xor,(self.inv[i] for i in bits(mask)),0)
 def column(self,mask):return sum(parity(row&mask)<<i for i,row in enumerate(self.rows))
 def pairplan(self,a,b):
  # In the current coordinates construct independent requested rows.
  A=self.coordinates(a);B=self.coordinates(b);best=None
  for i in bits(A):
   # applying row i <- A transports B's coefficients contragrediently
   BB=B^(A^(1<<i) if B>>i&1 else 0)
   for j in bits(BB & ~(1<<i)):
    c=(A.bit_count()+BB.bit_count()-2,i,j,A,BB)
    if best is None or c<best:best=c
  assert best is not None
  return best
 def pair(self,plan,ops):
  _,i,j,A,B=plan
  for k in bits(A^(1<<i)):self.cx(k,i,ops)
  for k in bits(B^(1<<j)):self.cx(k,j,ops)
  return i,j
 def direction(self,mask,ops):
  v=self.column(mask);t=(v&-v).bit_length()-1;assert t>=0
  for j in bits(v^(1<<t)):self.cx(t,j,ops)
  assert self.column(mask)==1<<t
  return t
 def central(self,masks,ops):
  piv=set()
  for w in masks:
   v=self.column(w);new=[j for j in bits(v) if j not in piv]
   if not new:continue
   p=new[0]
   for j in new[1:]:self.cx(p,j,ops)
   piv.add(p)
  assert all(set(bits(self.column(w)))<=piv for w in masks)
  return len(piv)
 def restore(self,ops):
  for i in range(self.n):
   if not self.rows[i]>>i&1:
    j=next(j for j in range(i+1,self.n) if self.rows[j]>>i&1)
    self.cx(i,j,ops);self.cx(j,i,ops);self.cx(i,j,ops)
   for j in range(self.n):
    if j!=i and self.rows[j]>>i&1:self.cx(i,j,ops)
  assert self.rows==[1<<i for i in range(self.n)]
def generate(w,terms,seed,central,greedy):
 I=Frame(w['input_wires']);O=Frame(w['output_wires']);ops=[]
 r=O.central([z for a,b,z in terms],ops) if central else None
 rng=random.Random(seed);remain=list(terms)
 if not greedy and seed:rng.shuffle(remain)
 while remain:
  if greedy:
   choices=[]
   for k,(a,b,z) in enumerate(remain):
    # Fast optimistic input count, exact output weight.
    A=I.coordinates(a);B=I.coordinates(b)
    choices.append((A.bit_count()+B.bit_count()+O.column(z).bit_count(),rng.random(),k))
   i=min(choices)[2]
  else:i=0
  a,b,z=remain.pop(i)
  i,j=I.pair(I.pairplan(a,b),ops);t=O.direction(z,ops)
  assert I.rows[i]==a and I.rows[j]==b
  ops.append(('CCX',I.wires[i],I.wires[j],O.wires[t]))
 I.restore(ops);O.restore(ops);return ops,r
def verify(w,terms,ops):
 # Exact ANF in the 36 independent input variables and every dirty
 # output variable. CCX controls never read any output coordinate.
 I=w['input_wires'];O=w['output_wires'];n=len(I);assert n==36
 pos={q:i for i,q in enumerate(I)}
 base=1<<n
 # Each linear input polynomial represented as a 36-bit mask.
 inrows={q:1<<i for i,q in enumerate(I)}
 # Quadratic ANF monomial index for unordered i,j (i=j gives linear).
 def prod(a,b):
  z=0
  for i in bits(a):
   for j in bits(b):
    lo,hi=sorted((i,j));z^=1<<(hi*(hi+1)//2+lo)
  return z
 offset=n*(n+1)//2
 outrows={q:1<<(offset+i) for i,q in enumerate(O)}
 want=outrows.copy()
 for a,b,c in terms:
  p=prod(a,b)
  for i in bits(c):want[O[i]]^=p
 for g,*q in ops:
  if g=='CX':
   a,b=q
   if b in inrows:assert a in inrows;inrows[b]^=inrows[a]
   else:assert a in outrows;outrows[b]^=outrows[a]
  else:
   a,b,t=q;assert a in inrows and b in inrows and t in outrows
   outrows[t]^=prod(inrows[a],inrows[b])
 assert all(inrows[q]==1<<i for i,q in enumerate(I)) and outrows==want
def emit(ops,stream):
 for g,*q in ops:stream.write((g+' '+' '.join(f'q{x}' for x in q)+'\n').encode())
results=[]
def optimized(stream,path):
 w=json.loads(path.read_text());inputs=list(arithmetic.masks(path.parent/w['input_forms']));outputs=list(arithmetic.masks(path.parent/w['output_forms']))
 terms=[(a,b,z) for (a,b),(z,) in zip(inputs,outputs,strict=True)]
 old=io.BytesIO();arithmetic.emit_product(old,path);old_ops=len(old.getvalue().splitlines())
 # Preserve a baseline fallback; optimize actual physical layouts independently.
 best=None
 for central in (False,True):
  for greedy,seed in [(False,0),(True,1),(True,2),(False,3)]:
   ops,r=generate(w,terms,seed,central,greedy)
   if best is None or len(ops)<len(best[0]):best=(ops,r,central,greedy,seed)
 ops,r,cent,gr,seed=best
 verify(w,terms,ops)
 new=len(ops)
 if new>=old_ops:stream.write(old.getvalue());new=old_ops
 else:emit(ops,stream)
 receipt=dict(site=path.name,old_ops=old_ops,new_ops=new,paid=len(terms),inputs=len(w['input_wires']),outputs=len(w['output_wires']),output_rank=r,central=cent,greedy=gr,seed=seed,exact_anf=True)
 results.append(receipt);print(json.dumps(receipt),flush=True)
def main():
 target=Path(sys.argv[1]);build.emit_product=optimized
 with tempfile.TemporaryDirectory(dir='/tmp') as d:
  k=Path(d)/'full.kmx'
  with k.open('wb') as f:build.write_assembly(f,False)
  c=km.Circuit.from_file(str(k),format='kmx');c.to_file(str(target),format='kmb')
  receipt=dict(scope='full 316K source rebuild, exact D16 shared affine-frame replacement',Q=c.num_qubits,ops=len(c),static_paid=int(c.operation_statistics().num_toffoli_like),sha256=hashlib.file_digest(target.open('rb'),'sha256').hexdigest(),sites=results)
  print(json.dumps(receipt),flush=True);target.with_suffix('.json').write_text(json.dumps(receipt,indent=2)+'\n')
if __name__=='__main__':main()
