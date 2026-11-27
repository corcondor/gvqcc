"""Exact invariant rank<=17 wrapper, using #231's fixed extension pad,
and native bounded reciprocal/parser with #237 rank42, HMR and rank15.
The gate acts on 70 syndrome words in place. Classical bit 0 carries
phase debt; no external syndrome measurement or selection.
"""
import numpy as np,kickmix as km,crt882 as C,joint_phase as J,joint_rank15 as R
import argparse,json,hashlib
from pathlib import Path
F=[623,2571,2939,624,675,3740,2092,2078,27,1267,579,2078,3758,2078,2078,0,3862,1,1]
P=[1876,1746,1528,3064,914,2168,335,3124,618,215,2580,812,2956,2986,3154,2188,3334,498,1175,719,3499,3972,2403,2903,3898,1918,101,2520,1304,1268,3086,819,3820,3038,3618,3000,3791,2715,2801,1409,2566,4079,3374,1986,2077,2864,70,692,1338,889,36,2585,2599,2137,3707,4039,378,4085,2832,3394,1731,2729,1989,3092,136,3956,1909,2657,1243,3508]
def filt(s):return [C.xor_word(C.m(c,int(s[i+j])) for j,c in enumerate(F)) for i in range(52)]
assert filt(P)==[0]*52 and all(C.evalp(F,x) for x in range(4096))
assert F[-1]==1
def inv(a):return C.inv(a)
def rec_ref(a):
 b=[inv(a[0])]
 for i in range(1,len(a)):
  b.append(C.m(b[0],C.xor_word(C.m(a[j],b[i-j]) for j in range(1,i+1))))
 return b
def guard_ref(s,k=17):
 a=filt(s);i=0
 while i<=2*k:
  p=next((p for p in range(i,len(a)) if a[p]),len(a))
  if p==len(a):return True
  d=p-i+1
  if i+2*d>2*k:return False
  a[p:]=rec_ref(a[p:]);i+=2*d
 return False
