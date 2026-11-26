"""Block-2 targets with planted low-rank elements of R-perp (own-batch dead flips + block-1 steering pay for them).
usage: python planted_targets.py DESIGN_TAG BASE_WORDS BANK BATCH NEED KIND COUNT [SEED]
 KIND: r1 (k rank-1 elements s_j x^T sharing x) or r2 (k rank-2 elements s_j x1^T + s'_j x2^T on one pair)
Writes planner/designs/<tag>/plant_*.txt (+.ten) and adds them to inst/manifest.json (status open)."""
import json, os, random, sys, time
from pathlib import Path
import numpy as np
from design import *
from inst import Instance
from export_inst import add

tag, base_words, k, batch, need, kind, count = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), sys.argv[6], int(sys.argv[7])
seed = int(sys.argv[8]) if len(sys.argv) > 8 else 1
rng = random.Random(seed)
d = HERE / "designs" / tag
des = json.load(open(d / "design.json"))
blk1 = des["blocks_outputs"][0]
names = []
for g in blk1:
    n = g.bit_length() - 1
    names.append(f"s{n//7}b{n%7}")
D = Design(k, names, f"plant_{tag}", words=np.load(base_words) if base_words != "-" else None, seed=seed)
for pj in des["prods"]:
    pr = Prod.from_json(pj)
    if pr.block == 1:
        c0 = pr.coef.get("0", pr.coef.get(0, 0))
        D.prods.append(Prod(pr.alpha, pr.beta, pr.q1, pr.q2, {0: c0}, 1))
D.blocks_outputs = [D.B1]
D.check_block(1, D.B1, 0)
prior = list(range(len(D.prods)))
flips = D.flip_list([batch], D.B1)
zc = D.zeta_candidates(prior, flips, outputs_dim=8, top=40)
print("flips", len(flips), "best zeta margins", [(a, b) for a, b, c, z in zc[:4]], flush=True)
words_before = D.words.copy()
m = 8
nk = int(os.environ.get("PLANT_K", "1"))
made = 0
t0 = time.time()
tries = 0
while made < count and tries < 600 and time.time() - t0 < float(os.environ.get("MAXSEC", "240")):
    tries += 1
    marg, ra, cap, z = zc[tries % min(len(zc), 16)]
    B2 = D.random_subspace(m)
    D.words = words_before.copy()

    def lowf():
        while True:
            x = rng.randrange(1, 1 << 13)
            if x != z:
                return x
    x1 = lowf()
    x2 = lowf()
    while x2 in (x1, x1 ^ z):
        x2 = lowf()
    elements = []
    ss = []
    basis = {}
    for j in range(nk):
        while True:
            s = rng.randrange(1, 1 << m)
            s2 = rng.randrange(1, 1 << m) if kind == "r2" else 0
            if kind == "r2" and s2 == s:
                continue
            if ins(basis, s | (s2 << m)):
                break
        ss.append((s, s2))
        el = []
        for o in range(m):
            xf = (x1 if s >> o & 1 else 0) ^ (x2 if s2 >> o & 1 else 0)
            if xf:
                el.append((o, xf))
        elements.append(el)
    x, nvar = D.solve_with_flips(B2, flips, prior, z, elements)
    if x is None:
        continue
    nsteer = m * len(prior)
    D.apply_flips(flips, x >> nsteer)
    steer = [[prior[i] for i in range(len(prior)) if x >> (o * len(prior) + i) & 1] for o in range(m)]
    mats = D.target_mats(B2, steer)
    slices = block_slices13(mats)
    I = Instance(slices, m, zeta=z)
    name = f"plant_L{k}b2_{kind}x{nk}_n{need}_{tag}_{made}"
    kext = 2 * need - I.rankR
    I.write(name, kext, outdir=D.dir, meta={"zeta13": z, "x1": x1, "x2": x2, "s": ss, "batch": batch, "B2": B2,
                                             "steer": steer, "kind": kind, "count_planted": nk})
    np.save(D.dir / f"{name}.words.npy", D.words)
    add(name, D.dir / f"{name}.txt", k, 2, m, I.w, I.q, kext, need, "open", f"planted {nk} {kind} element(s) in R-perp",
        src_ten=D.dir / f"{name}.ten")
    print(f"made {name}: rankR {I.rankR} q {I.q} k {kext} (try {tries}, {time.time()-t0:.0f}s)", flush=True)
    made += 1
print("done", made, "tries", tries, f"{time.time()-t0:.0f}s")
