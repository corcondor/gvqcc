"""
V75 Mathematical Audit of the 91 + 2 = 93 > 92 Bottleneck on k=5 (14 relations, H=146).

Tests two exact routes to break dim(K cap R) + delta_rank <= 92:
  Route A (Shrink dim(R) <= 143):
    Search early-chip subsets E (size e=29, 30, 31) minimizing dim(R) where R is the span of all
    high-control vectors of the remaining (95 - e) chips plus the linear/tag base.
    If dim(R) <= 143, then dim(K cap R) = dim(K) + dim(R) - 146 <= 90, so 90 + 2 = 92 <= 92!
  Route B (Find a rank-1 residual chip):
    For any candidate early-chip set E (with K = span(E controls + linear base)), check if ANY
    remaining chip i not in E has residual rank <= 1 modulo K (so 91 + 1 = 92 <= 92!).
"""

import os
import pickle
import random
import sys
from pathlib import Path
import numpy as np

WORK = Path(r"c:\Users\81808\.openclaw\gvqcc_v2832\v71_heads_232_for_3275")
os.chdir(WORK)
os.environ["K8_NPZ"] = str(WORK / "words_3284.npz")
sys.path.insert(0, str(WORK))

from common import *
from frame import *
from gf2 import Ech
from solve2 import coef_vectors

k = 5
F = Frame(k)
cov = pickle.load(open("cover95_k5_5col.pkl", "rb"))
sol = pickle.load(open("sol2_k5_n95x1_r13.pkl", "rb"))

# Inspect sol structure!
print("sol keys:", list(sol.keys()))
z = sol["z"]
n = len(cov)  # 95
# Convert z[y] (bit j = control j at high value y) to 190 ints `ctrl[j]` (bit y = value at y)
ctrl = [0] * (2 * n)
for y in range(F.ny):
    zy = int(z[y])
    for j in range(2 * n):
        if (zy >> j) & 1:
            ctrl[j] |= (1 << y)

# Base linear + tag functions over F.ny
base_vecs = []
# const 1
base_vecs.append((1 << F.ny) - 1)
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

H_ech = Ech(base_vecs + ctrl)
print(f"Total high space dim(H) = {H_ech.n} (base={Ech(base_vecs).n}, 190 controls)")

# Check valid early-chip constraints (same as order_util.py)
coef = coef_vectors(cov, F.NX)
masks = {}
for y in range(F.ny):
    if len(F.carex[y]) < F.nx:
        masks.setdefault(F.carex[y], F.care_mask(y))
big = max(len(R) for R in masks)
Rb = [m for R, m in masks.items() if len(R) == big]
def nz(i):
    return sum(1 for j in (2 * i, 2 * i + 1) for m in Rb if coef[j] & m)

# Check how many chips have unique directions in H!
# Specifically, for each chip i, check dim(R) when chip i is removed, or greedy search for e=29, 30, 31!
rng = random.Random(42)
for e in (29, 30, 31, 32):
    best_dimR = 999
    best_cap = 999
    best_res1_cnt = 0
    best_valid = 0
    for trial in range(400):
        o = sorted(range(n), key=lambda i: (nz(i), rng.random()))
        E_set = set(o[:e])
        if not all(Ech([coef[j] & m for j in range(2 * n) if j // 2 not in E_set]).n >= 30 * (len(R) - 1) for R, m in masks.items()):
            continue
        best_valid += 1
        # Compute dim(R) = span(base_vecs + controls of chips NOT in E_set)
        R_vecs = base_vecs + [ctrl[j] for i in range(n) if i not in E_set for j in (2 * i, 2 * i + 1)]
        K_vecs = base_vecs + [ctrl[j] for i in E_set for j in (2 * i, 2 * i + 1)]
        dR = Ech(R_vecs).n
        Ke = Ech(K_vecs)
        dK = Ke.n
        # dim(K cap R) = dK + dR - H_ech.n
        dCap = dK + dR - H_ech.n
        # Count remaining chips with residual rank <= 1 mod K
        res1 = 0
        for i in range(n):
            if i in E_set:
                continue
            r0 = Ke.reduce(ctrl[2 * i])
            r1 = Ke.reduce(ctrl[2 * i + 1])
            if r0 == 0 or r1 == 0 or r0 == r1:
                res1 += 1
        if dR < best_dimR:
            best_dimR = dR
        if dCap < best_cap:
            best_cap = dCap
        if res1 > best_res1_cnt:
            best_res1_cnt = res1
    print(f"e={e:2d} (valid={best_valid:3d}/400): min dim(R)={best_dimR:3d}, min dim(K cap R)={best_cap:2d}, max rank<=1 remaining chips={best_res1_cnt:2d}")
