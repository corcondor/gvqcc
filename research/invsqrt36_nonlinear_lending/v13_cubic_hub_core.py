"""V13 mathematical synthesis core.
Companion archive supplies native_kmb, transport, width_quadratic and full BDD
admission. This file alone is not a full compiler or an official submission.
"""
from itertools import permutations, product
from functools import reduce
from operator import xor
from native_kmb import Op
from transport import bits, affine_gates, rank_basis
from phase_potential import sig, mul
from width_quadratic import decomp

def form(mask,constant):
    return {1<<q for q in bits(mask)} ^ ({0} if constant else set())

def cost(g):
    return sum(o.raw==49 for o in g),len(g)

def synth(poly,t,st):
    cubic=[x for x in poly if x.bit_count()==3]
    assert len(cubic)==2
    common=cubic[0]&cubic[1]
    assert common.bit_count()==2
    a,b=bits(common)
    F=[1<<a,1<<b,cubic[0]^cubic[1]]
    span=[reduce(xor,(F[j] for j in range(3) if m>>j&1),0)
          for m in range(1,8)]
    W=list(bits(cubic[0]|cubic[1]))
    best=None
    for fs in permutations(span,3):
        if len(rank_basis(fs))!=3: continue
        prebest=None
        for piv in permutations(W,3):
            rows=[1<<q for q in range(37)]
            for q,f in zip(piv,fs): rows[q]=f
            if len(rank_basis(rows))!=37: continue
            pre=affine_gates(rows)
            if prebest is None or len(pre)<len(prebest[0]):
                prebest=(pre,piv)
        if prebest is None: continue
        pre,piv=prebest
        d=next(q for q in range(36) if q not in (*W,t))
        for c in product([0,1],repeat=3):
            st['affine_factor_bases']+=1
            atom=mul(mul(form(fs[0],c[0]),form(fs[1],c[1])),form(fs[2],c[2]))
            res=poly^atom
            if any(x.bit_count()>2 for x in res): continue
            g=decomp(res,t)
            if g is None: continue
            setup=pre+[Op(17,(p,)) for p,v in zip(piv,c) if v]
            u,v,w=piv
            chunk=setup+[Op(49,(u,v,d)),Op(49,(d,w,t)),
                          Op(49,(u,v,d)),Op(49,(d,w,t))]+setup[::-1]
            cand=g+chunk
            if best is None or cost(cand)<cost(best): best=cand
    return best

def certified_resynthesis(old,target,stats):
    """Check universal Boolean equality before returning the new native list.
    Reachable decoder premise and HMR semantics are checked separately.
    """
    rows,ph=sig(old)
    poly=rows[target]^{1<<target}
    assert not ph and all(rows[q]=={1<<q} for q in range(37) if q!=target)
    new=synth(poly,target,stats)
    assert new is not None and sig(new)==sig(old)
    assert all(q<36 for o in new for q in o.wires)
    return new
