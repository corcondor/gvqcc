# Screen choices of the pair relation (support and free values of z_y1) for the lowest boundary pressure.
# usage: screen_pair.py k cover_f1.pkl nsamples e
import sys, os, pickle, random, time
from frame import *
from solve2 import solve_all, coef_vectors
from solve3 import solve_pair
from minconn import chip_rows, lam, completion_ok
from gf2 import Ech

k = int(sys.argv[1]); cover_file = sys.argv[2]; N = int(sys.argv[3]); e = int(sys.argv[4])
F = Frame(k)
cov = pickle.load(open(cover_file, 'rb'))
forced = pickle.load(open(cover_file.replace('.pkl', '.five.pkl'), 'rb'))
five = [y for y in range(F.ny) if len(F.carex[y]) == 5]
pair = tuple([y for y in five if y not in forced][:2])
basef = f'base_k{k}_{os.path.basename(cover_file)[:-4]}.pkl'
if os.path.exists(basef):
    base = pickle.load(open(basef, 'rb'))
else:
    base = solve_all(F, cov, 13, forced=forced)
    pickle.dump(base, open(basef, 'wb'))
coef = coef_vectors(cov, F.NX)
masks = {}
for y in range(F.ny):
    if len(F.carex[y]) < F.nx:
        masks.setdefault(F.carex[y], F.care_mask(y))
n = len(cov)
best = None
t0 = time.time()
for ps in range(N):
    sol = solve_pair(F, cov, 13, pair, seed=1000 + ps, forced=forced, verbose=False, base=base)
    rows, brows = chip_rows(F, sol)
    total = Ech(brows + rows).n
    rng = random.Random(ps)
    Rb = [m for R, m in masks.items() if len(R) == max(len(R) for R in masks)]
    nz = {i: sum(1 for j in (2 * i, 2 * i + 1) for m in Rb if coef[j] & m) for i in range(n)}
    E = None
    for t in range(200):
        cand = set(sorted(range(n), key=lambda i: (nz[i], rng.random()))[:e])
        if completion_ok(F, cov, cand, n, coef, masks):
            E = cand
            break
    val = lam(rows, brows, E, n, total)
    for it in range(1500):
        i = rng.choice(sorted(E)); j = rng.choice([x for x in range(n) if x not in E])
        new = (E - {i}) | {j}
        v = lam(rows, brows, new, n, total)
        if (v[0], v[2]) <= (val[0], val[2]) and completion_ok(F, cov, new, n, coef, masks):
            E, val = new, v
    if best is None or val[0] < best[0]:
        best = (val[0], 1000 + ps)
        pickle.dump(sol, open(f'sol3_k{k}_{os.path.basename(cover_file)[:-4]}_p{1000 + ps}.pkl', 'wb'))
    print(f'pair sample {ps}: boundary measure {val[0]} (rank rest {val[2]}, total {total}); best {best[0]} (seed {best[1]}) ({time.time() - t0:.0f}s)', flush=True)
