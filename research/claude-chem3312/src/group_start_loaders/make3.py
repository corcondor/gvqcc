# head loader with delayed low products.  usage: make3.py k cover.pkl nrel e npre seed [p1limit]
import sys, os, pickle, time, itertools
from common import *
from frame import *
from solve import check_function
from solve2 import solve_all
from build3 import Builder3, w_order, wchips_of
from lowplan import full_plan

NL = [3, 5, 6, 7]


def mono_table(m):
    return sum(1 << x for x in range(8) if (x & m) == m)


def best_plan(cov, npre):
    """the low subspace (3 early products, else 2) with the most compatible products that still leaves npre."""
    found = []
    for j in (2, 3):
        funcs = list(range(1, 16))
        subsets = [(f,) for f in funcs] if j == 3 else [c for c in itertools.combinations(funcs, 2)]
        for fs in subsets:
            ker = [v for v in range(1, 16) if all(bin(v & f).count('1') % 2 == 0 for f in fs)]
            targets = [mono_table(1), mono_table(2), mono_table(4)]
            for v in ker:
                t = 0
                for b in range(4):
                    if v >> b & 1:
                        t ^= mono_table(NL[b])
                targets.append(t)
            p = full_plan(j, targets)
            if p is None:
                continue
            w = wchips_of(cov, p[0])
            if len(w) >= npre:
                found.append((j, -len(w), p))
        if found:
            break
    if not found:
        return None
    found.sort(key=lambda t: (t[0], t[1]))
    j, nw, (early, late) = found[0]
    return early, late


if __name__ == '__main__':
    k = int(sys.argv[1]); cover_file = sys.argv[2]; nrel = int(sys.argv[3]); e = int(sys.argv[4]); npre = int(sys.argv[5])
    seed = int(sys.argv[6]); limit = float(sys.argv[7]) if len(sys.argv) > 7 else 0
    t0 = time.time()
    F = Frame(k)
    cov = pickle.load(open(cover_file, 'rb'))
    plan = best_plan(cov, npre)
    assert plan is not None, 'no low plan with enough products'
    early, late = plan
    wchips = wchips_of(cov, early)
    print(f'low plan: {len(early)} early + {len(late)} late products, {len(wchips)} compatible chips of {len(cov)}', flush=True)
    stem = os.path.splitext(os.path.basename(cover_file))[0]
    solf = f'sol3_{stem}_r{nrel}.pkl'
    if os.path.exists(solf):
        sol = pickle.load(open(solf, 'rb'))
    else:
        sol = solve_all(F, cov, nrel)
        pickle.dump(sol, open(solf, 'wb'))
    B = Builder3(k, F, cov, sol, wchips, early, late, seed=seed)
    B.npre = npre
    B.prefer_closable = False
    order = w_order(F, cov, e, wchips, npre, B.rng)
    orig = B.phase1
    B.phase1 = lambda o, ee: orig(o, ee, p1seed=seed, limit=limit)
    B.run(e=e, order=order)
    bad, _ = check_function(F, cov, B.sol); assert bad == 0
    sp = B.spec()
    print('spec built; toffoli', sp.toffoli, 'cache', sp.toffoli - len(cov), 'chips', len(cov), f'({time.time() - t0:.0f}s)', flush=True)
    bk = K.Bank(k)
    res = K.evaluate(sp, bk)
    print('evaluate ok', res.ok, 'toffoli', res.toffoli, 'peak width', res.peak_width, res.violations[:5], f'({time.time() - t0:.0f}s)', flush=True)
    if res.ok:
        tag = f'_n{len(cov)}w'
        sp.save(f'spec2_k{k}{tag}_r{nrel}_s{seed}.json')
        kmb = K.emit(sp, bk, template=FAM / f'angle_k_{k}.kmb', check=False)
        out = f'angle_k_{k}{tag}_f{nrel}_s{seed}.kmb'
        sha = K.write_kmb(kmb, out)
        print('emitted', out, 'sha', sha[:16], 'ops', len(kmb.ops), f'({time.time() - t0:.0f}s)', flush=True)
        v = K.verify_kmb(out, k, direction='forward' if k == 0 else 'both')
        print('verify:', v, f'({time.time() - t0:.0f}s)')
