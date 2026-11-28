import hashlib,json,subprocess,sys
import kickmix as km
import numpy as np
from pathlib import Path

# Dirty-target phase sandwich with changed input coordinates, copy and undo.
# The old CCX controls are NOT physically stable throughout the window.
b=km.CircuitBuilder()
b.set_max_qubits(7)
q=list(b.create_quantum_register(7,'Q'))
b.ccx(q[0],q[1],q[3])
b.cx(q[3],q[4])
b.cx(q[2],q[0])
b.x(q[1])
b.z(q[3])
b.cx(q[3],q[4])
b.x(q[1])
b.cx(q[2],q[0])
b.ccx(q[0],q[1],q[3])
c=b.finish_circuit()
c.to_file('/tmp/observer_sample.kmb',format='kmb')
subprocess.run([sys.argv[1],'/tmp/observer_sample.kmb','/tmp/observer_sample_new.kmb'],check=True)
a=km.Circuit.from_file('/tmp/observer_sample.kmb')
z=km.Circuit.from_file('/tmp/observer_sample_new.kmb')
assert int(a.operation_statistics().num_toffoli_like)==2
assert int(z.operation_statistics().num_toffoli_like)==0
X=((np.arange(128,dtype=np.uint64)[None,:]>>np.arange(7,dtype=np.uint64)[:,None])&1).astype(bool)
def run(c,seed):
    s=km.Simulator(batch_size=128,seed=seed,debug_print=False,counting_operations=True)
    s.use_same_registers_as(c)
    q=km.array([km.q(i) for i in range(7)])
    s.write_across_shots(q,X);s.do(c)
    return s.read_across_shots(q),s.read_phase_flipped_across_shots()
for seed in (11,97):
    u,v=run(a,seed);w,t=run(z,seed)
    assert np.array_equal(u,w) and np.array_equal(v,t)
print('AFFINE_OBSERVER_NATIVE_SAMPLE 256/256 exact, 2 -> 0 paid')
