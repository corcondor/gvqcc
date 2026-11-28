"""Block 2 at 41 products with one planted rank-1 element s x^T (paid by the own-batch flips), then stop
(finish block 3 with block3.py or the designer).
usage: python planted_design.py BANK TAG BLOCK1 BATCHES SEED WORDS_NPY MAXSEC
The base linear system (zero column + Phi) is reduced once per (zeta2, block-2 outputs); planted elements are then
tested against it, so thousands of (s, x) cost little."""
import json, os, random, sys, time
from pathlib import Path
import numpy as np
from design import *
from inst import Instance

k = int(sys.argv[1]); tag = sys.argv[2]; block1 = sys.argv[3].split(",")
batches = [int(b) for b in sys.argv[4].split(",")]; seed = int(sys.argv[5])
words = np.load(sys.argv[6]) if sys.argv[6] != "-" else None
maxsec = float(sys.argv[7])
NEED = int(os.environ.get("NEED2", "41"))
D = Design(k, block1, tag, words=words, seed=seed)
t0 = time.time()
D.block1()
prior = [i for i, pr in enumerate(D.prods) if pr.block == 1]
np_ = len(prior)
flips = D.flip_list(batches, D.B1)
zc = D.zeta_candidates(prior, flips, outputs_dim=8, top=40)
D.log(f"   flips {len(flips)}; best zeta margins {[(a, b) for a, b, c, z in zc[:4]]}")
words_before = D.words.copy()
Prow = [[D.prods[i].slice13(p) for p in range(75)] for i in prior]
rng = D.rng
m = 8
x0 = ORDX[0]
colidx = {x: t for t, x in enumerate(ORDX[1:])}
nsteer = m * np_


def echelon(eqs):
    piv = {}
    for mm, r in eqs:
        while mm:
            t = mm.bit_length() - 1
            if t in piv:
                mm ^= piv[t][0]
                r ^= piv[t][1]
            else:
                piv[t] = (mm, r)
                break
        else:
            if r:
                return None
    return piv


def element_builder(B2, z):
    """returns f(s, x1) -> list of 75 (mask, rhs) for the element sum_{o in s} x1 on T'_o(p)"""
    Dm = D.Dm()
    Trows = [rows_int(combo_mixed(Dm, g)) for g in B2]
    # per output o and column functional bit t: XOR of flip variables per row p
    F = [[[0] * 75 for t in range(13)] for o in range(m)]
    for fi, (p_, x, v, a, b) in enumerate(flips):
        bit = 1 << (nsteer + fi)
        for o, g in enumerate(B2):
            if not parity(g & v):
                continue
            if x == x0:
                ts = range(13)           # flipping column x0 changes every coordinate
            else:
                ts = [colidx[x]]
            for t in ts:
                if 1 <= p_ <= 75:
                    F[o][t][p_ - 1] ^= bit
                elif p_ == 0:
                    for p in range(75):
                        F[o][t][p] ^= bit

    def build(s, x1):
        tbits = [t for t in range(13) if x1 >> t & 1]
        outs = [o for o in range(m) if s >> o & 1]
        eqs = []
        pmask = [0] * 75
        for ii in range(np_):
            col = [parity(Prow[ii][p] & x1) for p in range(75)]
            for o in outs:
                bit = 1 << (o * np_ + ii)
                for p in range(75):
                    if col[p]:
                        pmask[p] ^= bit
        for p in range(75):
            mm = pmask[p]
            rhs = 0
            for o in outs:
                rhs ^= parity(Trows[o][p] & x1)
                for t in tbits:
                    mm ^= F[o][t][p]
            eqs.append((mm, rhs))
        return eqs
    return build


def extend(piv, eqs):
    new = {}
    for mm, r in eqs:
        while mm:
            t = mm.bit_length() - 1
            if t in piv:
                mm ^= piv[t][0]
                r ^= piv[t][1]
            elif t in new:
                mm ^= new[t][0]
                r ^= new[t][1]
            else:
                new[t] = (mm, r)
                break
        else:
            if r:
                return None
    return new


