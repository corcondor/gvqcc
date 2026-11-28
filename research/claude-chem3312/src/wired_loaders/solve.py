"""Exact joint linear system for one block-2 candidate: m output combos, zero functional(s), planted elements.
Unknowns: stage-A steering bits s[o][i] (m x 39) and admissible dead-cell flips.
Equations: zero functional rows p=1..75 for every combo; planted element rows p=1..75; Phi of every wire's flips."""
import sys, json, random
import numpy as np
from tgt import *
from capacity import Cap
from zc_scan import zeta_list

def solve_system(eqs, nvar, rng=None):
    """eqs: list of (mask, rhs). returns (rank, solution or None, nullspace dimension)"""
    piv = {}
    for m, r in eqs:
        while m:
            t = m.bit_length() - 1
            if t in piv:
                pm, pr = piv[t]
                m ^= pm
                r ^= pr
            else:
                piv[t] = (m, r)
                break
        else:
            if r:
                return len(piv), None, None
    # random solution: assign free vars randomly, back-substitute from low pivots upward
    x = 0
    if rng is not None:
        x = rng.getrandbits(nvar)
    for t in sorted(piv):
        m, r = piv[t]
        rest = m & ~(1 << t)
        val = r ^ (bin(rest & x).count("1") & 1)
        x = (x & ~(1 << t)) | (val << t)
    return len(piv), x, nvar - len(piv)

class Block2:
    def __init__(self, k, batches, B, cap=None):
        """B: list of output combos given as 35-bit wire functionals (modulo cache-linear / A combos)"""
        self.cap = cap or Cap(k)
        T = self.T = self.cap.T
        self.k = k
        self.batches = batches
        self.B = B
        self.m = len(B)
        self.flips = self.cap.flips(batches)          # (p, x, image, a, batch, vec35)
        self.nsteer = self.m * 39
        self.nflip = len(self.flips)
        self.nvar = self.nsteer + self.nflip
        # mixed delta of every combo: [75, 14] (columns = ordinary x)
        self.D = [T.combo_delta(g) for g in B]
        self.Dcol = [[bits(D[:, j]) for j in range(14)] for D in self.D]
        self.Acol = self.cap.Acol
        self.colidx = self.cap.colidx
        # flip effect on combo o: parity(B[o] & vec)
        self.fhit = [[bin(g & f[5]).count("1") & 1 for f in self.flips] for g in B]
        # Phi equations (flips only): for each wire n and each phi
        eqs = []
        for n in range(35):
            for cells in T.phi:
                cs = set(cells)
                m = 0
                for i, f in enumerate(self.flips):
                    p, x, im, a, b, v = f
                    if v >> n & 1 and (p, x) in cs:
                        m |= 1 << (self.nsteer + i)
                if m:
                    eqs.append((m, 0))
        self.phi_eqs = eqs

    def functional_eqs(self, terms):
        """terms: list of (o, xmask14) : the functional sum_o sum_{x in xmask} mixed(T'_o)(p, x) = 0 for p = 1..75"""
        # steering part
        Asl = {}
        for o, xm in terms:
            for i in range(39):
                v = 0
                for j in range(14):
                    if xm >> j & 1:
                        v ^= self.Acol[i][j]
                key = (o, i)
                Asl[key] = Asl.get(key, 0) ^ v
        rhs = 0
        for o, xm in terms:
            for j in range(14):
                if xm >> j & 1:
                    rhs ^= self.Dcol[o][j]
        # flip part: for each flip its set of rows
        frows = []
        for i, f in enumerate(self.flips):
            p, x, im, a, b, v = f
            if x not in self.colidx:
                continue
            jx = self.colidx[x]
            par = 0
            for o, xm in terms:
                if xm >> jx & 1 and self.fhit[o][i]:
                    par ^= 1
            if not par:
                continue
            if 1 <= p <= 75:
                rows = 1 << (p - 1)
            elif p == 0:
                rows = (1 << 75) - 1
            else:
                continue
            frows.append((i, rows))
        masks = [0] * 75
        for (o, i), v in Asl.items():
            while v:
                low = v & -v
                masks[low.bit_length() - 1] ^= 1 << (o * 39 + i)
                v ^= low
        for i, rows in frows:
            bit = 1 << (self.nsteer + i)
            while rows:
                low = rows & -rows
                masks[low.bit_length() - 1] ^= bit
                rows ^= low
        return [(masks[r], (rhs >> r) & 1) for r in range(75)]

    def zero_eqs(self, zmask):
        eqs = []
        for o in range(self.m):
            eqs += self.functional_eqs([(o, zmask)])
        return eqs

def zmask_cols(cols):
    colidx = {x: j for j, x in enumerate(ORDX)}
    return sum(1 << colidx[x] for x in cols)

def random_combos(cap, m, rng):
    G = cap.G
    while True:
        out = []
        piv = {}
        while len(out) < m:
            c = rng.getrandbits(len(G))
            if c and ins(piv, c):
                g = 0
                for i in range(len(G)):
                    if c >> i & 1:
                        g ^= G[i]
                out.append(g)
        return out

def best_zetas(cap, batches, m, top=5):
    res = []
    rA = {}
    for z in zeta_list():
        ra = cap.rankA(z)
        if ra < 33:
            continue
        c = cap.capacity(batches, z, m)
        res.append((c - m * (75 - ra), ra, z))
    # also low A-rank but huge capacity
    for z in zeta_list():
        ra = cap.rankA(z)
        if ra >= 33:
            continue
        c = cap.capacity(batches, z, m)
        res.append((c - m * (75 - ra), ra, z))
    res.sort(reverse=True)
    return res[:top]

if __name__ == "__main__":
    rng = random.Random(1)
    for spec in sys.argv[1:]:
        k, bs = spec.split(":")
        k = int(k); batches = [int(b) for b in bs.split(",")]
        cap = Cap(k)
        for m in (7, 8):
            bz = best_zetas(cap, batches, m, 6)
            line = []
            for marg, ra, z in bz:
                B = random_combos(cap, m, rng)
                blk = Block2(k, batches, B, cap)
                eqs = blk.zero_eqs(z) + blk.phi_eqs
                rk, x, nd = solve_system(eqs, blk.nvar, rng)
                line.append((marg, ra, "OK" if x is not None else "fail", rk, len(eqs), nd))
            print(f"bank {k} batches {batches} m={m} (nvar {blk.nvar}):", line, flush=True)
