"""Bounded Laurent-CF rank predicate. Pure reversible X/CX/CCX/SWAP."""
import argparse,functools,hashlib,json,pathlib,time
import numpy as np,kickmix as km
import direct_codec as D
from transport42_lean import gate_tape
@functools.cache
def mat_ops(cols):
 n=len(cols);r=[sum(((cols[j]>>i)&1)<<j for j in range(n)) for i in range(n)];ops=[]
 for j in range(n):
  k=next(k for k in range(j,n) if r[k]>>j&1)
  if k!=j:r[k],r[j]=r[j],r[k];ops.append(('swap',k,j))
  for i in range(n):
   if i!=j and r[i]>>j&1:r[i]^=r[j];ops.append(('cx',j,i))
 assert r==[1<<i for i in range(n)];return tuple(reversed(ops))
def pw(x,n):
 a=1
 while n:
  if n&1:a=D.mul(a,x)
  x=D.mul(x,x);n>>=1
 return a
A=D.EXP[65];base=[pw(A,i) for i in range(6)];sub=[0]*64
for x in range(64):
 for i,v in enumerate(base):
  if x>>i&1:sub[x]^=v
subidx={v:k for k,v in enumerate(sub)};beta=next(x for x in range(4096) if x^pw(x,64)==1);kappa=subidx[D.mul(beta,beta)^beta];BASIS=mat_ops(tuple(base+[D.mul(beta,v) for v in base]))
def m6(a,b):return subidx[D.mul(sub[a],sub[b])]
ANF=[subidx[D.inv(x)] if x else 0 for x in sub]
for k in range(6):
 for x in range(64):
  if x>>k&1:ANF[x]^=ANF[x^(1<<k)]
def rec_ref(a):
 b=[D.inv(a[0])]
 for i in range(1,len(a)):
  s=0
  for j in range(1,i+1):s^=D.mul(a[j],b[i-j])
  b.append(D.mul(b[0],s))
 return b
def guard_ref(s,k):
 a=list(map(int,s));i=0
 while i<=2*k:
  p=next((p for p in range(i,len(a)) if a[p]),len(a))
  if p==len(a):return True
  d=p-i+1
  if i+2*d>2*k:return False
  a[p:]=rec_ref(a[p:]);i+=2*d
 return False
