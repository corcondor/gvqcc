# Lazy low products ("call by need"): only some of the four low-bit products are live while the window is tight;
# the chips compatible with them run first, with one more free wire; the others are computed just before the first
# chip that needs them.  The low-product handling follows heads/build3.py; spill/rematerialise and the conditional
# CCZ closure come from build3.Builder3.
import time
from common import *
from frame import *
from gf2 import *
from build3 import Builder3
from lowplan import ONE, X0, X1, X2, express


def mono_table(m):
    return sum(1 << x for x in range(8) if (x & m) == m)


class LazyBuilder(Builder3):
    def __init__(self, k, F, cov, sol, wchips, early_plan, late_plan, seed=1):
        super().__init__(k, F, cov, sol, seed=seed)
        self.wchips = set(wchips)
        self.early_plan = early_plan
        self.late_plan = late_plan
        base = self.cap - 78
        self.cap_full = base + 78
        self.cap = base + 82 - len(early_plan)
        self.C1 = self.cap - len(self.free)
        self.late_done = False
        self.low_events = []

    def low_products(self):
        X = self.F.X
        self.low_forms = {1: 1 << (1 + X[0]), 2: 1 << (1 + X[1]), 4: 1 << (1 + X[2])}
        self.low_basis = [(ONE, 1), (X0, 1 << (1 + X[0])), (X1, 1 << (1 + X[1])), (X2, 1 << (1 + X[2]))]
        for L, M in self.early_plan:
            self.low_and(L, M)

    def low_and(self, L, M):
        fl = express(self.low_basis, L)
        fm = express(self.low_basis, M)
        assert fl is not None and fm is not None
        sym = self.ev_compute(fl, fm, 'O')           # 'O' so it is not recorded as a rematerialisable cache value
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
        print(f'  late low products computed after {self.chips_done} chips', flush=True)
        for L, M in self.late_plan:
            self.low_and(L, M)
        assert all(m in self.low_forms for m in range(1, 8))
        self.late_done = True

    # compute the late products just before the first chip that needs them
    def before_chip(self, i, needed):
        if not self.late_done and i not in self.wchips:
            self.late_lows(needed)

    # anchor supports go last; among the others keep the compatible chips first
    def place_anchors(self, order, e):
        if self.nanchors == 0:                    # no anchors: the end is closed with conditional CCZ instead
            self.anchors, self.last_count = [], 0
        else:
            super().place_anchors(order, e)
        n = len(order)
        last = getattr(self, 'last_count', 0) or 0
        head = e + (1 if self.extra_rows else 0)
        mid = order[head:n - last]
        order[head:n - last] = [i for i in mid if i in self.wchips] + [i for i in mid if i not in self.wchips]

    def final_releases(self):
        if not self.late_done:
            self.late_lows([])
        super().final_releases()
