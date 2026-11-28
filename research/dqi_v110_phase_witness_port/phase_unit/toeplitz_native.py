"""Native non-overlapping Toeplitz shear. Reuse #261 rank-42 product and frames."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import kickmix as km
import crt882 as C
import joint_phase as J

LAYOUT = json.loads((Path(__file__).resolve().parent.parent/'phase261/raw_audit.json').read_text())['layout']


def roll(a, x, t, k):
    # Add k*x to t with fixed linear CNOT network.
    for i in range(12):
        for j in C.bits(C.m(k, 1<<i)):
            a.cx(x[i],t[j])


def mul_frame(b, w, k):
    J.frame(b, w, [C.m(k,1<<i) for i in range(12)])


def lagrange(points, x):
    p, denominator = [1], 1
    for y in points:
        if y != x:
            p = C.mul(p,[y,1])
            denominator = C.m(denominator,x^y)
    return [C.m(t,C.inv(denominator)) for t in p]


def shear(b, c, xwords, ywords, blocked):
    shear_shared(b, c, [(xwords,ywords)], blocked)


def shear_shared(b, c, sectors, blocked):
    r,s = len(sectors[0][1]),len(sectors[0][0])
    assert all(len(x)==s and len(y)==r for x,y in sectors)
    assert len(c)==r+s-1
    # Index c[i+j] makes this Hankel. Reverse x order for the Toeplitz
    # off-diagonal in the Euclidean merge.
    if not blocked:
        for xwords,ywords in sectors:
            for i,y in enumerate(ywords):
                for j,v in enumerate(xwords):
                    J.arith(b,'prod',c[i+j],v,y,12,C.MOD)
        return
    points=list(range(r+s-1))
    for x in points:
        gamma=lagrange(points,x)
        h=next(i for i,v in enumerate(gamma) if v)
        mul_frame(b,c[h],gamma[h])
        for i,k in enumerate(gamma):
            if i!=h and k:roll(b,c[i],c[h],k)
        xp,yp = [C.gf_pow(x,j,12,C.MOD) for j in range(s)], [C.gf_pow(x,j,12,C.MOD) for j in range(r)]
        for xwords,ywords in sectors:
            for j in range(1,s):roll(b,xwords[j],xwords[0],xp[j])
            for i in range(1,r):roll(b,ywords[0],ywords[i],yp[i])
            J.arith(b,'prod',c[h],xwords[0],ywords[0],12,C.MOD)
            for i in range(1,r):roll(b,ywords[0],ywords[i],yp[i])
            for j in range(1,s):roll(b,xwords[j],xwords[0],xp[j])
        for i,k in enumerate(gamma):
            if i!=h and k:roll(b,c[i],c[h],k)
        mul_frame(b,c[h],C.inv(gamma[h]))


def audit(r,s,blocked,root):
    b = km.CircuitBuilder()
    b.set_max_qubits(900)
    q = list(b.create_quantum_register(865,'seam'))
    c = LAYOUT['D'][::2][:r+s-1]
    y = LAYOUT['N'][::2][:r]
    x = LAYOUT['N'][::2][r:r+s][::-1]
    assert len(set(sum(c+x+y,[])))==12*(len(c)+len(x)+len(y))
    shear(b,*[[[q[i] for i in w] for w in seq] for seq in (c,x,y)],blocked)
    path = root/f'shear_{r}_{s}_{blocked}.kmb'
    b.finish_circuit().to_file(str(path),format='kmb')
    tape=km.Circuit.from_file(str(path))
    n=64
    rng=np.random.default_rng(71521+r*152+s)
    q=km.array([km.q(i) for i in range(865)])
    for k in range(16):
        state=rng.integers(0,2,(865,n),dtype=np.uint8).astype(bool)
        expect=state.copy()
        def words(w):
            return np.einsum('ijn,j->in',state[np.array(w)],1<<np.arange(12))
        cc,xx=words(c),words(x)
        for i,w in enumerate(y):
            v=[0]*n
            for j in range(s):
                for t in range(n): v[t]^=C.m(int(cc[i+j,t]),int(xx[j,t]))
            expect[np.array(w)] ^= ((np.array(v)[None,:]>>np.arange(12)[:,None])&1).astype(bool)
        sim=km.Simulator(batch_size=n,seed=k,counting_operations=True,debug_print=False)
        sim.use_same_registers_as(tape)
        sim.write_across_shots(q,state)
        sim.do(tape)
        assert np.array_equal(sim.read_across_shots(q),expect)
        assert not sim.read_phase_flipped_across_shots().any()
        sim.do(tape)
        assert np.array_equal(sim.read_across_shots(q),state)
        assert not sim.read_phase_flipped_across_shots().any()
    ops=tape.operation_statistics()
    assert ops.num_toffoli_like==42*(r+s-1 if blocked else r*s)
    return dict(rows=r,cols=s,blocked=blocked,qubits=tape.num_qubits,shots_each_direction=16*n,
                instructions=len(tape),ccx=ops.num_toffoli_like,paid=ops.num_toffoli_like,
                standalone_t=ops.num_t_like,sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('out',type=Path)
    ap.add_argument('shapes',nargs='+',help='e.g. 8x8 7x10')
    a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    out=[]
    for shape in a.shapes:
        r,s=map(int,shape.split('x'))
        for mode in (False,True):
            row=audit(r,s,mode,a.out)
            out.append(row)
            print(row,flush=True)
    (a.out/'toeplitz_native.json').write_text(json.dumps(out,indent=2)+'\n')


if __name__=='__main__':
    main()
