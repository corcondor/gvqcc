"""All planes (c, <q1,q2>) of a found subspace W = R + <E>, and selection of an independent set (matroid parity)
that avoids ker(zeta) where asked.  Own code."""
import itertools, random
import numpy as np
from design import *


def read_E(res_path):
    out = []
    for line in open(res_path):
        if line.startswith("E "):
            head, vals = line.split(":")
            nu = int(head.split()[1].split("=")[1])
            out.append((nu, [int(v) for v in vals.split()]))
    return out


def all_planes(inst, E):
    """lines (c, q1, q2) in instance coords: q-span in K_c = {q : image of c(x)q in span(E)}"""
    cols = inst.columns()
    Eb = {}
    for e in E:
        ins(Eb, e)
    pivs = sorted(Eb, reverse=True)

    def full_reduce(v):          # canonical representative modulo span(E) (a linear map)
        for h in pivs:
            if v >> h & 1:
                v ^= Eb[h]
        return v
    planes = []
    for c, cl in cols.items():
        # kernel of q -> full_reduce(sum q_t cl[t])
        piv = {}
        ker = []
        for t in range(inst.w):
            v = full_reduce(cl[t])
            comb = 1 << t
            while v:
                h = v.bit_length() - 1
                if h in piv:
                    v ^= piv[h][0]
                    comb ^= piv[h][1]
                else:
                    piv[h] = (v, comb)
                    break
            else:
                ker.append(comb)
        d = len(ker)
        if d < 2:
            continue
        span = [0]
        for b in ker:
            span += [x ^ b for x in span]
        seen = set()
        for a, b in itertools.combinations(range(1, len(span)), 2):
            u, v = span[a], span[b]
            key = frozenset((u, v, u ^ v))
            if key not in seen:
                seen.add(key)
                planes.append((c, u, v))
    return planes


def plane_vectors(inst, pl, m):
    c, q1, q2 = pl
    out = []
    for q in (q1, q2):
        f = lift_low(q, inst)
        v = 0
        for o in range(m):
            if c >> o & 1:
                v |= f << (13 * o)
        out.append(v)
    return out


class Ech2:
    def __init__(self):
        self.p = {}

    def reduce(self, v):
        p = self.p
        while v:
            t = v.bit_length() - 1
            if t not in p:
                return v
            v ^= p[t]
        return 0

    def add_pair(self, a, b):
        a2 = self.reduce(a)
        if not a2:
            return False
        self.p[a2.bit_length() - 1] = a2
        b2 = self.reduce(b)
        if not b2:
            del self.p[a2.bit_length() - 1]
            return False
        self.p[b2.bit_length() - 1] = b2
        return True


def select(vecs, need, rng, tries=3000, base=None):
    """vecs: list of (v1, v2); greedy randomized + 1-out-2-in augmentation; returns indices (len need) or best found"""
    n = len(vecs)
    best = []

    def greedy(order, start):
        E = Ech2()
        sel = []
        for i in start:
            assert E.add_pair(*vecs[i])
            sel.append(i)
        for i in order:
            if len(sel) >= need:
                break
            if i in sel:
                continue
            if E.add_pair(*vecs[i]):
                sel.append(i)
        return sel

    order = list(range(n))
    for t in range(tries):
        rng.shuffle(order)
        if t % 3 == 0 or not best:
            sel = greedy(order, [])
        else:
            # perturb the best: drop a few random members and refill
            drop = rng.randrange(1, 4)
            keep = best[:]
            rng.shuffle(keep)
            keep = keep[drop:]
            E = Ech2()
            ok = []
            for i in keep:
                if E.add_pair(*vecs[i]):
                    ok.append(i)
            sel = greedy(order, ok)
        if len(sel) >= len(best):
            best = sel
        if len(best) >= need:
            break
    return best


def nonzero_on(inst, pl, z):
    c, q1, q2 = pl
    return parity(lift_low(q1, inst) & z) | parity(lift_low(q2, inst) & z)


# ---------------------------------------------------------------- exact matroid parity (randomised, GF(2^16))
_EX = None


def _tables():
    global _EX, _LG
    if _EX is None:
        ex = np.zeros(131070 + 2, np.int64)
        lg = np.zeros(65536, np.int64)
        x = 1
        for i in range(65535):
            ex[i] = x
            lg[x] = i
            x <<= 1
            if x & 0x10000:
                x ^= 0x1002D
        ex[65535:131070] = ex[0:65535]
        _EX, _LG = ex, lg
    return _EX, _LG


def _rank_gf16(M):
    ex, lg = _tables()
    M = M.copy()
    n = M.shape[0]
    r = 0
    for c in range(n):
        nz = np.nonzero(M[r:, c])[0]
        if len(nz) == 0:
            continue
        p = r + nz[0]
        if p != r:
            M[[r, p]] = M[[p, r]]
        inv = ex[65535 - lg[M[r, c]]]
        rows = r + 1 + np.nonzero(M[r + 1:, c])[0]
        if len(rows):
            f = M[rows, c]
            f = ex[lg[f] + lg[inv]]                    # factor per row
            prow = M[r]
            nzc = np.nonzero(prow)[0]
            prod = ex[lg[f][:, None] + lg[prow[nzc]][None, :]]
            M[np.ix_(rows, nzc)] ^= prod
        r += 1
        if r == n:
            break
    return r


def parity_rank(vecs, rng):
    """vecs: list of (v1, v2) ints.  maximum number of independent pairs (matroid parity)"""
    piv = {}
    order = []

    def coords(v):
        c = 0
        while v:
            t = v.bit_length() - 1
            if t not in piv:
                piv[t] = (v, 1 << len(order))
                order.append(t)
                return c ^ (1 << (len(order) - 1))
            v ^= piv[t][0]
            c ^= piv[t][1]
        return c
    cv = [(coords(a), coords(b)) for a, b in vecs]
    d = len(order)
    if d < 2:
        return 0
    A = np.zeros((len(cv), d), np.uint8)
    B = np.zeros((len(cv), d), np.uint8)
    for i, (a, b) in enumerate(cv):
        for t in range(d):
            A[i, t] = (a >> t) & 1
            B[i, t] = (b >> t) & 1
    Y = np.zeros((d, d), np.int64)
    for i in range(len(cv)):
        x = rng.randrange(1, 1 << 16)
        outer = (np.outer(A[i], B[i]) ^ np.outer(B[i], A[i])).astype(bool)
        Y[outer] ^= x
    return _rank_gf16(Y) // 2


def select_exact(vecs, need, rng, log=None):
    """indices of `need` independent pairs, or None.  deletion-based self-reduction on the exact parity rank"""
    idx = list(range(len(vecs)))
    if parity_rank(vecs, rng) < need:
        return None
    order = idx[:]
    rng.shuffle(order)
    keep = set(idx)
    for i in order:
        if len(keep) == need:
            break
        trial = [j for j in keep if j != i]
        if parity_rank([vecs[j] for j in trial], rng) >= need:
            keep.discard(i)
    sel = sorted(keep)
    E = Ech2()
    if not all(E.add_pair(*vecs[j]) for j in sel) or len(sel) != need:
        return None
    return sel
