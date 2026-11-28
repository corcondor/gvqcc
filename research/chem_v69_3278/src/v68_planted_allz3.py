"""
V68 All-8191-z3 Vectorized Planted Block-2 Designer (41 products -> Bank 14 at 207 CCX!).

Upgrade over planted_design.py:
  Instead of fixing a single D.z3 before select_min_bad and only sampling 300 random z3 afterward,
  for EVERY 41-product state E found by eng_copy.exe we scan ALL 8,191 non-zero functionals
  zt in 1..8191 in vectorized NumPy (~0.02s), rank them by combined (# of Prow in ker(zt)) +
  (# of planes in ker(zt)), and run select_min_bad + exact col_rank == 75 on the top-20 best zt!
"""
import json, os, random, sys, time
from pathlib import Path
import numpy as np
from design import *
from inst import Instance
from planes import all_planes, nonzero_on

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
D.log(f"[V68-ALLZ3] bank={k} tag={tag} NEED={NEED} flips={len(flips)} best_zeta={[(a, b) for a, b, c, z in zc[:4]]}")
words_before = D.words.copy()
Prow = [[D.prods[i].slice13(p) for p in range(75)] for i in prior]
rng = D.rng
m = 8
x0 = ORDX[0]
colidx = {x: t for t, x in enumerate(ORDX[1:])}
nsteer = m * np_

# Precompute parity table for 13-bit integers (8192,)
POP13 = np.array([bin(i).count("1") & 1 for i in range(8192)], dtype=np.uint8)
ALL_Z = np.arange(1, 8192, dtype=np.int32)  # (8191,)

# Precompute which Prow[i] are identically 0 on functional zt (all 75 rows orthogonal to zt):
# For each i in 0..38, Prow_span[i] is the set of distinct non-zero 13-bit ints in Prow[i].
# Actually, a 75-row product pr is in ker(zt) iff zt is orthogonal to ALL rows of pr -> i.e. to the GF(2) basis of pr!
def row_basis13(rows75):
    b = {}
    for v in rows75:
        ins(b, int(v))
    return list(b.values())

PROW_BASES = [row_basis13(Prow[i]) for i in range(np_)]
# Compute prow_ker_cnt[zt-1] = number of block-1 products in ker(zt)
PROW_KER_CNT = np.zeros(8191, dtype=np.int16)
for basis in PROW_BASES:
    if not basis:
        PROW_KER_CNT += 1
        continue
    in_ker = np.ones(8191, dtype=bool)
    for bv in basis:
        in_ker &= (POP13[ALL_Z & bv] == 0)
    PROW_KER_CNT += in_ker


def rank_all_z3_for_planes(I, planes):
    """Vectorized scan of ALL 8,191 functionals zt: return top-24 zt minimizing (prow_ker + frac_bad_planes)."""
    # Lift each plane's (q1, q2) to 13-bit low functionals
    q1s = np.array([lift_low(pl[1], I) for pl in planes], dtype=np.int32)
    q2s = np.array([lift_low(pl[2], I) for pl in planes], dtype=np.int32)
    # bad(pl, zt) iff parity(q1 & zt) == 0 AND parity(q2 & zt) == 0
    # Compute in chunks of zt to keep RAM tiny (< 5 MB)
    npl = len(planes)
    bad_cnt = np.zeros(8191, dtype=np.int32)
    chunk = 512
    for s0 in range(0, 8191, chunk):
        zs = ALL_Z[s0 : s0 + chunk][:, None]  # (C, 1)
        b1 = POP13[zs & q1s[None, :]]         # (C, npl)
        b2 = POP13[zs & q2s[None, :]]         # (C, npl)
        bad_cnt[s0 : s0 + chunk] = ((b1 == 0) & (b2 == 0)).sum(axis=1)
    # Score: prefer small prow_ker_cnt (must be <= 5) and small bad_cnt
    # Filter to zt where prow_ker_cnt <= 5!
    valid = np.where(PROW_KER_CNT <= 5)[0]
    order = valid[np.argsort(bad_cnt[valid] + 4 * PROW_KER_CNT[valid])]
    return [(int(ALL_Z[idx]), int(PROW_KER_CNT[idx]), int(bad_cnt[idx])) for idx in order[:24]]


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
    Dm = D.Dm()
    Trows = [rows_int(combo_mixed(Dm, g)) for g in B2]
    F = [[[0] * 75 for t in range(13)] for o in range(m)]
    for fi, (p_, x, v, a, b) in enumerate(flips):
        bit = 1 << (nsteer + fi)
        for o, g in enumerate(B2):
            if not parity(g & v):
                continue
            ts = range(13) if x == x0 else [colidx[x]]
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
searches = 0
bases = 0
done2 = False
best_nbad_seen = 999

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
        kext = 2 * NEED - I.rankR
        I.write(f"{tag}_b2", kext, outdir=D.dir, meta={"zeta13": z, "planted_x": x1, "planted_s": s})
        searches += 1
        prods = run_engine(D.dir / f"{tag}_b2.txt", D.dir / f"{tag}_b2.res", kext, width=8000, weights="0,1,6,14,26",
                           jitter=8, seed=seed + searches, maxsec=120)
        if len(prods) != NEED:
            continue
        states = [E for nu, E in run_engine.states if nu >= NEED]
        for si, E in enumerate(states[:12]):
            planes = all_planes(I, E)
            # V68 UPGRADE: scan ALL 8,191 functionals zt!
            top_z3 = rank_all_z3_for_planes(I, planes)
            for zt, pk, bc in top_z3[:12]:
                res = D.select_min_bad(I, planes, NEED, m, zt, tries=120)
                if res is None:
                    continue
                nbad, sel = res
                if nbad < best_nbad_seen:
                    best_nbad_seen = nbad
                if nbad + pk > 5:
                    continue
                al, be = solve_coeffs(I, slices, sel, m)
                prods2 = [Prod(a, b, lift_low(q1, I), lift_low(q2, I), {1: c}, 2) for (c, q1, q2), a, b in zip(sel, al, be)]
                rows = Prow + [[pr.slice13(p) for p in range(75)] for pr in prods2]
                rk = D.col_rank(rows, zt)
                D.log(f"      [V68] state {si} zt={zt} (prow_ker={pk}, nbad={nbad}, planes={len(planes)}): col_rank={rk}/75")
                if rk == 75:
                    for o in range(m):
                        for i in steer[o]:
                            D.prods[i].coef[1] = D.prods[i].coef.get(1, 0) | (1 << o)
                    D.prods += prods2
                    D.blocks_outputs.append(B2)
                    D.zeta2 = z
                    D.z3 = zt
                    D.check_block(2, B2, 1)
                    D.check_block(1, D.B1, 0)
                    done2 = True
                    break
            if done2:
                break
        if done2:
            break
    D.log(f"   base {bases}: found={found}, searches={searches}, best_nbad={best_nbad_seen}, {time.time()-t0:.0f}s")

print(f"V68 block 2 (planted 41) done={done2} best_nbad={best_nbad_seen} {time.time()-t0:.0f}s", flush=True)
if done2:
    D.save()
sys.exit(0 if done2 else 1)
