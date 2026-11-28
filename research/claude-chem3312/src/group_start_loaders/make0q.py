# loader 0: no separately kept tags.  The tags are ordinary members of the needed space; instead the first `nq`
# products of the window search (built from the address bits only, hence closable) are kept to the end, so that the
# final releases close.  Retries after the (cached) search vary anchors and release randomness.
# usage: make0q.py cover.pkl nrel e C1 seed limit [trials] [nq] [nanch]
import sys, os, pickle, time, copy, random
from common import *
from frame import *
from gf2 import *
from solve import check_function
from solve2 import solve_all
from build2 import Builder2
from order_util import early_order

cover_file = sys.argv[1]; nrel = int(sys.argv[2]); e = int(sys.argv[3]); C1 = int(sys.argv[4]); seed = int(sys.argv[5])
limit = float(sys.argv[6])
trials = int(sys.argv[7]) if len(sys.argv) > 7 else 6
NQ = int(sys.argv[8]) if len(sys.argv) > 8 else 5
NANCH = int(sys.argv[9]) if len(sys.argv) > 9 else 2
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


B = Builder2(k, F, cov, sol, seed=seed)
B.C1 = C1
order = early_order(F, cov, e, B.rng)
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
print(f'snapshot after the search and lift ({time.time() - t0:.0f}s); keeping the first {NQ} products', flush=True)
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
    first, mid, last = list(oa[:e]), list(oa[e:len(oa) - last_count]), list(oa[len(oa) - last_count:])
    if trial:
        rng.shuffle(mid)
        rng.shuffle(last)
    o = first + mid + last
    B.rng = random.Random(trial)
    B.anchors = list(anchors)
    B.prefer_closable = trial % 2 == 1
    B.run_rest(o, verbose=False)
    return B


found = None
for trial in range(trials):
    try:
        found = attempt(trial)
        print(f'trial {trial}: closed ({time.time() - t0:.0f}s)', flush=True)
        break
    except (RuntimeError, AssertionError) as ex:
        print(f'trial {trial}: {str(ex)[:100]} ({time.time() - t0:.0f}s)', flush=True)
if found is None:
    sys.exit(1)
B = found
bad, _ = check_function(F, cov, B.sol); assert bad == 0
sp = B.spec()
print('spec built; toffoli', sp.toffoli, 'cache', sp.toffoli - len(cov), 'chips', len(cov), f'({time.time() - t0:.0f}s)', flush=True)


def present_bank(direction):
    bk = K.Bank(0, direction=direction)
    bk.present = [True] * len(bk.present)
    bk.present_mask = sum(1 << (1 + i) for i in range(len(bk.present)))
    return bk


bk = present_bank('forward')
res = K.evaluate(sp, bk, directions='forward')
rv, _ = K.check_functions(sp, present_bank('reverse'))
print('evaluate ok', res.ok, 'toffoli', res.toffoli, 'peak width', res.peak_width, res.violations[:5], 'reverse function violations', rv[:5],
      f'({time.time() - t0:.0f}s)', flush=True)
if res.ok and not rv:
    sp.save(f'spec2_k{k}{tag}_r{nrel}_s{seed}q.json')
    kmb = K.emit(sp, bk, template=FAM / f'angle_k_{k}.kmb', check=False)
    out = f'angle_k_{k}{tag}_f{nrel}_s{seed}q.kmb'
    sha = K.write_kmb(kmb, out)
    print('emitted', out, 'sha', sha[:16], 'ops', len(kmb.ops), f'({time.time() - t0:.0f}s)', flush=True)
    w = K.load_words()
    v = K.verify_kmb(out, 0, words=w, direction='forward')
    print('verify forward:', v['status'], v['toffoli'], v['qubits'], flush=True)
    # reverse pass: batch 0 in the word registers on entry, zero on exit (verified as "bank 1" of a rearranged table)
    w2 = w.copy()
    w2[:, 0:5] = w[:, 0:5]
    w2[:, 5:10] = 0
    v2 = K.verify_kmb(out, 1, words=w2, direction='forward')
    print('verify reverse:', v2['status'], v2['toffoli'], v2['qubits'], f'({time.time() - t0:.0f}s)', flush=True)
    if v['status'].startswith('PASS') and v2['status'].startswith('PASS'):
        print('BOTH PASS')
