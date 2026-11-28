"""Low-rank elements in the annihilator of each block's slice span R (our maoxin-based loaders).
Block target = the block's output combos minus the contributions of earlier-stage products (exact fan coords)."""
import sys, json
from collections import Counter
from tgt import *

def low_functional_coords():
    return None

def block_mixed(k, T, which):
    """returns list of m matrices [75,14] = target of block `which` restricted to its own products."""
    L = T.L
    P = L.Ug & L.Vg
    seg = {"A": range(0, 39), "B": range(39, 78), "C": range(78, T.nmain)}[which]
    combos = {"A": T.A, "B": T.B, "C": T.C}[which]
    out = []
    for g in combos:
        M = np.zeros((75, 14), np.uint8)
        for i in seg:
            if bin(int(g) & bits(L.FAN[i])).count("1") & 1:
                M ^= T.mix(P[i])
        out.append(M)
    return out

def to13(M):
    """[75,14] mixed part with x0 column zero -> [75,13] int rows"""
    cols = [j for j in range(14) if ORDX[j] != T0x0]
    return M[:, cols]

T0x0 = ORDX[0]

def analyze_block(mats, name, verbose=True, w=13):
    m = len(mats)
    cols = list(range(1, 14))           # column of x0 (index 0) is identically zero
    slices = []
    for p in range(75):
        v = 0
        for o, M in enumerate(mats):
            for jj, j in enumerate(cols):
                if M[p, j]:
                    v |= 1 << (13 * o + jj)
        slices.append(v)
    r = rank(slices)
    # zero columns: low functionals x (13-bit) with <x, row> = 0 for every slice and combo
    lows = []
    for p in range(75):
        for o in range(m):
            lows.append((slices[p] >> (13 * o)) & 0x1FFF)
    zc = nullspace(lows, 13)
    ann = nullspace(slices, 13 * m)
    d = len(ann)
    cnt = Counter(); r1x = Counter(); r1s = Counter()
    if d <= 22:
        x = 0
        for it in range(1, 1 << d):
            x ^= ann[(it & -it).bit_length() - 1]
            rows = [(x >> (13 * o)) & 0x1FFF for o in range(m)]
            rk = rank(rows)
            cnt[min(rk, 4)] += 1
            if rk == 1:
                low = next(t for t in rows if t)
                r1x[low] += 1
    if verbose:
        print(f"   {name}: m={m} rankR={r} zero-col dim={len(zc)} annihilator dim={d} rank1={cnt.get(1,0)} (per x {sorted(r1x.values(), reverse=True)[:6]}) rank2={cnt.get(2,0)} rank3={cnt.get(3,0)}")
    return dict(m=m, rankR=r, zc=len(zc), annd=d, r1=cnt.get(1, 0), r2=cnt.get(2, 0), r3=cnt.get(3, 0))

if __name__ == "__main__":
    for k in [int(a) for a in sys.argv[1:]] or WIRED:
        T = Target(k)
        print(f"bank {k}:")
        for which in "ABC":
            mats = block_mixed(k, T, which)
            analyze_block(mats, which)
