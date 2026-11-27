"""900Q tag-free adaptive extension pads. Two disjoint root-free annihilators.
First Hermite pole excluded for every legal weight<=17, without retained tag.
Later poles are NOT guaranteed. Reuses exact invariant247 Guard.
"""
import invariant247 as I,crt882 as C,joint_rank15 as R
import numpy as np,kickmix as km
from pathlib import Path
import argparse,json,hashlib
m=C.m;F0=I.F.copy();P0=I.P.copy();K=2048
NODES=(3169,3257,3134,3302,3384,3431,3519,3552,3592,3633,3671,3727,3792,3854,3921,3977,4054)
def em(a,b):
 a0,a1=a&4095,a>>12;b0,b1=b&4095,b>>12;t=m(a1,b1)
 return (m(a0,b0)^m(K,t))|((m(a0,b1)^m(a1,b0)^t)<<12)
def conj(x):return x^(x>>12)
def ep(p,z):
 a=0
 for c in reversed(p):a=em(a,z)^c
 return a
def root(k):return next(c|4096 for c in range(4096) if m(c,c)^c^K==k)
U=[1]
for k in NODES:
 U=C.mul(U,[k,1,1]);U=C.mul(U,[k,1,1])
z=root(NODES[0])
Q=[0]*(len(U)-1);Q[-1]=U[-1]
for i in range(len(Q)-2,-1,-1):Q[i]=U[i+1]^em(z,Q[i+1])
assert U[0]==em(z,Q[0])
def jet(S):return C.xor_word(em(a,int(b)) for a,b in zip(Q,S))
u0=jet(P0);assert u0
rng=np.random.default_rng(247248)
F1=[1];P1=[0]*70;nodes=[]
while len(nodes)<9:
 c=int(rng.integers(0,4096));k=m(c,c)^c^K
 if k in NODES or k in nodes or ep(F0,c|4096)==0:continue
 nodes.append(k);F1=C.mul(F1,[k,1,1]);v=int(rng.integers(1,4096**2));p=c|4096
 for j in range(70):
  x=em(v,p);P1[j]^=x^conj(x);p=em(p,c|4096)
assert len(F1)==19 and F1[-1]==1 and all(C.evalp(F1,x) for x in range(4096))
assert jet(P1) not in (0,u0)
def filt(F,S):return [C.xor_word(m(c,int(S[i+j])) for j,c in enumerate(F)) for i in range(52)]
assert filt(F0,P0)==[0]*52 and filt(F1,P1)==[0]*52
# Irreducible roots for the two pad families are disjoint.
for k in nodes:assert ep(F0,root(k))!=0
class Adaptive(I.Guard):
 def __init__(self):
  super().__init__(17);self.debt1=self.b.create_classical_register(1,'debt1')[0];self.tag=self.alloc(1)[0]
 def linear_jet(self,a):
  b=self.b;x=self.alloc(24)
  for j,c in enumerate(Q):
   for k in range(12):
    for t in C.bits(em(c,1<<k)):b.cx(self.data[j][k],x[t])
  self.zero(x,a)
  for t in C.bits(u0):b.x(x[t])
  self.zero(x,a)
  for t in C.bits(u0):b.x(x[t])
  for j,c in enumerate(Q):
   for k in range(12):
    for t in C.bits(em(c,1<<k)):b.cx(self.data[j][k],x[t])
  self.free(x)
 def guarded(self,F,action,label):
  I.F=F
  self.transform();a=self.alloc(1)[0]
  for p in range(2*self.k-1):
   self.active(p,a);self.reciprocal(p,a);self.active(p,a)
   if p%8==0:print(label,'forward',p,flush=True)
  self.free([a]);self.readout();action(self.out);self.readout();a=self.alloc(1)[0]
  for p in reversed(range(2*self.k-1)):
   self.active(p,a);self.reciprocal(p,a);self.active(p,a)
   if p%8==0:print(label,'reverse',p,flush=True)
  self.free([a]);self.transform(True)
 def first(self):
  # a is invariant under P0 (u in {0,u0}); only pad when low & not a.
  b=self.b;a=self.alloc(1)[0];self.linear_jet(a)
  def action(low):
   b.ccx(low,a,self.tag)
   b.x(a)
   for j,v in enumerate(P0[:18]):
    for k in C.bits(v):b.ccx(low,a,self.data[j][k])
   b.ccz(low,a,self.debt)
   b.x(a)
  self.guarded(F0,action,'F0');self.linear_jet(a);self.free([a])
 def second(self,reverse):
  b=self.b
  def recognize(low):b.cx(low,self.tag)
  def translate():
   b.cz(self.tag,self.debt1)
   for j,v in enumerate(P1):
    for k in C.bits(v):b.cx(self.tag,self.data[j][k])
  if reverse:self.guarded(F1,recognize,'F1');translate()
  else:translate();self.guarded(F1,recognize,'F1')
 def emit(self,reverse=False):
  if reverse:self.second(True);self.first()
  else:self.first();self.second(False)
  self.free([self.tag,self.out]);return self.b.finish_circuit()
