"""Compare the half-coordinate seam before/after moving joint scaling past U,T."""
import json, random
import crt882 as C

def sqrtr(v):
    return C.gf_pow(v,2048,12,C.MOD)
def parts(v):
    return [list(map(sqrtr,v[i::2])) for i in (0,1)]
def raw_words(a,b,s):
    return [C.m(s,C.m(x,x)) for pair in zip(a,b) for x in pair]

def main():
    rng=random.Random(316227)
    done=0
    def sample(n):
        return [rng.randrange(4096) for _ in range(n)]
    for _ in range(256):
        b=sample(17)+[1]
        a=sample(18)
        try:
            c=C.inversemod(a,b)
        except AssertionError:
            continue
        s=rng.randrange(2,4096)
        ac,bc=parts(raw_words(a,b,s))
        p,q=sample(18),sample(17)
        pc,qc=parts(raw_words(p,q+[0],s)[:-1])
        # B-only scaling before reduction; split path never scales lower N words.
        bn=[C.m(sqrtr(C.inv(s)),x) for x in bc]
        assert bn==b
        cc=C.inversemod(ac,bn)
        rr=lambda k,x:C.div(C.mul(k,x),b)[1]
        h=(p[-1],rr(c,p),rr(c,q))
        k=(C.m(pc[-1],sqrtr(C.inv(s))),rr(cc,pc),rr(cc,qc))
        assert h==k
        done+=1
    print(json.dumps(dict(sampled=256,coprime_cases=done,errors=0)))
if __name__=='__main__':
    main()
