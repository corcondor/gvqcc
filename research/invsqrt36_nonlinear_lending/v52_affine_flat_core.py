"""Finite GF(2) affine care-flat core used in V52.
The exact legal-domain masks are supplied by the pinned native frame capture.
Physical gate emission and complete receipts are in the companion archive.
"""
def indices(v):
    while v:
        b = v & -v
        yield b.bit_length()-1
        v ^= b

def echelon(vs):
    B = {}
    for v in vs:
        while v:
            p = v.bit_length()-1
            if p in B:
                v ^= B[p]
            else:
                B[p] = v
                break
    return B

def orthogonal_constraints(B, allowed):
    out = []
    for k in allowed:
        if k in B:
            continue
        v = 1 << k
        for p in sorted(B):
            if (v & B[p]).bit_count() & 1:
                v ^= 1 << p
        assert all((v & w).bit_count() % 2 == 0 for w in B.values())
        out.append((k,v))
    return out

def form_mask(v, fs):
    m = 0
    for q in indices(v):
        m ^= fs[q]
    return m

def grow_exact_quotient(anchor, forbidden_keys, on_keys, mode=0):
    """Select nonzero cosets absent from forbidden quotient; each selected
    direction enlarges the safe flat by one dimension."""
    import numpy as np
    a = np.uint64(anchor)
    o = np.unique(forbidden_keys ^ a)
    q = on_keys ^ a
    B = {}
    if o.size and o[0] == 0:
        return None
    while True:
        vals,cnt = np.unique(q[q!=0],return_counts=True)
        if not len(vals):
            break
        pos = np.searchsorted(o,vals)
        bad = np.zeros(len(vals),bool)
        z = pos < len(o)
        bad[z] = o[pos[z]] == vals[z]
        ids = np.flatnonzero(~bad)
        if not len(ids):
            break
        k = max(ids,key=lambda k:(int(cnt[k]),(-int(vals[k]).bit_count() if mode==0 else int(vals[k]).bit_count()),int(vals[k]) if mode==2 else -int(vals[k])))
        d = int(vals[k])
        p = d.bit_length()-1
        assert p not in B
        B[p] = d
        bit,u = np.uint64(1<<p),np.uint64(d)
        o = np.unique(o ^ np.where(o&bit!=0,u,np.uint64(0)))
        q ^= np.where(q&bit!=0,u,np.uint64(0))
        assert not (o.size and o[0] == 0)
    return B

def affine_flat_mask(anchor, points, feature_masks, domain_mask):
    B = echelon(p ^ anchor for p in points)
    out = domain_mask
    for p,v in orthogonal_constraints(B,range(len(feature_masks))):
        m = form_mask(v,feature_masks)
        out &= m if (v&anchor).bit_count()&1 else domain_mask^m
    return out

def test():
    from itertools import product
    for n in range(1,7):
        N=1<<n
        fs=[sum(1<<x for x in range(N) if x>>q&1) for q in range(n)]
        pts=[0,1,N-1]
        B=echelon(pts)
        span={0}
        for d in B.values():
            span |= {x^d for x in span}
        got=affine_flat_mask(0,pts,fs,(1<<N)-1)
        assert got==sum(1<<x for x in span)
    print("V52 finite affine-flat regression PASS")

if __name__=="__main__": test()
