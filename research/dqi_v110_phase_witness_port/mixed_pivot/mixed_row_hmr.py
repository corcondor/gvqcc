"""Conditionally erase g1 from an already-valid four-word pivot record."""
import hashlib,json
from pathlib import Path
import numpy as np
import kickmix as km
import crt882 as F
import joint_phase as J
from mixed_row_native import products

def build(delta,mode):
    b=km.CircuitBuilder()
    q=list(b.create_quantum_register(72,'retained'))
    gone=list(b.alloc_qubits(24))
    g=[q[:12],q[12:24]];tau=q[36:48]
    r=[q[48:60],q[60:72]]
    old=[gone[:12],gone[12:]]
    d2=F.m(delta,delta)
    coeff=[F.m(d2,1<<i) for i in range(12)]
    if mode=='undo':
        products(b,tau,g,old,True)
        for u,v in zip(r,old,strict=True):
            for i,x in enumerate(u):
                for j in F.bits(coeff[i]):b.cx(x,v[j])
    else:
        if mode=='production':
            m=[list(b.alloc_bits(12)) for i in range(2)]
        else:
            m=[list(b.create_classical_register(12,f'm{i}')) for i in range(2)]
        for i in range(2):
            b.hmr(old[i],m[i])
            if mode!='uncompensated':
                J.linearphase(b,r[i],m[i],coeff)
                J.prodphase(b,tau,g[i],m[i],12,F.MOD)
            if mode=='production':J.cclear(b,m[i])
    b.free(gone)
    return b.finish_circuit()

def test(delta,mode):
    p=Path(f'row_erase_{delta}_{mode}.kmb')
    build(delta,mode).to_file(str(p),format='kmb')
    c=km.Circuit.from_file(str(p))
    q=km.array([km.q(i) for i in range(96)])
    cl=km.array([km.b(i) for i in range(24)])
    d2=F.m(delta,delta);rng=np.random.default_rng(82286+delta); fl=0;neg=0
    for k in range(20):
        faulty=k>=16
        if faulty and mode in ('production','undo'):continue
        w=rng.integers(0,4096,(64,8))
        for i in range(64):
            for j in range(2):
                w[i,6+j]=F.m(d2,int(w[i,4+j]))^F.m(int(w[i,3]),int(w[i,j]))
        x=((w[:,:,None]>>np.arange(12))&1).reshape(64,96).T.astype(bool)
        fault=np.zeros_like(x[72:])
        if faulty:fault=rng.integers(0,2,fault.shape,dtype=bool)
        inp=x.copy();inp[72:]^=fault
        s=km.Simulator(batch_size=64,seed=1153+k,debug_print=False,counting_operations=True)
        s.use_same_registers_as(c);s.write_across_shots(q,inp);s.do(c)
        out=s.read_across_shots(q)
        assert (out[:72]==inp[:72]).all() and not out[72:].any()
        if mode in ('production','undo'):
            reference=np.zeros(64,dtype=bool)
        else:
            data=inp[72:] if mode=='uncompensated' else fault
            reference=np.logical_xor.reduce(data&s.read_across_shots(cl),axis=0)
        expected_paid=84 if mode=='undo' else 0
        assert s.operation_statistics().num_toffoli_like==64*expected_paid
        measured=s.read_phase_flipped_across_shots()
        assert np.array_equal(measured,reference)
        if faulty:neg+=int(measured.sum())
        else:fl+=int(measured.sum())
    return dict(mode=mode,delta=delta,width=c.num_qubits,paid=c.operation_statistics().num_toffoli_like,
                instructions=len(c),good_shots=1024,good_phase_flips=fl,
                negative_shots=256 if mode in ('diagnostic','uncompensated') else 0,
                negative_phase_flips=neg,sha256=hashlib.sha256(p.read_bytes()).hexdigest())

if __name__=='__main__':
    out=[test(d,m) for d in (1,1017) for m in ('undo','production','diagnostic','uncompensated')]
    assert all((x['good_phase_flips']>0)==(x['mode']=='uncompensated') for x in out)
    Path('mixed_hmr_receipt.json').write_text(json.dumps(out,indent=2)+'\n')
    print(out)
