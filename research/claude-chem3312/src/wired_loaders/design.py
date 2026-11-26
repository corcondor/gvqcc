"""End-to-end design of the ordinary part of one loader (own code):
  block 1: 7 outputs, 13-dim low, searched fresh (39 products)
  block 2: 8 outputs with a zero functional paid by dead-word flips (own batch) + block-1 steering (searched, 42)
  block 3: the other 8 outputs, zero functional paid by block-1/2 steering (searched, 42)
Search itself = w_push14/engine (copied exe).  Output: planner/designs/<tag>/design.json + words.npy
"""
import json, os, random, subprocess, sys, time
from pathlib import Path
import numpy as np
from tgt import *
from tgt import BLK, ANN, WIRED
from inst import Instance, block_slices_from_mixed, LOWCOLS
from zc_scan import zeta_list

HERE = Path(__file__).resolve().parent
FAM = ROOT / "w_push12" / "dc3356" / "family_merged"
ENG = HERE / "tmp" / "eng_copy.exe"
WORDS0 = np.load(FAM / "submission.npz")["angle_words"].astype(np.int64)
SPECIALS = SPECIAL


def wire(s):
    return 1 << (7 * int(s[1]) + int(s[3]))


def parity(x):
    return bin(x).count("1") & 1


# ------------------------------------------------------------------ table access
def delta_planes(k, words):
    """35 x 1219 array: word delta of loader k per wire (new ^ old)"""
    w = words
    out = np.zeros((35, NV), np.uint8)
    for j in range(5):
        for b in range(7):
            new = (w[:, 5 * k + j] >> b) & 1
            old = (w[:, 5 * (k - 1) + j] >> b) & 1 if k else 0
            out[7 * j + b] = (new ^ old).astype(np.uint8)
    return out


def mixed75(f):
    """[75,13] mixed part (rows p=1..75 rel. p=0; columns = ordinary x_j rel. x0) of a 1219 function"""
    G = grid(f)
    x0 = ORDX[0]
    H = G[1:76][:, ORDX[1:]]
    return (H ^ G[1:76][:, [x0]] ^ G[[0]][:, ORDX[1:]] ^ G[0, x0]).astype(np.uint8)


def combo_mixed(Dm, g):
    out = np.zeros((75, 13), np.uint8)
    n = 0
    while g >> n:
        if g >> n & 1:
            out ^= Dm[n]
        n += 1
    return out


def rows_int(M):
    return [int(sum(int(M[p, t]) << t for t in range(13))) for p in range(M.shape[0])]


# ------------------------------------------------------------------ products
class Prod:
    __slots__ = ("alpha", "beta", "q1", "q2", "coef", "block")

    def __init__(self, alpha, beta, q1, q2, coef, block):
        self.alpha, self.beta, self.q1, self.q2, self.coef, self.block = alpha, beta, q1, q2, coef, block

    def mixed(self):
        M = np.zeros((75, 13), np.uint8)
        for p in range(75):
            r = 0
            if self.alpha >> p & 1:
                r ^= self.q2
            if self.beta >> p & 1:
                r ^= self.q1
            for t in range(13):
                M[p, t] = (r >> t) & 1
        return M

    def slice13(self, p):
        r = 0
        if self.alpha >> p & 1:
            r ^= self.q2
        if self.beta >> p & 1:
            r ^= self.q1
        return r

    def to_json(self):
        return dict(alpha=hex(self.alpha), beta=hex(self.beta), q1=self.q1, q2=self.q2, coef=self.coef, block=self.block)

    @staticmethod
    def from_json(d):
        return Prod(int(d["alpha"], 16), int(d["beta"], 16), d["q1"], d["q2"], d["coef"], d["block"])


def zeta_of_low(q, zeta13):
    return parity(q & zeta13)


