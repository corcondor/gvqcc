"""Exact stage blocks of our loaders: output functionals fed only by stage-A products, then by A+B."""
import json
from lib import *
BNAMES = [wn(n) for n in range(35)]
def combos_str(g):
    return '+'.join(BNAMES[n] for n in range(35) if g >> n & 1)
def rref(vs):
    piv = {}
    for g in vs:
        for p, row in piv.items():
            if g >> p & 1: g ^= row
        if g:
            p = g.bit_length()-1
            for q in list(piv):
                if piv[q] >> p & 1: piv[q] ^= g
            piv[p] = g
    return [piv[p] for p in sorted(piv)]
out = {}
for k in WIRED:
    L = Loader(k)
    nmain = L.no - (3 if k == 14 else 4)
    F = [bits(L.FAN[i]) for i in range(L.no)]
    # functionals g on the 35 wires with <g, fan_i> = 0 for all i in range
    def ann(rng):
        return nullspace([F[i] for i in rng], 35)
    allann = ann(range(nmain))            # wires combos never fed by main products (cache-linear)
    a_ex = ann(range(39, nmain))          # fed only by A (and trivially cache)
    ab_ex = ann(range(78, nmain))
    def quot(basis, mod):
        piv = {}
        for g in mod: ins(piv, g)
        res = []
        for g in rref(basis):
            r = reduce(piv, g)
            if r:
                ins(piv, r); res.append(r)
        return res
    A = quot(a_ex, allann); AB = quot(ab_ex, a_ex); C = quot([1 << n for n in range(35)], ab_ex)
    print(f'bank {k}: cache-linear combos {len(allann)}, A {len(A)}, B {len(AB)}, C {len(C)} (nmain {nmain})')
    for name, S in (('A', A), ('B', AB), ('C', C)):
        print('   ', name, [combos_str(g) for g in S])
    print('    zero-mixed', [combos_str(g) for g in rref(allann)])
    out[k] = dict(A=A, B=AB, C=C, Z=rref(allann), nmain=nmain)
json.dump({str(k): v for k, v in out.items()}, open('data/blocks.json', 'w'))
