"""Block 2 without zero column on 8 outputs, 13-dim low (45 products, gs2, q=29): for 24-output loaders that have no
free dead words.  Blocks 1 must exist.  usage: python block2gs.py BANK TAG BLOCK1 SEED WORDS NPAR MAXATT"""
import json, os, random, subprocess, sys, time
from pathlib import Path
import numpy as np
from design import *
from inst import Instance, write_gs2
from planes import all_planes, plane_vectors, parity_rank

k = int(sys.argv[1]); tag = sys.argv[2]; block1 = sys.argv[3].split(","); seed = int(sys.argv[4])
words = np.load(sys.argv[5]); npar = int(sys.argv[6]); maxatt = int(sys.argv[7])
NEED = 45
BEAM = int(os.environ.get("BEAM", "1000"))
D = Design(k, block1, tag, words=words, seed=seed)
D.block1()
prior = list(range(len(D.prods)))
Prow = [[D.prods[i].slice13(p) for p in range(75)] for i in prior]
t0 = time.time()


def attempt(j):
    rng = random.Random(seed * 100 + j)
    D.rng = rng
    B2 = D.random_subspace(8)
    mats = D.target_mats(B2, [[] for _ in range(8)])
    I = Instance(block_slices13(mats), 8)
    k_ext = 2 * NEED - I.rankR
    name = f"{tag}_b2g{j}"
    I.write(name, k_ext, outdir=D.dir)
    write_gs2(I, D.dir / f"{name}.gs2")
    env = dict(os.environ, DUMP="30")
    out = open(D.dir / f"{name}.gs2.out", "w")
    p = subprocess.Popen([str(GS2), str(D.dir / f"{name}.gs2"), str(k_ext), str(BEAM), "60", "4", "10", str(31 + j),
                          "100000", "0.2", "1"], stdout=out, stderr=subprocess.DEVNULL, env=env)
    return dict(j=j, B2=B2, I=I, name=name, proc=p, slices=block_slices13(mats), t0=time.time())


def collect(att):
    I = att["I"]
    states = []
    for line in open(D.dir / f"{att['name']}.gs2.out"):
        if line.startswith("STATE "):
            a = list(map(int, line.split()[1:]))
            states.append((a[1], a[0], a[2:]))
    states.sort(key=lambda s: (-s[0], -s[1]))
    rng = random.Random(att["j"])
    for IL, L, E in states[:20]:
        if L < NEED:
            continue
        planes = all_planes(I, E)
        if parity_rank([plane_vectors(I, p, 8) for p in planes], rng) < NEED:
            continue
        res = D.select_min_bad(I, planes, NEED, 8, D.z3)
        if res is None:
            continue
        nbad, sel = res
        al, be = solve_coeffs(I, att["slices"], sel, 8)
        prods2 = [Prod(a, b, lift_low(q1, I), lift_low(q2, I), {1: c}, 2) for (c, q1, q2), a, b in zip(sel, al, be)]
        rows = Prow + [[pr.slice13(p) for p in range(75)] for pr in prods2]
        zlist = [D.z3] + [rng.randrange(1, 1 << 13) for _ in range(400)]
        z3 = next((z for z in zlist if D.col_rank(rows, z) == 75), None)
        print(f"   attempt {att['j']}: state IL={IL} L={L}: {len(planes)} lines, {nbad} in ker(z3), block-3 functional {'found' if z3 else 'not found'}", flush=True)
        if z3 is None:
            continue
        D.prods += prods2
        D.blocks_outputs.append(att["B2"])
        D.z3 = z3
        D.check_block(2, att["B2"], 1)
        D.check_block(1, D.B1, 0)
        return True
    return False


running = []
nxt = 0
done = False
while not done and (running or nxt < maxatt):
    while len(running) < npar and nxt < maxatt:
        running.append(attempt(nxt))
        nxt += 1
    time.sleep(2)
    for att in list(running):
        if att["proc"].poll() is None:
            continue
        running.remove(att)
        ok = collect(att)
        print(f"attempt {att['j']} finished after {time.time()-att['t0']:.0f}s: {'SOLVED' if ok else 'no'}", flush=True)
        if ok:
            for other in running:
                other["proc"].kill()
            running = []
            D.save()
            done = True
            break
print("done" if done else "no attempt solved", f"{time.time()-t0:.0f}s")
sys.exit(0 if done else 1)
