# Independent replay of the published DQI sampling and score formula.
import os,sys,hashlib,json,math,multiprocessing as mp
import numpy as np
import kickmix as km
from scipy.stats import beta
path=sys.argv[1]; N=int(sys.argv[2]); batch=256
h=hashlib.file_digest(open(path,'rb'),'sha256').hexdigest()
c=km.Circuit.from_file(path)
reg=c.register_data
assert set(reg)=={f'S{i}' for i in range(70)}|{f'E{j}' for j in range(4095)}
q=km.array([v for i in range(70) for v in reg[f'S{i}']]); b=km.array([v for j in range(4095) for v in reg[f'E{j}']])
qset=set(q);a=km.array([km.q(i) for i in range(c.num_qubits) if km.q(i) not in qset])
field=km.GF2Field(12); ant=np.array([field.pow(field.primitive_element,i) for i in range(4095)],dtype=np.int64); log=np.zeros(4096,dtype=np.int64);log[ant]=np.arange(4095)
k=np.arange(36,dtype=float); off=np.sqrt(k[1:]*(4095-k[1:]+1));d=(4096-4032)/math.sqrt(2016*(4096-2016));_,ev=np.linalg.eigh(np.diag(k*d)+np.diag(off,1)+np.diag(off,-1));p=np.abs(ev[:,-1]);p/=np.linalg.norm(p);p=p*p
rows=np.arange(1,71,dtype=np.int64)[:,None]
def bits(v):return (((v[:,:,None]>>np.arange(12))&1)==1).transpose(1,2,0).reshape(-1,len(v))
def run(task):
 rs,ss=task;r=np.random.default_rng(rs); w=r.choice(36,size=batch,p=p);M=r.integers(0,4095,size=(batch,4095),endpoint=True,dtype=np.int64);S=np.zeros((batch,70),dtype=np.int64);phase=np.zeros(batch,dtype=bool)
 for j in np.flatnonzero(w):
  z=int(w[j]);pos=r.choice(4095,size=z,replace=False);v=r.integers(1,4095,size=z,endpoint=True,dtype=np.int64);S[j]=np.bitwise_xor.reduce(ant[(log[v][None,:]+rows*pos[None,:])%4095],axis=1);phase[j]=sum(int(x).bit_count() for x in v&M[j,pos])&1==1
 sim=km.Simulator(batch_size=batch,debug_print=False,counting_operations=True,seed=ss);sim.use_same_registers_as(c);x=bits(S);y=bits(M);sim.write_across_shots(q,x);sim.write_across_shots(b,y);sim.do(c);ve=(sim.read_across_shots(q)^x).any(0)|sim.read_across_shots(a).any(0);pe=(sim.read_phase_flipped_across_shots()^phase)&~ve;me=(sim.read_across_shots(b)^y).any(0);return int(ve.sum()),int(pe.sum()),int(me.sum()),int(sim.operation_statistics().num_toffoli_like)
if __name__=='__main__':
 seed=int(h,16); seeds=np.random.SeedSequence(seed,pool_size=8).generate_state(8*(N//batch),dtype=np.uint64).reshape(-1,2,4); tasks=[(int.from_bytes(s[0],'little'),int.from_bytes(s[1],'little')) for s in seeds]
 acc=np.zeros(4,dtype=np.int64);done=0
 with mp.get_context('fork').Pool(4) as pool:
  for r in pool.imap(run,tasks):
   acc+=r;done+=batch
   if done%8192==0 or done==N:
    err=int(acc[0]+acc[1]);eps=beta.isf(2.**-128,err+1,done-err) if err<done else 1.;R=math.log(2)/-math.log(.5+2*math.sqrt(eps)) if eps<1/16 else None;T=float(acc[3]/done);res=dict(sha256=h,shots=done,value=int(acc[0]),phase=int(acc[1]),mask=int(acc[2]),Q=c.num_qubits,static_paid=int(c.operation_statistics().num_toffoli_like),ops=len(c),T=T,eps=eps,R=R,score=R*c.num_qubits**2*T if R else None);print(json.dumps(res),flush=True);open('/tmp/direct_score.json','w').write(json.dumps(res,indent=2))
