"""
V75 Min-dim(R) Early-Order 231-CCX Builder.

Breaks V101's 91 + 2 = 93 > 92 obstruction mathematically:
  At e=29, min dim(R) = 144 -> dim(K cap R) = 93 + 144 - 146 = 91 -> 91 + 2 = 93 > 92 (always fails!).
  At e=30, we explicitly select a valid early-chip set E minimizing dim(R) <= 143,
  so dim(K cap R) = 93 + 143 - 146 = 90 -> 90 + 2 = 92 <= 92!
"""
import os
import pickle
import random
import sys
import time
from pathlib import Path
import numpy as np

WORK = Path(r"c:\Users\81808\.openclaw\gvqcc_v2832\v71_heads_232_for_3275")
os.chdir(WORK)
os.environ["K8_NPZ"] = str(WORK / "words_3284.npz")
sys.path.insert(0, str(WORK))

from common import *
from frame import *
from solve import check_function
from solve2 import solve_all, coef_vectors
from build2 import Builder2
from gf2 import Ech

k = int(sys.argv[1])
cover_file = sys.argv[2]
nrel = int(sys.argv[3])
e = int(sys.argv[4])
seed = int(sys.argv[5])
limit = float(sys.argv[6])

t0 = time.time()
F = Frame(k)
cov = pickle.load(open(cover_file, "rb"))
ncov = len(cov)
tag = "" if ncov == 96 else f"_n{ncov}"
fivef = cover_file.replace(".pkl", ".five.pkl")
forced = pickle.load(open(fivef, "rb")) if os.path.exists(fivef) else None
if forced:
    tag += f"x{len(forced)}"
solf = f"sol2_k{k}{tag}_r{nrel}.pkl"
if os.path.exists(solf):
    sol = pickle.load(open(solf, "rb"))
else:
    sol = solve_all(F, cov, nrel, forced=forced)
    pickle.dump(sol, open(solf, "wb"))

# Extract 190 high control vectors and base vectors to minimize dim(R)!
z = sol["z"]
n = len(cov)
ctrl = [0] * (2 * n)
for y in range(F.ny):
    zy = int(z[y])
    for j in range(2 * n):
        if (zy >> j) & 1:
            ctrl[j] |= (1 << y)

base_vecs = [(1 << F.ny) - 1]
for t in range(len(F.Y)):
    v = 0
    for y in range(F.ny):
        if F.ybits[t][y]:
            v |= (1 << y)
    base_vecs.append(v)
for f in F.tagf:
    v = 0
    for y in range(F.ny):
        if f[y]:
            v |= (1 << y)
    base_vecs.append(v)

coef = coef_vectors(cov, F.NX)
masks = {}
for y in range(F.ny):
    if len(F.carex[y]) < F.nx:
        masks.setdefault(F.carex[y], F.care_mask(y))
big = max(len(R) for R in masks)
Rb = [m for R, m in masks.items() if len(R) == big]
def nz(i):
    return sum(1 for j in (2 * i, 2 * i + 1) for m in Rb if coef[j] & m)

rng = random.Random(seed * 10007 + 13)
best_order = None
best_dR = 999
best_dK = 999
for trial in range(1500):
    o = sorted(range(n), key=lambda i: (nz(i), rng.random()))
    E_set = set(o[:e])
    if not all(Ech([coef[j] & m for j in range(2 * n) if j // 2 not in E_set]).n >= 30 * (len(R) - 1) for R, m in masks.items()):
        continue
    R_vecs = base_vecs + [ctrl[j] for i in range(n) if i not in E_set for j in (2 * i, 2 * i + 1)]
    dR = Ech(R_vecs).n
    if dR < best_dR:
        K_vecs = base_vecs + [ctrl[j] for i in E_set for j in (2 * i, 2 * i + 1)]
        dK = Ech(K_vecs).n
        best_dR = dR
        best_dK = dK
        first = o[:e]
        rest = o[e:]
        rng.shuffle(first)
        rng.shuffle(rest)
        best_order = first + rest
        if dR <= 142:
            break

print(f"[V75-MINR] k={k} e={e} seed={seed}: selected early_order with dim(R)={best_dR} (dim(K_early)={best_dK}, max_keep_bound={93+best_dR-146})", flush=True)

B = Builder2(k, F, cov, sol, seed=seed)
B.p1seed = seed
B.extra_rows = 0
B.eager_tail = True
orig = B.phase1
B.phase1 = lambda o, ee: orig(o, ee, p1seed=seed, limit=limit)
B.run(e=e, order=best_order)
bad, _ = check_function(F, cov, B.sol)
assert bad == 0
sp = B.spec()
print("spec built; toffoli", sp.toffoli, "cache", sp.toffoli - len(cov), "chips", len(cov), f"({time.time()-t0:.0f}s)", flush=True)
bk = K.Bank(k)
res = K.evaluate(sp, bk)
print("evaluate ok", res.ok, "toffoli", res.toffoli, "peak width", res.peak_width, res.violations[:5], f"({time.time()-t0:.0f}s)", flush=True)
if res.ok:
    sp.save(f"spec_v75_231_k{k}_s{seed}.json")
    kmb = K.emit(sp, bk, template=FAM / f"angle_k_{k}.kmb", check=False)
    out = f"best231_v75_angle_k_{k}_s{seed}.kmb"
    sha = K.write_kmb(kmb, out)
    print("emitted", out, "sha", sha[:16], "ops", len(kmb.ops), flush=True)
    v = K.verify_kmb(out, k, direction="forward" if k == 0 else "both")
    print("VERIFY_KMB:", v, flush=True)
