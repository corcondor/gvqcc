"""GF(2) shared trilinear factor core, extracted from V47 native emitter.
Factors are nonnegative bit masks of homogeneous linear forms. Products
are evaluated in the Boolean quotient x_i**2=x_i. No native emitter
dependencies in this core.
"""
from collections import defaultdict
from itertools import combinations

def bits(x):
    while x:
        b=x&-x
        yield b.bit_length()-1
        x^=b

def expand(forms):
    p={()}
    for f in forms:
        q=set()
        for t in p:
            for i in bits(f):
                q.symmetric_difference_update({tuple(sorted(set(t)|{i}))})
        p=q
    return p

def merge(triples,low=()):
    ts=set();lo=set(low);history=[]
    def add(t):
        if not all(t):return
        z=tuple(sorted(set(t)))
        if len(z)<3:lo.symmetric_difference_update(expand(z))
        else:ts.symmetric_difference_update({z})
    original=set(lo)
    for t in triples:
        original.symmetric_difference_update(expand(t))
        add(t)
    while True:
        pairs=defaultdict(list)
        for t in sorted(ts):
            for p in combinations(t,2):pairs[p].append(t)
        if not pairs:break
        pair,group=max(pairs.items(),key=lambda x:(len(x[1]),-sum(a.bit_count() for a in x[0])))
        if len(group)<2:break
        residue=0
        for t in group:
            ts.remove(t);residue^=next(v for v in t if v not in pair)
        add((*pair,residue))
        history.append((pair,len(group),residue))
    check=set(lo)
    for t in ts:check.symmetric_difference_update(expand(t))
    assert check==original
    return sorted(ts),sorted(lo,key=lambda t:(len(t),t)),history

def regression():
    import random
    r=random.Random(47)
    for _ in range(512):
        terms=[tuple(r.randrange(1,64) for j in range(3)) for i in range(30)]
        ts,lo,_=merge(terms)
        for row in range(64):
            def l(f):return (f&row).bit_count()%2
            def p(t):return all(l(f) for f in t)
            expect=sum(p(t) for t in terms)%2
            got=(sum(p(t) for t in ts)+sum(all((row>>i)&1 for i in t) for t in lo))%2
            assert expect==got
    print("GF2 shared factor regression PASS")

if __name__=="__main__":regression()
