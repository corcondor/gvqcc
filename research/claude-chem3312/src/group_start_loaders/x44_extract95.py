# extract a 95-chip cover from the C++ design search output and check it against Theta
import sys, random, pickle
import numpy as np
from planner import *
from gf2 import *


def run(k, outfile, d=20, seed=1, save=None):
    F = Frame(k); S = Space(F)
    toks = open(outfile).read().split()
    assert toks[0] == 'FOUND'
    nitems = int(toks[2]); pos = 3 + 4 * nitems
    nch = int(toks[pos]); pos += 1
    chips = []
    seen = set()
    for i in range(nch):
        s, u1, u2 = int(toks[pos]), int(toks[pos + 1]), int(toks[pos + 2]); pos += 3
        c = (s, (u1, u2))
        if c not in seen:
            seen.add(c); chips.append(c)
    need = (30 * S.NX - d) // 2
    rng = random.Random(seed); nrng = np.random.default_rng(seed)
    P = Parity(chips, S.NX, nrng)
    nu = P.nu(range(len(chips)))
    assert nu >= need, nu
    idx = extract(P, list(range(len(chips))), nu, rng)[:need]
    assert check_independent(chips, idx, S.NX)
    cov = [chips[i] for i in idx]
    e = Ech([v for s, U in cov for v in chip_vecs(s, U, S.NX)])
    bad = sum(1 for v in S.cols if e.reduce(v))
    print('loader', k, 'chips', len(cov), 'distinct candidates', len(chips), 'nu', nu, 'columns outside span', bad)
    assert bad == 0 and len(cov) == need
    if save:
        pickle.dump(cov, open(save, 'wb'))
    return cov


if __name__ == '__main__':
    run(int(sys.argv[1]), sys.argv[2], save=sys.argv[3])
