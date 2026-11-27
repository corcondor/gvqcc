"""Native predicate for first/second repeated Hermite pole of pad0.
Uses existing #190 42-CCX GF12 product and an in-place GF(2) coordinate change.
Flag XORs the unsafe-chart predicate. Does not prove pad1 safe for every input.
"""
import json,hashlib,pathlib,numpy as np,kickmix as km
import direct_codec as D
from transport42_lean import gate_tape
from test_extension_padding import em,m,F,K
z=next(c|F for c in range(F) if m(c,c)^c^K==D.NODES[0])
def divide(p):
 q=[0]*(len(p)-1);q[-1]=p[-1]
 for i in range(len(q)-2,-1,-1):q[i]=p[i+1]^em(z,q[i+1])
 assert p[0]==em(z,q[0]);return q
Q=[divide(D.U)];Q.append(divide(Q[0]))
def jet(s):
 ans=[]
 for q in Q:
  v=0
  for c,a in zip(q,s):v^=em(c,int(a))
  ans.append(v)
 return ans
P=json.load(open('extension_padding_receipt.json'))['pads'][0]['padding'];pc=jet(P)
def unsafe(s):
 u,v=[a^b for a,b in zip(jet(s),pc)];a,b=u&4095,u>>12;norm=m(a,a)^m(a,b)^m(K,m(b,b));return em(norm,v)==em(b,em(u,u))
# 48 rows of the GF(2)-linear jet map, choose independent physical pivot columns.
rows=[0]*48
for t,q in enumerate(Q):
 for j,c in enumerate(q):
  for k in range(12):
   v=em(c,1<<k)
   for l in range(24):
    if v>>l&1:rows[24*t+l]|=1<<(12*j+k)
R=rows[:];piv=[]
for j in range(840):
 i=next((i for i in range(len(piv),48) if R[i]>>j&1),None)
 if i is None:continue
 k=len(piv);R[i],R[k]=R[k],R[i]
 for i in range(48):
  if i!=k and R[i]>>j&1:R[i]^=R[k]
 piv.append(j)
 if len(piv)==48:break
assert len(piv)==48
mat=[sum(((r>>p)&1)<<i for i,p in enumerate(piv)) for r in rows];ops=[]
for j in range(48):
 k=next(k for k in range(j,48) if mat[k]>>j&1)
 if k!=j:mat[k],mat[j]=mat[j],mat[k];ops.append(('swap',k,j))
 for k in range(48):
  if k!=j and mat[k]>>j&1:mat[k]^=mat[j];ops.append(('cx',j,k))
assert mat==[1<<j for j in range(48)]
b=km.CircuitBuilder();S=b.create_quantum_register(840,'data');tag=b.create_quantum_register(1,'tag')[0];reg=[S[j] for j in piv];nonp=set(range(840))-set(piv)
lin=[]
for op,j,k in reversed(ops):lin.append((op,reg[j],reg[k]))
for i,r in enumerate(rows):
 for j in sorted(nonp):
  if r>>j&1:lin.append(('cx',S[j],reg[i]))
for op,a,c in lin:getattr(b,op)(a,c)
for i,v in enumerate(pc):
 for k in range(24):
  if v>>k&1:b.x(reg[24*i+k])
a,c,v0,v1=[reg[12*j:12*j+12] for j in range(4)]
N=b.alloc_qubits(12);T=b.alloc_qubits(12);R=b.alloc_qubits(12);L=b.alloc_qubits(10);fl=b.alloc_qubits(2)
def square_xor(u,y,k=1):
 for i in range(12):
  v=m(k,m(1<<i,1<<i))
  for j in range(12):
   if v>>j&1:b.cx(u[i],y[j])
def norm():
 square_xor(a,N);square_xor(c,N,K);gate_tape(b,a,c,N)
def zero_test(x,f):
 b.x(x);b.ccx(x[0],x[1],L[0])
 for i in range(2,11):b.ccx(L[i-2],x[i],L[i-1])
 b.ccx(L[9],x[11],f)
 for i in range(10,1,-1):b.ccx(L[i-2],x[i],L[i-1])
 b.ccx(x[0],x[1],L[0]);b.x(x)
def test(i):
 if i==0:square_xor(a,T);square_xor(c,T,K)
 else:square_xor(c,T)
 gate_tape(b,N,(v0,v1)[i],R);gate_tape(b,c,T,R);zero_test(R,fl[i]);gate_tape(b,c,T,R);gate_tape(b,N,(v0,v1)[i],R)
 if i==0:square_xor(c,T,K);square_xor(a,T)
 else:square_xor(c,T)
norm();test(0);test(1);b.ccx(fl[0],fl[1],tag);test(1);test(0);norm();b.free(fl);b.free(L);b.free(R);b.free(T);b.free(N)
for i,v in enumerate(pc):
 for k in range(24):
  if v>>k&1:b.x(reg[24*i+k])
for op,a,c in reversed(lin):getattr(b,op)(a,c)
c=b.finish_circuit();path=pathlib.Path('two_pole_selector.kmb');c.to_file(str(path),format='kmb');c=km.Circuit.from_file(str(path))
S0=np.concatenate((np.load('adversarial_cases.npz')['S'],np.load('second_pole_cases.npz')['S']));rng=np.random.default_rng(14128);S0=np.concatenate((S0,rng.integers(0,F,(256,70),dtype=np.int64)));t=np.array([unsafe(s) for s in S0],bool);assert t[517:553].all();bits=((S0[:,:,None]>>np.arange(12))&1).reshape(len(S0),840).T.astype(bool);Qq=km.array([km.q(j) for j in range(840)]);Tq=km.array([km.q(840)]);Aq=km.array([km.q(j) for j in range(841,c.num_qubits)]);err=[0]*4;shots=0
for seed in (14129,14130):
 for st in range(0,len(S0),128):
  en=min(st+128,len(S0));dirty=rng.integers(0,2,en-st).astype(bool);sim=km.Simulator(batch_size=en-st,seed=seed+st,debug_print=False);sim.use_same_registers_as(c);sim.write_across_shots(Qq,bits[:,st:en]);sim.write_across_shots(Tq,dirty[None,:]);sim.do(c);er=[(sim.read_across_shots(Qq)!=bits[:,st:en]).any(0),sim.read_across_shots(Tq)[0]!=(dirty^t[st:en]),sim.read_across_shots(Aq).any(0),sim.read_phase_flipped_across_shots()];err=[x+int(y.sum()) for x,y in zip(err,er)];shots+=en-st
assert not any(err),err
r={'scope':'two chart predicate XOR; both chart conditions of pad0, no universal guarantee pad1','Q':c.num_qubits,'ops':len(c),'static_paid':int(c.operation_statistics().num_toffoli_like),'sha256':hashlib.file_digest(path.open('rb'),'sha256').hexdigest(),'shots':shots,'errors':err,'unsafe_inputs':int(t.sum()),'pad_jet':pc,'pivots':piv};print(r,flush=True);pathlib.Path('two_pole_selector.json').write_text(json.dumps(r,indent=2)+'\n')
