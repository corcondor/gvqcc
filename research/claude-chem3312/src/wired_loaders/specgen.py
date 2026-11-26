"""Generalised special rows for a designed loader (own code, a parameterised rewrite of our dc/oracle/pass4
sp4lib.py + p4build.py): any special columns (GVQ_SPECIAL env), any closer count s, erasures from batch k and/or k-1
(preserving the codes of every wired bank the cell enters).

usage:
  python specgen.py export TAG [--s 4] [--gseed 1] [--erase k,k-1] [--name X]
  python specgen.py build  TAG NAME --name X [--base FAMILY]       (needs designs/TAG/X_row0.json, X_row1.json)
"""
import argparse, hashlib, itertools, json, random, shutil, sys, time
from collections import Counter
from pathlib import Path
import numpy as np

from assemble import *            # Forms, fan_vectors, load_design, NewPub, solve_rows, K (via sp4lib)
from tgt import SPECIAL, ORDX, BLK
from sp4lib import K, CElim, Ech, func_of, FULL, P0, N_BASE, span_basis, perp_basis
import sp4lib, p4build

HERE = Path(__file__).resolve().parent
ROOT = Path(r"<ROOT>")
SPEC = json.load(open(ROOT / "w_push11" / "dc" / "prep" / "data" / "dontcare_spec.json"))["spec"]
ADDR = np.arange(1219)
XI = ADDR & 15
PI = ADDR >> 4
FREE = [7 * j + b for j in range(5) for b in range(1, 6)]
WIDX = {n: i for i, n in enumerate(FREE)}
C1, C2 = SPECIAL
ROWS = (C1, C2)


def fint(bits):
    return int.from_bytes(np.packbits(np.asarray(bits, np.uint8), bitorder="little").tobytes(), "little")


def fbits(f):
    return np.unpackbits(np.frombuffer(f.to_bytes(153, "little"), np.uint8), bitorder="little")[:1219]


E_ROW = [fint(XI == r) for r in range(16)]
BLKF = [fint(PI == p) for p in range(77)]
ORD = FULL & ~(E_ROW[C1] | E_ROW[C2])
SP_IDX = np.array([c + 16 * p for c in ROWS for p in range(76)])


def R152(f):
    return fint(fbits(f)[SP_IDX])


def split_form(form):
    """(x-form, p-form) of a control form built on the 82-cache (no deep wires, no outputs)"""
    xf = form & 1
    pf = 0
    f = form & ~1
    while f:
        low = f & -f
        b = low.bit_length() - 1
        f ^= low
        if 1 <= b <= 4 or 12 <= b <= N_BASE:
            xf |= low
        elif 5 <= b <= 11:
            pf |= low
        else:
            k = b - P0
            if 0 <= k < 68:
                pf |= low
            elif 68 <= k < 74:
                xf |= low
            else:
                raise ValueError("control uses a deep wire or output")
    return xf, pf


def parity(x):
    return bin(x).count("1") & 1


