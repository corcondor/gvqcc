"""Turn a design (products with alpha/beta/q/fan coefficients) into KMB-level forms on top of OUR loader's cache,
check the ordinary rows exactly, and prepare the special-row systems (our dc/oracle/pass4 sp4lib / p4build).
Own code; sp4lib/p4build/k8lib are this project's earlier tools (read-only use)."""
import json, sys, random
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = Path(r"<ROOT>")
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "w_push11" / "dc" / "oracle" / "pass4"))
import sp4lib
import p4build
from sp4lib import (K, Bank, Ech, CElim, func_of, FULL, P0, N_BASE, Spec, Event, symbol_functions, ORD_MASK,
                    SpecialSystem4, ClassSystems4, span_basis, perp_basis, E_ROW)
from design import Prod, ORDX, parity

SPECIAL = (7, 14)
NB = 77


def fbits(f):
    return sp4lib.fbits(f)


def solve_rows(rows):
    """rows: (mask, rhs). return solution int or None (free vars 0)"""
    piv = {}
    for m, r in rows:
        while m:
            t = m.bit_length() - 1
            if t in piv:
                m ^= piv[t][0]
                r ^= piv[t][1]
            else:
                piv[t] = (m, r)
                break
        else:
            if r:
                return None
    x = 0
    for t in sorted(piv):
        m, r = piv[t]
        v = r ^ (bin(m & x).count("1") & 1)
        if v:
            x |= 1 << t
    return x


class Forms:
    """form synthesis over the cache of our loader k (scratch forms from planner/data/dec_k{k}.json)"""

    def __init__(self, k, words):
        self.k = k
        self.bk = Bank(k, words)
        j = json.load(open(HERE / "data" / f"dec_k{k}.json"))
        self.scratch = [(int(a, 16), int(b, 16)) for a, b in j["scratch"]]
        ns = len(self.scratch)
        canon = Spec(k, [Event("S", L, M) for (L, M) in self.scratch], [0] * N_BASE)
        self.fn, viol = symbol_functions(canon, self.bk)
        assert not viol, viol[:2]
        # pure-p generators
        self.pgens = [(1, FULL)] + [(1 << (1 + i), self.bk.base_fn[i]) for i in range(4, 11)] + \
                     [(1 << (P0 + i), self.fn[P0 + i]) for i in range(68)]
        self.pvals = []
        for form, f in self.pgens:
            b = fbits(f)
            v = np.array([b[16 * p] for p in range(NB)], np.uint8)
            addr = np.arange(1219)
            assert (v[addr >> 4] == b).all(), "not pure p"
            self.pvals.append(v)
        xs = [(1, FULL)] + [(1 << (1 + i), self.bk.base_fn[i]) for i in range(4)]
        for jj in range(5):
            r5 = 11 + 7 * jj + 5
            xs.append(((1 << (1 + r5)) ^ (1 << (2 + r5)), self.bk.base_fn[r5] ^ self.bk.base_fn[r5 + 1]))
        xs += [(1 << (P0 + i), self.fn[P0 + i]) for i in range(68, 74)]
        self.xgens = xs
        self.xvals = []
        for form, f in xs:
            b = fbits(f)
            v = np.array([b[x] for x in range(16)], np.uint8)
            addr = np.arange(1219)
            assert (v[addr & 15] == b).all(), "not pure x"
            self.xvals.append(v)

    def pform(self, vals76):
        rows = []
        for p in range(76):
            m = 0
            for g, v in enumerate(self.pvals):
                if v[p]:
                    m |= 1 << g
            rows.append((m, int(vals76[p])))
        z = solve_rows(rows)
        assert z is not None, "p pattern not realisable"
        form = 0
        for g in range(len(self.pgens)):
            if z >> g & 1:
                form ^= self.pgens[g][0]
        return form

    def xform(self, vals_by_x):
        """vals_by_x: dict x -> bit on the columns that matter (others free)"""
        rows = []
        for x, b in vals_by_x.items():
            m = 0
            for g, v in enumerate(self.xvals):
                if v[x]:
                    m |= 1 << g
            rows.append((m, int(b)))
        z = solve_rows(rows)
        assert z is not None
        form = 0
        for g in range(len(self.xgens)):
            if z >> g & 1:
                form ^= self.xgens[g][0]
        return form

    def prod_forms(self, pr: Prod):
        al = [0] + [(pr.alpha >> p) & 1 for p in range(75)]
        be = [0] + [(pr.beta >> p) & 1 for p in range(75)]
        x0 = ORDX[0]
        q1 = {x0: 0}
        q2 = {x0: 0}
        for t, x in enumerate(ORDX[1:]):
            q1[x] = (pr.q1 >> t) & 1
            q2[x] = (pr.q2 >> t) & 1
        L = self.pform(al) ^ self.xform(q1)
        M = self.pform(be) ^ self.xform(q2)
        return L, M


