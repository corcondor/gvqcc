"""Exact official seed reconstruction and paired full native replay.
No candidate-dependent input selection or verifier modification for scoring.
"""
import sys,os,json,hashlib,time
from pathlib import Path
import numpy as np
import kickmix as km
sys.path.insert(0,'/tmp/fusion/google-verifiable-quantum-circuit-compilation/verifiers/dqi')
import verify_submission_dqi as V
import multiprocessing as mp
N=102400; B=256
spec=V.ProblemSpecDQI.benchmark_instance(num_shots=N)
table=V.FieldTables(km.GF2Field(12))
prob=V.optimal_dqi_weights(spec.m,spec.max_errors,spec.degree,spec.r)**2
paths=['joint_monotone.kmb','joint_alias.kmb','full_fft.kmb']
c=km.Circuit.from_file(paths[0])
h=V._circuit_sha256(c);assert h=='8db1fd9d2b03979e355659e8cf2df421c3938e44133a5b760c9e7242d5afe9b9'
seeds=np.random.SeedSequence(int(h,16),pool_size=8).generate_state(8*(N//B),dtype=np.uint64).reshape(-1,2,4)
def gen(i):
 r,s=[int.from_bytes(x,'little') for x in seeds[i]]
 S,M,P=V.sample_shots(spec,table,np.random.default_rng(r),B,prob)
 return S,M,P,s
def run(c,S,M,P,s):
 q,m,a=map(km.array,V.validate_registers(c,spec));sim=km.Simulator(batch_size=len(S),debug_print=False,counting_operations=True,seed=s);sim.use_same_registers_as(c)
 X=V.to_bits(S,12);Y=V.to_bits(M,12);sim.write_across_shots(q,X);sim.write_across_shots(m,Y);sim.do(c)
 return np.array([(sim.read_across_shots(q)!=X).any(0),sim.read_phase_flipped_across_shots()^P,sim.read_across_shots(a).any(0),(sim.read_across_shots(m)!=Y).any(0)]),int(sim.operation_statistics().num_toffoli_like)
def task(i):
 S,M,P,s=gen(i);E,T=run(c,S,M,P,s)
 idx=np.flatnonzero(E.any(0))
 if len(idx):
  np.savez_compressed(f'failure_batch_{i}.npz',S=S,M=M,P=P,idx=idx)
  return i,idx.tolist(),E[:,idx].T.astype(int).tolist(),T
 return i,[],[],T
if __name__=='__main__':
 out=[];paid=0
 with mp.get_context('fork').Pool(4) as pool:
  for j,(i,idx,E,T) in enumerate(pool.imap_unordered(task,range(N//B)),1):
   paid+=T
   if idx:
    out.append(dict(batch=i,indices=idx,errors=E))
    Path('failure_batches.json').write_text(json.dumps(out,indent=2))
    print('FAIL',out[-1],flush=True)
   if j%40==0:print('PROGRESS',j*B,flush=True)
 print('CAPTURE',json.dumps(dict(hash=h,shots=N,failures=out,mean_paid=paid/N)),flush=True)
 res=[]
 for f in out:
  i=f['batch'];S,M,P,s=gen(i)
  for name in paths:
   cc=km.Circuit.from_file(name);E,T=run(cc,S,M,P,s);res.append(dict(batch=i,path=name,sha=V._circuit_sha256(cc),errors=E.sum(1).tolist(),indices=np.flatnonzero(E.any(0)).tolist(),paid=T));del cc
  print('PAIRED',json.dumps(res),flush=True)
 Path('paired_failure_receipt.json').write_text(json.dumps(dict(hash=h,shots=N,failures=out,mean_paid=paid/N,paired=res),indent=2))

