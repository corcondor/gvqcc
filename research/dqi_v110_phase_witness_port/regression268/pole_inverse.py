"""Canonical, residue-reconstructed inverse for #268 fraction-free chart."""
import argparse
import json
from pathlib import Path
import random
import crt882 as F


def regular_head(n, d, q):
    return F.div(F.mul(n,F.inversemod(d,q)),q)[1]


def forward(n,d,q):
    dr=F.div(d,q)[1]
    if not dr:
        assert F.div(n,q)[1] and d
        u,v,h=F.mul(q,d),n,[]
    else:
        h=regular_head(F.div(n,q)[1],dr,q)
        v,z=F.div(F.add(n,F.mul(h,d)),q)
        assert not z
        u=d
    assert F.div(u,q)[1]==dr
    return u,v,h


def inverse(u,v,q,h):
    if not F.div(u,q)[1]:
        assert not h and u and F.div(v,q)[1]
        d,r=F.div(u,q)
        assert not r
        return v,d
    return F.add(F.mul(q,v),F.mul(h,u)),u


def exact_witness(path):
    w=json.loads((path/'captured_input.json').read_text())
    observed=json.loads((path/'extract_witness.json').read_text())['words'][-1]
    xs=[F.exp[k] for k in w['support']]
    qs=[[F.m(c,c)^c^2048,1,1] for c in [2*i for i in range(17) for _ in range(2)]]
    u=[0,0,1]
    for q in qs:u=F.mul(u,q)
    d=[1]
    for a in xs:d=F.mul(d,[a,1])
    n=[]
    for a,e in zip(xs,w['magnitudes']):
        dq,r=F.div(d,[a,1]);assert not r
        t=F.m(F.m(a,e),F.evalp(u,a))
        n=F.add(n,[F.m(t,x) for x in dq])
    old=n,d
    poles=[]
    zero_regular=0
    internal=[]
    for k,q in enumerate(qs):
        a,b,h=forward(n,d,q)
        assert inverse(a,b,q,h)==(n,d)
        if not F.div(a,q)[1]:poles.append(k)
        elif not h:zero_regular+=1
        internal.append(h)
        assert (h+[0,0])[:2]==observed[2*k:2*k+2]
        n,d=a,b
    assert len(d)==1
    n=[F.m(y,F.inv(d[0])) for y in n]; d=[1]
    assert (n+[0,0])[:2]==observed[-2:]
    for q,h in reversed(list(zip(qs,internal,strict=True))):
        n,d=inverse(n,d,q,h)
    a=[F.m(y,F.inv(d[-1])) for y in n]
    b=[F.m(y,F.inv(d[-1])) for y in d]
    assert old==(a,b)
    return dict(poles=poles,zero_regular_heads=zero_regular,
        reconstructed_degrees=[len(a)-1,len(b)-1],exact_up_to_scalar=True)


def stress():
    rng=random.Random(208628)
    checks=poles=regular_zero=0
    for j in range(256):
        q=[F.ks[j%len(F.ks)],1,1]
        d=[rng.randrange(4096) for _ in range(2+j%6)]+[1]
        d=F.mul(d,q)
        n=[rng.randrange(1,4096)]
        start=n,d
        data=[]
        for k in range(2+2*(j%11)):
            a,b,h=forward(n,d,q)
            assert not h
            assert inverse(a,b,q,h)==(n,d)
            poles+=not F.div(a,q)[1]
            regular_zero+=bool(F.div(a,q)[1])
            data.append(h)
            n,d=a,b
            checks+=1
        for h in reversed(data):n,d=inverse(n,d,q,h)
        assert (n,d)==start
    return dict(paths=256,steps=checks,poles=poles,regular_h_zero=regular_zero)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('fixture',type=Path)
    p.add_argument('out',type=Path)
    a=p.parse_args()
    v=dict(pr268_exact=exact_witness(a.fixture),alternating_repeated_quadratic=stress(),
        scope='Classical coefficient recurrence only; no physical register or gate claims.')
    a.out.write_text(json.dumps(v,indent=2)+'\n')
    print(v)


if __name__=='__main__':
    main()
