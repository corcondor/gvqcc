"""Call-by-need affine frame scheduler: a shared live context per bilinear tensor.
No change in nonlinear tensor terms; all affine contexts restored at return.
"""
from functools import lru_cache
import kickmix as km
def bits(x):
 while x:
  i=(x&-x).bit_length()-1;yield i;x^=1<<i
def parity(x):return x.bit_count()&1
class Frame:
 def __init__(self,n):
  self.n=n;self.rows=[1<<i for i in range(n)];self.inv=self.rows[:];self.tape=[]
 def cx(self,i,j,out,k):
  assert i!=j
  self.rows[j]^=self.rows[i]
  for h in range(self.n):
   if self.inv[h]>>j&1:self.inv[h]^=1<<i
  self.tape.append((i,j));out.append((0,k,i,j))
 def coord(self,v):
  a=0
  for i in bits(v):a^=self.inv[i]
  return a
 def vector(self,v):return sum(parity(r&v)<<i for i,r in enumerate(self.rows))
 def finish(self,out,k):
  for i,j in reversed(self.tape):out.append((0,k,i,j))
def choose(v):return (v&-v).bit_length()-1
@lru_cache(None)
def schedule(terms,n):
 A,B,T=[Frame(n) for _ in range(3)];frames=(A,B,T)
 todo=list(terms);out=[]
 while todo:
  candidates=[]
  for j,(a,b,c) in enumerate(todo):
   x,y,z=A.coord(a),B.coord(b),T.vector(c)
   assert x and y and z
   candidates.append((x.bit_count()+y.bit_count()+z.bit_count()-3,j,x,y,z))
  _,j,x,y,z=min(candidates)
  a,b,c=todo.pop(j);i,h,k=choose(x),choose(y),choose(z)
  for v in bits(x^(1<<i)):A.cx(v,i,out,0)
  for v in bits(y^(1<<h)):B.cx(v,h,out,1)
  for v in bits(z^(1<<k)):T.cx(k,v,out,2)
  assert A.rows[i]==a and B.rows[h]==b and T.vector(c)==1<<k
  out.append((1,i,h,k))
 for k,f in enumerate(frames):f.finish(out,k)
 # Exact symbolic certificate on all bilinear basis vectors and every linear restoration.
 for i in range(n):
  for j in range(n):
   a,b,z=1<<i,1<<j,0;v=[a,b,z]
   for op,k,x,y in out:
    if op==0:v[k]^=((v[k]>>x)&1)<<y
    else:v[2]^=(((v[0]>>k)&1)&((v[1]>>x)&1))<<y
   expect=0
   for x,y,z in terms:
    if x>>i&1 and y>>j&1:expect^=z
   assert v==[a,b,expect]
 for i in range(n):
  v=[0,0,1<<i]
  for op,k,x,y in out:
   if op==0:v[k]^=((v[k]>>x)&1)<<y
  assert v==[0,0,1<<i]
 return tuple(out)
def install(Synthesis):
 orig=Synthesis.accumulate_product;M=__import__(orig.__module__,fromlist=['multiplication_tensor']);terms=tuple(M.multiplication_tensor());tape=schedule(terms,12)
 oldcx=sum(2*(a.bit_count()+b.bit_count()+c.bit_count()-3) for a,b,c in terms)
 print('SCHEDULE42',dict(oldcx=oldcx,newcx=sum(x[0]==0 for x in tape),paid=sum(x[0]==1 for x in tape),basis_checks=144),flush=True)
 def emit(b,left,right,target,terms=None):
  regs=(list(left),list(right),list(target))
  if len(regs[0])!=12 or len(regs[1])!=12 or len(regs[2])!=12 or terms is not None:return orig(b,left,right,target,terms)
  assert len(set(sum(regs,[])))==36
  for op,k,i,j in tape:
   if op==0:b.cx(regs[k][i],regs[k][j])
   else:b.ccx(regs[0][k],regs[1][i],regs[2][j])
 Synthesis.accumulate_product=emit
 return tape