class Loader:
    """the designed loader: cache (deep wires re-pointed to the chosen special columns) + main products"""

    def __init__(self, tag, s, words_override=None):
        d, prods, words = load_design(tag)
        if words_override is not None:
            words = np.array(words_override, copy=True)
        self.k = d["k"]
        self.d = d
        F = self.F = Forms(self.k, words)
        self.words = words
        self.xform_e = {c: F.xform({x: int(x == c) for x in range(16)}) for c in ROWS}
        scratch = list(F.scratch)
        for k8 in range(8):
            c = ROWS[0] if k8 < 4 else ROWS[1]
            scratch[74 + k8] = (self.xform_e[c], scratch[74 + k8][1])
        self.scratch = scratch
        fans = fan_vectors(prods, d["blocks_outputs"], d["Z"])
        outs = []
        for pr, v in zip(prods, fans):
            L, M = F.prod_forms(pr)
            outs.append((L, M, v))
        self.main = outs
        self.n = len(outs)
        self.s = s
        self.pub = NewPub(self.k, words, scratch, outs + [(0, 0, 0)] * s, s)
        P = self.pub
        for k8 in range(8):
            c = ROWS[0] if k8 < 4 else ROWS[1]
            assert func_of(scratch[74 + k8][0], P.fn) == E_ROW[c]
        self.fan_int = [sum(((v >> n) & 1) << i for i, n in enumerate(FREE)) for (_, _, v) in outs]
        self.nrel = 25 - len(span_basis(self.fan_int))
        self._stripped()

    def _stripped(self):
        P = self.pub
        self.l0, self.m0, self.oldbits = [], [], []
        for L, M, v in self.main:
            res = []
            for form in (L, M):
                xf, pf = split_form(form)
                fx = func_of(xf, P.fn)
                fp = func_of(pf, P.fn)
                xb = [int(fbits(fx)[c]) for c in ROWS]
                full = func_of(form, P.fn)
                assert full == fx ^ fp
                res.append(((fx & ORD) ^ fp, xb))
            self.l0.append(res[0][0])
            self.m0.append(res[1][0])
            self.oldbits.append((res[0][1], res[1][1]))
        # cache generators (ordinary rows) + hyperplane complement
        gens = [FULL] + [P.bk.base_fn[i] for i in range(11)] + \
               [P.bk.base_fn[11 + 7 * j + 5] ^ P.bk.base_fn[11 + 7 * j + 6] for j in range(5)] + \
               [P.fn[P0 + i] for i in range(82)]
        E = Ech()
        for g in gens:
            E.add(g)
        extra = next(BLKF[p] for p in range(77) if not E.contains(BLKF[p]))
        self.cgens = gens + [extra]
        self.cord = [g & ORD for g in self.cgens]
        self.cel = CElim(self.cord)
        self.cR = [R152(g) for g in self.cgens]
        self.RAW, self.eps = [], 0
        for w, n in enumerate(FREE):
            r = P.delta[w]
            for o in range(self.n):
                if self.fan_int[o] >> w & 1:
                    r ^= self.l0[o] & self.m0[o]
            c = self.cel.coords(r & ORD)
            if c is None:
                raise ValueError(f"ordinary rows not reproduced on wire {n}")
            if c >> (len(self.cord) - 1) & 1:
                self.eps |= 1 << w
            v = R152(r)
            for i in range(len(self.cord)):
                if c >> i & 1:
                    v ^= self.cR[i]
            self.RAW.append(v)
        # LSB / top-bit wires must be cache-linear on ordinary rows
        for n in range(35):
            if n in WIDX:
                continue
            j, b = divmod(n, 7)
            r = P.bk.target[11 + n] ^ P.bk.base_fn[11 + n]
            if b == 6:
                r ^= P.bk.target[11 + n - 1] ^ P.bk.base_fn[11 + n - 1]
            assert self.cel.coords(r & ORD) is not None, f"wire {n} not cache-linear on ordinary rows"

    def pick_gamma(self, seed):
        U = span_basis(self.fan_int)
        rng = random.Random(seed)
        gamma = [self.eps] if self.eps else []
        while len(gamma) < self.s:
            v = 0
            for u in U:
                if rng.random() < 0.5:
                    v ^= u
            if v and len(span_basis(gamma + [v])) == len(gamma) + 1:
                gamma.append(v)
        return gamma


def erasure_items(k, a, batches):
    """admissible changes at address a: list of (batch, 35-bit mask, 25-bit wire vector)"""
    out = []
    for b in batches:
        if b < 0 or b > 14:
            continue
        ent = SPEC_INDEX.get(b)
        if ent is None:
            ent = SPEC_INDEX[b] = {e["a"]: e for e in SPEC[str(b)]}
        e = ent.get(a)
        if e is None:
            continue
        vecs = list(e["basis35"])
        Zs = []
        for n in {b, b + 1, k}:
            if str(n) in BLK:
                Zs += BLK[str(n)]["Z"]
        rows = [sum(parity(v & g) << i for i, v in enumerate(vecs)) for g in Zs]
        for sol in nullspace(rows, len(vecs)):
            m = 0
            for i, v in enumerate(vecs):
                if sol >> i & 1:
                    m ^= v
            wv = 0
            for n in range(35):
                if m >> n & 1:
                    j, bb = divmod(n, 7)
                    assert bb != 0, "LSB flip"
                    if bb == 6:
                        continue
                    wv |= 1 << WIDX[n]
            out.append((b, m, wv))
    return out


