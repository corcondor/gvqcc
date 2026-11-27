"""All-weight normalized phase scan, *packed-coordinate interface only*.
The syndrome-to-(D,K) reversible transform is not implemented here.
"""
import argparse,random,json
import numpy as np
import kickmix as km
import crt882 as C, joint_rank15 as R, joint_phase as J, guard4 as G

def pack(S):
 # Berlekamp-Massey on S_1,...,S_70, then B=[D*S(X)]_+.
 c=[1];b=[1];L=0;shift=1;prev=1
 for n,s in enumerate(S):
  d=s
  for i in range(1,L+1):
   if i<len(c):d^=C.m(c[i],S[n-i])
  if not d:shift+=1;continue
  old=c[:];c=C.add(c,[0]*shift+[C.m(C.m(d,C.inv(prev)),v) for v in b])
  if 2*L<=n:L=n+1-L;b=old;prev=d;shift=1
  else:shift+=1
 assert L<=35
 c+= [0]*(L+1-len(c))
 D=c[::-1]
 if L==0:return [0]*70
 B=[0]*L
 for j in range(L):
  for i in range(j+1,L+1):B[j]^=C.m(D[i],S[i-j-1])
 der=[D[i] if i%2 else 0 for i in range(1,L+1)]
 K=C.div(C.mul(der,C.inversemod(C.trim(B),D)),D)[1]
 dp=[0]*(35-L)+D
 return dp[:35]+K+[0]*(35-len(K))

def unpack_eval(p,x):
 if not (C.evalp(p[:35],x)^C.exp[(35*C.log[x])%4095]):
  k=C.evalp(p[35:],x)
  if k:return C.inv(C.m(x,k))
 return 0

def build(count):
 C.Compact=R.Rank15
 J.mask_cols=lambda x:tuple(C.m(C.inv(x),a) for a in C.BASIS12)
 b=km.CircuitBuilder();b.set_max_qubits(874)
 w=[list(b.create_quantum_register(12,f'S{i}')) for i in range(70)]
 m=[list(b.create_classical_register(12,f'E{i}')) for i in range(count)]
 tag,*work=list(b.alloc_qubits(34));b.x(tag)
 rolls=[tuple(C.m(C.exp[j],1<<i) for i in range(12)) for j in range(35)]
 for k in range(count):
  f,d=w[0],w[35];a=C.exp[(35*k)%4095]
  for j in range(1,35):J.xor(b,w[j],f);J.xor(b,w[35+j],d)
  for j in C.bits(a):b.x(f[j])
  G.kernel(b,f,d,tag,work,m[k],C.exp[k])
  for j in C.bits(a):b.x(f[j])
  for j in range(1,35):J.xor(b,w[j],f);J.xor(b,w[35+j],d)
  for j in range(1,35):J.frame(b,w[j],rolls[j]);J.frame(b,w[35+j],rolls[j])
 if count%4095:
  for j in range(1,35):
   co=C.exp[(-count*j)%4095];cols=tuple(C.m(co,1<<i) for i in range(12))
   J.frame(b,w[j],cols);J.frame(b,w[35+j],cols)
 b.x(tag);b.free(km.array([tag]+work))
 return b.finish_circuit()

def main():
 a=argparse.ArgumentParser();a.add_argument('--count',type=int,default=16);args=a.parse_args()
 rng=random.Random(20261128);cases=[]
 for w in range(36):
  n=min(w,args.count,4)
  loc=rng.sample(range(args.count),n)+rng.sample(range(args.count,4095),w-n)
  xs=[C.exp[i] for i in loc];es=[rng.randrange(1,4096) for _ in xs];p=pack(C.moment(xs,es))
  want=dict(zip(xs,es))
  assert all(unpack_eval(p,x)==want.get(x,0) for x in C.exp[:4095])
  cases.append((p,want))
 print(json.dumps(dict(algebra_cases=len(cases),algebra_points=len(cases)*4095)),flush=True)
 c=build(args.count);c.to_file(f'normalized_{args.count}.kmb',format='kmb')
 print(json.dumps(dict(Q=c.num_qubits,ops=len(c),static_paid=int(c.operation_statistics().num_toffoli_like),points=args.count,interface='packed coefficients only')),flush=True)
 # KickMix test: full packed register restored, phase from independently generated support.
 for seed in (17,31):
  n=len(cases);s=km.Simulator(batch_size=n,seed=seed,debug_print=False,counting_operations=True);s.use_same_registers_as(c)
  qin=np.asarray([[(v>>j)&1 for v in p for j in range(12)] for p,_ in cases],dtype=bool).T.copy()
  mask=np.asarray([[rng.randrange(4096) for _ in range(args.count)] for _ in cases],dtype=np.uint16)
  mb=((mask[:,:,None]>>np.arange(12))&1).reshape(n,-1).T.astype(bool)
  qi=[q for i in range(70) for q in c.get_quantum_register(f'S{i}')]
  ci=[v for i in range(args.count) for v in c.get_classical_register(f'E{i}')]
  s.write_across_shots(qi,qin);s.write_across_shots(ci,mb);s.do(c)
  phase=np.asarray([sum((int(mask[i,k])&want.get(C.exp[k],0)).bit_count() for k in range(args.count))%2 for i,(_,want) in enumerate(cases)],dtype=bool)
  assert np.array_equal(s.read_across_shots(qi),qin)
  assert np.array_equal(s.read_across_shots(ci),mb)
  assert np.array_equal(s.phase_across_shots(),phase)
 print('native phase PASS',flush=True)
if __name__=='__main__':main()
