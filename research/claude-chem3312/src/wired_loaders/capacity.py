"""Flip capacity per bank / batch set / zero functional, with dense block-2 output combos.
Output space = wire space modulo cache-linear combos; stage-A functionals removed (flips must not touch A)."""
import sys, json
from tgt import *
from zc_scan import zeta_list

class Cap:
    def __init__(self, k):
        T = self.T = Target(k)
        self.k = k
        # coordinates of the non-A output space: functionals g on wires that vanish on cache-linear flips are the
        # outputs; flips are wire vectors; a flip's image in output space is (g_i(flip))_i for g in B+C
        self.G = T.B + T.C                      # basis of outputs modulo A and cache-linear
        self.nout = len(self.G)
        self.colidx = {x: j for j, x in enumerate(ORDX)}
        self.Acol = [[bits(T.Amix[i][:, j]) for j in range(14)] for i in range(39)]
        self.cache = {}

    def image(self, v):
        return sum((bin(v & g).count("1") & 1) << i for i, g in enumerate(self.G))

    def flips(self, batches):
        """list of (p, x, image-in-output-space, addr, batch, mask35) admissible flips with A untouched"""
        key = tuple(sorted(batches))
        if key in self.cache:
            return self.cache[key]
        res = []
        for b in batches:
            if b < 0 or b > 14:
                continue
            for a, basis in cell_free_basis(b).items():
                # subspace of this address's admissible flips invisible to A
                vecs = list(basis)
                rows = []
                for g in self.T.A:
                    rows.append(sum((bin(v & g).count("1") & 1) << i for i, v in enumerate(vecs)))
                for sol in nullspace(rows, len(vecs)):
                    v = 0
                    for i, vv in enumerate(vecs):
                        if sol >> i & 1:
                            v ^= vv
                    res.append((a >> 4, a & 15, self.image(v), a, b, v))
        self.cache[key] = res
        return res

    def rankA(self, z):
        zc = [j for j in range(14) if z >> j & 1]
        b = {}
        r = 0
        for i in range(39):
            v = 0
            for j in zc:
                v ^= self.Acol[i][j]
            r += ins(b, v)
        return r

    def Fp(self, batches, z):
        """per row p: basis (dict) of the output-space images of flips at row p in zeta columns"""
        F = [dict() for _ in range(77)]
        for p, x, im, a, b, v in self.flips(batches):
            if x in self.colidx and z >> self.colidx[x] & 1 and im:
                ins(F[p], im)
        return F

    def capacity(self, batches, z, m=8):
        F = self.Fp(batches, z)
        return sum(min(m, len(F[p])) for p in range(1, 76)) + min(m, len(F[0]))

def main():
    zl = zeta_list()
    for k in [int(a) for a in sys.argv[1:]]:
        C = Cap(k)
        rA = {z: C.rankA(z) for z in zl}
        from collections import Counter
        print(f"bank {k}: outputs after A = {C.nout}; A rank on zeta histogram:", dict(sorted(Counter(rA.values()).items())))
        for batches in ([k], [k - 1], [k - 1, k]):
            if min(batches) < 0:
                continue
            best = None
            for z in zl:
                cap = C.capacity(batches, z)
                need = 8 * (75 - rA[z])
                marg = cap - need
                if best is None or marg > best[0]:
                    best = (marg, z, cap, need, rA[z])
            marg, z, cap, need, ra = best
            cols = [ORDX[j] for j in range(14) if z >> j & 1]
            print(f"   batches {batches}: flips {len(C.flips(batches))}; best margin {marg} (capacity {cap} - need {need}, rankA {ra}) zeta columns {cols}", flush=True)

if __name__ == "__main__":
    main()
