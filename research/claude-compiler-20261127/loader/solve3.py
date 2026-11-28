# solve2.solve_all with one extra relation that ties TWO partial columns: z_y1 + z_y2 = z(S), h_y1 + h_y2 = h(S).
# With z_y1 left free on its don't-care x, the 30 h conditions are LINEAR in z_y1 (polarisation:
# E(z) + E(z + v) = E(v) + B(z, v)), so no cover search is needed for this relation.  y1 is then fixed up front.
import numpy as np, random
from frame import *
from gf2 import *
from solve import e_vec, h_vec
from solve2 import coef_vectors, solve_all

NO = 30


def solve_pair(F, cov, nrel, pair, seed=7, forced=None, verbose=True, base=None):
    y1, y2 = pair
    assert y1 not in (forced or {}) and y2 not in (forced or {})
    # the single-column relations first (four-care by the h solver, forced five-care columns from the cover)
    sol = base if base is not None else solve_all(F, cov, nrel, seed=seed, forced=forced, verbose=verbose)
    assert y1 in sol['free'] and y2 in sol['free'], 'pair columns must still be free'
    rng = random.Random(seed * 31 + 5)
    s = sol['s']
    n = len(s)
    coef = sol['coef']
    full = F.full
    z, h = list(sol['z']), list(sol['h'])
    lin = sol['lin']
    both = [x for x in F.carex[y1] if x and x in F.carex[y2]]
    # support S over full columns: care equations where both columns are cared, plus the linear functions
    eqs, rhs = [], []
    for o in range(NO):
        for x in both:
            r = 0
            for t, y in enumerate(full):
                if F.N[o, x - 1, y]:
                    r |= 1 << t
            eqs.append(r)
            rhs.append(int(F.N[o, x - 1, y1]) ^ int(F.N[o, x - 1, y2]))
    for f in lin:
        r = 0
        for t, y in enumerate(full):
            if f[y]:
                r |= 1 << t
        eqs.append(r)
        rhs.append(int(f[y1]) ^ int(f[y2]))
    ssol = solve_linear(eqs, rhs, len(full))
    assert ssol is not None, 'pair relation: linear system unsolvable'
    part, null = ssol
    d0 = []
    for y in (y1, y2):
        d = 0
        for o in range(NO):
            if F.Dg[o, 0, y]:
                d |= 1 << o
        d0.append(d)
    tried = 0
    order = list(range(1 << min(len(null), 12)))
    rng.shuffle(order)
    for lam in order:
        tried += 1
        c = part
        for k, v in enumerate(null):
            if lam >> k & 1:
                c ^= v
        S = [y for t, y in enumerate(full) if c >> t & 1]
        v = 0
        hv = 0
        for y in S:
            v ^= z[y]
            hv ^= h[y]
        # unknown u = z_y1: care equations of y1 on all its cared x (y2's care then follows from S), and
        # B(u, v) = E(v) + d0(y1) + d0(y2) + sum_S h
        target = e_vec(v, s) ^ d0[0] ^ d0[1] ^ hv
        rows, vals = [], []
        for x in [x for x in F.carex[y1] if x]:
            for o in range(NO):
                bit = o * F.NX + x - 1
                r = 0
                for j in range(2 * n):
                    if coef[j] >> bit & 1:
                        r |= 1 << j
                rows.append(r)
                vals.append(int(F.N[o, x - 1, y1]))
        for o in range(NO):
            r = 0
            for i in range(n):
                if s[i] >> o & 1:
                    if v >> (2 * i + 1) & 1:
                        r |= 1 << (2 * i)
                    if v >> (2 * i) & 1:
                        r |= 1 << (2 * i + 1)
            rows.append(r)
            vals.append(target >> o & 1)
        usol = solve_linear(rows, vals, 2 * n)
        if usol is None:
            continue
        u, unull = usol
        for w in unull:
            if rng.random() < 0.5:
                u ^= w
        z[y1] = u
        z[y2] = u ^ v
        h[y1] = h_vec(F, y1, z[y1], s)
        h[y2] = h_vec(F, y2, z[y2], s)
        assert h[y1] ^ h[y2] == hv, 'pair relation: h fails'
        for y in (y1, y2):
            mask = F.care_mask(y)
            lhs = 0
            for j in range(2 * n):
                if z[y] >> j & 1:
                    lhs ^= coef[j] & mask
            assert lhs == (F.col_int(y) & mask), 'pair relation: care mismatch'
        if verbose:
            print(f'  pair relation ({y1},{y2}): support {len(S)}, free dims left in z_y1 {len(unull)} (support tried {tried})',
                  flush=True)
        break
    else:
        raise RuntimeError('no support makes the pair relation solvable')
    rel = dict(sol['rel'])
    rel[y2] = S + [y1]
    free = [y for y in sol['free'] if y not in pair]
    return dict(sol, z=z, h=h, rel=rel, free=free, relcols=sorted(set(sol['relcols']) | {y2}), nrel=len(rel))
