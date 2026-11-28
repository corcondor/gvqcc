"""Counterexample factory for arbitrary additive compression of filtered moments.
Matrix rows are bit masks for a binary probe restricted to the first 52 roots.
Candidate circuits must not use these examples as a selector.
"""
from random import Random
from functools import reduce
import numpy as np
from operator import xor
import direct_codec as D
from admission import filt,G

N=52*12
ALL=(1<<N)-1
def nullvec(rows):
    basis={}
    for r in rows:
        while r:
            p=r.bit_length()-1
            if p in basis:r^=basis[p]
            else:basis[p]=r;break
    assert len(basis)<N
    root=next(i for i in range(N) if i not in basis)
    x=1<<root
    for p,r in sorted(basis.items()):
        if (x&r).bit_count()%2:x^=1<<p
    assert x and all((x&r).bit_count()%2==0 for r in rows)
    return x
def pack(e):
    return sum((e.get(i,0)<<12*(i-1)) for i in range(1,53))
def split(x):
    d={i+1:(x>>12*i)&4095 for i in range(52) if (x>>12*i)&4095}
    s=len(d);xs=list(d)
    if s<18:
        common=dict((i,1) for i in [x for x in range(1,53) if x not in d][:18-s])
        low=common;high=common|d
    elif s<=35:low={};high=d
    else:low={i:d[i] for i in xs[35:]};high={i:d[i] for i in xs[:35]}
    assert len(low)<=17 and 18<=len(high)<=35
    assert pack(low)^pack(high)==x
    return low,high
def moments(e):
    return filt(D.moments({i:D.div(u,D.ev(G,i)) for i,u in e.items()}))
def run():
    r=Random(5334)
    pairs=[]
    for s in range(1,53):
        wanted=pack({i:r.randrange(1,4096) for i in range(1,s+1)})
        p=wanted.bit_length()-1
        rows=[(1<<i)|(((wanted>>i)&1)<<p) for i in range(N) if i!=p]
        actual=nullvec(rows);assert actual==wanted
        pairs.append((rows,actual))
    for _ in range(12):
        rows=[r.getrandbits(N) for _ in range(N-1)]
        pairs.append((rows,nullvec(rows)))
    for rows,x in pairs:
        lo,hi=split(x)
        assert all((pack(lo)&r).bit_count()%2==(pack(hi)&r).bit_count()%2 for r in rows)
        a,b=moments(lo),moments(hi)
        assert a!=b
    print('64 counterexamples: every possible kernel support size plus 12 random 623-bit linear probes')
if __name__=='__main__':run()
