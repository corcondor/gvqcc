import sys,subprocess,json
from pathlib import Path
import numpy as np,kickmix as km
b=km.CircuitBuilder();b.set_max_qubits(8)
q=list(b.create_quantum_register(4,'Q'));c=list(b.create_classical_register(2,'B'))
s=list(b.alloc_qubits(4))
b.ccx(q[0],q[1],s[0])
b.cx(s[0],s[1])
b.ccx(q[0],q[1],s[2])
b.ccz(q[0],q[1],q[2])
b.ccx(q[0],q[1],s[2])
b.cx(s[0],s[1])
b.ccx(q[0],q[1],s[0])
b.ccx(q[2],q[3],s[3]);b.ccx(q[2],q[3],s[3])
b.cx(c[0],s[1])
b.push_condition(c[0])
b.ccx(s[1],q[3],s[2]);b.ccz(s[1],q[2],q[3]);b.ccx(s[1],q[3],s[2])
b.pop_condition()
b.cx(c[0],s[1])
b.ccx(q[0],q[2],s[3]);b.del_and(q[0],q[2],s[3])
b.free(km.array(s))
parent=b.finish_circuit();parent.to_file('/tmp/live_sample.kmb',format='kmb')
N=64
A=((np.arange(N,dtype=np.uint64)[None,:]>>np.arange(4,dtype=np.uint64)[:,None])&1).astype(bool)
B=((np.arange(N,dtype=np.uint64)[None,:]>>np.arange(4,6,dtype=np.uint64)[:,None])&1).astype(bool)
def run(c,seed):
    sim=km.Simulator(batch_size=N,seed=seed,debug_print=False,counting_operations=True);sim.use_same_registers_as(c)
    sim.write_across_shots(km.array(c.register_data['Q']),A);sim.write_across_shots(km.array(c.register_data['B']),B);sim.do(c)
    return [sim.read_across_shots(km.array([km.q(i) for i in range(c.num_qubits)])),sim.read_across_shots(km.array(c.register_data['B'])),sim.read_phase_flipped_across_shots()]
for mode in ('unitary','hmr'):
    path='/tmp/live_sample_'+mode+'.kmb'
    rep=json.loads(subprocess.check_output([sys.argv[1],'/tmp/live_sample.kmb',path,mode,'pairs']))
    cand=km.Circuit.from_file(path)
    assert rep['new_paid']<rep['old_paid']
    assert int(cand.operation_statistics().num_toffoli_like)==rep['new_paid']
    for seed in (11,97,1128,2026):
        assert all(np.array_equal(x,y) for x,y in zip(run(parent,seed),run(cand,seed)))
    if mode=='hmr':assert rep['hmr']>0
    print('LOCAL',mode,json.dumps(rep),'256 exact state/phase/public-bit comparisons',flush=True)
