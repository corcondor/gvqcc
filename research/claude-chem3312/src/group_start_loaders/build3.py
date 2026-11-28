# Builder with delayed low products: only len(early) low products are live while the window is tight; the chips used
# up to then (the first `npre`) have both low parts in the span of the early ones.  The other low products are
# computed just before the first chip that needs them, after the needed set has saturated.
import time
from common import *
from frame import *
from gf2 import *
from build2 import Builder2
from lowplan import ONE, X0, X1, X2, express, full_plan
from order_util import early_order
from solve2 import coef_vectors


def mono_table(m):
    return sum(1 << x for x in range(8) if (x & m) == m)


class Builder3(Builder2):
    def __init__(self, k, F, cov, sol, wchips, early_plan, late_plan, seed=1):
        super().__init__(k, F, cov, sol, seed=seed)
        self.wchips = set(wchips)
        self.early_plan = early_plan
        self.late_plan = late_plan
        base = self.cap - 78                      # number of free functions
        self.cap_full = base + 78
        self.cap = base + 82 - len(early_plan)    # only the early low products occupy ancillas at first
        self.C1 = self.cap - len(self.free)
        self.late_done = False
        self.low_events = []

    # ---- low products
    def low_products(self):
        X = self.F.X
        self.low_basis = [(ONE, 1), (X0, 1 << (1 + X[0])), (X1, 1 << (1 + X[1])), (X2, 1 << (1 + X[2]))]
        for L, M in self.early_plan:
            self.low_and(L, M)

    def low_and(self, L, M):
        fl = express(self.low_basis, L)
        fm = express(self.low_basis, M)
        assert fl is not None and fm is not None
        sym = self.ev_compute(fl, fm)
        self.low_basis.append((L & M, sym))
        self.low_events.append((fl, fm, sym))
        for m in range(1, 8):
            f = express(self.low_basis, mono_table(m))
            if f is not None:
                self.low_forms[m] = f

    def low_form(self, u):
        f = express(self.low_basis, u << 1)
        assert f is not None, 'low function not available yet'
        return f

    def low_release(self):
        for fl, fm, sym in reversed(self.low_events):
            self.events.append(K.Event('E', row=sym))
            self.events.append(K.Event('P', mid=self.n_release, forms=(fl, fm)))
            self.n_release += 1

    def late_lows(self, needed):
        while Ech([v for v, _ in self.L_elems()]).n > self.cap_full:
            self.release_one(needed)
        self.cap = self.cap_full
        for L, M in self.late_plan:
            self.low_and(L, M)
        assert all(m in self.low_forms for m in range(1, 8))
        self.late_done = True

    # ---- main loop (as Builder.run, with the late low products inserted before the first chip that needs them)
    def run(self, e=24, order=None, verbose=True):
        n = len(self.cov)
        t0 = time.time()
        self.low_forms = {1: 1 << (1 + self.F.X[0]), 2: 1 << (1 + self.F.X[1]), 4: 1 << (1 + self.F.X[2])}
        self.low_products()
        self.phase1(order, e)
        if verbose:
            print(f'  phase1 done ({time.time() - t0:.0f}s): live dim {Ech([v for v, _ in self.L_elems()]).n}', flush=True)
        self.chipsym = {}
        dimH = Ech(self.H).n
        for t, i in enumerate(order):
            if not self.late_done and i not in self.wchips:
                needed = []
                for j in order[t:]:
                    needed += [self.zrows[2 * j], self.zrows[2 * j + 1]]
                self.late_lows(needed)
                if verbose:
                    print(f'  late low products before chip {t}', flush=True)
            for r in (self.zrows[2 * i], self.zrows[2 * i + 1]):
                if not self.in_live(r):
                    needed = []
                    for j in order[t:]:
                        needed += [self.zrows[2 * j], self.zrows[2 * j + 1]]
                    assert Ech([v for v, _ in self.computed]).reduce(r) != 0, 'recompute needed'
                    while Ech([v for v, _ in self.L_elems()]).n >= self.capacity():
                        self.release_one(needed)
                    self.compute_coset(r)
                    assert self.in_live(r)
            while Ech([v for v, _ in self.L_elems()]).n > self.capacity(extra_chip=1):
                needed = []
                for j in order[t:]:
                    needed += [self.zrows[2 * j], self.zrows[2 * j + 1]]
                self.release_one(needed)
            self.chipsym[i] = self.chip_event(i)
            self.chips_done += 1
        if not self.late_done:
            self.late_lows([])
        while Ech([v for v, _ in self.computed]).n < dimH:
            while Ech([v for v, _ in self.L_elems()]).n >= self.capacity():
                self.release_one([])
            ec = Ech([v for v, _ in self.computed])
            target = next(v for v in self.H if ec.reduce(v))
            self.compute_coset(target)
        assert Ech([v for v, _ in self.computed] + self.H).n == dimH
        self.final_releases()
        self.low_release()
        if verbose:
            print(f'  events {len(self.events)}, products {self.nprod}, releases {self.n_release} ({time.time() - t0:.0f}s)', flush=True)
        return order

    def place_anchors(self, order, e):
        # anchors over the non-early chips; their chips go last, and the prefix of W chips (up to npre) must
        # still be filled with W chips that are not part of any anchor
        from anchors import find_anchors
        n = len(order)
        nonE = order[e:]
        base = self.free + [(v, None) for v in self.keep_always]
        wn = frozenset(i for i in nonE if i in self.wchips)
        need = self.npre - e
        budget = len(wn) - need
        assert budget >= 0
        slots = n - self.npre
        best, minw, nf = find_anchors(self.zrows, nonE, base, self.ny, count=self.nanchors, tries=getattr(self, 'anchor_tries', 12000),
                                      limited=wn, budget=budget, maxsize=slots)
        assert best is not None and best[0] <= slots, f'no anchor fits: {best and best[0]} (W budget {budget}, slots {slots})'
        union = best[2]
        wfree = [i for i in nonE if i in wn and i not in union]
        mid = wfree[:need]
        rest = [i for i in nonE if i not in union and i not in set(mid)]
        last = [i for i in nonE if i in union]
        order[e:] = mid + rest + last
        self.anchors = [c[2] for c in best[1]]
        self.last_count = len(union)
        print(f'  anchors: {len(self.anchors)} sparse closable combinations, supports on the last {len(last)} chips ({len(union & wn)} of them W; budget {budget}; {nf} candidates, min support {minw})', flush=True)


