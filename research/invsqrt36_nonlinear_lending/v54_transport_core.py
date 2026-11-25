"""V54 finite rank-one transport core (stdlib only).
Actual KMB emitters, independent full-cube replay, source and plan data are
provided by the V54 companion archive. This is not the full native verifier.
"""
from collections import defaultdict
from itertools import product

def phase_identity(r,f):
    return (r^f)-r == f*(1-2*r)

def direction_transition(a,b):
    """(prefix,direction) state or None; output (p,q,v) toggles.
    A toggle acts by v*(I_p XOR I_q), I_None=0.
    Prefixes must have equal bit width, directions disjoint from prefix bits.
    """
    if a==b:return []
    if a is None:
        q,w=b
        return [(None,q,w)]
    if b is None:
        p,v=a
        return [(p,None,v)]
    p,v=a; q,w=b
    if p==q:return [(None,p,v^w)]
    if v==w:return [(p,q,v)]
    return [(None,p,v^w),(p,q,w)]

def affine_line(p,q):
    """Return pivot, affine CNOT pairs, remaining fixed bits.
    Two prefix points are a one-dimensional affine flat.
    """
    assert p!=q
    diff=p^q; z=(diff&-diff).bit_length()-1
    return z,[(z,j) for j in range(diff.bit_length()) if j!=z and diff>>j&1],p^( (diff^(1<<z)) if p>>z&1 else 0)

def sibling_contract(L,R,high,mod=1<<64):
    """Exact dyadic Walsh sibling contraction, only on even sums.
    Non-contractible terms remain in their original prefixes.
    """
    L=dict(L);R=dict(R);P=defaultdict(int)
    for s in set(L)|set(R):
        a=L.get(s,0);b=R.get(s,0)
        if (a+b)%2:continue
        L.pop(s,None);R.pop(s,None)
        P[s]=(P[s]+(a+b)//2)%mod
        P[s|high]=(P[s|high]+(a-b)//2)%mod
    return L,R,dict(P)

def embedding_capacity(codes,k,width=22):
    counts=defaultdict(int)
    for c in codes:
        assert 0<=c<1<<k
        counts[c]+=1
    cap=1<<(width-k)
    return max(counts.values(),default=0)<=cap, max(counts.values(),default=0),cap

def encode_fiber_rank(codes,k,width=22):
    counts=defaultdict(int);out=[]
    for c in codes:
        r=counts[c];counts[c]+=1
        assert r<1<<(width-k)
        out.append(c|(r<<k))
    assert len(out)==len(set(out))
    return out

def echo(a,b,g):
    return (a^g)+(b^g)-a-b

def selftest():
    for r,f in product(range(2),repeat=2):assert phase_identity(r,f)
    nodes=[None]+[(p,v) for p in range(4) for v in range(1,4)]
    for a,b,p in product(nodes,nodes,range(4)):
        old=0 if a is None or a[0]!=p else a[1]
        new=0 if b is None or b[0]!=p else b[1]
        for u,v,w in direction_transition(a,b):
            old^=w*((u==p)^(v==p))
        assert old==new
    for a,b,g in product(range(2),repeat=3):
        if not (a and b):assert echo(a,b,g)==2*(not a and not b and g)
    for p,q in product(range(8),repeat=2):
        if p==q:continue
        z,ops,pat=affine_line(p,q)
        def transform(x):
            for a,b in ops:x^=((x>>a)&1)<<b
            return x
        assert [x for x in range(8) if (transform(x)&~(1<<z))==(pat&~(1<<z))]==sorted([p,q])
    print('V54 finite transport identities PASS')
if __name__=='__main__':selftest()
