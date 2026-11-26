"""Common planner library: bit linear algebra and the grid view of our decoded loaders."""
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
NV = 1219
A = np.arange(NV)
BANK = A >> 4
LOW = A & 15
WIRED = [2, 3, 4, 6, 8, 9, 10, 12, 13, 14]
# word wire n = 7*j + b
def wn(n):
    return f"s{n//7}b{n%7}"

def ins(basis, v):
    """insert int v into dict-basis {pivot: vec}; True if independent"""
    while v:
        t = v.bit_length() - 1
        if t in basis:
            v ^= basis[t]
        else:
            basis[t] = v
            return True
    return False

def rank(vs):
    b = {}
    return sum(ins(b, int(v)) for v in vs)

def reduce(basis, v):
    while v:
        t = v.bit_length() - 1
        if t not in basis:
            return v
        v ^= basis[t]
    return 0

def nullspace(rows, n):
    """all x in GF(2)^n with parity(x & r) == 0 for every row r"""
    piv = {}
    for g in rows:
        g = int(g)
        for p, row in piv.items():
            if g >> p & 1:
                g ^= row
        if g:
            p = g.bit_length() - 1
            for q in list(piv):
                if piv[q] >> p & 1:
                    piv[q] ^= g
            piv[p] = g
    free = [i for i in range(n) if i not in piv]
    out = []
    for f in free:
        x = 1 << f
        for p, row in piv.items():
            if row >> f & 1:
                x |= 1 << p
        out.append(x)
    return out

def bits(vec):
    return int.from_bytes(np.packbits(np.asarray(vec, np.uint8), bitorder="little").tobytes(), "little")

def grid(f):
    """1219-bit function (array) -> 77x16 grid (cells outside the care set = 0)"""
    G = np.zeros((77, 16), np.uint8)
    G[BANK, LOW] = f
    return G

class Loader:
    def __init__(self, k):
        z = np.load(DATA / f"dec_k{k}.npz")
        j = json.load(open(DATA / f"dec_k{k}.json"))
        self.k = k
        self.S = z["S"]; self.SL = z["SL"]; self.SM = z["SM"]
        self.U = z["U"]; self.V = z["V"]; self.FAN = z["FAN"]
        self.BASE = z["BASE"]; self.TGT = z["TGT"]
        self.no = j["no"]; self.ns = j["ns"]
        self.forms = j
        # word deltas new ^ old for the 35 word wires (forward direction)
        self.DELTA = self.TGT[11:46] ^ self.BASE[11:46] if k else self.TGT[11:46].copy()
        self.Ug = np.array([grid(u) for u in self.U])
        self.Vg = np.array([grid(v) for v in self.V])
        self.Dg = np.array([grid(d) for d in self.DELTA])

def mixed_part(G, ordx, x0, nbank=76):
    """G[p, x] restricted to p<nbank and ordinary x: second difference w.r.t. (p=0, x=x0)."""
    H = G[:nbank][:, ordx]
    return H ^ G[:nbank][:, [x0]] ^ G[[0]][:, ordx] ^ G[0, x0]
