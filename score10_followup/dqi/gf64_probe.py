#!/usr/bin/env python3
"""Check exact live-wire relations in the GF64 cubic inverse."""
import argparse
import sys
from functools import reduce
from operator import xor

def table(fn):
    return sum(fn(x)<<x for x in range(64))

def bases(items):
    basis={}
    null=[]
    for i,v in enumerate(items):
        label=1<<i
        while v:
            k=v.bit_length()-1
            if k not in basis:
                basis[k]=(v,label)
                break
            w,l=basis[k]
            v^=w
            label^=l
        if not v:
            null.append(label)
    return basis,null

def solve(target,basis):
    label=0
    while target:
        k=target.bit_length()-1
        if k not in basis:
            return None
        w,l=basis[k]
        target^=w
        label^=l
    return label

def mix(tables, mask):
    return reduce(xor, (word for i,word in enumerate(tables) if (mask>>i)&1), 0)

def probe(source):
    sys.path.insert(0,source)
    import cubic_inverse130 as c
    import kickmix as km
    bits=[table(lambda x:(x>>i)&1) for i in range(6)]
    quads=[mix(bits,a)&mix(bits,b) for a,b in c.QUADRATIC_GATES]
    known=[(1<<64)-1, *bits,*quads]
    norm_terms=[mix(known[1:7],a)&mix(known,b) for a,b in c.NORM_GATES]
    norm=[mix(known+norm_terms,mask) for mask in c.NORM_OUTPUTS]
    f=km.GF2Field(6)
    inv=[f.invert(x) if x else 0 for x in range(64)]
    targets=[table(lambda x:((inv[x]>>i)&1)) for i in range(6)]
    a=known+norm
    columns=a+[u&v for u in norm for v in known[1:]]
    linear,null=bases(columns)
    assert all(solve(t,linear) is not None for t in targets)
    print(f'scaffold rank={len(bases(a)[0])}/{len(a)} full rank={len(linear)}/{len(columns)} null={len(null)}')
    print('null:', [hex(n) for n in null])
    print('solution:',[hex(solve(t,linear)) for t in targets])
    print('scaffold',a, 'target',targets)
    return a,targets,linear,null
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True)
    probe(p.parse_args().source)