SPEC_INDEX = {}
from lib import nullspace, ins


def donor_items(k, a, donor_batch, donor_gamma):
    """changes of batch `donor_batch` cells whose wire vector lies in span(donor_gamma): the bank owning
    donor_gamma absorbs them by re-emitting its closers (same special columns)."""
    own = erasure_items(k, a, [donor_batch])
    if not own:
        return []
    vecs = [wv for b, m, wv in own]
    gens = vecs + list(donor_gamma)
    red = []
    kernel = []
    for i, g in enumerate(gens):
        x, cmb = g, 1 << i
        for (h, r, cc) in red:
            if x >> h & 1:
                x ^= r
                cmb ^= cc
        if x:
            red.append((x.bit_length() - 1, x, cmb))
            red.sort(reverse=True)
        else:
            kernel.append(cmb)
    out = []
    seen = {}
    for cmb in kernel:
        m = 0
        wv = 0
        for i in range(len(vecs)):
            if cmb >> i & 1:
                m ^= own[i][1]
                wv ^= own[i][2]
        if m and ins(seen, m):
            out.append((donor_batch, m, wv))
    return out


class Classes:
    def __init__(self, L: Loader, gamma, batches, donor=None):
        self.L = L
        self.gamma = list(gamma)
        self.batches = list(batches)
        self.donor = donor
        n = L.n
        self.nunk = 2 * n + 25
        self.cap = 2 * n + 25 - len(self.gamma) - L.nrel
        self.rows = [[], []]
        self.items = {}
        for ri, c in enumerate(ROWS):
            for p in range(76):
                addr = c + 16 * p
                items = erasure_items(L.k, addr, self.batches)
                if donor:
                    items += donor_items(L.k, addr, donor["batch"], donor["gamma"])
                self.items[(ri, p)] = items
                H = perp_basis(self.gamma + [it[2] for it in items])
                m_addr = [(L.m0[o] >> addr) & 1 for o in range(n)]
                l_addr = [(L.l0[o] >> addr) & 1 for o in range(n)]
                out = []
                for h in H:
                    v = 0
                    for o in range(n):
                        if parity(h & L.fan_int[o]):
                            if m_addr[o]:
                                v |= 1 << (2 * o)
                            if l_addr[o]:
                                v |= 1 << (2 * o + 1)
                    v |= h << (2 * n)
                    rhs = 0
                    for w in range(25):
                        if h >> w & 1:
                            rhs ^= (L.RAW[w] >> (76 * ri + p)) & 1
                    out.append((v << 1) | rhs)
                self.rows[ri].append(out)

    def weights(self, ri):
        return [len(span_basis([v >> 1 for v in self.rows[ri][p]])) - self.L.nrel for p in range(76)]

    def export(self, outdir, name):
        info = []
        for ri in (0, 1):
            wts = self.weights(ri)
            fn = outdir / f"{name}_row{ri}.txt"
            with open(fn, "w") as fh:
                fh.write(f"76 {self.nunk}\n")
                for p in range(76):
                    rows = self.rows[ri][p]
                    fh.write(f"{len(rows)} {wts[p]}\n")
                    for v in rows:
                        ws = [(v >> (64 * i)) & ((1 << 64) - 1) for i in range(5)]
                        assert v >> 320 == 0
                        fh.write(" ".join(map(str, ws)) + "\n")
            luck = sum(wts) - 5 * self.cap
            info.append(luck)
            print(f"row {ROWS[ri]}: total weight {sum(wts)}, 5 x cap {5*self.cap}, luck {luck}", flush=True)
        return info


def solve_class(rows, nunk):
    return p4build.solve_rows(rows, nunk)


def decompose_in(basis, v):
    return p4build.decompose_in(basis, v)


