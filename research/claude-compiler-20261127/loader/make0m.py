# loader 0 with Builder3 (conditional CCZ phase terms + spill/rematerialise).  Same arguments as make0q.py,
# reuses the cached window search.  usage: make0r.py cover.pkl nrel e C1 seed limit trials nq nanch [first_trial]
import sys, os, pickle, time, copy, random
from common import *
from frame import *
from gf2 import *
from solve import check_function
from solve2 import solve_all
from build3 import Builder3
from order_util import early_order

cover_file = sys.argv[1]; nrel = int(sys.argv[2]); efl = float(sys.argv[3]); e = int(efl); C1 = int(sys.argv[4]); seed = int(sys.argv[5])
EXTRA = 1 if efl - e > 0.25 else 0
limit = float(sys.argv[6])
trials = int(sys.argv[7])
NQ = int(sys.argv[8])
NANCH = int(sys.argv[9])
first_trial = int(sys.argv[10]) if len(sys.argv) > 10 else 0
t0 = time.time()
k = 0
F = Frame(k)
cov = pickle.load(open(cover_file, 'rb'))
need_tags = [np.array([((int(F.G[0, y]) >> i1) & (int(F.G[0, y]) >> i2)) & 1 for y in range(F.ny)], np.uint8) for i1, i2 in TAGS]
tag = '' if len(cov) == 96 else f'_n{len(cov)}'
solf = f'sol2_k{k}{tag}_r{nrel}.pkl'
if os.path.exists(solf):
    sol = pickle.load(open(solf, 'rb'))
else:
    sol = solve_all(F, cov, nrel, need_tags=need_tags)
    pickle.dump(sol, open(solf, 'wb'))


class Stop(Exception):
    pass


B = Builder3(k, F, cov, sol, seed=seed)
B.C1 = C1
B.extra_rows = EXTRA
from minconn import early_set
order = early_set(F, cov, sol, e, B.rng, iters=int(os.environ.get('MCITERS', '4000')))
orig = B.phase1


def stop_at_anchors(o, ee):
    raise Stop


B.phase1 = lambda o, ee: orig(o, ee, p1seed=seed, limit=limit)
B.place_anchors = stop_at_anchors
B.low_products()
try:
    B.phase1(order, e)
except Stop:
    pass
del B.phase1, B.place_anchors
B.keep_always = [v for v, _ in B.live[:NQ]]
print(f'snapshot after the search and lift ({time.time() - t0:.0f}s); keeping the first {NQ} products; '
      f'recorded factors {len(B.factors)}', flush=True)
snap = copy.deepcopy(B)
order0 = list(order)

A = copy.deepcopy(snap)
A.rng = random.Random(7)
A.nanchors = NANCH
A.anchor_tries = 4000
oa = list(order0)
if NANCH:
    A.place_anchors(oa, e)
    anchors = list(A.anchors)
    last_count = A.last_count
else:
    anchors = []
    last_count = 0
print(f'anchors fixed ({len(anchors)}; {time.time() - t0:.0f}s)', flush=True)


def attempt(trial):
    B = copy.deepcopy(snap)
    rng = random.Random(1000 + trial)
    first, mid, last = list(oa[:e + EXTRA]), list(oa[e + EXTRA:len(oa) - last_count]), list(oa[len(oa) - last_count:])
    if trial:
        rng.shuffle(mid)
        rng.shuffle(last)
    o = first + mid + last
    B.rng = random.Random(trial)
    B.last_count = last_count
    import greedy_order
    o = greedy_order.reorder(B, o, e + EXTRA, trial)
    B.anchors = list(anchors)
    B.prefer_closable = trial % 2 == 1
    B.run_rest(o, verbose=False)
    return B


best = None
for trial in range(first_trial, first_trial + trials):
    try:
        B = attempt(trial)
    except (RuntimeError, AssertionError) as ex:
        print(f'trial {trial}: {str(ex)[:90]} ({time.time() - t0:.0f}s)', flush=True)
        continue
    sp = B.spec()
    cost = sp.toffoli_like
    print(f'trial {trial}: closed  CCX {sp.toffoli}  cond-CCZ {B.n_ccz}  spills {B.n_spill}  remat {B.n_remat}'
          f'  mean Toffoli {cost} ({time.time() - t0:.0f}s)', flush=True)
    if best is None or cost < best[0]:
        best = (cost, trial, B, sp)
        sp.save(f'spec5_k{k}{tag}_r{nrel}_s{seed}_q{NQ}a{NANCH}.json')
if best is None:
    sys.exit(1)
cost, trial, B, sp = best
bad, _ = check_function(F, cov, B.sol); assert bad == 0


def present_bank(direction):
    bk = K.Bank(0, direction=direction)
    bk.present = [True] * len(bk.present)
    bk.present_mask = sum(1 << (1 + i) for i in range(len(bk.present)))
    return bk


bk = present_bank('forward')
res = K.evaluate(sp, bk, directions='forward')
rv, _ = K.check_functions(sp, present_bank('reverse'))
print('best trial', trial, 'mean Toffoli', cost, 'evaluate ok', res.ok, 'peak width', res.peak_width, res.violations[:5],
      'reverse function violations', rv[:5], flush=True)
if res.ok and not rv:
    kmb = K.emit(sp, bk, template=FAM / f'angle_k_{k}.kmb', check=False)
    out = f'angle_k_{k}{tag}_f{nrel}_s{seed}_q{NQ}a{NANCH}m.kmb'
    sha = K.write_kmb(kmb, out)
    print('emitted', out, 'sha', sha[:16], 'ops', len(kmb.ops), flush=True)
    w = K.load_words()
    v = K.verify_kmb(out, 0, words=w, direction='forward')
    print('verify forward:', v['status'], v['toffoli'], v['qubits'], flush=True)
    w2 = w.copy()
    w2[:, 0:5] = w[:, 0:5]
    w2[:, 5:10] = 0
    v2 = K.verify_kmb(out, 1, words=w2, direction='forward')
    print('verify reverse:', v2['status'], v2['toffoli'], v2['qubits'], flush=True)
