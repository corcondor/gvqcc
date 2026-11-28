"""Native quadratic-difference low-chart selector; requires prior chart_selector.py.
Run against the existing pinned fixture and generator tree. NOT full DQI.
"""
from chart_selector import Selector,h,J,em,K,mat_ops
import direct_codec as D
class Shared(Selector):
 def dirty_mcx(self,c,t,d):
  n=len(c);b=self.b
  if n<=2:return self.mcx(c,t)
  assert len(d)>=n-2 and len(set(map(str,list(c)+[t]+list(d[:n-2]))))==2*n-1
  chain=[(c[0],c[1],d[0])]+[(d[j-1],c[j+1],d[j]) for j in range(1,n-2)]
  for l in (chain,chain[1:]):
   for x,y,z in l:b.ccx(x,y,z)
   b.ccx(d[n-3],c[-1],t)
   for x,y,z in reversed(l):b.ccx(x,y,z)
 def dirty_zero(self,r,f,d):
  for q in r:self.b.x(q)
  self.dirty_mcx(r,f,d)
  for q in r:self.b.x(q)
 def evalH(self,reg,r):
  b=self.b;a,c,v0,v1=[reg[12*i:12*i+12] for i in range(4)];r0,r1=r[:12],r[12:]
  sq=[D.mul(1<<i,1<<i) for i in range(12)];sqK=[D.mul(K,z) for z in sq];kmul=mat_ops(tuple(D.mul(K,1<<i) for i in range(12)))
  def add(x,y):
   for u,v in zip(x,y):b.cx(u,v)
  self.xors(a,r0,sq);self.xors(c,r0,sqK);self.xors(c,r1,sq)
  add(a,v0);add(c,v1)
  add(c,a);add(r0,r1);self.mul(a,v0,r0);add(r0,r1);add(c,a)
  self.frame(c,kmul);self.mul(c,v1,r0);self.frame(c,kmul,True)
  add(v1,v0);self.mul(a,v0,r1);add(v1,v0)
  add(c,v1);add(a,v0)
 def emit(self):
  b=self.b;reg,ops=self.linear_frame(1);self.apply_frame(ops)
  d=[q for q in self.data if q not in reg][:22];assert len(d)==22
  r=self.alloc(24);f1,f2=self.alloc(2)
  p,q=J[0][:2];assert h(p,q)!=0
  def shift(t):
   for l,a in enumerate((p,q)):
    for k in range(24):
     if em(t,a)>>k&1:b.x(reg[24*l+k])
  def delta(s,t):
   const=h(em(s,p),em(s,q))^h(em(t,p),em(t,q));cols=[]
   for k in range(48):
    u=(1<<k) if k<24 else 0;v=(1<<(k-24)) if k>=24 else 0
    cols.append(h(u^em(s,p),v^em(s,q))^h(u^em(t,p),v^em(t,q))^const)
   self.xors(reg,r,cols)
   for k in range(24):
    if const>>k&1:b.x(r[k])
  shift(1);self.evalH(reg,r);shift(1)
  self.dirty_zero(r,f1,d);delta(1,2);self.dirty_zero(r,f2,d)
  b.x(self.out[0]);b.cx(f1,self.out[0]);b.cx(f1,self.out[1]);b.ccx(f1,f2,self.out[0])
  self.dirty_zero(r,f2,d);delta(1,2);self.dirty_zero(r,f1,d)
  shift(1);self.evalH(reg,r);shift(1)
  self.free([f1,f2]);self.free(r);self.apply_frame(ops,True);return b.finish_circuit()

class Split(Shared):
 def emit(self):
  b=self.b;reg,ops=self.linear_frame(1);self.apply_frame(ops)
  d=[q for q in self.data if q not in reg][:22];r=self.alloc(12);flags=self.alloc(4);p,q=J[0][:2]
  a,c,v0,v1=[reg[12*i:12*i+12] for i in range(4)]
  kmul=mat_ops(tuple(D.mul(K,1<<i) for i in range(12)))
  sq=[D.mul(1<<i,1<<i) for i in range(12)]
  def add(x,y):
   for u,v in zip(x,y):b.cx(u,v)
  def shift(t):
   for l,val in enumerate((p,q)):
    for k in range(24):
     if em(t,val)>>k&1:b.x(reg[24*l+k])
  def delta(s,t,k):
   const=h(em(s,p),em(s,q))^h(em(t,p),em(t,q));cols=[]
   for j in range(48):
    u=(1<<j) if j<24 else 0;v=(1<<(j-24)) if j>=24 else 0
    cols.append(((h(u^em(s,p),v^em(s,q))^h(u^em(t,p),v^em(t,q))^const)>>(12*k))&4095)
   self.xors(reg,r,cols)
   for j in range(12):
    if const>>(12*k+j)&1:b.x(r[j])
  def evaluate(k):
   if k==0:
    add(c,a);self.mul(a,v0,r);add(c,a)
    self.frame(v1,kmul);add(a,v1);self.mul(c,v1,r);add(a,v1);self.frame(v1,kmul,True)
   else:
    self.mul(a,v1,r);self.mul(c,v0,r);self.xors(c,r,sq)
  def test(k):
   shift(1);evaluate(k);shift(1);self.dirty_zero(r,flags[2*k],d)
   delta(1,2,k);self.dirty_zero(r,flags[2*k+1],d);delta(1,2,k)
   shift(1);evaluate(k);shift(1)
  test(0);test(1)
  b.x(self.out[0]);b.ccx(flags[0],flags[2],self.out[0]);b.ccx(flags[0],flags[2],self.out[1]);self.dirty_mcx(flags,self.out[0],d)
  test(1);test(0);self.free(flags);self.free(r);self.apply_frame(ops,True);return b.finish_circuit()
if __name__=='__main__':
 for cls,name in ((Shared,'delta_low3'),(Split,'split_low3')):
  c=cls('low').emit();c.to_file(name+'.kmb',format='kmb')
  print(name,c.num_qubits,len(c),c.operation_statistics().num_toffoli_like)