def solve_from(piv, nvar):
    x = rng.getrandbits(nvar)
    for t in sorted(piv):
        mm, r = piv[t]
        rest = mm & ~(1 << t)
        val = r ^ (bin(rest & x).count("1") & 1)
        x = (x & ~(1 << t)) | (val << t)
    return x


nvar = nsteer + len(flips)
attempt = 0
searches = 0
bases = 0
done2 = False
while not done2 and time.time() - t0 < maxsec:
    marg, ra, cap, z = zc[bases % min(len(zc), 12)]
    B2 = D.random_subspace(m)
    D.words = words_before.copy()
    bases += 1
    eqs, nv = D.zero_system(B2, flips, prior, z)
    base = echelon(eqs)
    if base is None:
        continue
    build = element_builder(B2, z)
    found = 0
    for trial in range(1500):
        if time.time() - t0 > maxsec or found >= 3:
            break
        while True:
            x1 = rng.randrange(1, 1 << 13)
            if x1 != z:
                break
        s = rng.randrange(1, 1 << m)
        el = build(s, x1)
        new = extend(base, el)
        if new is None:
            continue
        found += 1
        piv = dict(base)
        piv.update(new)
        x = solve_from(piv, nvar)
        D.words = words_before.copy()
        D.apply_flips(flips, x >> nsteer)
        steer = [[prior[i] for i in range(np_) if x >> (o * np_ + i) & 1] for o in range(m)]
        mats = D.target_mats(B2, steer)
        slices = block_slices13(mats)
        I = Instance(slices, m, zeta=z)
        # sanity: planted element annihilates every slice
        assert all(sum(parity((slices[p] >> (13 * o)) & x1) for o in range(m) if s >> o & 1) % 2 == 0 for p in range(75))
        kext = 2 * NEED - I.rankR
        I.write(f"{tag}_b2", kext, outdir=D.dir, meta={"zeta13": z, "planted_x": x1, "planted_s": s})
        searches += 1
        prods = run_engine(D.dir / f"{tag}_b2.txt", D.dir / f"{tag}_b2.res", kext, width=8000, weights="0,1,6,14,26",
                           jitter=8, seed=seed + searches, maxsec=150)
        if len(prods) != NEED:
            continue
        states = [E for nu, E in run_engine.states if nu >= NEED]
        from planes import all_planes
        for si, E in enumerate(states[:12]):
            planes = all_planes(I, E)
            res = D.select_min_bad(I, planes, NEED, m, D.z3)
            if res is None:
                continue
            nbad, sel = res
            al, be = solve_coeffs(I, slices, sel, m)
            prods2 = [Prod(a, b, lift_low(q1, I), lift_low(q2, I), {1: c}, 2) for (c, q1, q2), a, b in zip(sel, al, be)]
            rows = Prow + [[pr.slice13(p) for p in range(75)] for pr in prods2]
            zlist = [D.z3] + [rng.randrange(1, 1 << 13) for _ in range(300)]
            z3 = next((zt for zt in zlist if D.col_rank(rows, zt) == 75), None)
            D.log(f"      state {si}: {len(planes)} lines, {nbad} lines inside ker(z3); block-3 functional {'found' if z3 else 'not found'}")
            if z3 is None:
                continue
            for o in range(m):
                for i in steer[o]:
                    D.prods[i].coef[1] = D.prods[i].coef.get(1, 0) | (1 << o)
            D.prods += prods2
            D.blocks_outputs.append(B2)
            D.zeta2 = z
            D.z3 = z3
            D.check_block(2, B2, 1)
            D.check_block(1, D.B1, 0)
            done2 = True
            break
        if done2:
            break
    D.log(f"   base {bases}: {found} consistent planted elements; searches so far {searches}; {time.time()-t0:.0f}s")
print("block 2 (planted)", done2, f"{time.time()-t0:.0f}s", flush=True)
if done2:
    D.save()
sys.exit(0 if done2 else 1)
