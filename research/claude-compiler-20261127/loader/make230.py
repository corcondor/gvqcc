# 230-Toffoli head: 13 four-care relations + one forced five-care column (from the cover) + one relation tying the
# other two five-care columns (solve3.solve_pair).  LAZY=1 delays one low-bit product (one more wire early on).
# MC=R chooses the early chips with the smallest span of the remaining rows (after V75).
# usage: make230.py k cover_f1.pkl e seed [p1limit]
import sys, os, pickle, time, random
from common import *
from frame import *
from solve import check_function
from solve2 import coef_vectors
from solve3 import solve_pair
from lazy import LazyBuilder
from build3 import Builder3
from wcount import subspaces, plan_for, count
from minconn import early_set, completion_ok
from order_util import early_order

k = int(sys.argv[1]); cover_file = sys.argv[2]; efl = float(sys.argv[3]); e = int(efl)
seed = int(sys.argv[4]); limit = float(sys.argv[5]) if len(sys.argv) > 5 else 0
LAZY = os.environ.get('LAZY', '1') == '1'
t0 = time.time()
F = Frame(k)
cov = pickle.load(open(cover_file, 'rb'))
forced = pickle.load(open(cover_file.replace('.pkl', '.five.pkl'), 'rb'))
five = [y for y in range(F.ny) if len(F.carex[y]) == 5]
pair = tuple([y for y in five if y not in forced][:2])
pairseed = int(os.environ.get('PAIRSEED', str(seed)))
solf = f'sol3_k{k}_{os.path.basename(cover_file)[:-4]}_p{pairseed}.pkl'
if os.path.exists(solf):
    sol = pickle.load(open(solf, 'rb'))
else:
    sol = solve_pair(F, cov, 13, pair, seed=pairseed, forced=forced)
    pickle.dump(sol, open(solf, 'wb'))
bad, _ = check_function(F, cov, sol)
assert bad == 0
assert sol['nrel'] == 15

coef = coef_vectors(cov, F.NX)
masks = {}
for y in range(F.ny):
    if len(F.carex[y]) < F.nx:
        masks.setdefault(F.carex[y], F.care_mask(y))
rng = random.Random(seed)
if LAZY:
    plans = []
    for j, fs in subspaces():
        if j != 3:
            continue
        p = plan_for(j, fs)
        if p is None:
            continue
        w = count(cov, p[0])
        if len(w) >= e + 1:
            plans.append((len(w), fs, w, p))
    plans.sort(reverse=True)
    chosen = None
    for nw, fs, w, p in plans:
        for t in range(300):
            if completion_ok(F, cov, set(rng.sample(w, e)), len(cov), coef, masks):
                chosen = (fs, w, p)
                break
        if chosen:
            break
    assert chosen, 'no delayed product allows an all-compatible early set'
    fs, wchips, (early_plan, late_plan) = chosen
    print(f'delayed low product: hyperplane {fs}, {len(wchips)} compatible chips', flush=True)
    B = LazyBuilder(k, F, cov, sol, wchips, early_plan, late_plan, seed=seed)
    allowed = set(wchips)
else:
    B = Builder3(k, F, cov, sol, seed=seed)
    allowed = None
B.C1 = int(os.environ.get("C1", "78"))
B.p1seed = seed
B.extra_rows = 1 if efl - e > 0.25 else 0
B.allow_spill = os.environ.get('SPILL', '0') == '1'
B.allow_ccz = os.environ.get('CCZ', '1') == '1'
order = early_set(F, cov, sol, e, B.rng, iters=int(os.environ.get('MCITERS', '4000')), allowed=allowed)
if os.environ.get('ORDER') == 'beam':
    import beam_order
    orig_rr = B.run_rest

    def scheduled(o, verbose=True, t0=None):
        B.last_count = 0
        return orig_rr(beam_order.reorder(B, list(o), 0, seed), verbose, t0)
    B.run_rest = scheduled
orig = B.phase1
B.phase1 = lambda o, ee: orig(o, ee, p1seed=seed, limit=limit)
B.run(e=e, order=order)
bad, _ = check_function(F, cov, B.sol)
assert bad == 0
sp = B.spec()
print(f'built: spills {B.n_spill} cond-CCZ {B.n_ccz} remat {B.n_remat}', flush=True)
print('mean toffoli', sp.toffoli_like, flush=True)
print('spec built; toffoli', sp.toffoli, f'({time.time() - t0:.0f}s)', flush=True)
bk = K.Bank(k)
res = K.evaluate(sp, bk)
print('evaluate ok', res.ok, 'toffoli', res.toffoli, 'peak width', res.peak_width, res.violations[:5], f'({time.time() - t0:.0f}s)', flush=True)
if res.ok:
    sp.save(f'spec230_k{k}_s{seed}{"l" if LAZY else "p"}.json')
    kmb = K.emit(sp, bk, template=FAM / f'angle_k_{k}.kmb', check=False)
    out = f'angle_k_{k}_230_s{seed}{"l" if LAZY else "p"}.kmb'
    sha = K.write_kmb(kmb, out)
    print('emitted', out, 'sha', sha[:16], 'ops', len(kmb.ops), '230-HEAD', flush=True)
    v = K.verify_kmb(out, k, direction='forward' if k == 0 else 'both')
    print('verify:', v, f'({time.time() - t0:.0f}s)', flush=True)
