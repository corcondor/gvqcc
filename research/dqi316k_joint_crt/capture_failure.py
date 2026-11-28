# Independent replay of the published DQI sampling and score formula.
import os,sys,hashlib,json,math,multiprocessing as mp
import numpy as np
import kickmix as km
from scipy.stats import beta
path=sys.argv[1]; N=int(sys.argv[2]); batch=256; other=sys.argv[3]
h=hashlib.file_digest(open(path,'rb'),'sha256').hexdigest()
c=km.Circuit.from_file(path)
c2=c
reg=c.register_data
assert c2.register_data==reg and c2.num_qubits==c.num_qubits
assert set(reg)=={f'S{i}' for i in range(70)}|{f'E{j}' for j in range(4095)}
q=km.array([v for i in range(70) for v in reg[f'S{i}']]); b=km.array([v for j in range(4095) for v in reg[f'E{j}']])
qset=set(q);a=km.array([km.q(i) for i in range(c.num_qubits) if km.q(i) not in qset])
field=km.GF2Field(12); ant=np.array([field.pow(field.primitive_element,i) for i in range(4095)],dtype=np.int64); log=np.zeros(4096,dtype=np.int64);log[ant]=np.arange(4095)
k=np.arange(36,dtype=float); off=np.sqrt(k[1:]*(4095-k[1:]+1));d=(4096-4032)/math.sqrt(2016*(4096-2016));_,ev=np.linalg.eigh(np.diag(k*d)+np.diag(off,1)+np.diag(off,-1));p=np.abs(ev[:,-1]);p/=np.linalg.norm(p);p=p*p
rows=np.arange(1,71,dtype=np.int64)[:,None]
def bits(v):return (((v[:,:,None]>>np.arange(12))&1)==1).transpose(1,2,0).reshape(-1,len(v))
def run(task):
 rs,ss,forced=task;r=np.random.default_rng(rs); w=r.choice(36,size=batch,p=p);M=r.integers(0,4095,size=(batch,4095),endpoint=True,dtype=np.int64);w=w if not forced else (np.arange(batch)+rs%36)%36;S=np.zeros((batch,70),dtype=np.int64);phase=np.zeros(batch,dtype=bool)
 for j in np.flatnonzero(w):
  z=int(w[j]);pos=r.choice(4095,size=z,replace=False);v=r.integers(1,4095,size=z,endpoint=True,dtype=np.int64);S[j]=np.bitwise_xor.reduce(ant[(log[v][None,:]+rows*pos[None,:])%4095],axis=1);phase[j]=sum(int(x).bit_count() for x in v&M[j,pos])&1==1
 x=bits(S);y=bits(M)
 out=[]
 for circuit in (c,):
  sim=km.Simulator(batch_size=batch,debug_print=False,counting_operations=True,seed=ss);sim.use_same_registers_as(circuit);sim.write_across_shots(q,x);sim.write_across_shots(b,y);sim.do(circuit)
  z=sim.read_across_shots(q); anc=sim.read_across_shots(a); mask=sim.read_across_shots(b); ph=sim.read_phase_flipped_across_shots()
  ve=(z^x).any(0); ae=anc.any(0); pe=ph^phase; me=(mask^y).any(0)
  bad=ve|pe|ae|me
  if bad.any():
   np.savez_compressed(f"/tmp/fail_{int(rs)}_{int(forced)}.npz",S=S[bad],M=M[bad].astype(np.uint16),weights=w[bad],expected=phase[bad],output=(z.T.reshape(batch,70,12).astype(np.uint16)*(1<<np.arange(12))).sum(2)[bad],phase=ph[bad])
  out.append((z,anc,mask,ph,[int(ve.sum()),int(pe.sum()),int(ae.sum()),int(me.sum()),int((ve|pe|ae|me).sum()),int(sim.operation_statistics().num_toffoli_like)]))
 return forced,out[0][-1],out[0][-1],[0]*4

if __name__=='__main__':
 h2=hashlib.file_digest(open(other,'rb'),'sha256').hexdigest()
 seed=202611280745; seeds=np.random.SeedSequence(seed,pool_size=8).generate_state(8*(N//batch+4),dtype=np.uint64).reshape(-1,2,4); tasks=[(int.from_bytes(s[0],'little'),int.from_bytes(s[1],'little'),i<4) for i,s in enumerate(seeds)]
 acc={True:np.zeros((2,6),dtype=np.int64),False:np.zeros((2,6),dtype=np.int64)};diff={True:np.zeros(4,dtype=np.int64),False:np.zeros(4,dtype=np.int64)};done={True:0,False:0}
 with mp.get_context('fork').Pool(4) as pool:
  for force,o,n,d in pool.imap(run,tasks):
   acc[force]+=np.array([o,n]);diff[force]+=d;done[force]+=batch
   if force or done[False]%4096==0 or done[False]==N:
    arr=acc[force];D=done[force];out=[]
    for m in arr:
     err=int(m[4]);eps=beta.isf(2.**-128,err+1,D-err) if err<D else 1.;R=math.log(2)/-math.log(.5+2*math.sqrt(eps)) if eps<1/16 else None;T=float(m[5]/D)
     out.append(dict(value=int(m[0]),raw_phase=int(m[1]),ancilla=int(m[2]),mask=int(m[3]),union=int(m[4]),T=T,eps=eps,R=R,cost=R*c.num_qubits**2*T if R and not force else None))
    result=dict(forced=force,shots=D,sha256=[h,h2],Q=c.num_qubits,old=out[0],new=out[1],paired_bit_diffs=diff[force].tolist())
    print(json.dumps(result),flush=True);open('/tmp/scope_'+('forced' if force else 'score')+'.json','w').write(json.dumps(result,indent=2))