def w_order(F, cov, e, wchips, npre, rng, tries=2000):
    """first e chips: W chips satisfying the free-column completability test; then W chips up to npre; then the rest."""
    coef = coef_vectors(cov, F.NX)
    masks = {}
    for y in range(F.ny):
        if len(F.carex[y]) < F.nx:
            masks.setdefault(F.carex[y], F.care_mask(y))
    n = len(cov)
    big = max(len(R) for R in masks)
    Rb = [m for R, m in masks.items() if len(R) == big]
    wl = sorted(wchips)
    assert len(wl) >= npre, ('not enough W chips', len(wl), npre)

    def nz(i):
        return sum(1 for j in (2 * i, 2 * i + 1) for m in Rb if coef[j] & m)

    for t in range(tries):
        o = sorted(wl, key=lambda i: (nz(i), rng.random()))
        E = set(o[:e])
        if all(Ech([coef[j] & m for j in range(2 * n) if j // 2 not in E]).n >= 30 * (len(R) - 1) for R, m in masks.items()):
            first = o[:e]
            rng.shuffle(first)
            others = o[e:]
            rng.shuffle(others)
            mid = others[:npre - e]
            rest = others[npre - e:] + [i for i in range(n) if i not in wchips]
            rng.shuffle(rest)
            return first + mid + rest
    raise RuntimeError('no suitable early chip set')


def wchips_of(cov, early_plan):
    basis = [(ONE, 1), (X0, 2), (X1, 4), (X2, 8)] + [(L & M, 1 << (4 + t)) for t, (L, M) in enumerate(early_plan)]
    return [i for i, (s, U) in enumerate(cov) if all(express(basis, u << 1) is not None for u in U)]
