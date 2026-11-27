import sys,json,hashlib
from pathlib import Path
import numpy as np,kickmix as km
import verify_submission_dqi as V
p=Path(sys.argv[1]);out=Path(sys.argv[2]);n=1024
spec=V.ProblemSpecDQI.benchmark_instance(num_shots=n)
t=V.FieldTables(km.GF2Field(12));rng=np.random.default_rng(202611280834)
S,M,P=V.sample_shots(spec,t,rng,n)
A,B=V.to_bits(S,12),V.to_bits(M,12)
c=km.Circuit.from_file(str(p));q,b,anc=map(km.array,V.validate_registers(c,spec))
r=dict(Q=c.num_qubits,ops=len(c),sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),shots=0,value=0,phase=0,dirty=0,mask=0,paid=0,static_paid=int(c.operation_statistics().num_toffoli_like),scope='fixed-seed distribution sampling, not official verifier')
for i in range(0,n,64):
 j=i+64
 sim=km.Simulator(batch_size=64,seed=202611280834+i,debug_print=False,counting_operations=True);sim.use_same_registers_as(c);sim.write_across_shots(q,A[:,i:j]);sim.write_across_shots(b,B[:,i:j]);sim.do(c)
 r['value']+=int((sim.read_across_shots(q)!=A[:,i:j]).any(0).sum());r['phase']+=int((np.asarray(sim.read_phase_flipped_across_shots())!=P[i:j]).sum());r['dirty']+=int(sim.read_across_shots(anc).any(0).sum());r['mask']+=int((sim.read_across_shots(b)!=B[:,i:j]).any(0).sum());r['paid']+=int(sim.operation_statistics().num_toffoli_like);r['shots']+=64
 print(r['shots'],r['value'],r['phase'],r['dirty'],r['mask'],flush=True)
r['mean_paid']=r['paid']/n;r['pass']=not any(r[k] for k in ('value','phase','dirty','mask'));out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)

