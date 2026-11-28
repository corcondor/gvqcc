"""Raw-input complete rational replacement for the frozen 316K nonlinear region.
Uses #254 guarded key, #244 shared norm phase, #251 additive subspace basis.
No host selection on the syndrome. Prefix diagnostic is separate from full circuit.
"""
import sys,inspect,hashlib,json,time
from pathlib import Path
sys.path.insert(0,'/tmp/seam')
from build_team import Pipeline,install_j_min
import build_team
import kickmix as km
import crt882 as C,joint_phase as J,general_scan as G
from functools import lru_cache
Pipeline.configure()
src=inspect.getsource(install_j_min)
assert src.count('assert 3 <= j_min < 35')==1
exec(src.replace('assert 3 <= j_min < 35','assert 0 <= j_min < 35'),build_team.__dict__)
Pipeline.First3.emit_prefix=Pipeline.BaseExtractor.Direct.emit_prefix
Pipeline.First3.emit_closing=Pipeline.BaseExtractor.Direct.emit_closing
build_team.install_j_min(0)
Pipeline.emit_key_prefix=Pipeline.P.emit_key_prefix
Pipeline.emit_key_closing=Pipeline.P.emit_key_closing
U=list(Pipeline.P.Public.geometry()['U'])
assert len(U)==71 and all(C.evalp(U,x) for x in range(4096))
BETA=(1,70,1971,2939,2,140,3942,1701,4,280,3743,3402)
@lru_cache(None)
def cols(c,d=1):
 return tuple(C.gf_pow(C.m(c,1<<i),d,12,C.MOD) for i in range(12))
def lx(b,a,z,c):
 if not c:return
 if c==1:J.xor(b,a,z);return
 for i,v in enumerate(cols(c)):
  for j in C.bits(v):b.cx(a[i],z[j])
def frame(b,a,c,d=1,rev=False):
 if c!=1 or d!=1:J.frame(b,a,cols(c,d),rev)
def root7(b,f,w,rev=False):
 a=w[:4];u,v,r=w[4:]
 if not rev:
  for x in f:b.x(x)
  for j in range(4):
   x,y,z=f[3*j:3*j+3];b.ccx(x,y,u);b.ccx(u,z,a[j]);b.del_and(x,y,u)
  b.ccx(a[0],a[1],u);b.ccx(a[2],a[3],v);b.ccx(u,v,r)
 else:
  b.del_and(u,v,r);b.del_and(a[2],a[3],v);b.del_and(a[0],a[1],u)
  for j in range(3,-1,-1):
   x,y,z=f[3*j:3*j+3]
   mb=b.alloc_bits(1)[0];b.hmr(a[j],mb)
   b.push_condition(mb);b.ccz(x,y,z);b.pop_condition()
   b.bit_store(mb,False);b.free(mb)
  for x in f:b.x(x)
def kernel(b,f,d,p,work,mask):
 chain=work[:7];n=work[7:13];c=work[13:19];shared=work[19:35];up=shared[:12];g=shared[:6];w=shared[6:]
 root7(b,f,chain);r=chain[-1]
 G.masked(b,p,mask,up)
 J.frame(b,d,C.BASIS12,True);a,bb=d[:6],d[6:];left=a+up[:6];right=bb+up[6:]
 G.compute_tensor(b,left,right,n+c)
 sa=[G.gf(1<<i,1<<i) for i in range(6)];sb=[G.gf(C.K6,x) for x in sa]
 J.arith(b,'square',a,n,1,6,0x43);J.arith(b,'square',bb,n,C.K6,6,0x43)
 G.masked(b,p,mask,up)
 for x,y in zip(c,g):b.ccx(r,x,y)
 G.phase16(b,n,g,w)
 for x,y in zip(c,g):b.del_and(r,x,y)
 G.masked(b,p,mask,up)
 mb=J.measure(b,n+c);G.repay_tensor(b,left,right,mb);J.linearphase(b,a,mb[:6],sa);J.linearphase(b,bb,mb[:6],sb);J.cclear(b,mb)
 J.frame(b,d,C.BASIS12);G.masked(b,p,mask,up);root7(b,f,chain,True)
