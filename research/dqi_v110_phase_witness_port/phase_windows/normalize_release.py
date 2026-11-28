"""Re-price #261 normalization with no live inverse word at the adapter seam."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
import kickmix as km
import crt882 as C
import joint_phase as J

L=json.loads(Path('raw_audit.json').read_text())['layout']
physical=[i for word in L['D']+L['N'] for i in word]
assert sorted(physical)==list(range(852))

ODD = tuple(range(1,35,2))
EVEN_AND_TOP = (*range(0,35,2),70)
FULL = (*range(35),*range(36,71))
SPLIT = (ODD, EVEN_AND_TOP)

def build(mode, split):
    b=km.CircuitBuilder()
    b.set_max_qubits(900)
    p=list(b.create_quantum_register(865,'raw'))
    x=[p[i] for i in physical]
    lead=x[420:432]

    def borrow(n, forbidden=()):
        w=list(b.alloc_qubits(n))
        assert len(set(w))==n and set(w)<={km.q(i) for i in range(865,900)} and not set(w).intersection(forbidden),w
        for v in w:
            b.x(v)
        for v in reversed(w):
            b.x(v)
        b.free(w)

    def direction(back, indices, pair=False, phase_probe=False):
        inv=list(b.alloc_qubits(12))
        cc=C.Compact()
        cc.inv12(list(range(12)),list(range(12,24)),list(range(24,42)))
        def invxor():
            work=list(b.alloc_qubits(18))
            q=lead+inv+work
            for g,*args in cc.ops:
                getattr(b,('x','cx','ccx')[g])(*(q[i] for i in args))
            b.free(work)
        def sweep(back):
            tmp=list(b.alloc_qubits(12))
            f,g=(lead,inv) if back else (inv,lead)
            for i in indices:
                v=x[12*i:12*i+12]
                J.arith(b,'prod',v,f,tmp,12,C.MOD)
                for z,t in zip(v,tmp):
                    b.swap(z,t)
                J.product_clear(b,v,g,tmp,12,C.MOD)
            b.free(tmp)
        invxor()
        sweep(back)
        if pair:
            if phase_probe:
                borrow(11,inv)
            sweep(not back)
        invxor()
        b.free(inv)
        assert b.num_allocated_qubits==865

    plans=SPLIT if split else (FULL,)
    if mode=='seam_probe':
        assert split
        direction(False,ODD)
        borrow(35)  # All adapter workspace available before completing scale.
        direction(False,EVEN_AND_TOP,pair=True,phase_probe=True)
        borrow(35)  # All adapter workspace available for inverse, too.
        direction(True,ODD)
    else:
        if mode!='reverse':
            direction(False,plans[0])
        if mode=='midpoint_probe':
            borrow(35)
        if mode!='reverse':
            for inds in plans[1:]:
                direction(False,inds)
        if mode!='forward':
            for inds in reversed(plans):
                direction(True,inds)
    c=b.finish_circuit()
    p=Path(f'released_{mode}{"_split" if split else ""}.kmb')
    c.to_file(str(p),format='kmb')
    return c,p

def verify(mode, split=False):
    c,p=build(mode,split)
    scaled = set(ODD+EVEN_AND_TOP if split else FULL)
    rng=np.random.default_rng(31366)
    count=errors=paid=0
    q=km.array([km.q(i) for i in range(c.num_qubits)])
    for i in range(20):
        s0=rng.integers(0,4096,(64,71),dtype=np.uint16)
        s0[:,35]=rng.integers(1,4096,64,dtype=np.uint16)
        s1=[[C.m(int(x),C.inv(int(v[35]))) if j in scaled else x for j,x in enumerate(v)]for v in s0]
        def state(s):
            bits=(np.array(s,dtype=np.uint16)[:,:,None]>>np.arange(12)&1).reshape(64,852).T.astype(bool)
            ans=np.zeros((c.num_qubits,64),dtype=bool)
            ans[physical]=bits
            ans[852:865]=aux
            return ans
        aux=rng.integers(0,2,(13,64),dtype=bool)
        inputs=state(s1 if mode=='reverse' else s0)
        wanted=state(s1 if mode=='forward' else s0)
        for seed in (3170+i,9170+i):
            s=km.Simulator(batch_size=64,seed=seed,debug_print=False,counting_operations=True)
            s.use_same_registers_as(c)
            s.write_across_shots(q,inputs)
            s.do(c)
            errors+=int(((s.read_across_shots(q)!=wanted).any(0)|s.read_phase_flipped_across_shots()).sum())
            paid+=int(s.operation_statistics().num_toffoli_like)
            count+=64
    return dict(mode=mode,split=split,declared_Q=c.num_qubits,operations=len(c),
                CCX=dict(c.operation_statistics()).get('CCX',0),
                static_paid=int(c.operation_statistics().num_toffoli_like),
                mean_paid=paid/count,shots=count,errors=errors,
                sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest())

if __name__=='__main__':
    result=[verify(m,split) for split in (False,True) for m in ('forward','reverse','roundtrip','midpoint_probe')]
    result.append(verify('seam_probe',split=True))
    print(json.dumps(result,indent=2))
    assert not any(r['errors'] for r in result)
