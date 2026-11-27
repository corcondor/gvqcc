from pathlib import Path
import sys, inspect, hashlib, json, time
from build_team import Pipeline, install_j_min, ORIGINAL_J_MIN, TEAM
import build_team
Pipeline.configure()
# Preserve the same low-level arithmetic and phase routines. Replace paired first-three fast chart with generic zero-safe rolling extractor, both directions.
src=inspect.getsource(install_j_min)
assert src.count('assert 3 <= j_min < 35')==1
exec(src.replace('assert 3 <= j_min < 35','assert 0 <= j_min < 35').replace('guarded=False','guarded=True'),build_team.__dict__)
Pipeline.First3.emit_prefix=Pipeline.BaseExtractor.Direct.emit_prefix
Pipeline.First3.emit_closing=Pipeline.BaseExtractor.Direct.emit_closing
build_team.install_j_min(0)
Pipeline.emit_key_prefix=Pipeline.P.emit_key_prefix
Pipeline.emit_key_closing=Pipeline.P.emit_key_closing
import kickmix as km
b=km.CircuitBuilder()
b.set_max_qubits(900)
S=[b.create_quantum_register(12,f'S{i}') for i in range(70)]
E=[b.create_classical_register(12,f'E{i}') for i in range(4095)]
start=time.monotonic()
def stage(x):
 if not isinstance(x,dict) or x.get('stage') not in ('extract_prefix','synthesis_prefix','extract_closing','synthesis_closing'):
  print('STAGE',str(x)[:240],b.num_allocated_qubits,flush=True)
key=Pipeline.emit_key_prefix(b,S,j_min=0,stage=stage)
D,N=key['D'],key['N']
print("registers",list(map(str,D[0])),list(map(str,N[0])),flush=True)
c=b.finish_circuit();print("prefix",len(c),c.num_qubits,flush=True)
sys.path.insert(0,"/tmp/native/google-verifiable-quantum-circuit-compilation/verifiers/dqi")
exec(Path("/tmp/verify_raw.py").read_text().split("rows=[]")[0],globals())
def ev(co,x):
 y=0
 for v in reversed(co):y=mul(y,x)^int(v)
 return y
cases0=[r for i,r in enumerate(cases()) if r[0]=="random" and i%4==0]
rows=[]
for tag,w,pos,v in cases0:
 S1=np.bitwise_xor.reduce(EXP[(LOG[v][None,:]+np.arange(1,71)[:,None]*pos[None,:])%4095],axis=1) if w else np.zeros(70,dtype=np.int64)
 rows.append((w,pos,v,S1))
SS=V.to_bits(np.array([r[3] for r in rows]),12)
sim=km.Simulator(batch_size=len(rows),seed=202611280834,debug_print=False,counting_operations=True)
sim.use_same_registers_as(c);sim.write_across_shots(km.array([q for word in S for q in word]),SS);sim.do(c)
def read_words(words):
 bits=sim.read_across_shots(km.array([q for word in words for q in word])).T.reshape(len(rows),len(words),12)
 return (bits*(1<<np.arange(12))).sum(axis=2)
Ds,Ns=read_words(D),read_words(N)

def trim(a):
 a=list(map(int,a))
 while a and not a[-1]:a.pop()
 return a
def rem(a,b):
 a=trim(a);b=trim(b)
 while len(a)>=len(b):
  z=mul(a[-1],int(EXP[(-int(LOG[b[-1]]))%4095]))
  k=len(a)-len(b)
  for j,x in enumerate(b):a[k+j]^=mul(x,z)
  a=trim(a)
 return a
def gcd(a,b):
 a=trim(a);b=trim(b)
 while b:a,b=b,rem(a,b)
 return a
res=[]
for i,(w,pos,v,S1) in enumerate(rows):
 d=trim(Ds[i]);n=trim(Ns[i]);g=gcd(d,n)
 rr=dict(w=w,degree_D=len(d)-1,degree_N=len(n)-1,degree_gcd=len(g)-1,expected_padding=35-w)
 res.append(rr);print(rr,flush=True)
Path('/tmp/key-prefix-gcd.json').write_text(json.dumps(res,indent=2))