class Guard:
 def __init__(self,k=17):
  self.n=52;self.k=k;self.b=km.CircuitBuilder();self.b.set_max_qubits(900)
  self.data=[list(self.b.create_quantum_register(12,f'S{i}')) for i in range(70)]
  self.debt=self.b.create_classical_register(1,'debt')[0]
  self.w=self.data[18:];self.out=self.alloc(1)[0]
 def alloc(self,n):return list(self.b.alloc_qubits(n)) if n else []
 def free(self,a):
  if a:self.b.free(km.array(a))
 def mcx(self,c,t):
  n=len(c);b=self.b
  if n==0:b.x(t);return
  if n==1:b.cx(c[0],t);return
  if n==2:b.ccx(*c,t);return
  if n<=6:
   a=self.alloc(n-2);b.ccx(c[0],c[1],a[0])
   for j in range(2,n-1):b.ccx(a[j-2],c[j],a[j-1])
   b.ccx(a[-1],c[-1],t)
   for j in range(n-2,1,-1):b.del_and(a[j-2],c[j],a[j-1])
   b.del_and(c[0],c[1],a[0]);self.free(a);return
  h=n//2;a=self.alloc(2);self.mcx(c[:h],a[0]);self.mcx(c[h:],a[1]);b.ccx(*a,t);self.mcx(c[h:],a[1]);self.mcx(c[:h],a[0]);self.free(a)
 def zero(self,x,t):
  for q in x:self.b.x(q)
  self.mcx(x,t)
  for q in x:self.b.x(q)
 def mul(self,x,y,z):
  q=x+y+z
  for g,*a in C.GATES:getattr(self.b,('x','cx','ccx')[g])(*(q[i] for i in a))
 def invxor(self,x,y):
  t=self.alloc(15)
  J.arith(self.b,'inv12',x,y,t)
  self.free(t)
 def scale(self,x,f,fi,tmp):
  self.mul(x,f,tmp)
  for a,b in zip(x,tmp):self.b.swap(a,b)
  # Old x = new x * inverse(f), including zero payload.
  J.product_clear(self.b,x,fi,tmp,12,C.MOD)
 def reciprocal(self,p,active):
  b=self.b;a=self.w[p:self.n];f=self.alloc(12);g=self.alloc(12);b.x(f[0]);b.cx(active,f[0])
  for u,v in zip(a[0],f):b.ccx(active,u,v)
  self.invxor(f,g);tmp=self.alloc(12)
  for x in a[1:]:self.scale(x,g,f,tmp)
  # U^(3*5*17) = U^-1 modulo X^52 for U(0)=1, char 2.
  for k in (1,2,4):
   m=1<<k
   if m>=len(a):continue
   frame=tuple(C.gf_pow(1<<i,m,12,C.MOD) for i in range(12))
   for i in range(len(a)-1,m-1,-1):
    for j in range(1,i//m+1):
     t=i-m*j
     J.frame(b,a[j],frame)
     if t==0:
      for u,v in zip(a[j],a[i]):b.ccx(active,u,v)
      J.frame(b,a[j],frame,True)
     else:
      for u,v in zip(a[j],tmp):b.ccx(active,u,v)
      J.frame(b,a[j],frame,True);self.mul(a[t],tmp,a[i]);J.frame(b,a[j],frame)
      for u,v in zip(a[j],tmp):b.del_and(active,u,v)
      J.frame(b,a[j],frame,True)
  for x in a[1:]:self.scale(x,g,f,tmp)
  self.free(tmp)
  for u,v,z in zip(f,g,a[0]):b.cx(u,z);b.cx(v,z)
  for u,v in zip(f,g):b.swap(u,v)
  self.invxor(f,g);self.free(g)
  for u,v in zip(a[0],f):b.ccx(active,u,v)
  b.cx(active,f[0]);b.x(f[0]);self.free(f)
 def bound_ops(self,z,B,end):
  ops=[]
  for j in range(2,end+1,2):
   for i in range(0,j,2):
    p=(i+j)//2-1
    if p>=len(z):continue
    c=([B[i//2-1]] if i else [])+z[i:p]+[z[p]];ops.append((c,z[p],B[j//2-1]))
  return ops
 def apply_ops(self,ops,rev=False):
  for c,neg,t in (reversed(ops) if rev else ops):self.b.x(neg);self.mcx(c,t);self.b.x(neg)
 def active(self,p,t):
  z=self.alloc(p+1);B=self.alloc(p//2)
  for j in range(p+1):self.zero(self.w[j],z[j])
  ops=self.bound_ops(z,B,p);self.apply_ops(ops)
  for i in range(0,p+1,2):
   if 2*p-i+2>2*self.k:continue
   c=([B[i//2-1]] if i else [])+z[i:p]+[z[p]];self.b.x(z[p]);self.mcx(c,t);self.b.x(z[p])
  self.apply_ops(ops,True)
  for j in reversed(range(p+1)):self.zero(self.w[j],z[j])
  self.free(B);self.free(z)
 def tailzero(self,j,t):
  groups=[self.w[i:min(i+4,self.n)] for i in range(j,self.n,4)];g=self.alloc(len(groups))
  def one(gr,flag):
   z=self.alloc(len(gr))
   for x,f in zip(gr,z):self.zero(x,f)
   self.mcx(z,flag)
   for x,f in reversed(list(zip(gr,z))):self.zero(x,f)
   self.free(z)
  for gr,f in zip(groups,g):one(gr,f)
  self.mcx(g,t)
  for gr,f in reversed(list(zip(groups,g))):one(gr,f)
  self.free(g)
 def readout(self):
  z=self.alloc(2*self.k-1);B=self.alloc(self.k)
  for j in range(len(z)):self.zero(self.w[j],z[j])
  self.apply_ops(self.bound_ops(z,B,2*self.k))
  for j in reversed(range(len(z))):self.zero(self.w[j],z[j])
  self.free(z);t=self.alloc(1)[0]
  for j in range(0,2*self.k+1,2):
   self.tailzero(j,t)
   if j:self.b.ccx(B[j//2-1],t,self.out)
   else:self.b.cx(t,self.out)
   self.tailzero(j,t)
  self.free([t]);z=self.alloc(2*self.k-1)
  for j in range(len(z)):self.zero(self.w[j],z[j])
  self.apply_ops(self.bound_ops(z,B,2*self.k),True)
  for j in reversed(range(len(z))):self.zero(self.w[j],z[j])
  self.free(z);self.free(B)
 def transform(self,rev=False):
  for i in (range(52) if rev else reversed(range(52))):
   for j,v in enumerate(F[:-1]):
    if v:
     for a in range(12):
      for k in C.bits(C.m(v,1<<a)):self.b.cx(self.data[i+j][a],self.data[i+18][k])
 def emit(self):
  self.transform();a=self.alloc(1)[0]
  for p in range(2*self.k-1):
   self.active(p,a);self.reciprocal(p,a);self.active(p,a)
   if p%4==0:print('forward',p,flush=True)
  self.free([a]);self.readout()
  # F(E)S invariant under pad translation, so guard can be erased now.
  for j,v in enumerate(P[:18]):
   for k in C.bits(v):self.b.cx(self.out,self.data[j][k])
  self.b.cz(self.out,self.debt)
  self.readout();a=self.alloc(1)[0]
  for p in reversed(range(2*self.k-1)):
   self.active(p,a);self.reciprocal(p,a);self.active(p,a)
   if p%4==0:print('reverse',p,flush=True)
  self.free([a]);self.free([self.out]);self.transform(True);return self.b.finish_circuit()
def main():
 p=argparse.ArgumentParser();p.add_argument('--k',type=int,default=17);p.add_argument('--out',default='invariant247.kmb');a=p.parse_args()
 C.Compact=R.Rank15
 g=Guard(a.k);c=g.emit();path=Path(a.out);c.to_file(str(path),format='kmb');del g,c
 c=km.Circuit.from_file(str(path));r=dict(Q=c.num_qubits,ops=len(c),paid=int(c.operation_statistics().num_toffoli_like),sha256=hashlib.file_digest(path.open('rb'),'sha256').hexdigest());print(json.dumps(r),flush=True)
 rng=np.random.default_rng(248247);rows=[];truth=[]
 for w in range(36):
  for _ in range(2):
   x=rng.choice(np.arange(1,4096),w,replace=False).tolist();e=rng.integers(1,4096,w).tolist();s=C.moment(x,e);assert guard_ref(s,a.k)==(w<=a.k);rows.append(s);truth.append(w<=a.k)
 rows=np.asarray(rows,np.uint16);truth=np.array(truth);out=rows^(truth[:,None]*np.array(P,np.uint16))
 q=km.array([km.q(i) for i in range(840)]);anc=km.array([km.q(i) for i in range(840,c.num_qubits)]);debt=km.array([km.b(0)])
 def bits(x):return ((x[:,:,None]>>np.arange(12))&1).reshape(len(x),840).T.astype(bool)
 errs=np.zeros(4,int)
 for seed in (2,3):
  for st in range(0,len(rows),32):
   en=min(st+32,len(rows));t=rng.integers(0,2,(1,en-st)).astype(bool);sim=km.Simulator(batch_size=en-st,seed=seed+st,debug_print=False);sim.use_same_registers_as(c);sim.write_across_shots(q,bits(rows[st:en]));sim.write_across_shots(debt,t);sim.do(c)
   E=[(sim.read_across_shots(q)!=bits(out[st:en])).any(0),sim.read_across_shots(anc).any(0),(sim.read_across_shots(debt)!=t).any(0),sim.read_phase_flipped_across_shots()!=(t[0]&truth[st:en])];errs+=np.array([int(x.sum()) for x in E]);print('test',seed,st,errs.tolist(),flush=True)
 r.update(shots=2*len(rows),errors=errs.tolist());print(json.dumps(r),flush=True);path.with_suffix('.json').write_text(json.dumps(r,indent=2));assert not any(errs)
 Path('pad_words.txt').write_text(' '.join(map(str,P))+'\n')
if __name__=='__main__':main()
