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
