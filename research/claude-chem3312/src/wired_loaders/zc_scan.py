"""Zero-column feasibility per wire: A-stage steering (39 fan bits) + dead flips, for every zero functional zeta.
Row p-1 (p=1..75): zeta(mixed T'(p,.))=0 ; 2 rows: Phi of the flips = 0."""
import json, sys, itertools
from tgt import *

def flips_by_wire(T, batches):
    """{wire n: list of (a, batch)} admissible flips that leave all A combos unchanged"""
    out = {n: [] for n in range(35)}
    for b in batches:
        if b < 0 or b > 14:
            continue
        for a, basis in cell_free_basis(b).items():
            for v in basis:
                if any(bin(v & g).count("1") & 1 for g in T.A):
                    continue            # would disturb stage A (single-basis-vector level)
                n = v.bit_length() - 1
                if bin(v).count("1") == 2:   # b5+b6 flip: count it on wire b5
                    n = n - 1
                out[n].append((a, b, v))
    return out

def zeta_list():
    # even-size subsets of the 14 ordinary columns (as 14-bit masks), modulo constants
    res = []
    for m in range(1, 1 << 14):
        if bin(m).count("1") % 2 == 0:
            res.append(m)
    return res

class ZC:
    def __init__(self, k, batches):
        self.T = T = Target(k)
        self.k = k
        # A-product column slices: for each product, each ordinary column -> 75-bit int
        self.Acol = [[bits(T.Amix[i][:, j]) for j in range(14)] for i in range(39)]
        self.Dcol = [[bits(T.Dmix[w][:, j]) for j in range(14)] for w in range(35)]
        self.flips = flips_by_wire(T, batches)
        # per flip: (effect on column-slices dict, phi bits)
        self.fx = {}
        colidx = {x: j for j, x in enumerate(ORDX)}
        for n, lst in self.flips.items():
            res = []
            for a, b, v in lst:
                p, x = a >> 4, a & 15
                phi = 0
                for f, cells in enumerate(T.phi):
                    if (p, x) in cells:
                        phi |= 1 << (75 + f)
                if x in colidx:
                    j = colidx[x]
                    if 1 <= p <= 75:
                        rows = 1 << (p - 1)
                    elif p == 0:
                        rows = (1 << 75) - 1
                    else:
                        rows = 0
                else:
                    j = None; rows = 0
                res.append((j, rows, phi, a, b, v))
            self.fx[n] = res

    def solvable(self, n, zmask, want_rank=False):
        zc = [j for j in range(14) if zmask >> j & 1]
        basis = {}
        r = 0
        for i in range(39):
            v = 0
            for j in zc:
                v ^= self.Acol[i][j]
            if v:
                r += ins(basis, v)
        for j, rows, phi, a, b, vv in self.fx[n]:
            v = phi
            if j is not None and zmask >> j & 1:
                v |= rows
            if v:
                r += ins(basis, v)
        rhs = 0
        for j in zc:
            rhs ^= self.Dcol[n][j]
        res = reduce(basis, rhs)
        return (res == 0, r) if want_rank else res == 0

NATIVE_NONA = None

def main():
    results = {}
    zl = zeta_list()
    for k in [int(a) for a in sys.argv[1:]]:
        T = Target(k)
        if any(bin(g).count("1") != 1 for g in T.A):
            print(f"bank {k}: stage A is not native; skipped here"); continue
        Aw = {g.bit_length() - 1 for g in T.A}
        wires = [7 * j + b for j in range(5) for b in range(1, 6) if 7 * j + b not in Aw]
        if k in (8, 13):
            wires = [n for n in wires if wn(n) not in ("s3b1", "s4b1")]
        for batches in ([k], [k - 1], [k, k - 1]):
            Z = ZC(k, batches)
            best = {}
            counts = {n: 0 for n in wires}
            good_z = {}
            for z in zl:
                ok = [n for n in wires if Z.solvable(n, z)]
                good_z[z] = ok
                for n in ok:
                    counts[n] += 1
            top = sorted(good_z.items(), key=lambda t: -len(t[1]))[:3]
            print(f"bank {k} batches {batches}: free flips per wire:", {wn(n): len(Z.fx[n]) for n in wires})
            print("    #zeta solvable per wire:", {wn(n): counts[n] for n in wires})
            print("    best zeta (wires jointly):", [(bin(z), len(ok), [wn(n) for n in ok]) for z, ok in top], flush=True)

if __name__ == "__main__":
    main()
