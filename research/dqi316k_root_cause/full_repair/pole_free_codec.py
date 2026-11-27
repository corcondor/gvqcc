"""Native 70-word infinity-CF codec; all weights, no finite Hermite chart.
Reuses bounded reciprocal and parser, extends parser using reversible counters.
This is the reversible encoder/decoder, NOT the complete DQI phase oracle.
"""
import argparse, pathlib,hashlib,json,time
import numpy as np,kickmix as km
from weight_guard import Guard,rec_ref
import direct_codec as D
class Codec(Guard):
 def __init__(self,n=70,k=35):
  self.n=self.total=n;self.k=k;self.b=km.CircuitBuilder();self.b.set_max_qubits(n*12+60);self.data=list(self.b.create_quantum_register(n*12,'data'));self.w=[self.data[i*12:i*12+12] for i in range(n)]
 def inc(self,c,z,reverse=False):
  js=list(range(len(c)-1,-1,-1))
  if reverse:js.reverse()
  for j in js:self.mcx([z]+c[:j],c[j])
 def large_bounds(self,p,B,reverse=False):
  b=self.b;count=self.alloc(6);z=self.alloc(1)[0];starts=list(range(0,p-1,2))
  if reverse:starts.reverse()
  for i in starts:
   end=(p+i)//2-1
   for j in range(i,end+1):
    self.zero(self.w[j],z);b.x(z)
    for q in count:b.x(q)
    self.mcx(([B[i//2-1]] if i else [])+count+[z],B[(2*j-i+2)//2-1])
    for q in count:b.x(q)
    self.inc(count,z);b.x(z);self.zero(self.w[j],z)
   for j in range(end,i-1,-1):
    self.zero(self.w[j],z);b.x(z);self.inc(count,z,True);b.x(z);self.zero(self.w[j],z)
  self.free([z]);self.free(count)
 def interval_zero(self,l,r,t):
  groups=[self.w[i:min(i+4,r)] for i in range(l,r,4)];g=self.alloc(len(groups))
  def one(gr,f):
   z=self.alloc(len(gr))
   for w,q in zip(gr,z):self.zero(w,q)
   self.mcx(z,f)
   for w,q in reversed(list(zip(gr,z))):self.zero(w,q)
   self.free(z)
  for gr,f in zip(groups,g):one(gr,f)
  self.mcx(g,t)
  for gr,f in reversed(list(zip(groups,g))):one(gr,f)
  self.free(g)
 def active(self,p,t):
  if p<=32:return super().active(p,t)
  b=self.b;B=self.alloc(p//2);self.large_bounds(p,B);f,z=self.alloc(2);self.zero(self.w[p],z);b.x(z)
  for i in range(0,p+1,2):
   if 2*p-i+2>2*self.k:continue
   self.interval_zero(i,p,f);self.mcx(([B[i//2-1]] if i else [])+[f,z],t);self.interval_zero(i,p,f)
  b.x(z);self.zero(self.w[p],z);self.free([f,z]);self.large_bounds(p,B,True);self.free(B)
 def emit(self,reverse=False):
  a=self.alloc(1)[0];ps=list(range(2*self.k-1))
  if reverse:ps.reverse()
  for p in ps:
   self.active(p,a);self.reciprocal(p,a);self.active(p,a)
   if p%4==0:print('stage',p,flush=True)
  self.free([a]);return self.b.finish_circuit()
def encode(s,k=35):
 a=list(map(int,s));i=0
 while i<2*k:
  p=next((p for p in range(i,len(a)) if a[p]),len(a));d=p-i+1
  if p==len(a) or i+2*d>2*k:break
  a[p:]=rec_ref(a[p:]);i+=2*d
 return a
def blocks(a,k=35):
 i=0;out=[]
 while i<2*k:
  p=next((p for p in range(i,len(a)) if a[p]),len(a));d=p-i+1
  if p==len(a) or i+2*d>2*k:break
  out.append((p,p+d+1,d));i+=2*d
 return out,i
def rational_from_code(a):
 bs,end=blocks(a);assert not any(a[end:]);N=[];P=[1]
 for p,q,d in reversed(bs):N,P=P,D.add(N,D.pmul(list(reversed(a[p:q])),P))
 return N,P,sum(d for _,_,d in bs)
def oracle_check(a,e):
 N,P,w=rational_from_code(a);assert w==len(e);assert len(P)-1==w
 dp=[v if k%2 else 0 for k,v in enumerate(P)][1:]
 for x,y in e.items():assert D.ev(P,x)==0 and D.div(D.ev(N,x),D.mul(x,D.ev(dp,x)))==y
def inputs():
 rng=np.random.default_rng(70893);a=[];known=[];labels=[]
 for w in range(36):
  for _ in range(3):
   e={int(x):int(y) for x,y in zip(rng.choice(np.arange(1,4096),w,replace=False),rng.integers(1,4096,w))};a.append(D.moments(e));known.append(e);labels.append(('random',w))
  if w>=2:
   xs=list(map(int,rng.choice(np.arange(1,4096),w,replace=False)));e=D.weights_for_n(xs,[1],False);a.append(D.moments(e));known.append(e);labels.append(('leading_zeros',w))
 for file in ('additional_cases.npz','exact_later_cases.npz','../affine/hybrid_cases.npz'):
  z=np.load(file)
  for s,w in zip(z['S'],z['weights']):
   e=D.forward_checked(list(map(int,s)))[4];assert len(e)==w;a.append(s.tolist());known.append(e);labels.append(('saved',int(w)))
 for _ in range(32):a.append(rng.integers(0,4096,70).tolist());known.append(None);labels.append(('arbitrary',0))
 return np.array(a,np.uint16),known,labels
def test(f,r):
 a,e,lab=inputs();t=time.time();code=np.array([encode(s) for s in a],np.uint16);checks=0
 for z,err in zip(code,e):
  if err is not None:oracle_check(list(map(int,z)),err);checks+=1
 print('classical rational verified',checks,flush=True)
 def bits(x):return ((x[:,:,None]>>np.arange(12))&1).reshape(len(x),840).T.astype(bool)
 A,B=bits(a),bits(code);q=km.array([km.q(i) for i in range(840)]);out=[]
 for path,src,dst in ((f,A,B),(r,B,A)):
  c=km.Circuit.from_file(str(path));anc=km.array([km.q(i) for i in range(840,c.num_qubits)]);errs=[0]*3;shots=0
  for seed in (70894,70895):
   for st in range(0,len(a),64):
    en=min(st+64,len(a));s=km.Simulator(batch_size=en-st,seed=seed+st,debug_print=False);s.use_same_registers_as(c);s.write_across_shots(q,src[:,st:en]);s.do(c);er=[(s.read_across_shots(q)!=dst[:,st:en]).any(0),s.read_across_shots(anc).any(0),s.read_phase_flipped_across_shots()];err=[int(x.sum()) for x in er];errs=[x+y for x,y in zip(errs,err)];shots+=en-st
    if any(err):print('FAIL',path,seed,st,err,flush=True)
  row=dict(file=str(path),Q=c.num_qubits,ops=len(c),static_paid=int(c.operation_statistics().num_toffoli_like),sha256=hashlib.file_digest(path.open('rb'),'sha256').hexdigest(),shots=shots,errors=errs);out.append(row);print(row,flush=True);del c
 result=dict(scope='complete all-weight reversible infinity-CF codec, not full DQI oracle',inputs=len(a),legal_inputs=checks,results=out,seconds=time.time()-t);pathlib.Path('pole_free_receipt.json').write_text(json.dumps(result,indent=2)+'\n');assert not any(sum(r['errors']) for r in out)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--test-only',action='store_true');p=a.parse_args();f=pathlib.Path('pole_free_fwd.kmb');r=pathlib.Path('pole_free_rev.kmb')
 if not p.test_only:
  for path,rev in ((f,False),(r,True)):
   c=Codec().emit(rev);c.to_file(str(path),format='kmb');print(path,c.num_qubits,len(c),c.operation_statistics().num_toffoli_like,flush=True);del c
 test(f,r)