def run_engine(inst_path, res_path, k_ext, width=3000, weights=None, jitter=0, seed=1, maxsec=300, threads=None):
    threads = threads or int(os.environ.get("GVQ_THREADS", "2"))
    cmd = [str(ENG), "beam", str(inst_path), "--width", str(width), "--threads", str(threads), "--seed", str(seed),
           "--maxsec", str(maxsec), "--out", str(res_path)]
    if weights:
        cmd += ["--weights", weights]
    if jitter:
        cmd += ["--jitter", str(jitter)]
    t0 = time.time()
    if Path(res_path).exists():
        Path(res_path).unlink()          # never read a stale result
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=maxsec + 120)
    tail = [l for l in p.stdout.splitlines() if l.startswith("RESULT")]
    prods = []
    states = []
    if Path(res_path).exists():
        for line in open(res_path):
            if line.startswith("P "):
                _, c, q1, q2 = line.split()
                prods.append((int(c), int(q1), int(q2)))
            elif line.startswith("E "):
                head, vals = line.split(":")
                nu = int(head.split()[1].split("=")[1])
                states.append((nu, [int(v) for v in vals.split()]))
    run_engine.states = states
    print(f"      engine {Path(inst_path).name}: {tail[-1] if tail else p.stdout[-300:]}  [{time.time()-t0:.1f}s]", flush=True)
    return prods


GS2 = HERE / "tmp" / "gs2_copy.exe"


def run_gs2(I, inst_path, k_ext, need, rng, beam=1500, seed=7, log=print, timeout=3000):
    """9-output blocks: our k8_ls beam gs2 (copied exe), then exact selection of `need` independent lines."""
    from inst import write_gs2
    from planes import all_planes, plane_vectors, select_exact
    write_gs2(I, inst_path)
    out = Path(str(inst_path) + f".s{seed}.out")
    env = dict(os.environ, DUMP="30")
    t0 = time.time()
    with open(out, "w") as fh:
        subprocess.run([str(GS2), str(inst_path), str(k_ext), str(beam), "60", "4", "12", str(seed), "100000", "0.2", "1"],
                       stdout=fh, stderr=subprocess.DEVNULL, env=env, timeout=timeout)
    states = []
    best = None
    for line in open(out):
        if line.startswith("STATE "):
            a = list(map(int, line.split()[1:]))
            states.append((a[1], a[0], a[2:]))
        elif line.startswith("E "):
            best = list(map(int, line.split()[1:]))
        elif line.startswith("BEST"):
            log(f"      gs2: {line.strip()}  [{time.time()-t0:.0f}s]")
    states.sort(reverse=True)
    if best is not None:
        states.append((0, 0, best))
    for il, L, E in states[:12]:
        if il and il < need:
            continue
        planes = all_planes(I, E)
        vecs = [plane_vectors(I, pl, I.m) for pl in planes]
        sel = select_exact(vecs, need, rng)
        if sel is not None:
            log(f"      gs2 state IL={il} L={L}: {len(planes)} lines, selected {need} independent")
            return [planes[i] for i in sel]
    log("      gs2: no state with enough independent lines")
    return []


def lift_low(q, inst):
    """w-coordinates of an instance -> 13 coordinates"""
    full = 0
    for i, t in enumerate(inst.keep):
        if q >> i & 1:
            full |= 1 << t
    if inst.zeta:
        if parity(full & inst.zeta):
            full |= 1 << inst.piv
    return full


def solve_coeffs(inst, slices13, prods, m):
    """prods: (c, q1, q2) in instance coords.  returns list of (alpha, beta) 75-bit ints with
    slice(p) = sum_i beta_i(p) c(x)q1 + alpha_i(p) c(x)q2   (all in m x 13)"""
    vecs = []
    for c, q1, q2 in prods:
        for q in (q1, q2):
            f = lift_low(q, inst)
            v = 0
            for o in range(m):
                if c >> o & 1:
                    v |= f << (13 * o)
            vecs.append(v)
    piv = {}
    for i, v in enumerate(vecs):
        comb = 1 << i
        while v:
            t = v.bit_length() - 1
            if t in piv:
                v ^= piv[t][0]
                comb ^= piv[t][1]
            else:
                piv[t] = (v, comb)
                break
        else:
            raise RuntimeError("product vectors are dependent")
    n = len(prods)
    alpha = [0] * n
    beta = [0] * n
    for p, s in enumerate(slices13):
        comb = 0
        v = s
        while v:
            t = v.bit_length() - 1
            if t not in piv:
                raise RuntimeError(f"slice {p} not in the span of the products")
            v ^= piv[t][0]
            comb ^= piv[t][1]
        for i in range(n):
            if comb >> (2 * i) & 1:       # coefficient of c(x)q1  ->  beta
                beta[i] |= 1 << p
            if comb >> (2 * i + 1) & 1:   # coefficient of c(x)q2  ->  alpha
                alpha[i] |= 1 << p
    return alpha, beta


