# sparse anchors: closable functions (degree <= 2 in the free functions) written as combinations of few rows of
# non-early chips; those chips are placed last, so the anchors cost no window space while it is tight.
import random, itertools
from gf2 import *

def closable_basis(free_funcs):
    e=Ech(); out=[]
    cand=[v for v,_ in free_funcs]
    prods=[a&b for i,a in enumerate(cand) for b in cand[i+1:]]
    for v in cand+prods:
        if e.add(v): out.append(v)
    return out

def codewords_basis(rows, Q, ny):
    """all lambda over rows with sum(lambda rows) in span(Q).  returns list of (lambda_mask, value)"""
    ce=CombEch()
    n=len(rows)
    deps=[]
    # first Q (tag bits beyond n are tracked as 0 contribution)
    for q in Q:
        ce.add(q, 0)
    for j,v in enumerate(rows):
        d=ce.add(v, 1<<j)
        if d is not None: deps.append(d)
    return deps

def find_anchors(rows, chip_ids, free_funcs, ny, count=3, tries=4000, seed=1, prior=frozenset(), limited=frozenset(), budget=10**9, maxsize=34):
    """rows: list of row functions (index = row id j), chip_ids: chips allowed (non-early).
    returns list of (value, chipset) for `count` anchors, minimising the union of chips."""
    rng=random.Random(seed)
    idx=[j for i in chip_ids for j in (2*i,2*i+1)]
    sub=[rows[j] for j in idx]
    Q=closable_basis(free_funcs)
    gens=codewords_basis(sub, Q, ny)
    fe=Ech([v for v,_ in free_funcs])
    def value(l):
        v=0; t=0; x=l
        while x:
            if x&1: v^=sub[t]
            x>>=1; t+=1
        return v
    def chips_of(l):
        s=set(); t=0; x=l
        while x:
            if x&1: s.add(idx[t]//2)
            x>>=1; t+=1
        return s
    L=len(idx)
    found={}
    k=len(gens)
    for it in range(tries):
        perm=list(range(L)); rng.shuffle(perm)
        # systematic form with respect to a random information set
        G=gens[:]
        piv=[]
        r=0
        for col in perm:
            p=next((t for t in range(r,k) if G[t]>>col&1), None)
            if p is None: continue
            G[r],G[p]=G[p],G[r]
            for t in range(k):
                if t!=r and G[t]>>col&1: G[t]^=G[r]
            r+=1
            if r==k: break
        cands=G+[G[a]^G[b] for a,b in rng.sample(list(itertools.combinations(range(k),2)), min(150,k*(k-1)//2))]
        for l in cands:
            c=chips_of(l)
            if len(c|prior)<=max(maxsize,len(prior)+2) and len(c&limited)<=budget and l not in found:
                v=value(l)
                if fe.reduce(v)!=0: found[l]=(len(c),c,v)
        if it>tries//2 and len(found)>=1500: break
    items=sorted(found.values(), key=lambda t:(len(t[1]|prior), t[0]))
    # greedy choice of `count` independent anchors with small chip union
    best=None
    for start in items[:40]:
        chosen=[start]; union=set(start[1])|set(prior); e=Ech([v for v,_ in free_funcs]+[start[2]])
        while len(chosen)<count:
            opts=[(len(union|t[1]),t) for t in items if e.reduce(t[2])!=0 and len((union|t[1])&limited)<=budget]
            if not opts: break
            sz,t=min(opts,key=lambda z:z[0])
            chosen.append(t); union|=t[1]; e.add(t[2])
        if len(chosen)==count and (best is None or len(union)<best[0]):
            best=(len(union),chosen,union)
    return best, (items[0][0] if items else None), len(items)


def anchor_set(rows, chip_ids, free_funcs, size, want, start, rng, rounds=40):
    """a set Z of `size` chips whose rows contain >= want independent closable combinations (mod free);
    local search by chip swaps.  returns (anchor values, Z) or None."""
    Q = closable_basis(free_funcs)
    qe = Ech(Q)
    fe = Ech([v for v, _ in free_funcs])

    def score(Z):
        e = Ech()
        for v in Q:
            e.add(v)
        r = Ech()
        n0 = e.n
        for i in Z:
            for v in (rows[2 * i], rows[2 * i + 1]):
                e.add(v)
                r.add(v)
        meet = n0 + r.n - e.n                      # dim(span rows ∩ closable)
        fr = Ech([v for v, _ in free_funcs])
        nf = fr.n
        for i in Z:
            for v in (rows[2 * i], rows[2 * i + 1]):
                fr.add(v)
        meetf = nf + r.n - fr.n                    # dim(span rows ∩ span free)
        return meet - meetf

    pool = list(chip_ids)
    Z = list(start)[:size]
    others = [i for i in pool if i not in set(Z)]
    rng.shuffle(others)
    while len(Z) < size:
        Z.append(others.pop())
    best = score(Z)
    for it in range(rounds):
        if best >= want:
            break
        improved = False
        out = [i for i in pool if i not in set(Z)]
        inn = Z[:]
        rng.shuffle(inn); rng.shuffle(out)
        for a in inn:
            for b in out:
                Z2 = [b if i == a else i for i in Z]
                s = score(Z2)
                if s > best or (s == best and rng.random() < 0.02):
                    improved = s > best
                    Z, best = Z2, s
                    break
            if improved or best >= want:
                break
        if not improved and rng.random() < 0.5:
            k = rng.randrange(len(Z))
            out = [i for i in pool if i not in set(Z)]
            Z[k] = rng.choice(out)
            best = score(Z)
    if best < want:
        return None, best
    # closable combinations inside Z
    ce = CombEch()
    for q in Q:
        ce.add(q, 0)
    idx = [j for i in Z for j in (2 * i, 2 * i + 1)]
    vals = []
    chosen = Ech([v for v, _ in free_funcs])
    for t, j in enumerate(idx):
        d = ce.add(rows[j], 1 << t)
        if d is not None:
            v = 0
            for s2 in range(len(idx)):
                if d >> s2 & 1:
                    v ^= rows[idx[s2]]
            if chosen.add(v):
                vals.append(v)
    return (vals[:want], set(Z)), best
