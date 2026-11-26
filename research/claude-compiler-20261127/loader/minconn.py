# Early-chip set with small "connectivity" (matroid pathwidth idea, after V75 min-dim(R) of PR #179):
# lambda(E) = rank(F + rows of E) + rank(F + rows of the others) - rank(F + all rows),
# the part that the live set must keep across the boundary of the window search.  Local search by swaps,
# keeping the completion condition of order_util.early_order.
import random
from frame import *
from gf2 import Ech
from solve2 import coef_vectors


def chip_rows(F, sol):
    n = len(sol['z'][0:0]) if False else None
    fmask = 0
    for y in sol['free']:
        fmask |= 1 << y
    z = sol['z']
    nchip = len(sol['s'])
    rows = []
    for j in range(2 * nchip):
        v = 0
        for y in range(F.ny):
            if (int(z[y]) >> j) & 1:
                v |= 1 << y
        rows.append(v & ~fmask)
    base = [((1 << F.ny) - 1) & ~fmask]
    for t in range(len(F.Y)):
        v = sum(1 << y for y in range(F.ny) if F.ybits[t][y])
        base.append(v & ~fmask)
    return rows, base


def completion_ok(F, cov, E, n, coef, masks):
    return all(Ech([coef[j] & m for j in range(2 * n) if j // 2 not in E]).n >= 30 * (len(R) - 1)
               for R, m in masks.items())


def lam(rows, base, E, n, total):
    a = Ech(base)
    b = Ech(base)
    for i in range(n):
        t = a if i in E else b
        t.add(rows[2 * i])
        t.add(rows[2 * i + 1])
    return a.n + b.n - total, a.n, b.n


def early_set(F, cov, sol, e, rng, iters=4000, verbose=True):
    coef = coef_vectors(cov, F.NX)
    masks = {}
    for y in range(F.ny):
        if len(F.carex[y]) < F.nx:
            masks.setdefault(F.carex[y], F.care_mask(y))
    n = len(cov)
    rows, base = chip_rows(F, sol)
    total = Ech(base + rows).n
    big = max(len(R) for R in masks)
    Rb = [m for R, m in masks.items() if len(R) == big]

    def nz(i):
        return sum(1 for j in (2 * i, 2 * i + 1) for m in Rb if coef[j] & m)
    E = None
    for t in range(1000):
        o = sorted(range(n), key=lambda i: (nz(i), rng.random()))
        cand = set(o[:e])
        if completion_ok(F, cov, cand, n, coef, masks):
            E = cand
            break
    assert E is not None, 'no suitable early chip set'
    best = lam(rows, base, E, n, total)
    start = best
    for it in range(iters):
        i = rng.choice(sorted(E))
        j = rng.choice([x for x in range(n) if x not in E])
        new = (E - {i}) | {j}
        val = lam(rows, base, new, n, total)
        if (val[0], val[2]) <= (best[0], best[2]) and completion_ok(F, cov, new, n, coef, masks):
            E, best = new, val
    if verbose:
        print(f'min-connectivity early set: lambda {start[0]} -> {best[0]} (rank E+F {best[1]}, rank rest+F {best[2]}, total {total})',
              flush=True)
    first = sorted(E)
    rng.shuffle(first)
    rest = [i for i in range(n) if i not in E]
    rng.shuffle(rest)
    return first + rest
