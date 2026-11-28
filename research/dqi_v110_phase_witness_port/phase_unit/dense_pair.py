"""Compare two dense monic Euclidean merges against an exact fused native map.

Inputs are live truncated Laurent frames, not computed from the syndrome here.
Two target sectors share the same coefficients. No phase, scratch, or host branching.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import kickmix as km
import crt882 as C
from toeplitz_native import LAYOUT, shear_shared

N=17


def actions(k, w):
    if len(w) <= 1:
        return []
    m=len(w)//2
    l,r=w[:m],w[m:]
    return actions(k,l)+[(k[1:len(w)][::-1],r[::-1],l)]+actions(k,r)


def frames(f,g):
    assert f[0]==g[0]==1
    return [_sum(C.m(f[j],g[i-j]) for j in range(i+1)) for i in range(N)]


def _sum(values):
    x=0
    for v in values:
        x^=int(v)
    return x


def tri(c, p):
    return [p[i] ^ _sum(C.m(c[j-i],p[j]) for j in range(i+1,len(p))) for i in range(len(p))]


def selection(mode,f,g,w):
    if mode=='separate':
        return actions(g,w[1:])+actions(f,w)
    rules=actions(f,w)
    if mode in ('fused','native_setup'):
        return [(g[1:],w[1:],[w[0]])]+rules
    assert mode=='uncorrected'
    return rules


def build(mode,rev):
    b=km.CircuitBuilder();b.set_max_qubits(900)
    q=list(b.create_quantum_register(865,'seam'))
    def regs(words):return [[q[i] for i in a] for a in words]
    f,g=(LAYOUT['D'][k::2][:16] for k in (0,1))
    W=[LAYOUT['N'][k::2][:N] for k in (0,1)]
    group=regs(f),regs(g)
    ff,gg=[None]+group[0],[None]+group[1]
    def prepare_h(inverse):
        # With coefficient 0 fixed at 1, multiplying F by G on the
        # truncated length-17 series is a reversed unit triangle plus G.
        a,c=group
        seq=actions(gg,a[::-1])
        def add_g():
            for src,dst in zip(c,a,strict=True):
                for x,y in zip(src,dst,strict=True): b.cx(x,y)
        if inverse:add_g()
        if inverse:seq.reverse()
        for cc,x,y in seq: shear_shared(b,cc,[(x,y)],len(x)*len(y)>len(cc))
        if not inverse:add_g()
    if mode=='native_setup': prepare_h(False)
    ops=list(zip(*(selection(mode,ff,gg,regs(w)) for w in W),strict=True))
    if rev:ops.reverse()
    for (c,x,y),(d,u,v) in ops:
        assert c==d
        shear_shared(b,c,[(x,y),(u,v)],len(x)*len(y)>len(c))
    if mode=='native_setup': prepare_h(True)
    return b.finish_circuit(),f,g,W


def verify(root):
    tapes={}
    receipt={}
    for mode in ('separate','fused','native_setup','uncorrected'):
        for rev in (False,True):
            if mode=='uncorrected' and rev:continue
            c,f,g,W=build(mode,rev)
            p=root/f'{mode}_{rev}.kmb'
            c.to_file(str(p),format='kmb')
            t=tapes[mode,rev]=km.Circuit.from_file(str(p))
            st=t.operation_statistics()
            receipt[f'{mode}_{rev}']=dict(qubits=t.num_qubits,ccx=st.num_toffoli_like,
                static_paid=st.num_toffoli_like,standalone_t=st.num_t_like,
                instructions=len(t),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    n=64
    rng=np.random.default_rng(471964)
    q=km.array([km.q(i) for i in range(865)])
    errors=0
    for k in range(16):
        old=rng.integers(0,2,(865,n),dtype=np.uint8).astype(bool)
        expected=old.copy()
        fs=rng.integers(0,4096,(n,N)).tolist()
        gs=rng.integers(0,4096,(n,N)).tolist()
        for a,d in zip(fs,gs):a[0]=d[0]=1
        hs=[frames(a,d) for a,d in zip(fs,gs)]
        def put(state,idx,p):
            state[np.array(idx)]=((np.asarray(p).T[:,None,:]>>np.arange(12)[None,:,None])&1).astype(bool)
        def get(state,idx):
            return np.einsum('ijn,j->ni',state[np.array(idx)],1<<np.arange(12)).tolist()
        put(old,f,[x[1:] for x in fs]);put(old,g,[x[1:] for x in gs])
        expected=old.copy()
        for w in W:
            xx=get(old,w)
            yy=[]
            for a,d,h,p in zip(fs,gs,hs,xx):
                u=tri(a,p[:1]+tri(d,p[1:]))
                z=tri(h,p)
                z[0]^=_sum(C.m(d[i],p[i]) for i in range(1,N))
                assert z==u
                yy.append(u)
            put(expected,w,yy)
        def run(state, mode, rev):
            t=tapes[mode,rev]
            s=km.Simulator(batch_size=n,seed=50019+k,counting_operations=True,debug_print=False)
            s.use_same_registers_as(t)
            s.write_across_shots(q,state)
            s.do(t)
            assert not s.read_phase_flipped_across_shots().any()
            name=f'{mode}_{rev}'
            paid=s.operation_statistics().num_toffoli_like/n
            assert paid==receipt[name]['static_paid']
            return s.read_across_shots(q)
        for mode in ('separate','fused','native_setup','uncorrected'):
            start=old.copy()
            want=expected.copy()
            if mode in ('fused','uncorrected'):
                put(start,f,[x[1:] for x in hs]);put(want,f,[x[1:] for x in hs])
            out=run(start,mode,False)
            if mode=='uncorrected':
                mismatch=out!=want
                allowed=W[0][0]+W[1][0]
                assert not np.delete(mismatch,allowed,axis=0).any()
                errors+=int(mismatch.any(0).sum())
                continue
            assert np.array_equal(out,want)
            assert np.array_equal(run(out,mode,True),start)
    return dict(tapes=receipt,shots_each_direction=1024,omitting_correction_error_lanes=errors,
                scope='Two monic degree-one merges on both sectors. Original F,G frames required, monic scale implicit. Native setup case computes H in place and restores F.')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('out',type=Path)
    a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    r=verify(a.out)
    (a.out/'pair_receipt.json').write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps(r,indent=2))


if __name__=='__main__':
    main()

