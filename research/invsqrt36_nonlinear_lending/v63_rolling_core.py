"""Pure-Python rolling coordinate model; no quantum compiler dependencies."""
def delta_path(words):
    """Compute XOR writes from the zero offset, with final restoration."""
    if not words:
        return []
    prev = [0] * len(words[0]); out = []
    for w in words:
        if len(w) != len(prev):
            raise ValueError('different table sizes')
        out.append([a ^ b for a,b in zip(prev,w)])
        prev = w
    out.append(list(prev))
    return out

def regression():
    import random
    r=random.Random(63)
    cases=0
    for _ in range(256):
        rows=64; n=r.randrange(1,16); base=[r.randrange(1<<n) for _ in range(rows)]
        words=[[r.randrange(1<<n) for _ in range(rows)] for _ in range(r.randrange(1,8))]
        ds=delta_path(words)
        for x,b in enumerate(base):
            for flag in (0,1):
                h=0 if flag else b
                state=h
                for j,w in enumerate(words):
                    state^=ds[j][x]
                    assert (state if flag else 0)==(w[x] if flag else 0)
                state^=ds[-1][x]
                assert state==h
                cases+=1
    print('rolling exact conditional-care regression PASS',cases)
if __name__=='__main__':regression()
