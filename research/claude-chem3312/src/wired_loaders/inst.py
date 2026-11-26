"""Block instance writer (nb26an / w_push14 engine format) from OUR table.
instance: 'q w nfan k' then 'c col_0 .. col_{w-1}' (column = image of c(x)e_t in Q = out x low / R).
Low coordinates: ordinary columns minus x0 (13 coords q(x_j)-q(x0)); with a zero functional the pivot coord is dropped."""
import json
from pathlib import Path
from tgt import *

INSTDIR = Path(__file__).resolve().parent / "inst"
INSTDIR.mkdir(exist_ok=True)
LOWCOLS = ORDX[1:]          # 13 coordinates

def zeta_vec(zmask14):
    """zmask over the 14 ordinary columns (bit j = ORDX[j]) -> functional on the 13 coords"""
    return zmask14 >> 1       # coordinate t = ORDX[t+1]; x0 term drops (even set)

def block_slices_from_mixed(mats):
    """mats: list (per output) of [75,14] mixed parts. returns 75 slices, each int of m*13 bits"""
    out = []
    for p in range(75):
        v = 0
        for o, M in enumerate(mats):
            row = 0
            for t in range(13):
                if M[p, t + 1]:
                    row |= 1 << t
            v |= row << (13 * o)
        out.append(v)
    return out

class Instance:
    def __init__(self, slices13, m, zeta=None):
        """slices13: ints over m*13 bits.  zeta: int functional on 13 coords that every slice satisfies (zero column)"""
        self.m = m
        self.zeta = zeta
        if zeta:
            piv = zeta.bit_length() - 1
            self.piv = piv
            self.keep = [t for t in range(13) if t != piv]
            for s in slices13:
                for o in range(m):
                    assert bin(((s >> (13 * o)) & 0x1FFF) & zeta).count("1") % 2 == 0, "zero functional violated"
        else:
            self.piv = None
            self.keep = list(range(13))
        self.w = len(self.keep)
        def squeeze(s):
            v = 0
            for o in range(m):
                row = (s >> (13 * o)) & 0x1FFF
                for i, t in enumerate(self.keep):
                    if row >> t & 1:
                        v |= 1 << (self.w * o + i)
            return v
        self.slices = [squeeze(s) for s in slices13]
        self.rankR = rank(self.slices)
        self.ann = nullspace(self.slices, m * self.w)
        self.q = len(self.ann)

    def proj(self, v):
        return sum((bin(a & v).count("1") & 1) << i for i, a in enumerate(self.ann))

    def columns(self):
        cols = {}
        for c in range(1, 1 << self.m):
            cols[c] = [self.proj(sum(1 << (self.w * o + t) for o in range(self.m) if c >> o & 1)) for t in range(self.w)]
        return cols

    def write(self, name, k_ext, meta=None, outdir=INSTDIR):
        """k_ext = extension dimension; products needed n = ceil((rankR + k)/2)"""
        n = (self.rankR + k_ext + 1) // 2
        cols = self.columns()
        p = outdir / f"{name}.txt"
        with open(p, "w") as f:
            f.write(f"{self.q} {self.w} {len(cols)} {k_ext}\n")
            for c, cl in cols.items():
                f.write(str(c) + " " + " ".join(map(str, cl)) + "\n")
        with open(outdir / f"{name}.ten", "w") as f:
            f.write(f"{self.q} {self.m} {self.w} {k_ext} {n}\n")
            f.write(" ".join(map(str, self.ann)) + "\n")
        md = dict(name=name, q=self.q, w=self.w, m=self.m, k=k_ext, n=n, rankR=self.rankR,
                  zeta13=self.zeta, low_coords=[LOWCOLS[t] for t in self.keep], pivot_coord=None if self.piv is None else LOWCOLS[self.piv])
        if meta:
            md.update(meta)
        json.dump(md, open(outdir / f"{name}.json", "w"))
        return n, md

def combo_mats(T, combos, extra=None):
    """target [75,14] per output combo; extra: {output index: [75,14] array to XOR (steering / flips)}"""
    mats = []
    for o, g in enumerate(combos):
        M = T.combo_delta(g).copy()
        if extra and o in extra:
            M ^= extra[o]
        mats.append(M)
    return mats

def wires(*names):
    out = []
    for s in names:
        j = int(s[1]); b = int(s[3])
        out.append(1 << (7 * j + b))
    return out

def write_gs2(I, path):
    """gs2 format: 'g xdim q' then values vals[w][x] = image of e_w (x) e_x"""
    with open(path, "w") as f:
        f.write(f"{I.m} {I.w} {I.q}\n")
        for o in range(I.m):
            f.write(" ".join(str(I.proj(1 << (I.w * o + t))) for t in range(I.w)) + " ")
        f.write("\n")
