"""SDK independent reproduction of phase-only S71 recurrence.
The 12-bit coefficient c is an input classical register. All P,S bits
are arbitrary dirty input, no raw-syndrome or whole-DQI splice."""
from pathlib import Path
import sys,json,random,hashlib
import numpy as np
import kickmix as km
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'dqi_frobenius_packed_return'))
from packed_return import mul as M, EXP
def tr(v):
    a=0
    for _ in range(12):a^=v;v=M(v,v)
    assert a in (0,1);return a
def xor(it):
    a=0
    for b in it:a^=b
    return a
forms=[sum(tr(M(1<<k,EXP[h]))<<k for k in range(12)) for h in range(23)]
for i in range(12):
    for j in range(12):
        for k in range(12):assert (forms[i+j]>>k)&1==tr(M(M(1<<i,1<<j),1<<k))
def run(d,rng):
    b=km.CircuitBuilder();b.set_max_qubits(24*d)
    p=list(b.create_quantum_register(12*d,'P'));s=list(b.create_quantum_register(12*d,'S'))
    c=list(b.create_classical_register(12,'C'));z=list(b.alloc_bits(23))
    for h,f in enumerate(forms):
        b.bit_store(z[h],False)
        for k in range(12):
            if f>>k&1:b.cx(c[k],z[h])
    for u in range(d):
        for i in range(12):
            for j in range(12):b.ccz(p[12*u+i],s[12*u+j],z[i+j])
    for a in z:b.bit_store(a,False)
    b.free(z);circ=b.finish_circuit()
    assert circ.num_qubits==24*d and int(circ.operation_statistics().num_toffoli_like)==0
    path=Path(__file__).with_name(f'dual71_{d}.kmb');circ.to_file(str(path),format='kmb');circ=km.Circuit.from_file(str(path))
    rows=[([rng.randrange(4096) for _ in range(d)],[rng.randrange(4096) for _ in range(d)],rng.randrange(4096)) for _ in range(256)]
    def pack(rows):
        return ((np.array(rows,dtype=np.uint16)[:,:,None]>>np.arange(12,dtype=np.uint16))&1).reshape(len(rows),-1).T.astype(bool)
    q=km.array([km.q(i) for i in range(24*d)])
    bc=km.array([km.b(i) for i in range(12)])
    A=pack([a+s for a,s,c in rows]);C=pack([[c] for a,s,c in rows]);E=np.array([tr(M(c,xor(M(x,y) for x,y in zip(a,s)))) for a,s,c in rows],dtype=bool)
    sim=km.Simulator(batch_size=len(rows),seed=17,debug_print=False,counting_operations=True);sim.use_same_registers_as(circ)
    sim.write_across_shots(q,A);sim.write_across_shots(bc,C);sim.do(circ)
    assert np.array_equal(sim.read_across_shots(q),A)
    assert np.array_equal(sim.read_across_shots(bc),C)
    assert np.array_equal(sim.read_phase_flipped_across_shots(),E)
    result=dict(d=d,Q=circ.num_qubits,paid=int(circ.operation_statistics().num_toffoli_like),ops=len(circ),shots=len(rows),errors=0,sha256=hashlib.sha256(path.read_bytes()).hexdigest());print(json.dumps(result),flush=True);return result
if __name__=='__main__':
    rng=random.Random(316085957);rec=[run(d,rng) for d in (1,4,8,17,24,35)]
    Path(__file__).with_name('dual_receipt.json').write_text(json.dumps(rec,indent=2)+'\n')
