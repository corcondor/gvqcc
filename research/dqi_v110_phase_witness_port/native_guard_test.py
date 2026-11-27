"""Native 900Q verification; diagnostic panels, not the full official verifier."""
import hashlib, json, os, sys
from pathlib import Path
import kickmix as km
import numpy as np
from guard_audit import make, mul, pow_, xor_
sys.path.insert(0,os.environ['DQI_VERIFIER_DIR'])
import verify_submission_dqi as V

def inv(x):
    assert x
    r=1
    for b in bin(4094)[2:]:
        r=mul(r,r)
        if b=='1':r=mul(r,x)
    assert mul(x,r)==1
    return r
def multiply(xs):
    r=1
    for x in xs:r=mul(r,x)
    return r

exps=[1+37*i for i in range(35)]
xs=[pow_(2,i) for i in exps]
weights=[inv(mul(x,multiply(x^y for y in xs if y!=x))) for x in xs]
boundary=[xor_(mul(a,pow_(x,j)) for a,x in zip(weights,xs)) for j in range(1,71)]
assert boundary[:34]==[0]*34 and boundary[34]==1
witness=json.loads(Path(sys.argv[1]).read_text())
abstract=make()
inputs=np.array([[0]*70,boundary,abstract['input'],witness['native_rows'][0]['input']])
supports=[([],[]),(exps,weights),(abstract['exponents'],abstract['magnitudes']),
          (witness['error_indices'],witness['error_values'])]
A=V.to_bits(inputs,12)
rng=np.random.default_rng(1129333)
def one(path):
    circuit=km.Circuit.from_file(path)
    q,b,anc=V.validate_registers(circuit,V.ProblemSpecDQI.benchmark_instance())
    q,b=km.array(q),km.array(b)
    summary=[dict(shots=0,value=0,phase=0,dirty=0,mask=0,trigger_false35=0,trigger_false70=0,paid=0,CCX=0) for _ in inputs]
    for run in range(4):
        for j,(exps,weights) in enumerate(supports):
            n=16
            masks=np.random.default_rng(25001+run*4+j).integers(0,4096,(n,4095),dtype=np.int64)
            if run==0:masks[:]=0
            B=V.to_bits(masks,12)
            sim=km.Simulator(batch_size=n,seed=11611+run,counting_operations=True)
            sim.use_same_registers_as(circuit);sim.write_across_shots(q,np.repeat(A[:,j:j+1],n,axis=1));sim.write_across_shots(b,B);sim.do(circuit)
            yy=sim.read_across_shots(q)
            E=np.array([sum(int(int(a)&int(m[x])).bit_count() for x,a in zip(exps,weights))&1 for m in masks],dtype=bool)
            t=summary[j];t['shots']+=n
            t['value']+=int((yy!=A[:,j,None]).any(0).sum());t['phase']+=int((np.asarray(sim.read_phase_flipped_across_shots())^E).sum())
            t['dirty']+=int(sim.read_across_shots(anc).any(0).sum());t['mask']+=int((sim.read_across_shots(b)!=B).any(0).sum())
            if j:
                t['trigger_false35']+=int((~yy[:420].any(0)).sum());t['trigger_false70']+=int((~yy.any(0)).sum())
            st=sim.operation_statistics();t['paid']+=st.num_toffoli_like;t['CCX']+=dict(st).get('CCX',0)
    s=circuit.operation_statistics()
    return dict(sha256=hashlib.file_digest(open(path,'rb'),'sha256').hexdigest(),
                Q=circuit.num_qubits,static_paid=s.num_toffoli_like,static_CCX=dict(s)['CCX'],
                panels=dict(zip(('zero','w35_first34_zero','w12_abstract_input','w33_archived_input'),summary)))

if __name__=='__main__':
    print(json.dumps(one(sys.argv[2]),indent=2))
