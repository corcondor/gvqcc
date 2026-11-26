# extract 95-covers rich in a low hyperplane W6 (or W5) from the design-search candidates, preferring W products
import sys, random, pickle
import numpy as np
from planner import *
from gf2 import Ech
from x49_w6cover import load_chips, in_w
from build3 import w_order

NEED = 95


def extract_from(P, fixed, removable, target, rng):
    """keep nu == target, remove chips only from `removable` (chunked)."""
    cur = list(removable)
    M = P.matrix(fixed + cur)
    assert gf.rank(M) // 2 == target
    chunk = max(1, len(cur) // 4)
    while len(fixed) + len(cur) > target and cur:
        rng.shuffle(cur); progress = False; pos = 0
        while pos < len(cur) and len(fixed) + len(cur) > target:
            sub = cur[pos:pos + chunk]
            if len(fixed) + len(cur) - len(sub) < target:
                pos += chunk; continue
            Mt = M ^ P.matrix(sub)
            if gf.rank(Mt) // 2 == target:
                M = Mt; cur = cur[:pos] + cur[pos + chunk:]; progress = True
            else:
                pos += chunk
        if not progress:
            if chunk == 1:
                break
            chunk = max(1, chunk // 2)
    return cur


def wcover(k, fs, want, e, seed=1, verbose=True):
    F = Frame(k); S = Space(F)
    chips = load_chips(f'd20_k{k}.out')
    nrng = np.random.default_rng(seed)
    rng = random.Random(seed)
    P = Parity(chips, S.NX, nrng)
    W = [i for i, (s, U) in enumerate(chips) if all(in_w(U, f) for f in fs)]
    O = [i for i in range(len(chips)) if i not in set(W)]
    nuW = P.nu(W)
    k_w = min(want, nuW)
    if verbose:
        print(f'  W pool {len(W)} chips, nu {nuW}', flush=True)
    idxW = extract_from(P, [], W, nuW, rng)
    idxW = idxW[:]
    rng.shuffle(idxW)
    idxW = idxW[:k_w]
    # contract: grow until the union with all other candidates reaches full parity
    others = [i for i in range(len(chips)) if i not in set(idxW)]
    while P.nu(idxW + others) < NEED:
        if len(idxW) < 10:
            return None
        idxW = idxW[:len(idxW) - 3]
        others = [i for i in range(len(chips)) if i not in set(idxW)]
    rest = extract_from(P, idxW, others, NEED, rng)
    cur = idxW + rest
    if len(cur) > NEED:
        extra = extract_from(P, rest, idxW, NEED, rng)
        cur = rest + extra
    if len(cur) != NEED or not check_independent(chips, cur, S.NX):
        if verbose:
            print(f'  extraction ended with {len(cur)} chips', flush=True)
        return None
    cov = [chips[i] for i in cur]
    ech = Ech([v for s, U in cov for v in chip_vecs(s, U, S.NX)])
    assert all(ech.reduce(v) == 0 for v in S.cols)
    nw = sum(1 for s, U in cov if all(in_w(U, f) for f in fs))
    if verbose:
        print(f'  cover with {nw} W chips', flush=True)
    return cov, nw


if __name__ == '__main__':
    k = int(sys.argv[1]); fs = [int(a) for a in sys.argv[2].split(',')]; want = int(sys.argv[3]); e = int(sys.argv[4])
    for seed in range(1, 6):
        r = wcover(k, fs, want, e, seed=seed)
        if r is None:
            continue
        cov, nw = r
        F = Frame(k)
        wi = [i for i, (s, U) in enumerate(cov) if all(in_w(U, f) for f in fs)]
        try:
            w_order(F, cov, e, wi, min(nw, want), random.Random(seed), tries=200)
        except (RuntimeError, AssertionError) as ex:
            print('  seed', seed, 'order failed', ex, flush=True)
            continue
        name = f'cover95w_k{k}_f{"_".join(map(str, fs))}.pkl'
        pickle.dump(cov, open(name, 'wb'))
        print('saved', name, 'W chips', nw, 'seed', seed, flush=True)
        break
