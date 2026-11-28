# chip order: early chips chosen so that every free column can still be completed afterwards
from frame import *
from gf2 import Ech
from solve2 import coef_vectors

def early_order(F, cov, e, rng, tries=1000):
    coef=coef_vectors(cov, F.NX)
    masks={}
    for y in range(F.ny):
        if len(F.carex[y])<F.nx: masks.setdefault(F.carex[y], F.care_mask(y))
    n=len(cov)
    big=max(len(R) for R in masks)
    Rb=[m for R,m in masks.items() if len(R)==big]
    def nz(i): return sum(1 for j in (2*i,2*i+1) for m in Rb if coef[j]&m)
    for t in range(tries):
        o=sorted(range(n), key=lambda i:(nz(i), rng.random()))
        E=set(o[:e])
        if all(Ech([coef[j]&m for j in range(2*n) if j//2 not in E]).n >= 30*(len(R)-1) for R,m in masks.items()):
            first=o[:e]; rng.shuffle(first)
            rest=o[e:]; rng.shuffle(rest)
            return first+rest
    raise RuntimeError('no suitable early chip set')