def make_cases():
 # Independently force first-pole cancellation after pad P0; use
 # two distinct base roots with nonzero 2x2 determinant.
 rng=np.random.default_rng(247249);rows=[];truth=[];labels=[]
 for w in (2,6,17,18,24,35):
  for rep in range(8):
   while True:
    xs=rng.choice(np.arange(1,4096),w,replace=False).tolist();es=rng.integers(1,4096,w).tolist();rhs=(u0 if w<=17 else 0)^jet(C.moment(xs[2:],es[2:]))
    a=jet(C.moment(xs[:1],[1]));b=jet(C.moment(xs[1:2],[1]));a0,a1=a&4095,a>>12;b0,b1=b&4095,b>>12;c0,c1=rhs&4095,rhs>>12
    det=m(a0,b1)^m(a1,b0)
    if not det:continue
    es[0]=m(m(c0,b1)^m(c1,b0),C.inv(det));es[1]=m(m(a0,c1)^m(a1,c0),C.inv(det))
    if all(es):break
   S=C.moment(xs,es);assert jet(S)==(u0 if w<=17 else 0)
   rows.append(S);truth.append(dict(zip(xs,es)));labels.append('low_pad0_pole' if w<=17 else 'high_first_pole')
 for w in range(36):
  xs=rng.choice(np.arange(1,4096),w,replace=False).tolist();es=rng.integers(1,4096,w).tolist();rows.append(C.moment(xs,es));truth.append(dict(zip(xs,es)));labels.append('random')
 # General allpole family, independent of the saved panel.
 for rep in range(8):
  xs=rng.choice(np.arange(1,4096),35,replace=False).tolist();D=[1]
  for x in xs:D=C.mul(D,[x,1])
  dp=[D[i] if i%2 else 0 for i in range(1,36)];a=int(rng.integers(1,4096))
  es=[m(a,C.inv(m(m(x,C.evalp(C.G,x)),C.evalp(dp,x)))) for x in xs]
  rows.append(C.moment(xs,es));truth.append(dict(zip(xs,es)));labels.append('high_allpole')
 S=np.asarray(rows,np.uint16);M=rng.integers(0,4096,(len(S),4095),dtype=np.uint16)
 log={x:i for i,x in enumerate(C.exp[:4095])}
 E=np.array([sum((int(M[i,log[x]])&v).bit_count() for x,v in e.items())%2 for i,e in enumerate(truth)],bool)
 W=np.array([len(e) for e in truth]);return S,M,W,E,np.array(labels)
def bits(v):return ((v[:,:,None]>>np.arange(12))&1).reshape(len(v),-1).T.astype(bool)
def main():
 p=argparse.ArgumentParser();p.add_argument('--part',choices=['pre','post','cases'],required=True);a=p.parse_args()
 Path('adaptive_pads.json').write_text(json.dumps(dict(F0=F0,F1=F1,P0=P0,P1=P1,u0=u0,u1=jet(P1)),indent=2))
 S,M,W,E,L=make_cases();np.savez_compressed('adaptive_stress.npz',S=S,M=M,weights=W,expected=E,labels=L)
 if a.part=='cases':return
 C.Compact=R.Rank15;c=Adaptive().emit(a.part=='post');path=Path('adaptive_'+a.part+'.kmb');c.to_file(str(path),format='kmb');del c;c=km.Circuit.from_file(str(path))
 A=np.array([jet(s) in (0,u0) for s in S]);low=W<=17;choose0=low&~A;choose1=low&A;O=S^(choose0[:,None]*np.array(P0,np.uint16))^(choose1[:,None]*np.array(P1,np.uint16))
 assert all(jet(s) for s in O[low])
 # Test the full wrapper with either phase debt bit, including inverse.
 q=km.array([km.q(i) for i in range(840)]);anc=km.array([km.q(i) for i in range(840,c.num_qubits)]);debt=km.array([km.b(0),km.b(1)])
 errs=[0]*4;rng=np.random.default_rng(247250)
 for seed in (821,822):
  for st in range(0,len(S),32):
   en=min(st+32,len(S));m0=rng.integers(0,2,(2,en-st)).astype(bool);sim=km.Simulator(batch_size=en-st,seed=seed+st,debug_print=False);sim.use_same_registers_as(c)
   src,dst=(O,S) if a.part=='post' else (S,O)
   sim.write_across_shots(q,bits(src[st:en]));sim.write_across_shots(debt,m0);sim.do(c)
   p=(m0[0]&choose0[st:en])^(m0[1]&choose1[st:en]);E=[(sim.read_across_shots(q)!=bits(dst[st:en])).any(0),sim.read_across_shots(anc).any(0),(sim.read_across_shots(debt)!=m0).any(0),sim.read_phase_flipped_across_shots()!=p]
   errs=[x+int(y.sum()) for x,y in zip(errs,E)];print('TEST',seed,st,errs,flush=True)
 r=dict(part=a.part,Q=c.num_qubits,ops=len(c),paid=int(c.operation_statistics().num_toffoli_like),sha256=hashlib.file_digest(path.open('rb'),'sha256').hexdigest(),shots=2*len(S),errors=errs,branches=[int(choose0.sum()),int(choose1.sum())])
 print(json.dumps(r),flush=True);path.with_suffix('.json').write_text(json.dumps(r,indent=2));assert not any(errs)
if __name__=='__main__':main()
