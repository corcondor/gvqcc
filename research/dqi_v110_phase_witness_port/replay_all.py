import sys,json,hashlib,numpy as np,kickmix as km,os
from pathlib import Path
sys.path.insert(0,os.environ['DQI_VERIFIER_DIR']);import verify_submission_dqi as V
p=Path(sys.argv[1]);c=km.Circuit.from_file(str(p));sp=V.ProblemSpecDQI.benchmark_instance();t=V.FieldTables(km.GF2Field(12));q,b,anc=V.validate_registers(c,sp);q,b=km.array(q),km.array(b)
rng=np.random.default_rng(125681)
R=[]
full='--all-weights' in sys.argv
for j in range(4):
 weights=np.repeat(np.arange(36),4) if full else np.r_[np.zeros(64,dtype=int),np.tile(np.arange(18,36),4)[:64]];n=len(weights);S=np.zeros((n,70),dtype=np.int64);M=rng.integers(0,4096,(n,4095),dtype=np.int64);P=np.zeros(n,dtype=bool)
 if j%2==0:M[:4 if full else 32]=0
 for i,w in enumerate(weights):
  if w:
   pos=rng.choice(4095,w,replace=False);val=rng.integers(1,4096,w,dtype=np.int64);S[i]=np.bitwise_xor.reduce(t.antilog[(t.log[val][None,:]+np.arange(1,71)[:,None]*pos[None,:])%4095],axis=1);P[i]=bool(sum(int(x).bit_count() for x in val&M[i,pos])&1)
 A=V.to_bits(S,12);B=V.to_bits(M,12);sim=km.Simulator(batch_size=n,seed=801+j,counting_operations=True);sim.use_same_registers_as(c);sim.write_across_shots(q,A);sim.write_across_shots(b,B);sim.do(c)
 v=(sim.read_across_shots(q)!=A).any(0);ph=np.asarray(sim.read_phase_flipped_across_shots())^P;dirty=sim.read_across_shots(anc).any(0);mb=(sim.read_across_shots(b)!=B).any(0)
 for label,sl in (([(str(w),weights==w) for w in range(36)]) if full else [('zero',weights==0),('high',weights>0)]):R.append(dict(seed=801+j,label=label,shots=int(sl.sum()),value=int(v[sl].sum()),phase=int(ph[sl].sum()),dirty=int(dirty[sl].sum()),mask=int(mb[sl].sum())))
 print(j,len(R),flush=True);Path(sys.argv[2]).write_text(json.dumps(dict(sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),Q=c.num_qubits,static_paid=c.operation_statistics().num_toffoli_like,results=R),indent=2))
