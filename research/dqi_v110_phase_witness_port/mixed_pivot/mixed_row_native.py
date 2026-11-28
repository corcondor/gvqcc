"""Serialized native g1-return shear, not the complete mixed pivot."""
import hashlib,json
from pathlib import Path
import numpy as np
import kickmix as km
import crt882 as F
import joint_phase as J

def scale(b,x,p):J.frame(b,x,[F.m(p,1<<i) for i in range(12)])

def products(b,lhs,g,r,shared):
    if not shared:
        for u,v in zip(g,r,strict=True):J.arith(b,'prod',lhs,u,v,12,F.MOD)
        return
    for code in F.CODES:
        a=code%64;y=code//64%64
        if code>=4096:
            assert a<12<=y<24 and 24<=code//4096-1<36
            z=code//4096-25
            for u,v in zip(g,r,strict=True):b.ccx(lhs[a],u[y-12],v[z])
        elif a<12:
            assert y<12;b.cx(lhs[a],lhs[y])
        elif a<24:
            assert 12<=y<24
            for g0 in g:b.cx(g0[a-12],g0[y-12])
        else:
            assert 24<=a<36 and 24<=y<36
            for out in r:b.cx(out[a-24],out[y-24])

def build(delta,rev,shared):
    b=km.CircuitBuilder()
    q=list(b.create_quantum_register(72,'words'))
    g=[q[:12],q[12:24]]
    # word 2 (rho) is a spectator; words 4,5 carry preexisting R(s).
    tau=q[36:48];r=[q[48:60],q[60:72]]
    d2=F.m(delta,delta)
    if not rev:
        for out in r:scale(b,out,d2)
    products(b,tau,g,r,shared)
    if rev:
        for out in r:scale(b,out,F.inv(d2))
    return b.finish_circuit()

def verify(delta,rev,shared):
    c=build(delta,rev,shared)
    k=Path(f'mixed_row_{delta}_{int(rev)}_{int(shared)}.kmb')
    c.to_file(str(k),format='kmb')
    t=km.Circuit.from_file(str(k))
    rng=np.random.default_rng(286+delta)
    q=km.array([km.q(i) for i in range(72)])
    d2=F.m(delta,delta);n=64
    def unpack(w):return ((w[:,:,None]>>np.arange(12))&1).reshape(len(w),72).T.astype(bool)
    for i in range(16):
        x=rng.integers(0,4096,(n,6),dtype=np.int32)
        ref=x.copy()
        for s,u in zip(ref,x,strict=True):
            for j in range(2):
                v=F.m(int(u[3]),int(u[j]))
                s[4+j]=F.m(F.inv(d2),int(u[4+j])^v) if rev else (F.m(d2,int(u[4+j]))^v)
        sim=km.Simulator(batch_size=n,seed=i,counting_operations=True,debug_print=False)
        sim.use_same_registers_as(t);sim.write_across_shots(q,unpack(x));sim.do(t)
        assert np.array_equal(sim.read_across_shots(q),unpack(ref))
        assert not sim.read_phase_flipped_across_shots().any()
        assert sim.operation_statistics().num_toffoli_like==84*n
    st=t.operation_statistics()
    assert st.num_toffoli_like==84
    return dict(delta=delta,reverse=rev,shared=shared,qubits=t.num_qubits,shots=1024,ccx=84,
                paid=84,standalone_t=st.num_t_like,instructions=len(t),
                sha256=hashlib.sha256(k.read_bytes()).hexdigest())

if __name__=='__main__':
    rows=[verify(d,r,s) for d in (1,1017) for r in (False,True) for s in (False,True)]
    Path('mixed_native_receipt.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(rows)
