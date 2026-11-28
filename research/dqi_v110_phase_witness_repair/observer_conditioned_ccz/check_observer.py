from pathlib import Path
from tempfile import TemporaryDirectory
import json, subprocess, sys
import numpy as np
import kickmix as km

def build(guarded):
    b = km.CircuitBuilder()
    b.set_max_qubits(9)
    a,d,c,u,v,z,t = b.create_quantum_register(7,'Q')
    ctrl, = b.create_classical_register(1,'B')
    w, ab = b.alloc_qubits(2)
    b.ccx(a,d,ab)
    b.ccx(c,ab,w)
    b.ccx(a,d,ab)
    b.ccx(c,u,w)
    b.ccx(c,v,w)
    b.cx(z,w)
    b.ccx(c,z,w)
    if guarded: b.push_condition(ctrl)
    b.ccz(a,d,c)
    if guarded: b.pop_condition()
    return b.finish_circuit()

def replay(c):
    shot = np.arange(256, dtype=np.uint16)
    s = km.Simulator(batch_size=len(shot),seed=7,debug_print=False,counting_operations=True)
    s.use_same_registers_as(c)
    for reg, idx in [('Q',range(7)),('B',[7])]:
        s.write_across_shots(km.array(c.register_data[reg]),((shot[None,:]>>np.array(idx,dtype=np.uint16)[:,None])&1).astype(bool))
    s.do(c)
    return (s.read_across_shots(km.array([km.q(i) for i in range(c.num_qubits)])),
            s.read_across_shots(km.array(c.register_data['B'])),
            s.read_phase_flipped_across_shots())

def main():
    with TemporaryDirectory() as tmp:
        for guarded in (False,True):
            parent = build(guarded)
            base, cand = [str(Path(tmp)/f'{name}{guarded}.kmb') for name in ('base','cand')]
            parent.to_file(base,format='kmb')
            stats = json.loads(subprocess.check_output([sys.argv[1],base,cand,'unitary','pairs']))
            assert stats['observer_affine']==1,stats
            assert stats['active_CCZ']==1,stats
            after = km.Circuit.from_file(cand)
            before_count = int(parent.operation_statistics().num_toffoli_like)
            after_count = int(after.operation_statistics().num_toffoli_like)
            assert before_count-after_count>=1,(before_count,after_count)
            left,right=replay(parent),replay(after)
            assert all(np.array_equal(x,y) for x,y in zip(left,right))
            print(guarded,before_count,after_count,int(sum(left[2])),stats,flush=True)
main()
