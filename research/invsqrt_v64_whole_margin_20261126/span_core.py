"""Portable exact span-intersection core from the V64 whole-oracle experiment."""
def independent(vs):
    piv, out = {}, []
    for v in vs:
        u = v
        while u and u.bit_length()-1 in piv:
            u ^= piv[u.bit_length()-1]
        if u:
            piv[u.bit_length()-1] = u
            out.append(v)
    return out

def intersection(A, B):
    piv = {}
    for v in A:
        u = v
        while u and u.bit_length()-1 in piv:
            u ^= piv[u.bit_length()-1][0]
        assert u
        piv[u.bit_length()-1] = (u, 0)
    out = []
    for j, v in enumerate(B):
        u, c = v, 1 << j
        while u and u.bit_length()-1 in piv:
            z, k = piv[u.bit_length()-1]
            u ^= z
            c ^= k
        if u:
            piv[u.bit_length()-1] = (u, c)
        else:
            z = 0
            for k in range(len(B)):
                if c >> k & 1:
                    z ^= B[k]
            assert z
            out.append(z)
    assert len(out) == len(A)+len(B)-len(independent(A+B))
    return out

def rankcost(A, B):
    return len(independent(A+B))-len(A)

if __name__ == "__main__":
    import random
    rng=random.Random(20261126)
    def span(xs):
        s={0}
        for x in xs:
            s |= {v^x for v in s}
        return s
    for _ in range(1000):
        a=independent([rng.randrange(1,256) for _ in range(rng.randrange(9))])
        b=independent([rng.randrange(1,256) for _ in range(rng.randrange(9))])
        i=intersection(a,b)
        assert span(i)==span(a)&span(b)
        assert rankcost(a,b)==len(b)-len(i)
    print("1000 span tests passed")
