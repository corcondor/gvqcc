"""Finish block 3 of a partial design (blocks 1,2 done) with several independent attempts:
each attempt = fresh random steering solution -> gs2 (9 outputs) or the engine (8 outputs) -> exact selection.
usage: python block3.py TAG NPARALLEL MAXATTEMPTS [BEAM]"""
import json, os, random, subprocess, sys, time
from pathlib import Path
import numpy as np
from design import *
from inst import Instance, write_gs2
from planes import all_planes, plane_vectors, select_exact
from solve import solve_system

tag = sys.argv[1]
npar = int(sys.argv[2])
maxatt = int(sys.argv[3])
beam = int(sys.argv[4]) if len(sys.argv) > 4 else 1500
d = HERE / "designs" / tag
des = json.load(open(d / "design.json"))
assert len(des["blocks_outputs"]) == 2, "need a design with blocks 1 and 2"
k = des["k"]
names = [f"s{(g.bit_length()-1)//7}b{(g.bit_length()-1)%7}" for g in des["blocks_outputs"][0]]
D = Design(k, names, tag, words=np.load(d / "words.npy"), seed=1)
D.words_in = np.load(d / "words_in.npy") if (d / "words_in.npy").exists() else D.words.copy()
for pj in des["prods"]:
    pr = Prod.from_json(pj)
    pr.coef = {int(a): b for a, b in pr.coef.items()}
    D.prods.append(pr)
D.blocks_outputs = [des["blocks_outputs"][0], des["blocks_outputs"][1]]
D.zeta2 = des.get("zeta2")
for bi, outs in enumerate(D.blocks_outputs):
    D.check_block(bi + 1, outs, bi)
B2 = D.blocks_outputs[1]
basis = {}
for g in D.B1 + D.Z + B2:
    ins(basis, g)
B3 = [g for g in D.comp if ins(basis, g)]
m = len(B3)
need = {7: 38, 8: 42, 9: 47}[m]
prior = list(range(len(D.prods)))
Prow = [[D.prods[i].slice13(p) for p in range(75)] for i in prior]


def col_rank(z):
    b = {}
    r = 0
    for pr in Prow:
        col = 0
        for p in range(75):
            if parity(pr[p] & z):
                col |= 1 << p
        r += ins(b, col)
    return r


good_z = []
t0 = time.time()
for z in random.Random(5).sample(range(1, 1 << 13), 8191):
    if col_rank(z) >= 75:
        good_z.append(z)
        if len(good_z) >= 12:
            break
print(f"block 3: m={m} need {need}; zeta with full column rank found: {len(good_z)} ({time.time()-t0:.0f}s)", flush=True)


def make_attempt(j):
    rng = random.Random(1000 + j)
    z = good_z[j % len(good_z)]
    eqs, nvar = D.zero_system(B3, [], prior, z)
    rk, x, nd = solve_system(eqs, nvar, rng)
    assert x is not None
    steer = [[prior[i] for i in range(len(prior)) if x >> (o * len(prior) + i) & 1] for o in range(m)]
    mats = D.target_mats(B3, steer)
    I = Instance(block_slices13(mats), m, zeta=z)
    k_ext = 2 * need - I.rankR
    name = f"{tag}_b3a{j}"
    I.write(name, k_ext, outdir=d, meta={"zeta13": z})
    return dict(j=j, z=z, steer=steer, I=I, k_ext=k_ext, name=name, slices=block_slices13(mats))