def build_candidate(cls: Classes, parts, seed=0):
    """parts[ri] = 5 block lists (class 0 = no deep wire).  returns scratch, outputs, words"""
    rng = random.Random(seed)
    L = cls.L
    n = L.n
    F = L.F
    P = L.pub
    s = len(cls.gamma)
    sol = []
    for ri in (0, 1):
        sl = []
        for c in range(5):
            rows = []
            for p in parts[ri][c]:
                rows += cls.rows[ri][p]
            z = solve_class(rows, cls.nunk)
            assert z is not None, f"class {c} of row {ROWS[ri]} inconsistent"
            sl.append(([(z >> (1 + 2 * o)) & 1 for o in range(n)], [(z >> (2 + 2 * o)) & 1 for o in range(n)],
                       [(z >> (1 + 2 * n + w)) & 1 for w in range(25)]))
        sol.append(sl)
    cval = [[[0] * 76, [0] * 76] for _ in range(s)]
    delta = {}
    for ri, c0 in enumerate(ROWS):
        for c in range(5):
            Lam, Mm, kap = sol[ri][c]
            for p in parts[ri][c]:
                addr = c0 + 16 * p
                res = 0
                for w in range(25):
                    v = (L.RAW[w] >> (76 * ri + p)) & 1
                    v ^= kap[w]
                    for o in range(n):
                        if L.fan_int[o] >> w & 1:
                            v ^= (Lam[o] & ((L.m0[o] >> addr) & 1)) ^ (Mm[o] & ((L.l0[o] >> addr) & 1))
                    if v:
                        res |= 1 << w
                items = cls.items[(ri, p)]
                basis = list(cls.gamma) + [it[2] for it in items]
                coef = decompose_in(basis, res)
                assert coef is not None, f"residual at row {c0} block {p} not in Gamma + erasures"
                for t in range(s):
                    cval[t][ri][p] = coef[t]
                ch = [(items[i][0], items[i][1]) for i in range(len(items)) if coef[s + i]]
                if ch:
                    delta[addr] = ch
    # pure-p generators / values
    pform = F.pform
    pvecs = F.pvals
    scratch = list(L.scratch)
    qidx = {}
    for ri in (0, 1):
        for c in range(1, 5):
            qidx[(ri, c)] = (0 if ri == 0 else 4) + (c - 1)
    for (ri, c), k8 in qidx.items():
        ind = [0] * 76
        for p in parts[ri][c]:
            ind[p] = 1
        scratch[74 + k8] = (L.xform_e[ROWS[ri]], pform(ind))
    outputs = []
    for o, (Lf, Mf, v) in enumerate(L.main):
        newforms = []
        for which, form in ((0, Lf), (1, Mf)):
            f = form
            old = L.oldbits[o][which]
            for ri in (0, 1):
                base = sol[ri][0][which][o]
                if old[ri] != base:
                    f ^= L.xform_e[ROWS[ri]]
                for c in range(1, 5):
                    if sol[ri][c][which][o] ^ base:
                        f ^= 1 << (P0 + 74 + qidx[(ri, c)])
            newforms.append(f)
        outputs.append((newforms[0], newforms[1], v))
    # closers
    pvec_ints = []
    for v in pvecs:
        pvec_ints.append(sum(int(v[p]) << p for p in range(77)))
    Ep = Ech(pvec_ints)
    Pt = decompose_in(list(cls.gamma), L.eps)
    assert Pt is not None, "eps not in Gamma"
    cls_of = [[0] * 76, [0] * 76]
    for ri in (0, 1):
        for c in range(5):
            for p in parts[ri][c]:
                cls_of[ri][p] = c

    def p_val77(form):
        f = func_of(form, P.fn)
        b = fbits(f)
        return np.array([b[16 * p] for p in range(77)], np.uint8)
    closers = []
    for t in range(s):
        done = None
        base1 = np.array(cval[t][0], np.uint8)
        base2 = np.array(cval[t][1], np.uint8)
        order = list(itertools.product([0, 1], repeat=10))
        rng.shuffle(order)
        for sig in order:
            v1 = base1 ^ np.array([sig[cls_of[0][p]] for p in range(76)], np.uint8)
            v2 = base2 ^ np.array([sig[5 + cls_of[1][p]] for p in range(76)], np.uint8)
            for swap in (0, 1):
                for c1 in (0, 1):
                    for c2 in (0, 1):
                        if not swap:
                            w2, w1 = v1 ^ c2, v2 ^ c1
                        else:
                            w2, w1 = v2 ^ c2, v1 ^ c1
                        f1 = pform(list(w1))
                        f2 = pform(list(w2))
                        g = ((p_val77(f1) ^ c1) & (p_val77(f2) ^ c2)).astype(np.uint8)
                        gint = sum(int(g[p]) << p for p in range(77))
                        if Ep.contains(gint) == (Pt[t] == 0):
                            done = (swap, c1, c2, f1, f2)
                            break
                    if done:
                        break
                if done:
                    break
            if done:
                break
        assert done is not None, f"closer {t} not realisable"
        swap, c1, c2, f1, f2 = done
        if not swap:
            Lt = c1 ^ f1 ^ L.xform_e[ROWS[0]]
            Mt = c2 ^ f2 ^ L.xform_e[ROWS[1]]
        else:
            Lt = c1 ^ f1 ^ L.xform_e[ROWS[1]]
            Mt = c2 ^ f2 ^ L.xform_e[ROWS[0]]
        vt = 0
        for i in range(25):
            if cls.gamma[t] >> i & 1:
                vt |= 1 << FREE[i]
        closers.append((Lt, Mt, vt))
    outputs += closers
    W2 = np.array(L.words, dtype=np.int64, copy=True)
    nchg = 0
    for a, ch in delta.items():
        for b, mask in ch:
            for j in range(5):
                m = (mask >> (7 * j)) & 127
                if m:
                    W2[a, 5 * b + j] ^= m
                    nchg += 1
    return scratch, outputs, W2, dict(ncells=len(delta), nchg=nchg, batches=sorted({b for ch in delta.values() for b, m in ch}))