def fan_vectors(prods, blocks_outputs, Z):
    basis = []
    for outs in blocks_outputs:
        basis += outs
    basis += Z
    assert len(basis) == 35
    out = []
    # solve <g_t, v> = rhs_t
    for pr in prods:
        rhs = []
        for bi, outs in enumerate(blocks_outputs):
            c = pr.coef.get(str(bi), pr.coef.get(bi, 0))
            rhs += [(c >> o) & 1 for o in range(len(outs))]
        rhs += [0] * len(Z)
        rows = [(g, r) for g, r in zip(basis, rhs)]
        v = solve_rows(rows)
        assert v is not None
        for g, r in rows:
            assert (bin(g & v).count("1") & 1) == r
        assert not any(v >> (7 * j) & 1 for j in range(5)), "LSB in fan-out"
        out.append(v)
    return out


class NewPub:
    """duck-typed replacement of sp4lib.Pub4 for a freshly designed loader"""

    def __init__(self, k, words, scratch, outputs, n_closers):
        self.k = k
        self.bk = Bank(k, words)
        self.scratch = list(scratch)
        self.outputs = list(outputs)
        self.ns = len(scratch)
        self.no = len(outputs)
        canon = Spec(k, [Event("S", L, M) for (L, M) in self.scratch] +
                     [Event("O", L, M) for (L, M, v) in self.outputs], [0] * N_BASE)
        self.fn, viol = symbol_functions(canon, self.bk)
        assert not viol, viol[:2]
        self.free = [7 * j + b for j in range(5) for b in range(1, 6)]
        self.windex = {n: i for i, n in enumerate(self.free)}
        self.delta = [self.bk.target[11 + n] ^ self.bk.base_fn[11 + n] for n in self.free]
        self.fan = [[(v >> n) & 1 for n in self.free] for (_, _, v) in self.outputs]
        self.fan_int = [sum(b << i for i, b in enumerate(f)) for f in self.fan]
        self.n_main = self.no - n_closers
        self.gens = [FULL] + [self.bk.base_fn[i] for i in range(11)] + \
                    [self.bk.base_fn[11 + 7 * j + 5] ^ self.bk.base_fn[11 + 7 * j + 6] for j in range(5)] + \
                    [self.fn[P0 + i] for i in range(self.ns)]

    def fform(self, form):
        return func_of(form, self.fn)


def load_design(tag):
    d = json.load(open(HERE / "designs" / tag / "design.json"))
    prods = [Prod.from_json(p) for p in d["prods"]]
    words = np.load(HERE / "designs" / tag / "words.npy")
    return d, prods, words


def build_pub(tag, n_closers=4, check=True):
    d, prods, words = load_design(tag)
    k = d["k"]
    F = Forms(k, words)
    fans = fan_vectors(prods, d["blocks_outputs"], d["Z"])
    outputs = []
    for pr, v in zip(prods, fans):
        L, M = F.prod_forms(pr)
        outputs.append((L, M, v))
    # placeholder closers (rebuilt later)
    outputs += [(0, 0, 0)] * n_closers
    pub = NewPub(k, words, F.scratch, outputs, n_closers)
    if check:
        check_ordinary(pub)
    return pub, F, d, prods, words


def check_ordinary(pub):
    """every word wire: delta + sum fan*u*v must lie in span(cache + hyperplane complement) on ordinary rows"""
    sp = SpecialSystem4(pub)       # raises if a residual is not in C + special rows
    # also the wires without products (bit0, bit6): delta must be cache-linear on ordinary rows
    for n in range(35):
        if n in pub.free:
            continue
        j, b = divmod(n, 7)
        r = pub.bk.target[11 + n] ^ pub.bk.base_fn[11 + n]
        if b == 6:
            r ^= pub.bk.target[11 + n - 1] ^ pub.bk.base_fn[11 + n - 1]
        c = sp.cel.coords(r & ORD_MASK)
        assert c is not None, f"wire {n} (bit {b}) not cache-linear on ordinary rows"
    print("   ordinary rows: all 35 word wires reproduced exactly (function level)")
    return sp


if __name__ == "__main__":
    tag = sys.argv[1]
    pub, F, d, prods, words = build_pub(tag)
    sp = SpecialSystem4(pub)
    print("main products", pub.n_main, "scratch", pub.ns, "fan rank", len(span_basis(pub.fan_int)))