def launch(att):
    if m <= 8:
        cmd = [str(ENG), "beam", str(d / f"{att['name']}.txt"), "--width", "8000", "--weights", "0,1,6,14,26", "--jitter", "6",
               "--threads", "1", "--seed", str(att["j"] + 1), "--maxsec", "200", "--out", str(d / f"{att['name']}.res")]
        if (d / f"{att['name']}.res").exists():
            (d / f"{att['name']}.res").unlink()
        return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    write_gs2(att["I"], d / f"{att['name']}.gs2")
    out = open(d / f"{att['name']}.gs2.out", "w")
    env = dict(os.environ, DUMP="30")
    return subprocess.Popen([str(GS2), str(d / f"{att['name']}.gs2"), str(att["k_ext"]), str(beam), "60", "4", "12",
                             str(11 + att["j"]), "100000", "0.2", "1"], stdout=out, stderr=subprocess.DEVNULL, env=env)


def collect(att):
    rng = random.Random(att["j"])
    I = att["I"]
    if m <= 8:
        res = d / f"{att['name']}.res"
        if not res.exists():
            return None
        states = []
        for line in open(res):
            if line.startswith("E "):
                head, vals = line.split(":")
                nu = int(head.split()[1].split("=")[1])
                states.append((nu, [int(v) for v in vals.split()]))
    else:
        states = []
        for line in open(d / f"{att['name']}.gs2.out"):
            if line.startswith("STATE "):
                a = list(map(int, line.split()[1:]))
                states.append((a[1], a[2:]))
            elif line.startswith("E "):
                states.append((0, list(map(int, line.split()[1:]))))
            elif line.startswith("BEST"):
                print(f"   attempt {att['j']}: gs2 {line.strip()}", flush=True)
        states.sort(key=lambda s: -s[0])
    # gs2's greedy line count is only a lower bound: test every promising state with the exact parity rank
    for nu, E in states[:30]:
        if nu and nu < need - 2:
            continue
        planes = all_planes(I, E)
        if len(planes) < need:
            continue
        vecs = [plane_vectors(I, pl, m) for pl in planes]
        sel = select_exact(vecs, need, rng)
        if sel is not None:
            return [planes[i] for i in sel]
    return None


def complete(att, prods):
    I = att["I"]
    al, be = solve_coeffs(I, att["slices"], prods, m)
    for o in range(m):
        for i in att["steer"][o]:
            D.prods[i].coef[2] = D.prods[i].coef.get(2, 0) | (1 << o)
    for (c, q1, q2), a, b in zip(prods, al, be):
        D.prods.append(Prod(a, b, lift_low(q1, I), lift_low(q2, I), {2: c}, 3))
    D.blocks_outputs.append(B3)
    D.zeta3 = att["z"]
    for bi, outs in enumerate(D.blocks_outputs):
        D.check_block(bi + 1, outs, bi)
    D.save()


FINISH = os.environ.get("FINISH")
if FINISH is not None:
    for j in [int(v) for v in FINISH.split(",")]:
        old_txt = (d / f"{tag}_b3a{j}.txt").read_text()
        att = make_attempt(j)                        # deterministic: same functional, same steering
        assert (d / f"{tag}_b3a{j}.txt").read_text() == old_txt, "attempt not reproduced"
        prods = collect(att)
        print(f"finish attempt {j}: {'SOLVED' if prods else 'no'}", flush=True)
        if prods:
            complete(att, prods)
            print("done", f"{time.time()-t0:.0f}s")
            sys.exit(0)
    sys.exit(1)
running = []
nxt = 0
done = False
while not done and (running or nxt < maxatt):
    while len(running) < npar and nxt < maxatt:
        att = make_attempt(nxt)
        att["proc"] = launch(att)
        att["t0"] = time.time()
        running.append(att)
        nxt += 1
    time.sleep(2)
    for att in list(running):
        if att["proc"].poll() is None:
            continue
        running.remove(att)
        prods = collect(att)
        print(f"attempt {att['j']} finished after {time.time()-att['t0']:.0f}s: {'SOLVED' if prods else 'no'}", flush=True)
        if prods:
            for other in running:
                other["proc"].kill()
            running = []
            complete(att, prods)
            done = True
            break
print("done" if done else "no attempt solved", f"{time.time()-t0:.0f}s")
sys.exit(0 if done else 1)