class Guard:
 def __init__(self,n,k,total=70):
  assert 2*k<n<=total and total<=70
  self.n=n;self.k=k;self.total=total;self.b=km.CircuitBuilder();self.b.set_max_qubits(total*12+60);self.data=list(self.b.create_quantum_register(total*12,'data'));self.w=[self.data[12*i:12*i+12] for i in range(total)];self.out=self.b.create_quantum_register(1,'low')[0]
 def frame(self,qs,ops,rev=False):
  for op,i,j in (reversed(ops) if rev else ops):getattr(self.b,op)(qs[i],qs[j])
 def xors(self,src,dst,cols):
  for i,x in enumerate(cols):
   for j in range(len(dst)):
    if x>>j&1:self.b.cx(src[i],dst[j])
 def alloc(self,n):return list(self.b.alloc_qubits(n)) if n else []
 def free(self,x):
  if x:self.b.free(km.array(x))
 def mcx(self,c,t):
  n=len(c);b=self.b
  if n==0:b.x(t);return
  if n==1:b.cx(c[0],t);return
  if n==2:b.ccx(*c,t);return
  if n<=6:
   a=self.alloc(n-2);b.ccx(c[0],c[1],a[0])
   for j in range(2,n-1):b.ccx(a[j-2],c[j],a[j-1])
   b.ccx(a[-1],c[-1],t)
   for j in range(n-2,1,-1):b.ccx(a[j-2],c[j],a[j-1])
   b.ccx(c[0],c[1],a[0]);self.free(a);return
  h=n//2;a=self.alloc(2);self.mcx(c[:h],a[0]);self.mcx(c[h:],a[1]);b.ccx(*a,t);self.mcx(c[h:],a[1]);self.mcx(c[:h],a[0]);self.free(a)
 def zero(self,x,t):
  for q in x:self.b.x(q)
  self.mcx(x,t)
  for q in x:self.b.x(q)
 def prod6(self,x,y,z):
  b=self.b
  for i in range(6):
   for j in range(6):
    v=m6(1<<i,1<<j);p=(v&-v).bit_length()-1;rest=[q for k,q in enumerate(z) if k!=p and v>>k&1]
    for q in rest:b.cx(z[p],q)
    b.ccx(x[i],y[j],z[p])
    for q in reversed(rest):b.cx(z[p],q)
 def inv6(self,x,y):
  b=self.b
  for j,v in enumerate(ANF):
   if not v:continue
   p=(v&-v).bit_length()-1;rest=[q for k,q in enumerate(y) if k!=p and v>>k&1]
   for q in rest:b.cx(y[p],q)
   self.mcx([q for k,q in enumerate(x) if j>>k&1],y[p])
   for q in reversed(rest):b.cx(y[p],q)
 def invxor(self,x,y):
  b=self.b;self.frame(x,BASIS,True);self.frame(y,BASIS,True);a,c=x[:6],x[6:];n=self.alloc(6);h=self.alloc(6)
  def norm():
   self.xors(a,n,[m6(1<<i,1<<i) for i in range(6)]);self.xors(c,n,[m6(kappa,m6(1<<i,1<<i)) for i in range(6)]);self.prod6(a,c,n)
  norm();self.inv6(n,h)
  for u,v in zip(c,a):b.cx(u,v)
  self.prod6(a,h,y[:6])
  for u,v in zip(c,a):b.cx(u,v)
  self.prod6(c,h,y[6:]);self.inv6(n,h);norm();self.free(h);self.free(n);self.frame(y,BASIS);self.frame(x,BASIS)
 def mul(self,x,y,z):gate_tape(self.b,x,y,z)
 def scale(self,x,f,fi,tmp):
  self.mul(x,f,tmp)
  for a,c in zip(x,tmp):self.b.swap(a,c)
  self.mul(x,fi,tmp)
 def reciprocal(self,p,active):
  b=self.b;a=self.w[p:self.n];f=self.alloc(12);g=self.alloc(12);b.x(f[0]);b.cx(active,f[0])
  for u,v in zip(a[0],f):b.ccx(active,u,v)
  self.invxor(f,g);tmp=self.alloc(12)
  for x in a[1:]:self.scale(x,g,f,tmp)
  # U^(3*5*17)=U^255=U^-1 modulo x^n, n<=70, U(0)=1.
  for k in (1,2,4):
   m=1<<k
   if m>=len(a):continue
   frame=mat_ops(tuple(pw(1<<i,m) for i in range(12)))
   for i in range(len(a)-1,m-1,-1):
    for j in range(1,i//m+1):
     t=i-m*j
     if t==0:
      self.frame(a[j],frame)
      for u,v in zip(a[j],a[i]):b.ccx(active,u,v)
      self.frame(a[j],frame,True)
     else:
      self.frame(a[j],frame)
      for u,v in zip(a[j],tmp):b.ccx(active,u,v)
      self.frame(a[j],frame,True);self.mul(a[t],tmp,a[i]);self.frame(a[j],frame)
      for u,v in zip(a[j],tmp):b.ccx(active,u,v)
      self.frame(a[j],frame,True)
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
 def emit(self):
  a=self.alloc(1)[0]
  for p in range(2*self.k-1):
   self.active(p,a);self.reciprocal(p,a);self.active(p,a)
   if p%4==0:print('forward',p,flush=True)
  self.free([a]);self.readout();a=self.alloc(1)[0]
  for p in reversed(range(2*self.k-1)):
   self.active(p,a);self.reciprocal(p,a);self.active(p,a)
   if p%4==0:print('reverse',p,flush=True)
  self.free([a]);return self.b.finish_circuit()
def test(c,n,k,total,extra=None):
 rng=np.random.default_rng(1783);rows=[];truth=[]
 for w in range(min(35,n-k)+1):
  for _ in range(4):
   e={int(x):int(y) for x,y in zip(rng.choice(np.arange(1,4096),w,replace=False),rng.integers(1,4096,w))};s=D.moments(e,total);assert guard_ref(s[:n],k)==(w<=k),(w,s);rows.append(s);truth.append(w<=k)
  if w>=2:
   xs=list(map(int,rng.choice(np.arange(1,4096),w,replace=False)));e=D.weights_for_n(xs,[1],False);s=D.moments(e,total);assert guard_ref(s[:n],k)==(w<=k);rows.append(s);truth.append(w<=k)
 if extra:
  for s,w in zip(np.load(extra)['S'],np.load(extra)['weights']):
   rows.append(list(s[:total]));truth.append(int(w)<=k);assert guard_ref(s[:n],k)==(int(w)<=k)
 for _ in range(32):
  s=rng.integers(0,4096,total).tolist();rows.append(s);truth.append(guard_ref(s[:n],k))
 rows=np.asarray(rows,np.uint16);bits=((rows[:,:,None]>>np.arange(12))&1).reshape(len(rows),total*12).T.astype(bool);truth=np.array(truth,bool);q=km.array([km.q(i) for i in range(total*12)]);tag=km.array([km.q(total*12)]);anc=km.array([km.q(i) for i in range(total*12+1,c.num_qubits)]);errors=[0]*4;shots=0
 for seed in (1937,1938):
  for st in range(0,len(rows),64):
   en=min(st+64,len(rows));dirty=rng.integers(0,2,en-st).astype(bool);s=km.Simulator(batch_size=en-st,seed=seed,debug_print=False);s.use_same_registers_as(c);s.write_across_shots(q,bits[:,st:en]);s.write_across_shots(tag,dirty[None,:]);s.do(c);flags=[(s.read_across_shots(q)!=bits[:,st:en]).any(0),s.read_across_shots(tag)[0]!=(dirty^truth[st:en]),s.read_across_shots(anc).any(0),s.read_phase_flipped_across_shots()];err=[int(f.sum()) for f in flags];errors=[x+y for x,y in zip(errors,err)];shots+=en-st;print('test',seed,st,en,err,flush=True)
 return dict(shots=shots,errors=errors,distinct_inputs=len(rows),positive_inputs=int(truth.sum()),negative_inputs=int((~truth).sum()))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--n',type=int,default=52);a.add_argument('--k',type=int,default=17);a.add_argument('--total',type=int,default=70);a.add_argument('--output',default='guard.kmb');a.add_argument('--extra');a.add_argument('--test-only',action='store_true');p=a.parse_args();out=pathlib.Path(p.output);t=time.time()
 if not p.test_only:
  g=Guard(p.n,p.k,p.total);c=g.emit();c.to_file(str(out),format='kmb');del g,c
 c=km.Circuit.from_file(str(out));r=dict(scope='exact bounded continued-fraction rank predicate; not full oracle',Q=c.num_qubits,ops=len(c),static_paid=int(c.operation_statistics().num_toffoli_like),sha256=hashlib.file_digest(out.open('rb'),'sha256').hexdigest(),n=p.n,k=p.k,total=p.total);print(r,flush=True);r.update(test(c,p.n,p.k,p.total,p.extra));r['seconds']=time.time()-t;out.with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n');print(r,flush=True);assert not any(r['errors'])
