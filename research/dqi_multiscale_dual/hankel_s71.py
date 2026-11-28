"""PR337 residual-preserving Hankel diagonal adjoint, GF(4096).
No full-tape splice or official score claim. --native runs component SDK only.
"""
from random import Random
from pathlib import Path
import argparse, json, hashlib

N=35
EXP=[0]*8190
LOG=[-1]*4096
v=1
for i in range(4095):
    assert LOG[v]==-1
    LOG[v]=i
    EXP[i]=EXP[i+4095]=v
    v <<= 1
    if v & 4096: v ^= 0x1053
assert v==1

def mul(a,b): return EXP[LOG[a]+LOG[b]] if a and b else 0
def inv(a):
    assert a
    return EXP[4095-LOG[a]]
def xor(xs):
    a=0
    for x in xs: a ^= x
    return a
def dot(a,b): return xor(mul(x,y) for x,y in zip(a,b))
def tr(a):
    t=0
    for _ in range(12):
        t ^= a
        a=mul(a,a)
    assert t in (0,1)
    return t
def moments(xs,es,n=71):
    s=[0]*n
    for x,e in zip(xs,es):
        u=mul(e,x)
        for j in range(n):
            s[j]^=u
            u=mul(u,x)
    return s
def locator(xs):
    p=[1]
    for x in xs:
        q=[0]*(len(p)+1)
        for j,a in enumerate(p):
            q[j]^=mul(a,x)
            q[j+1]^=a
        p=q
    return p
def padded(p):
    assert p and p[-1]==1 and len(p)<=N+1
    return [0]*(N+1-len(p))+p[:-1]
def solve(H,r):
    """Independent dense reference only, NOT a coherent decoder."""
    A=[list(row)+[a] for row,a in zip(H,r)]
    k=0
    piv=[]
    for j in range(N):
        p=next((i for i in range(k,N) if A[i][j]),None)
        if p is None: continue
        A[k],A[p]=A[p],A[k]
        u=inv(A[k][j])
        for h in range(j,N+1): A[k][h]=mul(A[k][h],u)
        for i in range(N):
            if i!=k and A[i][j]:
                u=A[i][j]
                for h in range(j,N+1): A[i][h]^=mul(u,A[k][h])
        piv.append(j)
        k+=1
    assert all(not A[i][N] for i in range(k,N))
    t=[0]*N
    for i,j in enumerate(piv): t[j]=A[i][N]
    assert [dot(row,t) for row in H]==list(r)
    return t,k
def diag(u,odd): return dot([mul(x,x) for x in u],odd)
def recover(s,p):
    """Input only S1..S70 and arbitrary monic candidate (degree <=35)."""
    assert len(s)==70
    p=padded(p)
    H=[s[i:i+N] for i in range(N)]
    b=s[N:]
    r=[dot(row,p)^bi for row,bi in zip(H,b)]
    t,rank=solve(H,r)
    odd=s[::2]
    return diag(p,odd)^diag(t,odd),r,t,rank

def check_reference():
    rng=Random(337)
    rec=dict(cases=0,singular=0,missing=0,extra=0,weighted=0,binary=0,rank_checks=0)
    for w in range(N+1):
        for it in range(32):
            xs=rng.sample(range(1,4096),w)
            e=[1 if it%2 else rng.randrange(1,4096) for _ in xs]
            s=moments(xs,e)
            roots=[x for x in xs if it<2 or rng.randrange(4)]
            missing=len(roots)!=w
            ne=rng.randrange(min(6,N-len(roots))+1) if it>=2 else 0
            extra=rng.sample([x for x in range(1,4096) if x not in xs],ne)
            p=locator(roots+extra)
            pred,r,t,rank=recover(s[:70],p)
            assert pred==s[70] and rank==w
            assert (not any(r))== (not missing)
            if not missing:
                d=len(p)-1
                assert xor(mul(mul(p[i],p[i]),s[70-2*d+2*i]) for i in range(d))==s[70]
            rec['cases']+=1
            rec['singular']+=rank<N
            rec['missing']+=missing
            rec['extra']+=bool(extra)
            rec['binary' if it%2 else 'weighted']+=1
            rec['rank_checks']+=1
    return rec

# Exact trace coefficient tensor for p^2*s; the classical c bank is arbitrary.
FORMS=[sum(tr(mul(EXP[h],1<<k))<<k for k in range(12)) for h in range(34)]
def check_tensor():
    n=0
    for i in range(12):
        for j in range(12):
            for k in range(12):
                assert (FORMS[2*i+j]>>k)&1==tr(mul(mul(mul(1<<i,1<<i),1<<j),1<<k))
                n+=1
    return n

def native(d,rng):
    import numpy as np
    import kickmix as km
    b=km.CircuitBuilder()
    b.set_max_qubits(24*d)
    p=list(b.create_quantum_register(12*d,'P'))
    s=list(b.create_quantum_register(12*d,'ODD'))
    c=list(b.create_classical_register(12,'C'))
    z=list(b.alloc_bits(34))
    for h,f in enumerate(FORMS):
        b.bit_store(z[h],False)
        for k in range(12):
            if f>>k&1: b.cx(c[k],z[h])
    for u in range(d):
        for i in range(12):
            for j in range(12):
                # Classical third operand, as in PR332's measured adjoint.
                # Fail closed if SDK counts this as a paid quantum CCZ.
                b.ccz(p[12*u+i],s[12*u+j],z[2*i+j])
    for a in z: b.bit_store(a,False)
    b.free(z)
    circ=b.finish_circuit()
    assert circ.num_qubits==24*d
    assert int(circ.operation_statistics().num_toffoli_like)==0
    path=Path(__file__).with_name(f'hankel_diagonal_{d}.kmb')
    circ.to_file(str(path),format='kmb')
    circ=km.Circuit.from_file(str(path))
    rows=[([rng.randrange(4096) for _ in range(d)],
           [rng.randrange(4096) for _ in range(d)],rng.randrange(4096)) for _ in range(256)]
    def pack(rows):
        return ((np.array(rows,dtype=np.uint16)[:,:,None]>>np.arange(12,dtype=np.uint16))&1).reshape(len(rows),-1).T.astype(bool)
    q=km.array([km.q(i) for i in range(24*d)])
    bc=km.array([km.b(i) for i in range(12)])
    A=pack([p+s for p,s,c in rows])
    C=pack([[c] for p,s,c in rows])
    E=np.array([tr(mul(c,diag(p,s))) for p,s,c in rows],dtype=bool)
    sim=km.Simulator(batch_size=len(rows),seed=17,debug_print=False,counting_operations=True)
    sim.use_same_registers_as(circ)
    sim.write_across_shots(q,A)
    sim.write_across_shots(bc,C)
    sim.do(circ)
    assert np.array_equal(sim.read_across_shots(q),A)
    assert np.array_equal(sim.read_across_shots(bc),C)
    assert np.array_equal(sim.read_phase_flipped_across_shots(),E)
    return dict(d=d,Q=circ.num_qubits,paid=int(circ.operation_statistics().num_toffoli_like),ops=len(circ),shots=len(rows),errors=0,sha256=hashlib.sha256(path.read_bytes()).hexdigest())

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--native',action='store_true')
    args=parser.parse_args()
    out=dict(reference=check_reference(),tensor_basis_checks=check_tensor())
    if args.native:
        rng=Random(33771)
        out['native']=[native(d,rng) for d in (1,4,8,17,24,35)]
    print(json.dumps(out,indent=2),flush=True)
    Path(__file__).with_name('hankel_receipt.json').write_text(json.dumps(out,indent=2)+'\n')
