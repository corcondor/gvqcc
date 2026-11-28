"""Compare candidate-free EEA, dense dual, and native phase contraction.
The reversible EEA lowering and physical whole-DQI seam are not implemented.
"""
from random import Random
from pathlib import Path
import json, hashlib, sys
import numpy as np
import kickmix as km
import hankel_s71 as H

def trim(a):
    while a and not a[-1]:a.pop()
    return a

def gcd_decode(s):
    """Euclidean rational reconstruction of C(z) S(z) mod z^70.
    Cost counter is for nontrivial GF12 multiplications only, not gate cost.
    """
    assert len(s)==70
    paid=0
    def m(a,b):
        nonlocal paid
        paid+=int(a not in (0,1) and b not in (0,1))
        return H.mul(a,b)
    r0=[0]*70+[1];r1=trim(s[:]);b0=[];b1=[1];bursts=[]
    if not r1:return [1],0,bursts
    while len(r1)>35:
        iv=H.inv(r1[-1])
        d0=len(r0)-1;d1=len(r1)-1
        while len(r0)>=len(r1):
            z=len(r0)-len(r1); c=m(r0[-1],iv)
            for j,x in enumerate(r1):r0[z+j]^=m(c,x)
            trim(r0)
            while len(b0)<z+len(b1):b0.append(0)
            for j,x in enumerate(b1):b0[z+j]^=m(c,x)
            trim(b0)
        r0,r1,b0,b1=r1,r0,b1,b0
        bursts.append((d0,d1,len(r1)-1))
    assert b1 and b1[0] and len(b1)<=36
    scale=H.inv(b1[0])
    c=[m(a,scale) for a in b1]
    assert all(H.xor(H.mul(c[j],s[k-j]) for j in range(len(c)))==0 for k in range(len(c)-1,70))
    return c,paid,bursts

def high_xor(s,c):
    w=len(c)-1
    return H.xor(H.mul(H.mul(c[j],c[j]),s[70-2*j]) for j in range(1,w+1))

def sqrt(a):
    return H.EXP[(H.LOG[a]*2048)%4095] if a else 0

def independent_dual(s):
    h=[s[i:i+35] for i in range(35)]
    e=[sqrt(h[i][i]) for i in range(35)]
    l,rank=H.solve(h,e)
    z=H.dot(l,s[35:70])
    return H.mul(z,z), rank

def reference():
    r=Random(338339); out={}
    for w in range(36):
        cc=[]
        for j in range(10):
            xs=r.sample(range(1,4096),w)
            es=[r.randrange(1,4096) if j%2 else 1 for _ in xs]
            s=H.moments(xs,es)
            c,p,b=gcd_decode(s[:70]); cc.append(p)
            assert c==H.locator(xs)[::-1]
            assert high_xor(s,c)==s[70]
            assert independent_dual(s[:70])==(s[70],w)
        out[w]={"mean_nontrivial_products":sum(cc)/len(cc),"max":max(cc)}
    c=H.locator(list(range(5,39))+[282]);p=H.padded(c);s=H.moments([1,4],[1,1])
    assert s[70]==457 and H.diag(p,s[:70:2])==457
    res=[H.dot(s[i:i+35],p)^s[35+i] for i in range(35)]
    assert len([x for x in res if x])==35 and res[0]==3804
    return out

def pack(rows):
    return ((np.array(rows,dtype=np.uint16)[:,:,None]>>np.arange(12,dtype=np.uint16))&1).reshape(len(rows),-1).T.astype(bool)

def native(d,rng):
    # l,b on distinct already-live word banks. Gamma is CLASSICAL.
    b=km.CircuitBuilder()
    b.set_max_qubits(24*d)
    a=list(b.create_quantum_register(12*d,"L"))
    v=list(b.create_quantum_register(12*d,"B"))
    g=list(b.create_classical_register(12,"C"))
    z=list(b.alloc_bits(23))
    forms=[]
    for h,p in enumerate(z):
        f=sum(H.tr(H.mul(H.EXP[h],sqrt(1<<k)))<<k for k in range(12))
        forms.append(f)
        b.bit_store(p,False)
        for k in range(12):
            if f>>k&1:b.cx(g[k],p)
    for i in range(12):
        for j in range(12):
            for k in range(12):
                assert forms[i+j]>>k&1==H.tr(H.mul(H.mul(1<<i,1<<j),sqrt(1<<k)))
    for u in range(d):
        for i in range(12):
            for j in range(12):
                b.ccz(a[12*u+i],v[12*u+j],z[i+j])
    for p in z:b.bit_store(p,False)
    b.free(z)
    c=b.finish_circuit()
    path=Path(__file__).with_name(f"direct_trace_{d}.kmb")
    c.to_file(str(path),format="kmb")
    c=km.Circuit.from_file(str(path))
    q=km.array([km.q(i) for i in range(24*d)])
    k=km.array([km.b(i) for i in range(12)])
    rows=[([rng.randrange(4096) for _ in range(d)],[rng.randrange(4096) for _ in range(d)], rng.randrange(4096)) for _ in range(512)]
    Q=pack([l+x for l,x,g in rows]);B=pack([[g] for l,x,g in rows])
    P=np.array([H.tr(H.mul(sqrt(g),H.dot(l,x))) for l,x,g in rows],dtype=bool)
    sim=km.Simulator(batch_size=len(rows),seed=338,debug_print=False,counting_operations=True)
    sim.use_same_registers_as(c);sim.write_across_shots(q,Q);sim.write_across_shots(k,B);sim.do(c)
    assert np.array_equal(sim.read_across_shots(q),Q)
    assert np.array_equal(sim.read_across_shots(k),B)
    assert np.array_equal(sim.read_phase_flipped_across_shots(),P)
    assert c.operation_statistics().num_toffoli_like==0 and sim.operation_statistics().num_toffoli_like==0
    return dict(d=d,ops=len(c),Q=c.num_qubits,scratch_classical=23,paired_cases=len(rows),paid=0,sha256=hashlib.file_digest(path.open("rb"),"sha256").hexdigest())

if __name__=="__main__":
    r=Random(339338); res={"euclid_reference":reference(),"native":[native(d,r) for d in (1,4,8,17,24,35)]}
    print(json.dumps(res,indent=2))
