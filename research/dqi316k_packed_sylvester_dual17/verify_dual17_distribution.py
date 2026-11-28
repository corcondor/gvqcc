"""Fixed-seed ordinary distribution; not official salted scoring."""
import hashlib,json,sys,numpy as np,kickmix as km
from pathlib import Path
import verify_submission_dqi as V
p=Path(sys.argv[1]);out=Path(sys.argv[2]);c=km.Circuit.from_file(str(p))
sp=V.ProblemSpecDQI.benchmark_instance(num_shots=1024);tables=V.FieldTables(km.GF2Field(12));q,b,anc=map(km.array,V.validate_registers(c,sp))
rng=np.random.default_rng(202611280825)
S,M,P=V.sample_shots(sp,tables,rng,1024)
res=dict(Q=c.num_qubits,ops=len(c),sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),shots=0,value=0,phase=0,dirty=0,mask=0,paid=0,static_paid=int(c.operation_statistics().num_toffoli_like),scope='fixed-seed distribution sampling, not official verifier')
for i in range(0,1024,64):
 a=V.to_bits(S[i:i+64],12);m=V.to_bits(M[i:i+64],12);phase=P[i:i+64]
 sim=km.Simulator(batch_size=64,seed=202611280825+i,debug_print=False,counting_operations=True);sim.use_same_registers_as(c);sim.write_across_shots(q,a);sim.write_across_shots(b,m);sim.do(c)
 errs=[(sim.read_across_shots(q)!=a).any(0),np.asarray(sim.read_phase_flipped_across_shots())!=phase,sim.read_across_shots(anc).any(0),(sim.read_across_shots(b)!=m).any(0)]
 for k,e in zip(('value','phase','dirty','mask'),errs):res[k]+=int(e.sum())
 res['paid']+=int(sim.operation_statistics().num_toffoli_like);res['shots']+=64
 print(res['shots'],[res[k] for k in ('value','phase','dirty','mask')],res['paid'],flush=True)
res['mean_paid']=res['paid']/res['shots'];res['pass']=not any(res[k] for k in ('value','phase','dirty','mask'));out.write_text(json.dumps(res,indent=2)+'\n');print(res)

