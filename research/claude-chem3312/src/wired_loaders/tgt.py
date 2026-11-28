"""Target model of one loader: ordinary-column mixed slices, A-stage steering, dead-cell flips."""
import json
from pathlib import Path
from lib import *

ROOT = Path(r"<ROOT>")
DEAD = np.load(ROOT / "w_push11" / "dead" / "dead_mask_1e-13.npy")      # [1219,75]
SPEC = json.load(open(ROOT / "w_push11" / "dc" / "prep" / "data" / "dontcare_spec.json"))["spec"]
ANN = {k: json.load(open(ROOT / "w_push11" / "dc" / "oracle" / "data" / f"annihilator_k{k}.json"))["annihilator_supports"] for k in WIRED}
BLK = json.load(open(DATA / "blocks.json"))
import os
SPECIAL = tuple(int(v) for v in os.environ.get("GVQ_SPECIAL", "7,14").split(","))
assert len(SPECIAL) == 2 and min(SPECIAL) > 2, "special columns must avoid the partial block's columns 0..2"
ORDX = [x for x in range(16) if x not in SPECIAL]

def cell_free_basis(b):
    """batch b: {address: [35-bit flip masks admissible for batch b (code preserving)]}"""
    out = {}
    for e in SPEC[str(b)]:
        out[e["a"]] = [int(v) for v in e["basis35"]]
    return out

class Target:
    def __init__(self, k):
        self.k = k
        L = self.L = Loader(k)
        info = BLK[str(k)]
        self.A = info["A"]; self.B = info["B"]; self.C = info["C"]; self.Z = info["Z"]
        self.nmain = info["nmain"]
        # mixed part (p=1..75 relative to p=0, ordinary x relative to x0) of every product of stage A
        self.x0 = ORDX[0]
        self.cols = ORDX
        P = L.Ug[:39] & L.Vg[:39]
        self.Amix = np.array([self.mix(P[i]) for i in range(39)])          # [39, 75, 14]
        self.Dmix = np.array([self.mix(L.Dg[w]) for w in range(35)])        # [35, 75, 14]
        # sanity: A wires are solved by A products alone
        ann_supports = ANN[k]
        self.phi = []   # list of two sets of (p, x)
        for s in ann_supports:
            self.phi.append([(a >> 4, a & 15) for a in s])

    def mix(self, G):
        H = G[1:76][:, ORDX]
        return (H ^ G[1:76][:, [self.x0]] ^ G[[0]][:, ORDX] ^ G[0, self.x0]).astype(np.uint8)

    def combo_delta(self, g):
        """mixed part [75,14] of wire combination g"""
        out = np.zeros((75, 14), np.uint8)
        for w in range(35):
            if g >> w & 1:
                out ^= self.Dmix[w]
        return out

    def check_A(self):
        """verify that each A combo's mixed part lies in the span of A products' mixed parts"""
        basis = {}
        for i in range(39):
            ins(basis, bits(self.Amix[i].ravel()))
        ok = []
        for g in self.A:
            ok.append(reduce(basis, bits(self.combo_delta(g).ravel())) == 0)
        return ok
