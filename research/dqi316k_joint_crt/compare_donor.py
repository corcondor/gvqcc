"""Matched donor replay on the 96 G-all-pole cases; requires public verifier and pinned donor.
The standalone version was executed with the existing independent direct_codec.py
over GF(4096). Here the same generator is imported from joint_phase.py.
Run PYTHONPATH=<public verifier directory> python compare_donor.py donor.kmb receipt.json.
"""
import sys,pathlib,hashlib,json
import numpy as np,kickmix as km
import verify_submission_dqi as V
import joint_phase as J
path=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2])
rows,mags,flags=J.cases(4095,96)
n=96;count=4095
assert len(rows)==216 and all(flags[:n])
c=km.Circuit.from_file(str(path))
q,b,anc=map(km.array,V.validate_registers(c,V.ProblemSpecDQI.benchmark_instance()))
A=V.to_bits(np.asarray(rows[:n],dtype=np.int64),12)
rng=np.random.default_rng(697237);errors=[0]*4;union=paid=0;receipts=[];expected_counts=[0,0]
for seed in (681,937):
 for st in range(0,216,32):
  en=min(st+32,216);N0=en-st
  M=rng.integers(0,4096,(N0,count),dtype=np.uint16)
  if st>=n:continue
  assert en<=n
  if seed==681:
   for i in range(N0):
    if (st+i)%4==0:M[i]=0
    elif (st+i)%4==1:
     M[i]=0;pos=next(iter(mags[st+i]));M[i,pos]=1<<((st+i)%12)
  exp=np.array([sum((int(M[i,p])&v).bit_count() for p,v in mags[st+i].items())%2 for i in range(N0)],bool)
  mb=V.to_bits(M,12)
  s=km.Simulator(batch_size=N0,seed=seed+st,debug_print=False,counting_operations=True)
  s.use_same_registers_as(c);s.write_across_shots(q,A[:,st:en]);s.write_across_shots(b,mb);s.do(c)
  E=[(s.read_across_shots(q)!=A[:,st:en]).any(0),(s.read_across_shots(b)!=mb).any(0),s.read_across_shots(anc).any(0),s.read_phase_flipped_across_shots()!=exp]
  e=[int(v.sum()) for v in E];errors=[u+v for u,v in zip(errors,e)]
  u=int(np.logical_or.reduce(E).sum());union+=u;paid+=int(s.operation_statistics().num_toffoli_like)
  expected_counts[1]+=int(exp.sum());expected_counts[0]+=N0-int(exp.sum())
  z=dict(seed=seed,st=st,errors=e,union=u,shots=N0);receipts.append(z);print(z,flush=True)
res=dict(scope='matched legal G all-pole stratum only, not official distribution',sha256=hashlib.file_digest(path.open('rb'),'sha256').hexdigest(),Q=c.num_qubits,ops=len(c),static_paid=int(c.operation_statistics().num_toffoli_like),shots=192,errors=errors,union=union,mean_paid=paid/192,expected_phase_counts=expected_counts,batches=receipts)
out.write_text(json.dumps(res,indent=2)+'\n');print(json.dumps(res),flush=True)
