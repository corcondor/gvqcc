# W6-rich 95-covers: from the design-search candidates, how many products can lie in a low hyperplane W6 =
# {U : f(coefficients of x0x1, x0x2, x1x2, x0x1x2) = 0}?  Report parity numbers per f.
import sys, random, pickle
import numpy as np
from planner import *

NL = [3, 5, 6, 7]


def moebius(u):
    val = [0] + [(u >> (x - 1)) & 1 for x in range(1, 8)]
    c = val[:]
    for i in range(3):
        for m in range(8):
            if m >> i & 1:
                c[m] ^= c[m ^ (1 << i)]
    return sum(c[m] << m for m in range(1, 8))


def nlbits(u):
    c = moebius(u)
    return sum(((c >> m) & 1) << t for t, m in enumerate(NL))


def in_w(U, f):
    return all(bin(nlbits(u) & f).count('1') % 2 == 0 for u in U)


def load_chips(path):
    toks = open(path).read().split()
    assert toks[0] == 'FOUND'
    nitems = int(toks[2]); pos = 3 + 4 * nitems
    nch = int(toks[pos]); pos += 1
    chips = []; seen = set()
    for i in range(nch):
        c = (int(toks[pos]), (int(toks[pos + 1]), int(toks[pos + 2]))); pos += 3
        if c not in seen:
            seen.add(c); chips.append(c)
    return chips


if __name__ == '__main__':
    for k in [int(a) for a in sys.argv[1:]]:
        F = Frame(k); S = Space(F)
        chips = load_chips(f'd20_k{k}.out')
        nrng = np.random.default_rng(1)
        P = Parity(chips, S.NX, nrng)
        res = []
        for f in range(1, 16):
            idx = [i for i, (s, U) in enumerate(chips) if in_w(U, f)]
            if len(idx) < 57:
                res.append((0, len(idx), f)); continue
            res.append((P.nu(idx), len(idx), f))
        res.sort(reverse=True)
        print('loader', k, 'candidates', len(chips), 'W6 best (nu, chips, f):', res[:4], flush=True)
        res5 = []
        seen = set()
        for f1 in range(1, 16):
            for f2 in range(f1 + 1, 16):
                key = frozenset([f1, f2, f1 ^ f2])
                if key in seen:
                    continue
                seen.add(key)
                idx = [i for i, (s, U) in enumerate(chips) if in_w(U, f1) and in_w(U, f2)]
                res5.append((len(idx), f1, f2))
        res5.sort(reverse=True)
        best5 = []
        for n, f1, f2 in res5[:6]:
            idx = [i for i, (s, U) in enumerate(chips) if in_w(U, f1) and in_w(U, f2)]
            best5.append((P.nu(idx) if n >= 20 else 0, n, f1, f2))
        best5.sort(reverse=True)
        print('loader', k, 'W5 best (nu, chips, f1, f2):', best5[:4], flush=True)