def fft(b,D,N,E):
 # Split the actual 36/35 physical coefficient words into square roots.
 words=[D[::2],D[1::2],N[::2],N[1::2]]
 assert [len(a) for a in words]==[18,18,18,17]
 A,B,P,Q=[a[0] for a in words]
 for a in words:
  for z in a:frame(b,z,1,2048)
 L=[0,1];S=[];NB=[[1]]
 for beta in BETA:
  c=C.evalp(L,beta);assert c
  S.append(tuple(C.m(x,C.inv(c)) for x in L))
  L=C.add(C.mul(L,L),[C.m(c,x) for x in L])
 for j in range(1,18):
  k=(j&-j).bit_length()-1;NB.append(C.mul(NB[j^(1<<k)],list(S[k])))
 assert all(len(v)==i+1 for i,v in enumerate(NB))
 def basis(a,rev=False):
  for i in (range(len(a)) if rev else range(len(a)-1,-1,-1)):
   d=NB[i][-1]
   if not rev:frame(b,a[i],C.inv(d))
   for j in range(i):lx(b,a[i],a[j],NB[i][j])
   if rev:frame(b,a[i],d)
 def shear(h,c,deg):
  for a in words:
   for j in range(h,min(len(a),deg+1)):lx(b,a[j],a[j-h],c)
 work=list(b.alloc_qubits(35));mask=list(b.alloc_bits(12));count=0
 def leaf(x):
  nonlocal count
  if not x:return
  j=C.log[x];r=C.gf_pow(x,2048,12,C.MOD)
  # Root A+sqrt(x) B; trace mask absorbs square and inverse U(x).
  frame(b,B,r);J.xor(b,B,A);lx(b,Q,P,r)
  for k in mask:b.bit_store(k,False)
  c=C.inv(C.evalp(U,x))
  for i,z in enumerate(cols(1,2)):
   for t in C.bits(C.m(c,z)):b.cx(E[j][t],mask[i])
  active=b.alloc_bits(1)[0];b.bit_store(active,False)
  for k in mask:b.bit_store(active,True,control=k)
  b.push_condition(active)
  kernel(b,A,B,P,work,mask)
  b.pop_condition()
  b.bit_store(active,False);b.free(active)
  for k in mask:b.bit_store(k,False)
  lx(b,Q,P,r);J.xor(b,B,A);frame(b,B,C.inv(r))
  count+=1
  if count%512==0:print('SCAN',count,b.num_allocated_qubits,flush=True)
 def dfs(k,x,deg):
  if not k:leaf(x);return
  h=1<<(k-1)
  if deg<h:
   dfs(k-1,x,deg);dfs(k-1,x^BETA[k-1],deg);return
  c=C.evalp(S[k-1],x)
  shear(h,c,deg);dfs(k-1,x,h-1);shear(h,1,deg);dfs(k-1,x^BETA[k-1],h-1);shear(h,c^1,deg)
 for a in words:basis(a)
 dfs(12,0,17);assert count==4095
 for a in words:basis(a,True)
 J.cclear(b,mask);b.free(km.array(work))
 for a in words:
  for z in a:frame(b,z,1,2)
def prefix_check(c,D,N,S):
 import numpy as np,random
 r=random.Random(259316);xs=[];v=[];sy=[]
 for w in range(36):
  for rep in range(2):
   X=r.sample(range(1,4096),w);V=[r.randrange(1,4096) for _ in X];xs.append(X);v.append(V);sy.append(C.moment(X,V))
 a=np.array(sy,np.uint16);bits=((a[:,:,None]>>np.arange(12))&1).reshape(len(a),840).T.astype(bool)
 sim=km.Simulator(batch_size=len(a),seed=123,debug_print=False);sim.use_same_registers_as(c);sim.write_across_shots(km.array(sum([list(x) for x in S],[])),bits);sim.do(c)
 def read(W):
  y=sim.read_across_shots(km.array(sum([list(x) for x in W],[]))).T.reshape(len(a),len(W),12)
  return (y*(1<<np.arange(12))).sum(2).tolist()
 DD,NN=read(D),read(N);bad=[]
 for i,(X,V) in enumerate(zip(xs,v)):
  d,n=DD[i],NN[i];der=[0]+[d[j] if j%2 else 0 for j in range(1,len(d))]
  for x,e in zip(X,V):
   den=C.m(C.evalp(U,x),C.evalp(der,x))
   if C.evalp(d,x) or not den or C.evalp(n,x)!=C.m(e,den):bad.append((i,len(X),x,e,den,C.evalp(n,x)))
  if len([x for x in range(1,4096) if C.evalp(d,x)==0])!=len(X):bad.append(('roots',i,len(X)))
 print('native prefix weighted rational check',len(a),len(bad),bad[:4],flush=True)
 assert not bad
import kernel_joint17
import central_schedule as CS
kernel=kernel_joint17.kernel
def main():
 b=km.CircuitBuilder();b.set_max_qubits(900)
 S=[list(b.create_quantum_register(12,f'S{i}')) for i in range(70)];E=[list(b.create_classical_register(12,f'E{i}')) for i in range(4095)]
 # Provider expects km.array registers for its own concatenation operations.
 S=[km.array(x) for x in S];E=[km.array(x) for x in E]
 CS.install(Pipeline.P.Synthesis)
 start=time.monotonic();key=Pipeline.emit_key_prefix(b,S,j_min=0,stage=lambda x:print('KEY',x,b.num_allocated_qubits,flush=True) if isinstance(x,str) else None)
 N=[list(x) for x in key['N']];D=[list(x) for x in key['D']]
 print('PREFIX',len(D),len(N),b.num_allocated_qubits,flush=True)
 if sys.argv[1]=='prefix':
  prefix_check(b.finish_circuit(),D,N,S);return
 fft(b,D,N,E)
 Pipeline.emit_key_closing(b,key,stage=lambda x:print('RETURN',x,b.num_allocated_qubits,flush=True) if isinstance(x,str) else None)
 assert b.num_allocated_qubits==840
 c=b.finish_circuit();p=Path(sys.argv[1]);c.to_file(str(p),format='kmb');stats=c.operation_statistics();r=dict(Q=c.num_qubits,ops=len(c),paid=int(stats.num_toffoli_like),sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),seconds=time.monotonic()-start)
 print('CORE',json.dumps(r),flush=True);p.with_suffix('.json').write_text(json.dumps(r,indent=2))
if __name__=='__main__':main()

