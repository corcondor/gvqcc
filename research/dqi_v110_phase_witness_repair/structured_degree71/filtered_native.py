"""In-place zero-paid materialization of the #334/#339 52 filtered moments.
The rectangular rank test remains a classical checker, not part of this KMB.
"""
import json
from random import Random
from pathlib import Path
import hashlib
import numpy as np
import kickmix as km
import hankel_s71 as H
from structured_phase import pack

def times(p,q):
    out=[0]*(len(p)+len(q)-1)
    for i,a in enumerate(p):
        for j,b in enumerate(q):out[i+j]^=H.mul(a,b)
    return out

G=[1]
for c in range(2048,2057):
    assert all(H.mul(x,x)^x^c for x in range(4096))
    G=times(G,[c,1,1])
assert len(G)==19 and G[18]==1

def words_after(s):
    return s[:18]+[H.dot(G,s[i:i+19]) for i in range(52)]

def rank_rect(f):
    rows=[f[i:i+35] for i in range(18)]
    k=0
    for j in range(35):
        x=next((u for u in range(k,len(rows)) if rows[u][j]),None)
        if x is None:continue
        rows[k],rows[x]=rows[x],rows[k]
        a=rows[k]; ai=H.inv(a[j])
        for i in range(k+1,len(rows)):
            v=H.mul(rows[i][j],ai)
            if v:rows[i]=[x^H.mul(v,y) for x,y in zip(rows[i],a)]
        k+=1
        if k==18:break
    return k

def layer():
    for i in range(51,-1,-1):
        for j in range(18):
            for k in range(12):
                v=H.mul(G[j],1<<k)
                for l in range(12):
                    if v>>l&1:yield ((i+j)*12+k,(i+18)*12+l)

def make(inv,path):
    c=km.CircuitBuilder();c.set_max_qubits(840);q=list(c.create_quantum_register(840,'S'))
    seq=list(layer())
    if inv:seq.reverse()
    for i,j in seq:c.cx(q[i],q[j])
    c=c.finish_circuit()
    c.to_file(str(path),format="kmb")
    c=km.Circuit.from_file(str(path))
    assert c.num_qubits==840 and c.operation_statistics().num_toffoli_like==0
    return c

if __name__=='__main__':
    rng=Random(339334);s=[]
    for w in range(36):
        for trial in range(16):
            xs=rng.sample(range(1,4096),w)
            x=H.moments(xs,[rng.randrange(1,4096) for _ in xs],70)
            ghost=[rng.randrange(4096) for _ in range(18)]
            while len(ghost)<70:ghost.append(H.dot(G[:18],ghost[-18:]))
            y=[a^b for a,b in zip(x,ghost)]
            assert words_after(x)[18:]==words_after(y)[18:]
            assert rank_rect(words_after(y)[18:])==min(w,18)
            s.extend([x,y])
    for _ in range(128):s.append([rng.randrange(4096) for _ in range(70)])
    expected=[words_after(t) for t in s]
    paths=[Path('filter_forward.kmb'),Path('filter_inverse.kmb')]
    f,rev=[make(i,p) for i,p in enumerate(paths)]
    q=km.array([km.q(i) for i in range(840)])
    A=pack(s); E=pack(expected)
    sim=km.Simulator(batch_size=len(s),seed=339334,debug_print=False,counting_operations=True)
    sim.use_same_registers_as(f);sim.write_across_shots(q,A);sim.do(f)
    assert np.array_equal(sim.read_across_shots(q),E)
    assert not np.any(sim.read_phase_flipped_across_shots())
    sim.do(rev)
    assert np.array_equal(sim.read_across_shots(q),A)
    assert not np.any(sim.read_phase_flipped_across_shots())
    assert sim.operation_statistics().num_toffoli_like==0
    print(json.dumps(dict(legal_and_ghost_pairs=576,dirty=128,shots=len(s),Q=840,
        CNOT_per_direction=len(f),paid=0,phase_errors=0,
        sha256=[hashlib.sha256(p.read_bytes()).hexdigest() for p in paths])))
