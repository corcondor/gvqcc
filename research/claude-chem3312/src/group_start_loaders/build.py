# Sliding-window loader builder for the new frame: events (compute / chip / measure+phase) -> k8lib Spec.
import numpy as np, subprocess, pickle, random, sys, os, time
from common import *
from frame import *
from gf2 import *
from solve import solve_relations, check_function, needed_rows
HERE = os.path.dirname(os.path.abspath(__file__))
P0 = K.P0


def ints_annih(vs, ny):
    piv = {}
    for v in vs:
        while v:
            h = v.bit_length() - 1
            if h in piv:
                v ^= piv[h]
            else:
                piv[h] = v
                break
    keys = sorted(piv)
    for h in keys:
        for h2 in keys:
            if h2 != h and (piv[h2] >> h) & 1:
                piv[h2] ^= piv[h]
    out = []
    for f in range(ny):
        if f not in piv:
            v = 1 << f
            for h, r in piv.items():
                if (r >> f) & 1:
                    v |= 1 << h
            out.append(v)
    return out


def par(x):
    return x.bit_count() & 1


def intersect(A, B, ny):
    return ints_annih(ints_annih(A, ny) + ints_annih(B, ny), ny)


class Builder:
    def __init__(self, k, F, cov, sol, seed=1):
        self.k = k
        self.F = F
        self.cov = cov
        self.sol = sol
        self.rng = random.Random(seed)
        self.ny = F.ny
        rows, hrows, lin = needed_rows(F, sol)
        self.zrows = rows
        self.hrows = hrows
        self.H = rows + hrows + lin
        self.annH = ints_annih(self.H, self.ny)
        self.events = []
        self.nprod = 0
        ones = (1 << self.ny) - 1
        free = [(ones, 1)]
        for t, b in enumerate(F.Y):
            v = sum(1 << y for y in range(self.ny) if F.ybits[t][y])
            free.append((v, 1 << (1 + b)))
        if k:
            for j, (i1, i2) in enumerate(TAGS):
                assert (i1 in F.Y) and (i2 in F.Y)
                v = sum(1 << y for y in range(self.ny) if F.tagf[j][y])
                free.append((v, (1 << (12 + 7 * j + 5)) | (1 << (12 + 7 * j + 6))))
        self.free = free
        self.live = []                      # list of (yfun, form)
        self.computed = list(free)          # all computed (yfun, form) incl free
        self.low_forms = {1: 1 << (1 + F.X[0]), 2: 1 << (1 + F.X[1]), 4: 1 << (1 + F.X[2])}
        self.cap = len(free) + 78
        self.chips_done = 0
        self.keep_always = []          # y-functions that must stay live to the end (loader 0 tags)
        self.anchors = []              # row combinations kept as needed until the final releases
        self.prefer_closable = False   # release non-closable elements first
        self.eager_tail = False        # after all functions exist, release unneeded non-closable ones at once
        self.nanchors = 2
        self.set_anchors = None        # (size, want): choose the last chips as a set holding `want` anchors
        self.hier_anchors = 0
        self.post_seed = None          # reseed after the phase-1 search (keeps its cached result valid)
        self.n_release = 0
        self.n_phase = 0

    # ---- events
    def ev_compute(self, L, M, kind='S'):
        self.events.append(K.Event(kind, L, M))
        sym = 1 << (P0 + self.nprod)
        self.nprod += 1
        return sym

    def add_live(self, yf, form):
        self.live.append((yf, form))
        self.computed.append((yf, form))

    def span_basis(self, elems):
        ce = CombEch()
        for i, (v, _) in enumerate(elems):
            d = ce.add(v, 1 << i)
            assert d is None, 'dependent basis'
        return ce

    def express(self, elems, ce, yf):
        c = ce.solve(yf)
        if c is None:
            return None
        form = 0
        i = 0
        while c:
            if c & 1:
                form ^= elems[i][1]
            c >>= 1
            i += 1
        return form

    def L_elems(self):
        return self.free + self.live

    def capacity(self, extra_chip=0):
        # maximum dim of free + live high functions (the word wires are never used as scratch)
        return self.cap

    # ---- low products
    def low_products(self):
        x0, x1, x2 = self.low_forms[1], self.low_forms[2], self.low_forms[4]
        p01 = self.ev_compute(x0, x1)
        p02 = self.ev_compute(x0, x2)
        p12 = self.ev_compute(x1, x2)
        p012 = self.ev_compute(p01, x2)
        self.low_forms.update({3: p01, 5: p02, 6: p12, 7: p012})

    def low_release(self):
        x0, x1, x2 = self.low_forms[1], self.low_forms[2], self.low_forms[4]
        for mono, (a, b) in [(7, (self.low_forms[3], x2)), (6, (x1, x2)), (5, (x0, x2)), (3, (x0, x1))]:
            self.events.append(K.Event('E', row=self.low_forms[mono]))
            self.events.append(K.Event('P', mid=self.n_release, forms=(a, b)))
            self.n_release += 1

    def low_form(self, u):
        # u: point-basis vector over x=1..7 (value at x = bit x-1); form of that function (zero at x=0)
        val = [0] + [(u >> (x - 1)) & 1 for x in range(1, 8)]
        c = val[:]
        for i in range(3):
            for m in range(8):
                if m >> i & 1:
                    c[m] ^= c[m ^ (1 << i)]
        assert c[0] == 0
        form = 0
        for m in range(1, 8):
            if c[m]:
                form ^= self.low_forms[m]
        return form

    # ---- phase fix: express w over products of basis elements
    def phase_terms(self, w, basis):
        assert basis[0][0] == (1 << self.ny) - 1
        items = basis[1:]
        ce = CombEch()
        cols = []

        def addcol(v, tag):
            idx = len(cols)
            cols.append(tag)
            ce.add(v, 1 << idx)

        addcol(basis[0][0], ('c',))
        for i, (v, _) in enumerate(items):
            addcol(v, ('l', i))
        c = ce.solve(w)
        i = 0
        while c is None:
            assert i < len(items) - 1, 'phase not expressible'
            for j in range(i + 1, len(items)):
                addcol(items[i][0] & items[j][0], ('p', i, j))
            i += 1
            c = ce.solve(w)
        const = 0
        lin = 0
        pairs = {}
        t = 0
        while c:
            if c & 1:
                tag = cols[t]
                if tag[0] == 'c':
                    const ^= 1
                elif tag[0] == 'l':
                    lin ^= items[tag[1]][1]
                else:
                    pairs[tag[1]] = pairs.get(tag[1], 0) ^ items[tag[2]][1]
            c >>= 1
            t += 1
        return const, lin, [(items[i][1], m) for i, m in pairs.items() if m]

    def release(self, rel, keep_elems):
        # rel: (yf, form) element leaving; keep_elems: remaining live list (free excluded)
        mid = self.n_release
        self.n_release += 1
        self.events.append(K.Event('E', row=rel[1]))
        const, lin, pairs = self.phase_terms(rel[0], self.free + keep_elems)
        for a, b in pairs:
            self.events.append(K.Event('P', mid=mid, forms=(a, b)))
            self.n_phase += 1
        if lin:
            self.events.append(K.Event('P', mid=mid, forms=(lin,)))
        if const:
            self.events.append(K.Event('P', mid=mid, forms=()))
        self.live = list(keep_elems)

    def release_one(self, needed_vecs):
        C = [v for v, _ in self.computed]
        needed_vecs = list(needed_vecs) + self.anchors
        keep_target = intersect(needed_vecs, C, self.ny) if needed_vecs else []
        elems = self.L_elems()
        ce = self.span_basis(elems)
        newfree = Ech([v for v, _ in self.free])
        kept = []
        for v in self.keep_always + keep_target:
            if newfree.add(v):
                f = self.express(elems, ce, v)
                assert f is not None, 'needed value was released'
                kept.append((v, f))
        if self.prefer_closable:
            # keep as much of the closure of the free set as possible (it makes the final releases close)
            total = Ech([v for v, _ in elems]).n
            for v in self.closure_in_live(elems, ce):
                if newfree.n >= total - 1:
                    break
                if newfree.add(v):
                    kept.append((v, self.express(elems, ce, v)))
        extra = []
        for v, f in self.live:
            if newfree.add(v):
                extra.append((v, f))
        assert extra, f'nothing to release: needed dim {len(kept) + len(self.free)}'
        i = self.rng.randrange(len(extra))
        rel = extra.pop(i)
        self.release(rel, kept + extra)

    def closure_in_live(self, elems, ce):
        # fixpoint: functions of span(elems) reachable from the free set (and kept tags) by degree-2 closure
        Z = [v for v, _ in elems]
        S = [v for v, _ in self.free]
        Sech = Ech(S)
        for v in self.keep_always:
            if Sech.add(v):
                S.append(v)
        clo = Ech(S)
        for i, a in enumerate(S):
            for b in S[i + 1:]:
                clo.add(a & b)
        out = []
        while True:
            inter = intersect(Z, list(clo.piv.values()), self.ny)
            new = [v for v in inter if Sech.reduce(v)]
            if not new:
                return out
            for v in new:
                if Sech.reduce(v) == 0:
                    continue
                for a in S:
                    clo.add(a & v)
                clo.add(v)
                S.append(v)
                Sech.add(v)
                out.append(v)

    def release_eagerly(self, needed_vecs):
        # release everything that is neither needed any more nor in the closure of the free set, while the other
        # live functions are still there to express its phase fix
        C = [v for v, _ in self.computed]
        needed_vecs = list(needed_vecs) + self.anchors
        keep_target = intersect(needed_vecs, C, self.ny) if needed_vecs else []
        while True:
            elems = self.L_elems()
            ce = self.span_basis(elems)
            total = len(elems)
            newfree = Ech([v for v, _ in self.free])
            kept = []
            for v in self.keep_always + keep_target + self.closure_in_live(elems, ce):
                if newfree.add(v):
                    f = self.express(elems, ce, v)
                    assert f is not None
                    kept.append((v, f))
            extra = []
            for v, f in self.live:
                if newfree.add(v):
                    extra.append((v, f))
            if not extra:
                return
            order = list(range(len(extra)))
            self.rng.shuffle(order)
            for i in order:
                rel = extra[i]
                rest = kept + extra[:i] + extra[i + 1:]
                if self.expressible(rel[0], self.free + rest):
                    self.release(rel, rest)
                    break
            else:
                return

    def expressible(self, w, basis):
        e = Ech([v for v, _ in basis])
        if e.reduce(w) == 0:
            return True
        items = basis[1:]
        for i, (v, _) in enumerate(items):
            for u, _ in items[i + 1:]:
                e.add(v & u)
            if e.reduce(w) == 0:
                return True
        return False

    # ---- compute a needed value r (mod live): product u*v = r (mod span live)
    def compute_coset(self, r):
        elems = self.L_elems()
        vecs = [v for v, _ in elems]
        ann = ints_annih(vecs, self.ny)
        rhs = [par(a & r) for a in ann]
        m = len(elems)
        ech = Ech(vecs)
        sb = self.span_basis(elems)
        for trial in range(20000):
            um = self.rng.getrandbits(m)
            u = 0
            for j in range(m):
                if um >> j & 1:
                    u ^= vecs[j]
            if not u:
                continue
            ub = [u & v for v in vecs]
            rows = []
            for a in ann:
                row = 0
                for j in range(m):
                    if (a & ub[j]).bit_count() & 1:
                        row |= 1 << j
                rows.append(row)
            sol = solve_linear(rows, rhs, m)
            if sol is None:
                continue
            part, null = sol
            vm = part
            for nv in null:
                if self.rng.random() < 0.5:
                    vm ^= nv
            v = 0
            for j in range(m):
                if vm >> j & 1:
                    v ^= vecs[j]
            f = u & v
            if ech.reduce(f) == 0:
                continue
            fu = self.express(elems, sb, u)
            fv = self.express(elems, sb, v)
            if fu in (0, 1) or fv in (0, 1) or (fu ^ fv) in (0, 1):
                continue
            sym = self.ev_compute(fu, fv)
            self.add_live(f, sym)
            return f
        raise RuntimeError('compute failed')

    def in_live(self, r):
        return Ech([v for v, _ in self.L_elems()]).reduce(r) == 0

    # ---- phase 1 via C++
    def phase1(self, order, e):
        Erows = []
        for i in order[:e]:
            Erows += [self.zrows[2 * i], self.zrows[2 * i + 1]]
        fv = [v for v, _ in self.free]
        eE = Ech(fv)
        rk = sum(1 for v in Erows if eE.add(v))
        p = self.cap - len(self.free) - rk
        assert p >= 0
        M = (1 << 64) - 1

        def s3(v):
            return f'{v & M} {(v >> 64) & M} {(v >> 128) & M}'

        txt = [f'{self.ny} {len(fv)} {len(self.annH)} {len(Erows)} {self.cap} {p}']
        txt += [s3(v) for v in fv] + [s3(v) for v in self.annH] + [s3(v) for v in Erows]
        out = subprocess.run([os.path.join(HERE, 'phase1.exe')], input='\n'.join(txt), capture_output=True, text=True)
        if out.returncode:
            raise RuntimeError('phase1 failed: ' + out.stderr[-2000:])
        tok = out.stdout.split()
        n = int(tok[0])
        assert n == self.cap - len(self.free)
        basis = list(self.free)
        for t in range(n):
            a, b, c, d = map(int, tok[1 + 4 * t:5 + 4 * t])
            um = a | (b << 64)
            vm = c | (d << 64)
            u = 0
            fu = 0
            v = 0
            fv_ = 0
            for j, (val, form) in enumerate(basis):
                if um >> j & 1:
                    u ^= val
                    fu ^= form
                if vm >> j & 1:
                    v ^= val
                    fv_ ^= form
            sym = self.ev_compute(fu, fv_)
            el = (u & v, sym)
            basis.append(el)
            self.add_live(*el)
        assert Ech([v for v, _ in self.L_elems()]).n == self.cap
        assert all(self.in_live(r) for r in Erows)

    def chip_event(self, i):
        s, U = self.cov[i]
        elems = self.L_elems()
        ce = self.span_basis(elems)
        al = self.express(elems, ce, self.zrows[2 * i])
        be = self.express(elems, ce, self.zrows[2 * i + 1])
        assert al is not None and be is not None
        L = al ^ self.low_form(U[0])
        M = be ^ self.low_form(U[1])
        return self.ev_compute(L, M, 'O')

    def run(self, e=24, order=None, verbose=True):
        n = len(self.cov)
        if order is None:
            order = list(range(n))
            self.rng.shuffle(order)
        t0 = time.time()
        self.low_products()
        self.phase1(order, e)
        if verbose:
            print(f'  phase1 done ({time.time() - t0:.0f}s): live dim {Ech([v for v, _ in self.L_elems()]).n}', flush=True)
        return self.run_rest(order, verbose, t0)

    def run_rest(self, order, verbose=True, t0=None):
        t0 = t0 or time.time()
        self.chipsym = {}
        dimH = Ech(self.H).n
        for t, i in enumerate(order):
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
            if self.eager_tail and Ech([v for v, _ in self.computed]).n == dimH:
                needed = []
                for j in order[t + 1:]:
                    needed += [self.zrows[2 * j], self.zrows[2 * j + 1]]
                self.release_eagerly(needed)
            if verbose and t % 16 == 15:
                print(f'  chip {t + 1}: products {self.nprod}, releases {self.n_release}, computed dim {Ech([v for v, _ in self.computed]).n} ({time.time() - t0:.0f}s)', flush=True)
        # remaining dimensions of H
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

    def final_releases(self):
        # greedy closure order from the free set; release in reverse
        S = list(self.free)
        Sech = Ech([v for v, _ in S])
        elems = self.L_elems()
        ce = self.span_basis(elems)
        Z = [v for v, _ in elems]
        added = []
        full = Ech(Z).n
        clo = Ech([v for v, _ in S])
        for i, (a, _) in enumerate(S):
            for (b, _) in S[i + 1:]:
                clo.add(a & b)
        while Sech.n < full:
            inter = intersect(Z, list(clo.piv.values()), self.ny)
            cand = [v for v in inter if Sech.reduce(v)]
            if not cand:
                raise RuntimeError(f'closure stuck at {Sech.n} of {full}')
            self.rng.shuffle(cand)
            cnt = 0
            for v in cand:
                if Sech.reduce(v) == 0:
                    continue
                f = self.express(elems, ce, v)
                assert f is not None
                for (a, _) in S:
                    clo.add(a & v)
                clo.add(v)
                S.append((v, f))
                Sech.add(v)
                added.append((v, f))
                cnt += 1
                if cnt >= 4:
                    break
        self.live = list(added)
        while self.live:
            rel = self.live[-1]
            self.release(rel, self.live[:-1])

    # ---- final rows
    def final_rows(self):
        F = self.F
        k = self.k
        elems = []
        ce = CombEch()
        for (v, f) in self.computed:
            d = ce.add(v, 1 << len(elems))
            assert d is None, 'dependent computed element'
            elems.append((v, f))
        bad, lx = check_function(F, self.cov, self.sol)
        assert bad == 0
        final = [0] * 46
        for i in range(11):
            final[i] = 1 << (1 + i)
        for j in range(5):
            for b in range(6):
                o = 6 * j + b
                form = self.express(elems, ce, self.hrows[o])
                assert form is not None
                val = [(lx[x] >> o) & 1 for x in range(8)]
                c = val[:]
                for t in range(3):
                    for m in range(8):
                        if m >> t & 1:
                            c[m] ^= c[m ^ (1 << t)]
                assert c[0] == 0
                for m in range(1, 8):
                    if c[m]:
                        form ^= self.low_forms[m]
                for i, (s, U) in enumerate(self.cov):
                    if s >> o & 1:
                        form ^= self.chipsym[i]
                # XOR oracle: the incoming word bit stays in place (also for loader 0, whose words are
                # not empty when the verifier runs the circuits in reverse order)
                form ^= 1 << (12 + 7 * j + b)
                final[11 + 7 * j + b] = form
            keep6 = final[11 + 7 * j + 5] ^ (1 << (12 + 7 * j + 5)) ^ (1 << (12 + 7 * j + 6))
            if k:
                final[11 + 7 * j + 6] = keep6
            else:
                i1, i2 = TAGS[j]
                gv = sum(1 << y for y in range(self.ny) if ((int(F.G[0, y]) >> i1) & (int(F.G[0, y]) >> i2)) & 1)
                gf = self.express(elems, ce, gv)
                assert gf is not None, 'tag not in computed span'
                final[11 + 7 * j + 6] = keep6 ^ gf
        return final

    def spec(self):
        return K.Spec(self.k, self.events, self.final_rows(), {})
