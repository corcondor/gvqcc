"""Exact packed Boolean factorization in a supplied invariant affine subspace."""
from functools import reduce
from operator import xor
from itertools import product

def bxor(xs):
    return reduce(xor, xs, 0)

def basis(values, mask):
    piv = {}
    for i, value in enumerate(values):
        v, m = value & mask, 1 << i
        while v:
            k = v.bit_length() - 1
            if k not in piv:
                piv[k] = (v, m)
                break
            w, n = piv[k]
            v, m = v ^ w, m ^ n
    return piv

def solve(piv, v):
    m = 0
    while v:
        k = v.bit_length() - 1
        if k not in piv:
            return None
        w, n = piv[k]
        v, m = v ^ w, m ^ n
    return m

def evaluate(values, m):
    return bxor(v for i, v in enumerate(values) if m >> i & 1)

def factor(values, a, f, full):
    """Find l,b in span(values) such that f=l XOR (a AND b), exactly."""
    l = solve(basis(values, full ^ a), f & (full ^ a))
    r = solve(basis(values, a), f & a)
    if l is None or r is None:
        return None
    b = l ^ r
    assert evaluate(values, l) ^ (a & evaluate(values, b)) == f
    return l, b

def test():
    rows = list(product((0, 1), repeat=3))
    x,y,z = [sum(row[i] << j for j,row in enumerate(rows)) for i in range(3)]
    full=(1<<len(rows))-1;values=[x,y,z,full]
    affine=[evaluate(values,m) for m in range(16)]
    for a in affine:
        want={l^(a&b) for l in affine for b in affine}
        for f in range(full+1):
            assert (factor(values,a,f,full) is not None)==(f in want)
    for d,e,p,q,r in product((0,1),repeat=5):
        assert (d&p)^(e&q)^((d^e)&r)==(d&(p^r))^(e&(q^r))
    print('PASS: 4096 exact factorization cases; 32 triangle identities')
if __name__=='__main__':test()
