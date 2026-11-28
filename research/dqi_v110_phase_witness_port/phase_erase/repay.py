"""Native HMR of two redundant numerator coefficients on the physical #261 seam."""
import json, hashlib, sys
from pathlib import Path
from functools import lru_cache
import numpy as np
import kickmix as km
import crt882 as C
import joint_phase as J

L=json.loads(Path('raw_audit.json').read_text())['layout']

def prodphase_many(b,pairs,m,n,mod):
    # Transpose reduction once, then share the same classical mask among all
    # terms of one coefficient. No coherent work register is needed.
    extra=list(b.alloc_bits(n-1))
    mask=list(m)+extra
    for d in range(n,2*n-1):
        b.bit_store(mask[d],False)
        for j in C.bits(mod^(1<<n)):
            b.cx(mask[d-n+j],mask[d])
    for x,y in pairs:
        for i,a in enumerate(x):
            for j,c in enumerate(y):
                b.ccz(a,c,mask[i+j])
    J.cclear(b,extra)

def tensor_pullback(b,x,y,m):
    ctrl=x+y
    t=list(b.alloc_bits(12))
    for target in t:b.bit_store(target,False)
    for source,target in zip(m,t):b.cx(source,target)
    undone=[]
    for g in reversed(C.CODES):
        a=g%64
        c=g//64%64
        if g<4096:
            if a//12==2:
                assert c//12==2
                b.cx(t[c-24],t[a-24])
            else:
                b.cx(ctrl[a],ctrl[c])
                undone.append((a,c))
        else:
            b.ccz(ctrl[a],ctrl[c],t[g//4096-1-24])
    for a,c in reversed(undone):b.cx(ctrl[a],ctrl[c])
    J.cclear(b,t)

def xor_word(b,x,y):
    for a,c in zip(x,y):b.cx(a,c)

def kara_mask(b, pairs_by_product, m):
    # Two low coefficients: AB0=x0*y0, AB1=x0*y1+x1*y0.
    # Karatsuba z=(x0+x1)*(y0+y1) needs mask m1, while
    # x0*y0 has the combined mask m0+m1. Share the mask prep between AU and BZ.
    mm=list(b.alloc_bits(12))
    for p in mm:b.bit_store(p,False)
    for x,y,z in zip(m[0],m[1],mm):
        b.cx(x,z);b.cx(y,z)
    prodphase_many(b,[(x[0],y[0]) for x,y in pairs_by_product],mm,12,C.MOD)
    J.cclear(b,mm)
    prodphase_many(b,[(x[1],y[1]) for x,y in pairs_by_product],m[1],12,C.MOD)
    for x,y in pairs_by_product:
        xor_word(b,x[1],x[0]);xor_word(b,y[1],y[0])
    prodphase_many(b,[(x[0],y[0]) for x,y in pairs_by_product],m[1],12,C.MOD)
    for x,y in reversed(pairs_by_product):
        xor_word(b,y[1],y[0]);xor_word(b,x[1],x[0])

def build(mode,sector):
    b=km.CircuitBuilder()
    b.set_max_qubits(900)
    p=list(b.create_quantum_register(865,'raw'))
    start=list(b.alloc_qubits(24))
    assert start[:12]==[km.q(i) for i in range(865,877)] and start[12:]==[km.q(i) for i in range(877,889)]
    source=[L['D'][i::2][:17] for i in (0,1)]
    live=[L['N'][i::2][:17] for i in (sector,1-sector)]
    def data(groups):return [[p[i] for i in word] for word in groups]
    a,d=map(data,source)
    u,z=map(data,live)
    products=((a,u),(d,z))
    contrib=[[(x[i],y[j-i]) for x,y in products for i in range(j+1)] for j in range(2)]
    old=[start[j*12:(j+1)*12] for j in range(2)]
    # Leave HMR records accessible only in the diagnostic, to test exact
    # phase on deliberately broken redundant inputs.
    m=[list(b.create_classical_register(12,'m'+str(j))) for j in range(2)] if mode!='undo' else []
    if mode=='undo':
        for j,row in enumerate(contrib):
            for x,y in row:J.arith(b,'prod',x,y,old[j],12,C.MOD)
    else:
        for j in range(2):b.hmr(old[j],m[j])
        if mode=='school':
            for j,row in enumerate(contrib):prodphase_many(b,row,m[j],12,C.MOD)
        elif mode=='tensor':
            for j,row in enumerate(contrib):
                for x,y in row:tensor_pullback(b,x,y,m[j])
        elif mode=='kara':
            kara_mask(b,products,m)
        elif mode=='control':pass
        else:raise ValueError(mode)
    b.free(start)
    return b.finish_circuit(),source,live

def test(mode,sector):
    c,coeff,mults=build(mode,sector)
    name=f'numerator_{mode}_{sector}.kmb'
    path=Path(name)
    c.to_file(name,format='kmb')
    # Reload native serialization for the experiment.
    c=km.Circuit.from_file(name)
    rng=np.random.default_rng(518031+sector)
    shots=negative=paid=errors=negerrors=negflips=unpaid_detected=0
    q=km.array([km.q(i) for i in range(c.num_qubits)])
    bits=km.array([km.b(i) for i in range(24)])
    for i in range(20):
        raw=rng.integers(0,2,(865,64),dtype=bool)
        word=lambda l: (raw[l[:2]]*np.uint16(1<<np.arange(12))[None,:,None]).sum(axis=1)
        a,d=map(word,coeff)
        u,z=map(word,mults)
        pp=np.array([[C.m(int(a[0,k]),int(u[0,k]))^C.m(int(d[0,k]),int(z[0,k])),
                       C.m(int(a[1,k]),int(u[0,k]))^C.m(int(a[0,k]),int(u[1,k]))^
                       C.m(int(d[1,k]),int(z[0,k]))^C.m(int(d[0,k]),int(z[1,k]))] for k in range(64)],np.uint16)
        old=((pp[:,:,None]>>np.arange(12))&1).reshape(64,24).T.astype(bool)
        fault=rng.integers(0,2,(24,64),dtype=bool) if i>=16 else np.zeros_like(old)
        if mode=='undo' and i>=16:continue
        given=np.vstack((raw,old^fault))
        for seed in (5531+i,6873+i):
            s=km.Simulator(batch_size=64,seed=seed,counting_operations=True,debug_print=False)
            s.use_same_registers_as(c)
            s.write_across_shots(q,given)
            s.do(c)
            y=s.read_across_shots(q)
            bad=(y[:865]!=raw).any(0)|y[865:].any(0)
            got=s.read_phase_flipped_across_shots()
            measured=s.read_across_shots(bits) if mode!='undo' else np.zeros_like(old)
            expected=np.logical_xor.reduce((old^fault if mode=='control' else fault)&measured,axis=0)
            if i<16:
                errors+=int((bad|(got!=expected)).sum())
                unpaid_detected+=int(got.sum())
                paid+=int(s.operation_statistics().num_toffoli_like)
                shots+=64
            else:
                negerrors+=int((bad|(got!=expected)).sum())
                negflips+=int(got.sum())
                negative+=64
    stats=dict(c.operation_statistics())
    return dict(mode=mode,sector=sector,Q=c.num_qubits,ops=len(c),CCX=stats.get('CCX',0),
        static_paid=int(c.operation_statistics().num_toffoli_like),mean_paid=paid/shots,
        shots=shots,errors=errors,phase_flips=unpaid_detected,negative=negative,
        negative_errors=negerrors,negative_phase_flips=negflips,stats=stats,
        sha256=hashlib.file_digest(path.open('rb'),'sha256').hexdigest())

if __name__=='__main__':
    rows=[test(m,s) for m in ('undo','school','tensor','kara','control') for s in (0,1)]
    print(json.dumps(rows,indent=2))
    assert not any(r['errors'] or r['negative_errors'] for r in rows)
    assert [r['static_paid'] for r in rows]==[252,252,0,0,0,0,0,0,0,0]
    assert all((r['phase_flips']>0)==(r['mode']=='control') for r in rows)
