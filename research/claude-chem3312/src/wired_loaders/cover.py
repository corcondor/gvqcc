"""Choose block-2 output subspaces with large minimum row coverage, then solve exactly."""
import sys, random, json
import numpy as np
from tgt import *
from capacity import Cap
from solve import *
from zc_scan import zeta_list

def coverage_table(cap, batches, z):
    """cov[c] for every output coefficient vector c (over cap.G): number of rows p=1..75 where c is hit by a flip"""
    F = cap.Fp(batches, z)
    n = cap.nout
    N = 1 << n
    idx = np.arange(N, dtype=np.uint32)
    cov = np.zeros(N, np.int16)
    for p in range(1, 76):
        hit = np.zeros(N, bool)
        for v in F[p].values():
            hit |= (popc16(idx & np.uint32(v)) & 1).astype(bool)
        cov += hit
    return cov

_PT = np.array([bin(i).count("1") for i in range(1 << 16)], np.uint8)
def popc16(a):
    return _PT[a & 0xFFFF] + _PT[(a >> 16) & 0xFFFF]

def pick_subspace(cov, m, thr, rng, tries=4000):
    good = np.flatnonzero(cov >= thr)
    good = good[good != 0]
    if len(good) == 0:
        return None
    goodset = np.zeros(len(cov), bool)
    goodset[good] = True
    for t in range(tries):
        basis = []
        span = np.array([0], np.int64)
        cand = rng.permutation(good)
        for c in cand:
            c = int(c)
            new = span ^ c
            if not goodset[new].all():
                continue
            basis.append(c)
            span = np.concatenate([span, new])
            if len(basis) == m:
                return basis
        if t > 40:
            break
    return None

def combos_from_coeffs(cap, coeffs):
    out = []
    for c in coeffs:
        g = 0
        for i in range(cap.nout):
            if c >> i & 1:
                g ^= cap.G[i]
        out.append(g)
    return out

def try_block(k, batches, m, nz=40, verbose=False, seed=1):
    cap = Cap(k)
    rng = np.random.default_rng(seed)
    pyr = random.Random(seed)
    zl = zeta_list()
    cand = []
    rA = {z: cap.rankA(z) for z in zl}
    # preselect zetas by capacity margin
    scored = sorted(((cap.capacity(batches, z, m) - m * (75 - rA[z]), rA[z], z) for z in zl), reverse=True)[:nz]
    best = None
    for marg, ra, z in scored:
        cov = coverage_table(cap, batches, z)
        # largest threshold at which an m-dim subspace exists
        lo = None
        for thr in range(75 - ra + 14, 75 - ra - 4, -1):
            sub = pick_subspace(cov, m, thr, rng)
            if sub is not None:
                lo = thr
                break
        if lo is None:
            continue
        B = combos_from_coeffs(cap, sub)
        blk = Block2(k, batches, B, cap)
        eqs = blk.zero_eqs(z) + blk.phi_eqs
        rk, x, nd = solve_system(eqs, blk.nvar, pyr)
        ok = x is not None
        if best is None or (ok, lo - (75 - ra), marg) > (best[0], best[1], best[2]):
            best = (ok, lo - (75 - ra), marg, ra, z, sub, lo)
        if verbose:
            print(f"      zeta {z:014b} margin {marg} rankA {ra} min-coverage {lo} (need >= {75-ra}) solvable {ok}", flush=True)
        if ok and lo - (75 - ra) >= 6:
            break
    return cap, best

if __name__ == "__main__":
    res = {}
    for spec in sys.argv[1:]:
        k, bs, m = spec.split(":")
        k = int(k); batches = [int(b) for b in bs.split(",")]; m = int(m)
        cap, best = try_block(k, batches, m)
        if best is None:
            print(f"bank {k} batches {batches} m={m}: no zeta with a covering subspace", flush=True)
            continue
        ok, slack, marg, ra, z, sub, lo = best
        cols = [ORDX[j] for j in range(14) if z >> j & 1]
        print(f"bank {k} batches {batches} m={m}: solvable={ok} min-coverage {lo} slack {slack} margin {marg} rankA {ra} zeta cols {cols} coeffs {sub}", flush=True)