# ------------------------------------------------------------------ designer
class Design:
    def __init__(self, k, block1, tag, words=None, seed=1, log=print):
        self.k = k
        self.words = np.array(WORDS0 if words is None else words, copy=True)
        self.words_in = self.words.copy()
        self.T = Target(k)
        self.Z = self.T.Z
        self.nz = len(self.Z)
        self.dir = HERE / "designs" / tag
        self.dir.mkdir(parents=True, exist_ok=True)
        self.tag = tag
        self.rng = random.Random(seed)
        self.seed = seed
        self.B1 = [wire(s) for s in block1]
        assert self._independent(self.B1 + self.Z), "block 1 not independent of the code combos"
        # complement basis (16 or 17 outputs)
        self.comp = []
        basis = {}
        for g in self.B1 + self.Z:
            ins(basis, g)
        for n in range(35):
            if ins(basis, 1 << n):
                self.comp.append(1 << n)
        self.prods = []
        self.blocks_outputs = []
        self.log = log

    def _independent(self, vs):
        b = {}
        return all(ins(b, v) for v in vs)

    def Dm(self):
        d = delta_planes(self.k, self.words)
        return [mixed75(d[n]) for n in range(35)]

    # ---- selection among all lines of a found subspace, avoiding ker(zeta3)
    def lines_of_states(self, I, need, max_states=4):
        from planes import all_planes
        out = []
        for nu, E in run_engine.states:
            if nu >= need:
                out.append(all_planes(I, E))
            if len(out) >= max_states:
                break
        return out

    def select_avoiding(self, I, planes, need, m, z3, tries=4000):
        from planes import select, plane_vectors, nonzero_on
        cand = [pl for pl in planes if z3 is None or nonzero_on(I, pl, z3)]
        if len(cand) < need:
            return None
        vecs = [plane_vectors(I, pl, m) for pl in cand]
        sel = select(vecs, need, self.rng, tries=tries)
        if len(sel) < need:
            return None
        return [cand[i] for i in sel]

    def col_rank(self, rows_list, z):
        b = {}
        r = 0
        for pr in rows_list:
            col = 0
            for p in range(75):
                if parity(pr[p] & z):
                    col |= 1 << p
            r += ins(b, col)
        return r

    def select_min_bad(self, I, planes, need, m, z3, tries=200):
        """independent set of `need` lines using as few lines inside ker(z3) as possible: (nbad, lines) or None"""
        from planes import plane_vectors, nonzero_on, select_exact, Ech2, parity_rank
        good = [pl for pl in planes if nonzero_on(I, pl, z3)]
        bad = [pl for pl in planes if not nonzero_on(I, pl, z3)]
        gv = [plane_vectors(I, pl, m) for pl in good]
        bv = [plane_vectors(I, pl, m) for pl in bad]
        best = None
        for t in range(tries):
            og = list(range(len(good)))
            ob = list(range(len(bad)))
            self.rng.shuffle(og)
            self.rng.shuffle(ob)
            E = Ech2()
            sel = []
            for i in og:
                if len(sel) == need:
                    break
                if E.add_pair(*gv[i]):
                    sel.append(good[i])
            nb = 0
            for i in ob:
                if len(sel) == need:
                    break
                if E.add_pair(*bv[i]):
                    sel.append(bad[i])
                    nb += 1
            if len(sel) == need and (best is None or nb < best[0]):
                best = (nb, sel)
                if nb == 0:
                    break
        if best is None or best[0] > 4:
            # exact: delete the kernel lines first from the full set while the parity rank stays at `need`
            allp = good + bad
            vecs = gv + bv
            if parity_rank(vecs, self.rng) >= need:
                keep = list(range(len(allp)))
                order = list(range(len(good), len(allp)))
                self.rng.shuffle(order)
                order2 = list(range(len(good)))
                self.rng.shuffle(order2)
                for i in order + order2:
                    if len(keep) == need:
                        break
                    trial = [j for j in keep if j != i]
                    if parity_rank([vecs[j] for j in trial], self.rng) >= need:
                        keep = trial
                if len(keep) == need:
                    E = Ech2()
                    if all(E.add_pair(*vecs[j]) for j in keep):
                        nb = sum(1 for j in keep if j >= len(good))
                        if best is None or nb < best[0]:
                            best = (nb, [allp[j] for j in keep])
        return best

    def pick_zeta3(self, I, plane_sets, need, m, top=24):
        """rank zeta3 candidates by the number of usable lines; return (zeta3, selection)"""
        from planes import nonzero_on
        counts = []
        for z in range(1, 1 << 13):
            c = max(sum(nonzero_on(I, pl, z) for pl in planes) for planes in plane_sets)
            counts.append((c, self.rng.random(), z))
        counts.sort(reverse=True)
        for c, _, z in counts[:top]:
            for planes in plane_sets:
                sel = self.select_avoiding(I, planes, need, m, z, tries=1500)
                if sel is not None:
                    return z, sel, c
        return None, None, counts[0][0]

    # ---- block 1
    def block1(self, width=3000, seeds=(1, 2, 3, 4, 5), use_z3=True):
        Dm = self.Dm()
        m = len(self.B1)
        mats = [combo_mixed(Dm, g) for g in self.B1]
        slices = block_slices13(mats)
        I = Instance(slices, m)
        n_target = 39
        k_ext = 2 * n_target - I.rankR
        I.write(f"{self.tag}_b1", k_ext, outdir=self.dir)
        for s in seeds:
            prods = run_engine(self.dir / f"{self.tag}_b1.txt", self.dir / f"{self.tag}_b1_s{s}.res", k_ext, width=width, seed=s)
            if len(prods) == n_target:
                break
        assert len(prods) == n_target, "block 1 not solved"
        self.z3 = None
        if use_z3:
            z3, sel, cnt = self.pick_zeta3(I, self.lines_of_states(I, n_target), n_target, m)
            if z3 is not None:
                self.z3 = z3
                prods = sel
                self.log(f"   block 1: zeta3 = {z3:013b} with {cnt} usable lines; selected {len(sel)} outside its kernel")
            else:
                self.log(f"   block 1: no zeta3 admits {n_target} independent lines outside its kernel (max usable {cnt})")
        al, be = solve_coeffs(I, slices, prods, m)
        for (c, q1, q2), a, b in zip(prods, al, be):
            self.prods.append(Prod(a, b, lift_low(q1, I), lift_low(q2, I), {0: c}, 1))
        self.blocks_outputs = [self.B1]
        self.check_block(1, self.B1, 0)
        return I

    # ---- helpers for target with steering
    def target_mats(self, outputs, steer):
        """outputs: combos; steer[o] = set of earlier product indices whose fan reaches output o"""
        Dm = self.Dm()
        mats = []
        for o, g in enumerate(outputs):
            M = combo_mixed(Dm, g)
            for i in steer[o]:
                M ^= self.prods[i].mixed()
            mats.append(M)
        return mats

    def check_block(self, blk, outputs, blk_index):
        """verify: target of each output == sum of all products' contributions (block fan + steering)"""
        Dm = self.Dm()
        for o, g in enumerate(outputs):
            M = combo_mixed(Dm, g)
            for pr in self.prods:
                if (pr.coef.get(blk_index, 0) >> o) & 1:
                    M ^= pr.mixed()
            assert not M.any(), f"block {blk} output {o} not reproduced"

    # ---- flips
    def neighbors(self, b):
        """other wired banks whose target changes with a cell of batch b (they must keep codes and Phi)"""
        return [n for n in (b, b + 1) if n != self.k and n in WIRED]

    def flip_list(self, batches, invisible_to):
        """admissible flips (p, x, mask35, addr, batch) on ordinary columns that leave the given combos unchanged
        and preserve the cache-linear combos of every other bank the cell enters"""
        res = []
        for b in batches:
            extra = []
            for n in self.neighbors(b):
                extra += BLK[str(n)]["Z"]
            for a, basis in cell_free_basis(b).items():
                p, x = a >> 4, a & 15
                if x in SPECIALS:
                    continue
                vecs = list(basis)
                rows = [sum(parity(v & g) << i for i, v in enumerate(vecs)) for g in list(invisible_to) + extra]
                for sol in nullspace(rows, len(vecs)):
                    v = 0
                    for i, vv in enumerate(vecs):
                        if sol >> i & 1:
                            v ^= vv
                    res.append((p, x, v, a, b))
        return res

    def apply_flips(self, flips, sel):
        for i, f in enumerate(flips):
            if sel >> i & 1:
                p, x, v, a, b = f
                for j in range(5):
                    m = (v >> (7 * j)) & 127
                    if m:
                        self.words[a, 5 * b + j] ^= m

    def phi_eqs(self, flips, nsteer):
        eqs = []
        banks = {self.k}
        for f in flips:
            banks.update(self.neighbors(f[4]))
        for bank in sorted(banks):
            phi = [[(a >> 4, a & 15) for a in s] for s in ANN[bank]] if bank != self.k else self.T.phi
            for n in range(35):
                for cells in phi:
                    cs = set(cells)
                    mask = 0
                    for i, f in enumerate(flips):
                        p, x, v, a, b = f
                        if bank != self.k and bank not in self.neighbors(b):
                            continue
                        if v >> n & 1 and (p, x) in cs:
                            mask |= 1 << (nsteer + i)
                    if mask:
                        eqs.append((mask, 0))
        return eqs

    def zero_system(self, outputs, flips, prior, zeta, planted=()):
        """unknowns: steer bits s[o][i] (len(outputs) x len(prior)) then flips.
        zeta: 13-bit functional; planted: list of (list of (o, xfunctional13)) elements. returns (eqs, nvar)"""
        m = len(outputs)
        np_ = len(prior)
        nsteer = m * np_
        Dm = self.Dm()
        T = [combo_mixed(Dm, g) for g in outputs]
        Trows = [rows_int(M) for M in T]
        Prow = [[self.prods[i].slice13(p) for p in range(75)] for i in prior]
        elements = [[(o, zeta)] for o in range(m)] + [list(el) for el in planted]
        x0 = ORDX[0]
        colidx = {x: t for t, x in enumerate(ORDX[1:])}
        # flip row effects per (output): value of mixed flip at (p, t)
        eqs = []
        fl_info = []
        for p_, x, v, a, b in flips:
            hit = 0
            for o, g in enumerate(outputs):
                if parity(g & v):
                    hit |= 1 << o
            fl_info.append(hit)
        for el in elements:
            masks = [0] * 75
            rhs = [0] * 75
            for o, xf in el:
                for p in range(75):
                    rhs[p] ^= parity(Trows[o][p] & xf)
                for ii in range(np_):
                    bit = 1 << (o * np_ + ii)
                    for p in range(75):
                        if parity(Prow[ii][p] & xf):
                            masks[p] ^= bit
            for fi, (pp, x, v, a, b) in enumerate(flips):
                hit = fl_info[fi]
                if not hit:
                    continue
                # parity of the functional's action on a unit flip at column x
                par = 0
                for o, xf in el:
                    if hit >> o & 1:
                        if x == x0:
                            # flipping column x0 changes every coordinate: functional of all-ones over its support
                            par ^= parity(xf)
                        else:
                            par ^= (xf >> colidx[x]) & 1
                if not par:
                    continue
                bit = 1 << (nsteer + fi)
                if 1 <= pp <= 75:
                    masks[pp - 1] ^= bit
                elif pp == 0:
                    for p in range(75):
                        masks[p] ^= bit
            eqs += [(masks[p], rhs[p]) for p in range(75)]
        nvar = nsteer + len(flips)
        eqs += self.phi_eqs(flips, nsteer)
        return eqs, nvar

    def solve_with_flips(self, outputs, flips, prior, zeta, planted=(), rng=None):
        eqs, nvar = self.zero_system(outputs, flips, prior, zeta, planted)
        from solve import solve_system
        rk, x, nd = solve_system(eqs, nvar, rng or self.rng)
        return x, nvar

    def zeta_candidates(self, prior, flips, outputs_dim=8, top=40):
        """rank zeta (13-bit functionals = even column sets) by capacity margin"""
        Prow = [[self.prods[i].slice13(p) for p in range(75)] for i in prior]
        x0 = ORDX[0]
        res = []
        rows_by_p = {}
        for pp, x, v, a, b in flips:
            rows_by_p.setdefault(pp, []).append((x, v))
        for z in range(1, 1 << 13):
            # rank of prior products on zeta
            basis = {}
            r = 0
            for pr in Prow:
                col = 0
                for p in range(75):
                    if parity(pr[p] & z):
                        col |= 1 << p
                r += ins(basis, col)
            cap = 0
            for p in range(1, 76):
                F = {}
                for x, v in rows_by_p.get(p, []):
                    hit = parity(z) if x == x0 else (z >> LOWCOLS.index(x)) & 1
                    if hit:
                        ins(F, self.out_image(v))
                cap += min(outputs_dim, len(F))
            res.append((cap - outputs_dim * (75 - r), r, cap, z))
        res.sort(reverse=True)
        return res[:top]

    def out_image(self, v):
        return sum(parity(v & g) << i for i, g in enumerate(self.comp))

    # ---- block 2
    def block2(self, batches, tries=int(os.environ.get("GVQ_TRIES", "1200")), n_products=42, weights="0,1,6,14,26", width=5000, m=8, zeta=None, planted_fn=None):
        prior = [i for i, pr in enumerate(self.prods) if pr.block == 1]
        flips = self.flip_list(batches, self.B1)
        self.log(f"   block 2: {len(flips)} admissible flips (batches {batches}), invisible to block 1")
        zc = self.zeta_candidates(prior, flips, outputs_dim=m, top=60) if zeta is None else [(0, 0, 0, zeta)]
        self.log(f"   best zeta margins {[(a, b) for a, b, c, d in zc[:5]]}")
        words_before = self.words.copy()
        for t in range(tries):
            marg, ra, cap, z = zc[t % min(len(zc), int(os.environ.get("GVQ_ZETAS", "24")))]
            B2 = self.random_subspace(m)
            self.words = words_before.copy()          # every try starts from the unflipped table
            planted = planted_fn(self, B2, z) if planted_fn else ()
            x, nvar = self.solve_with_flips(B2, flips, prior, z, planted)
            if x is None:
                if t % 50 == 0:
                    self.log(f"      try {t}: zeta margin {marg} rankA {ra}: linear system inconsistent")
                continue
            nsteer = m * len(prior)
            sel = x >> nsteer
            self.words = words_before.copy()
            self.apply_flips(flips, sel)
            steer = [[prior[i] for i in range(len(prior)) if x >> (o * len(prior) + i) & 1] for o in range(m)]
            mats = self.target_mats(B2, steer)
            slices = block_slices13(mats)
            I = Instance(slices, m, zeta=z)
            k_ext = 2 * n_products - I.rankR
            I.write(f"{self.tag}_b2", k_ext, outdir=self.dir, meta={"zeta13": z, "batches": batches})
            self.log(f"      try {t}: zeta margin {marg} rankA {ra}: solved; rankR {I.rankR} q {I.q} k {k_ext}; searching")
            prods = run_engine(self.dir / f"{self.tag}_b2.txt", self.dir / f"{self.tag}_b2.res", k_ext, width=width, weights=weights, seed=self.seed + t)
            if len(prods) != n_products:
                continue
            if self.z3 is not None:
                prev_rows = [[self.prods[i].slice13(p) for p in range(75)] for i in prior]
                chosen = None
                for planes in self.lines_of_states(I, n_products, max_states=8):
                    res = self.select_min_bad(I, planes, n_products, m, self.z3)
                    if res is None:
                        continue
                    nbad, sel = res
                    al, be = solve_coeffs(I, slices, sel, m)
                    rows = prev_rows + [[Prod(a, b, lift_low(q1, I), lift_low(q2, I), {}, 2).slice13(p) for p in range(75)]
                                        for (c, q1, q2), a, b in zip(sel, al, be)]
                    zlist = [self.z3] + [self.rng.randrange(1, 1 << 13) for _ in range(300)]
                    zok = next((zt for zt in zlist if self.col_rank(rows, zt) == 75), None)
                    self.log(f"      selection: {nbad} lines inside ker(z3), block-3 functional {'found' if zok else 'not found'}")
                    if zok:
                        self.z3 = zok
                        chosen = sel
                        break
                if chosen is None:
                    self.log("      no usable selection for block 3; next try")
                    continue
                prods = chosen
            al, be = solve_coeffs(I, slices, prods, m)
            # add block-1 steering coefficients on block-2 outputs
            for o in range(m):
                for i in steer[o]:
                    self.prods[i].coef[1] = self.prods[i].coef.get(1, 0) | (1 << o)
            for (c, q1, q2), a, b in zip(prods, al, be):
                self.prods.append(Prod(a, b, lift_low(q1, I), lift_low(q2, I), {1: c}, 2))
            self.blocks_outputs.append(B2)
            self.zeta2 = z
            self.check_block(2, B2, 1)
            self.check_block(1, self.B1, 0)
            return True
        self.words = words_before
        return False

    def block2_noflip(self, n_products=39, m=7, tries=20):
        """block 2 without zero column (for loaders with no free dead words): a fresh 7-output target, 13-dim low,
        searched like block 1; lines chosen outside ker(zeta3) so that block 3's zero column stays payable."""
        prior = [i for i, pr in enumerate(self.prods) if pr.block == 1]
        for t in range(tries):
            B2 = self.random_subspace(m)
            steer = [[] for _ in range(m)]
            mats = self.target_mats(B2, steer)
            slices = block_slices13(mats)
            I = Instance(slices, m)
            k_ext = 2 * n_products - I.rankR
            I.write(f"{self.tag}_b2", k_ext, outdir=self.dir)
            prods = run_engine(self.dir / f"{self.tag}_b2.txt", self.dir / f"{self.tag}_b2.res", k_ext, width=3000, seed=self.seed + t)
            if len(prods) != n_products:
                continue
            if self.z3 is not None:
                prev_rows = [[self.prods[i].slice13(p) for p in range(75)] for i in prior]
                chosen = None
                for planes in self.lines_of_states(I, n_products, max_states=8):
                    res = self.select_min_bad(I, planes, n_products, m, self.z3)
                    if res is None:
                        continue
                    nbad, sel = res
                    al, be = solve_coeffs(I, slices, sel, m)
                    rows = prev_rows + [[Prod(a, b, lift_low(q1, I), lift_low(q2, I), {}, 2).slice13(p) for p in range(75)]
                                        for (c, q1, q2), a, b in zip(sel, al, be)]
                    zlist = [self.z3] + [self.rng.randrange(1, 1 << 13) for _ in range(300)]
                    zok = next((zt for zt in zlist if self.col_rank(rows, zt) == 75), None)
                    self.log(f"      selection: {nbad} lines inside ker(z3), block-3 functional {'found' if zok else 'not found'}")
                    if zok:
                        self.z3 = zok
                        chosen = sel
                        break
                if chosen is None:
                    continue
                prods = chosen
            al, be = solve_coeffs(I, slices, prods, m)
            for (c, q1, q2), a, b in zip(prods, al, be):
                self.prods.append(Prod(a, b, lift_low(q1, I), lift_low(q2, I), {1: c}, 2))
            self.blocks_outputs.append(B2)
            self.check_block(2, B2, 1)
            self.check_block(1, self.B1, 0)
            return True
        return False

    def random_subspace(self, m, tries=1000):
        while True:
            out = []
            basis = {}
            while len(out) < m:
                c = self.rng.getrandbits(len(self.comp))
                if c and ins(basis, c):
                    g = 0
                    for i in range(len(self.comp)):
                        if c >> i & 1:
                            g ^= self.comp[i]
                    out.append(g)
            return out

    # ---- block 3
    def block3(self, n_products=None, weights="0,1,6,14,26", width=5000, tries=6):
        B2 = self.blocks_outputs[1]
        basis = {}
        for g in self.B1 + self.Z + B2:
            ins(basis, g)
        B3 = [g for g in self.comp if ins(basis, g)]
        m = len(B3)
        if n_products is None:
            n_products = {7: 38, 8: 42, 9: 47}[m]
        prior = list(range(len(self.prods)))
        from solve import solve_system
        Prow = [[self.prods[i].slice13(p) for p in range(75)] for i in prior]
        for t in range(tries):
            z = self.z3 if (self.z3 is not None and t == 0) else self.rng.randrange(1, 1 << 13)
            basis_c = {}
            r = 0
            for pr in Prow:
                col = 0
                for p in range(75):
                    if parity(pr[p] & z):
                        col |= 1 << p
                r += ins(basis_c, col)
            if r < 75:
                self.log(f"   block 3 try {t}: column rank of the {len(prior)} earlier products on zeta is {r} < 75")
                if t == 0 and self.z3 is not None:
                    pass
                continue
            eqs, nvar = self.zero_system(B3, [], prior, z)
            rk, x, nd = solve_system(eqs, nvar, self.rng)
            if x is None:
                continue
            steer = [[prior[i] for i in range(len(prior)) if x >> (o * len(prior) + i) & 1] for o in range(m)]
            mats = self.target_mats(B3, steer)
            slices = block_slices13(mats)
            I = Instance(slices, m, zeta=z)
            k_ext = 2 * n_products - I.rankR
            I.write(f"{self.tag}_b3", k_ext, outdir=self.dir, meta={"zeta13": z})
            self.log(f"   block 3 try {t}: m={m} rankR {I.rankR} q {I.q} k {k_ext}")
            if m <= 8:
                prods = run_engine(self.dir / f"{self.tag}_b3.txt", self.dir / f"{self.tag}_b3.res", k_ext, width=width, weights=weights, seed=self.seed + 100 + t)
            else:
                prods = run_gs2(I, self.dir / f"{self.tag}_b3.gs2", k_ext, n_products, self.rng, seed=7 + self.seed + t, log=self.log)
            if len(prods) != n_products:
                continue
            al, be = solve_coeffs(I, slices, prods, m)
            for o in range(m):
                for i in steer[o]:
                    self.prods[i].coef[2] = self.prods[i].coef.get(2, 0) | (1 << o)
            for (c, q1, q2), a, b in zip(prods, al, be):
                self.prods.append(Prod(a, b, lift_low(q1, I), lift_low(q2, I), {2: c}, 3))
            self.blocks_outputs.append(B3)
            self.zeta3 = z
            for bi, outs in enumerate(self.blocks_outputs):
                self.check_block(bi + 1, outs, bi)
            return True
        return False

    def save(self):
        d = dict(k=self.k, blocks_outputs=self.blocks_outputs, Z=self.Z, prods=[p.to_json() for p in self.prods],
                 zeta2=getattr(self, "zeta2", None), zeta3=getattr(self, "zeta3", None))
        json.dump(d, open(self.dir / "design.json", "w"))
        np.save(self.dir / "words.npy", self.words)
        np.save(self.dir / "words_in.npy", self.words_in)
        nflip = int((self.words != self.words_in).sum())
        self.log(f"saved {self.dir}: {len(self.prods)} products, {nflip} words changed")


def block_slices13(mats):
    out = []
    for p in range(75):
        v = 0
        for o, M in enumerate(mats):
            row = 0
            for t in range(13):
                if M[p, t]:
                    row |= 1 << t
            v |= row << (13 * o)
        out.append(v)
    return out


if __name__ == "__main__":
    k = int(sys.argv[1])
    tag = sys.argv[2]
    block1 = sys.argv[3].split(",")
    batches = [int(b) for b in sys.argv[4].split(",")]
    seed = int(sys.argv[5]) if len(sys.argv) > 5 else 1
    words = np.load(sys.argv[6]) if len(sys.argv) > 6 else None
    D = Design(k, block1, tag, words=words, seed=seed)
    t0 = time.time()
    D.block1()
    print("block 1 done", time.time() - t0, flush=True)
    ok2 = D.block2(batches) if batches != [-1] else D.block2_noflip()
    print("block 2", ok2, time.time() - t0, flush=True)
    if ok2 and not os.environ.get("GVQ_STOP2"):
        ok3 = D.block3()
        print("block 3", ok3, time.time() - t0, flush=True)
    D.save()
