"""Strict, full-tape regression for #266 and its gauge successor.
The archived #262 batch is reconstructed, not reselected from a new circuit.
Uses the exact official verifier and independent all-four-error checks.
"""
import hashlib,json,sys
from pathlib import Path
import numpy as np,kickmix as km
import verify_submission_dqi as V
p=Path(sys.argv[1]);out=Path(sys.argv[2])
c=km.Circuit.from_file(str(p));spec=V.ProblemSpecDQI.benchmark_instance(num_shots=256)
table=V.FieldTables(km.GF2Field(12))
q,m,a=map(km.array,V.validate_registers(c,spec))
h='8db1fd9d2b03979e355659e8cf2df421c3938e44133a5b760c9e7242d5afe9b9'
seeds=np.random.SeedSequence(int(h,16),pool_size=8).generate_state(8*400,dtype=np.uint64).reshape(-1,2,4)
r,s=[int.from_bytes(x,'little') for x in seeds[157]]
probs=V.optimal_dqi_weights(spec.m,spec.max_errors,spec.degree,spec.r)**2
S,M,P=V.sample_shots(spec,table,np.random.default_rng(r),256,probs)
fixture=json.loads(Path(sys.argv[3]).read_text())
assert S[244].tolist()==fixture['syndrome'] and bool(P[244])==fixture['expected_phase']
report=dict(sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),Q=c.num_qubits,ops=len(c),static_paid=int(c.operation_statistics().num_toffoli_like),panels={})
def run(name,X,Y,Z,seed):
    X=V.to_bits(X,12);Y=V.to_bits(Y,12)
    sim=km.Simulator(batch_size=len(Z),seed=seed,debug_print=False,counting_operations=True)
    sim.use_same_registers_as(c);sim.write_across_shots(q,X);sim.write_across_shots(m,Y);sim.do(c)
    errors=np.array([(sim.read_across_shots(q)!=X).any(0),sim.read_phase_flipped_across_shots()^Z,
                     sim.read_across_shots(a).any(0),(sim.read_across_shots(m)!=Y).any(0)])
    report['panels'][name]=dict(shots=len(Z),errors=errors.sum(1).tolist(),failed=np.flatnonzero(errors.any(0)).tolist(),
                                 mean_paid=int(sim.operation_statistics().num_toffoli_like)/len(Z))
    out.write_text(json.dumps(report,indent=2)+'\n')
    print(name,report['panels'][name],flush=True)
run('archived_official_batch_157',S,M,P,s)
A=np.repeat(S[244:245],256,axis=0);B=np.repeat(M[244:245],256,axis=0);B[:64]=0
xs=fixture['support'];es=fixture['magnitudes']
for k in range(64,128):
    B[k]=0;B[k,xs[(k-64)%len(xs)]]=1<<((k-64)%12)
B[192:]=np.random.default_rng(260259).integers(0,4096,(64,4095))
E=np.array([sum((int(v[j])&e).bit_count() for j,e in zip(xs,es))%2 for v in B],bool)
for seed in (1,2,s):run('captured_weight32_seed_'+str(seed),A,B,E,seed)
raise SystemExit(int(any(any(v['errors']) for v in report['panels'].values())))
