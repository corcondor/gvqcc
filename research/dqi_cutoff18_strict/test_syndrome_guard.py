"""Strict classical tests; no KickMix or Lean oracle claim."""
import random
from syndrome_guard import mul,power,inv,Certificate,certify_rank_le_two,mask_phase

def main():
    rng=random.Random(20261128)
    assert len({power(2,i) for i in range(4095)})==4095
    for _ in range(2000):
        x=rng.randrange(1,4096); y=rng.randrange(1,4096)
        assert mul(x,inv(x))==1 and mul(mul(x,y),inv(y))==x
    for n in (0,1,2):
        for _ in range(120):
            roots=tuple(rng.sample(range(1,4096),n))
            amps=tuple(rng.randrange(1,4096) for _ in roots)
            c=Certificate(roots,amps)
            got=certify_rank_le_two(c.moments())
            assert got is not None and got.moments()==c.moments()
            assert sorted(zip(got.roots,got.magnitudes))==sorted(zip(roots,amps))
            y=c.moments()
            y[-1]^=1
            assert certify_rank_le_two(y) is None
    # 3 distinct support points but first 2x2 Hankel minor is zero.
    c=Certificate((1,2,4),(1,inv(2),inv(4)))
    s=c.moments()
    assert mul(s[0],s[2])^mul(s[1],s[1])==0
    assert certify_rank_le_two(s) is None
    mask=[0]*4095
    mask[0]=2
    assert mask_phase(Certificate((1,),(3,)),mask)==1
    print("PASS: GF arithmetic, rank<=2 full-70 witnesses, rank-3 counterexample")

if __name__=="__main__":
    main()

def test_sharp_37():
    # 37 distinct nonzero roots; barycentric null-vector of the first
    # 36 Vandermonde rows. Split the 37-term null-vector into 35+2.
    roots=[power(2,i) for i in range(37)]
    weights=[]
    for i,x in enumerate(roots):
        den=x
        for j,y in enumerate(roots):
            if i!=j: den=mul(den,x^y)
        weights.append(inv(den))
    old=Certificate(tuple(roots[:35]),tuple(weights[:35])).moments()
    cand=Certificate(tuple(roots[35:]),tuple(weights[35:])).moments()
    assert old[:36]==cand[:36] and old[36]!=cand[36]
    print("SHARP: first 36 DQI moments coincide, moment 37 differs")

if __name__=="__main__":
    test_sharp_37()

def test_rank2_37_recurrence():
    from syndrome_guard import certify_promised_input_rank2_first37
    r=random.Random(326723)
    for rank in (0,1,2,3,4,17,35):
        for _ in range(25):
            roots=tuple(r.sample(range(1,4096),rank))
            c=Certificate(roots,tuple(r.randrange(1,4096) for _ in roots))
            z=certify_promised_input_rank2_first37(c.moments())
            if rank<=2:
                assert z is not None and z.moments()==c.moments()
            else: assert z is None
    roots=[power(2,i) for i in range(37)]
    weights=[]
    for i,x in enumerate(roots):
        den=x
        for j,y in enumerate(roots):
            if i!=j:den=mul(den,x^y)
        weights.append(inv(den))
    original=Certificate(tuple(roots[:35]),tuple(weights[:35])).moments()
    assert certify_promised_input_rank2_first37(original) is None
    print("PASS: exact 37-moment legal-input rank<=2 recurrence")

if __name__=="__main__":
    test_rank2_37_recurrence()