def finalize(L, scratch, outputs, W2, name, base_fam, t0):
    k = L.k
    bk = K.Bank(k, W2)
    spec = K.build_spec(bk, scratch, outputs)
    res = K.evaluate(spec, bk)
    print(f"evaluate: ok={res.ok} toffoli={res.toffoli} peak width {res.peak_width}", flush=True)
    assert res.ok, res.violations[:3]
    out = HERE / "out" / name
    out.mkdir(parents=True, exist_ok=True)
    kmb = K.emit(spec, bk)
    path = out / f"angle_k_{k}.kmb"
    sha = K.write_kmb(kmb, path)
    fwd = K.verify_kmb(path, k, words=W2, direction="forward")
    rev = K.verify_kmb(path, k, words=W2, direction="reverse")
    print("verify_one forward", fwd["status"], fwd["toffoli"], "| reverse", rev["status"], flush=True)
    assert fwd["status"].startswith("PASS") and rev["status"].startswith("PASS")
    np.save(out / "words.npy", W2)
    fam = out / "family"
    fam.mkdir(exist_ok=True)
    for i in range(15):
        src = path if i == k else Path(base_fam) / f"angle_k_{i}.kmb"
        shutil.copyfile(src, fam / f"angle_k_{i}.kmb")
    sys.path.append(str(ROOT / "w_push11" / "dc" / "prep"))
    import deadlib as dl
    with np.load(Path(base_fam) / "submission.npz", allow_pickle=False) as z:
        npz = {key: z[key].copy() for key in z.files}
    W0 = npz["angle_words"].astype(np.int64)
    npz["angle_words"] = W2.astype(npz["angle_words"].dtype)
    V = dl.decode(W2, npz["tree_edges"].astype(np.int64))
    R, Bb, N = npz["U"].shape
    npz["U"] = V[N:].reshape(R, Bb, N).astype(npz["U"].dtype)
    np.savez(fam / "submission.npz", **npz)
    diff = np.argwhere(W0 != W2)
    mask = np.load(ROOT / "w_push11" / "dead" / "dead_mask_1e-13.npy")
    dead_ok = bool(all(mask[a, c] for a, c in diff))
    batches = sorted(set(int(c) // 5 for a, c in diff))
    print(f"table: {len(diff)} words changed vs base, all dead: {dead_ok}, batches {batches}", flush=True)
    assert dead_ok
    json.dump(dict(name=name, bank=k, toffoli=res.toffoli, sha=sha, words_changed=len(diff), batches=batches,
                   special=list(ROWS), s=L.s, base=str(base_fam), seconds=time.time() - t0),
              open(out / "report.json", "w"), indent=1)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["export", "build"])
    ap.add_argument("tag")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--s", type=int, default=4)
    ap.add_argument("--gseed", type=int, default=1)
    ap.add_argument("--erase", default=None, help="comma list of batches")
    ap.add_argument("--name", default=None)
    ap.add_argument("--base", default=str(ROOT / "w_push12" / "dc3356" / "family_merged"))
    ap.add_argument("--gamma-wires", default=None, help="closer fan-outs = eps + these single wires, e.g. s3b2,s3b3,s3b4")
    ap.add_argument("--donor", default=None, help="TAG:NAME of the absorbing bank's export (its Gamma and batch)")
    ap.add_argument("--words", default=None, help="override the design words (rebuild after a neighbour change)")
    ap.add_argument("--noerase", action="store_true", help="no erasures (rebuild: table already carries them)")
    a = ap.parse_args()
    t0 = time.time()
    d = HERE / "designs" / a.tag
    name = a.name or f"sg_{a.tag}"
    override = np.load(a.words) if a.words else None
    if a.mode == "export":
        L = Loader(a.tag, a.s, override)
        batches = [int(x) for x in a.erase.split(",") if int(x) >= 0] if a.erase else [L.k]
        gamma = L.pick_gamma(a.gseed)
        if a.gamma_wires:
            gamma = [L.eps] if L.eps else []
            for w in a.gamma_wires.split(","):
                g = 1 << WIDX[7 * int(w[1]) + int(w[3])]
                if len(span_basis(gamma + [g])) == len(gamma) + 1:
                    gamma.append(g)
            U = span_basis(L.fan_int)
            assert all(len(span_basis(U + [g])) == len(U) for g in gamma), "gamma outside the code space"
            rng = random.Random(a.gseed)
            while len(gamma) < a.s:
                v = 0
                for u in U:
                    if rng.random() < 0.5:
                        v ^= u
                if v and len(span_basis(gamma + [v])) == len(gamma) + 1:
                    gamma.append(v)
        donor = None
        if a.donor:
            dtag, dname = a.donor.split(":")
            dmeta = json.load(open(HERE / "designs" / dtag / f"{dname}_meta.json"))
            assert tuple(dmeta["special"]) == ROWS, "donor needs the same special columns"
            assert len(dmeta["batches"]) == 1
            donor = dict(batch=dmeta["batches"][0], gamma=dmeta["gamma"], tag=dtag, name=dname)
        cls = Classes(L, gamma, batches, donor)
        er = sum(len(v) for v in cls.items.values())
        print(f"bank {L.k}: n={L.n} s={a.s} special {ROWS} erase batches {batches}: erasure dims {er}, nrel {L.nrel}, cap {cls.cap}")
        luck = cls.export(d, name)
        json.dump(dict(s=a.s, gamma=gamma, batches=batches, special=list(ROWS), cap=cls.cap, luck=luck, donor=donor),
                  open(d / f"{name}_meta.json", "w"))
    else:
        meta = json.load(open(d / f"{name}_meta.json"))
        assert tuple(meta["special"]) == ROWS, "set GVQ_SPECIAL to the export's columns"
        L = Loader(a.tag, meta["s"], override)
        batches = [] if a.noerase else meta["batches"]
        donor = None if a.noerase else meta.get("donor")
        cls = Classes(L, meta["gamma"], batches, donor)
        parts = [json.load(open(d / f"{name}_row{ri}.json"))["classes"] for ri in (0, 1)]
        scratch, outputs, W2, info = build_candidate(cls, parts)
        print("special rows:", info)
        out = finalize(L, scratch, outputs, W2, a.out, a.base, t0)
        print("written", out, f"{time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
