# Builder3: Builder2 plus two compiler-style fallbacks for the release stages.
#  (1) phase fix not quadratic in the live values -> add conditional CCZ terms (counted 0.5 each by the verifier,
#      since the measurement bit is 1 on half of the shots);
#  (2) nothing releasable (all live values still needed) -> spill one needed value (measure it now) and
#      rematerialise it later from its factors (one more Toffoli).
import os
import random
from common import *
from gf2 import *
from build2 import Builder2


def full_reduce(piv, v):
    """linear projection: clear every pivot bit of an Ech-style basis (piv: leading bit -> row)."""
    for h in sorted(piv, reverse=True):
        if (v >> h) & 1:
            v ^= piv[h]
    return v


class Builder3(Builder2):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.factors = {}          # product symbol -> (value of left factor, value of right factor)
        self.spilled = []          # (value, symbol) released while still needed
        self.n_ccz = 0
        self.n_spill = 0
        self.n_remat = 0
        self.allow_spill = True
        self.allow_ccz = True
        self.cubic_for = {}        # released value -> cubic terms chosen when it entered the closure
        self.n_remat_final = 0
        self.n_peel = 0
        self.final_mode = 0

    # record the factor values of every cache product so it can be recomputed
    def ev_compute(self, L, M, kind='S'):
        if kind == 'S':
            elems = self.L_elems()
            ce = CombEch()
            for i, (_, f) in enumerate(elems):
                ce.add(f, 1 << i)
            vals = []
            for form in (L, M):
                c = ce.solve(form)
                if c is None:
                    vals = None
                    break
                v = 0
                for i, (val, _) in enumerate(elems):
                    if (c >> i) & 1:
                        v ^= val
                vals.append(v)
        sym = super().ev_compute(L, M, kind)
        if kind == 'S' and vals is not None:
            self.factors[sym] = tuple(vals)
        return sym

    # ---- phase fix with optional cubic terms
    def phase_terms3(self, w, basis):
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
        while c is None and i < len(items) - 1:
            for j in range(i + 1, len(items)):
                addcol(items[i][0] & items[j][0], ('p', i, j))
            i += 1
            c = ce.solve(w)
        triples = []
        if c is None and w in self.cubic_for:
            for (va, fa), (vb, fb), (vc, fc) in self.cubic_for[w]:
                w ^= va & vb & vc
                triples.append((fa, fb, fc))
            c = ce.solve(w)
            assert c is not None, 'stored cubic terms do not close the phase'
        if c is None:
            assert self.allow_ccz, 'phase not expressible'
            piv = {h: p[0] for h, p in ce.piv.items()}
            rw = full_reduce(piv, w)
            seen = {}
            idx = list(range(len(items)))
            self.rng.shuffle(idx)
            found = None
            n3 = 0
            for x in range(len(idx)):
                a = idx[x]
                for y in range(x + 1, len(idx)):
                    b = idx[y]
                    ab = items[a][0] & items[b][0]
                    for z in range(y + 1, len(idx)):
                        cc = idx[z]
                        t = ab & items[cc][0]
                        rt = full_reduce(piv, t)
                        if not rt:
                            continue
                        if rt == rw:
                            found = [(a, b, cc)]
                            break
                        if rt ^ rw in seen:
                            found = [seen[rt ^ rw], (a, b, cc)]
                            break
                        seen.setdefault(rt, (a, b, cc))
                        n3 += 1
                    if found or n3 > 20000:
                        break
                if found or n3 > 20000:
                    break
            assert found is not None, 'phase not expressible (cubic)'
            for (a, b, cc) in found:
                w ^= items[a][0] & items[b][0] & items[cc][0]
                triples.append((items[a][1], items[b][1], items[cc][1]))
            c = ce.solve(w)
            assert c is not None
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
        return const, lin, [(items[i][1], m) for i, m in pairs.items() if m], triples

    def release(self, rel, keep_elems):
        mid = self.n_release
        self.n_release += 1
        self.events.append(K.Event('E', row=rel[1]))
        const, lin, pairs, triples = self.phase_terms3(rel[0], self.free + keep_elems)
        for forms in triples:
            self.events.append(K.Event('P', mid=mid, forms=forms))
            self.n_ccz += 1
        for a, b in pairs:
            self.events.append(K.Event('P', mid=mid, forms=(a, b)))
            self.n_phase += 1
        if lin:
            self.events.append(K.Event('P', mid=mid, forms=(lin,)))
        if const:
            self.events.append(K.Event('P', mid=mid, forms=()))
        self.live = list(keep_elems)

    # ---- release; when everything live is still needed, spill one needed value (rematerialised later)
    def release_one(self, needed_vecs):
        elems = self.L_elems()
        C = [v for v, _ in elems]          # only live values can be kept (spilled ones are recomputed on demand)
        needed = list(needed_vecs) + self.anchors
        keep_target = intersect_vecs(needed, C, self.ny) if needed else []
        ce = self.span_basis(elems)
        newfree = Ech([v for v, _ in self.free])
        kept = []
        for v in self.keep_always + keep_target:
            if newfree.add(v):
                f = self.express(elems, ce, v)
                if f is None:
                    assert v not in self.keep_always, 'a kept tag was released'
                    continue
                kept.append((v, f))
        n_must = len(kept)
        if self.prefer_closable:
            total = Ech(C).n
            for v in self.closure_in_live(elems, ce):
                if newfree.n >= total - 1:
                    break
                if newfree.add(v):
                    kept.append((v, self.express(elems, ce, v)))
        extra = []
        for v, f in self.live:
            if newfree.add(v):
                extra.append((v, f))
        if extra:
            i = self.rng.randrange(len(extra))
            rel = extra.pop(i)
            self.release(rel, kept + extra)
            return
        assert self.allow_spill, f'nothing to release: needed dim {len(kept) + len(self.free)}'
        # Belady: rebuild the kept basis in order of first future need and drop the one needed last
        ordered = Ech([v for v, _ in self.free])
        kept2 = []
        for v in self.keep_always:
            if ordered.add(v):
                kept2.append((v, self.express(elems, ce, v)))
        n_tags = len(kept2)
        for m in range(2, len(needed) + 2, 2):
            for v in intersect_vecs(needed[:m], C, self.ny):
                if ordered.add(v):
                    kept2.append((v, self.express(elems, ce, v)))
            if ordered.n >= newfree.n:
                break
        for v, f in kept:
            if ordered.add(v):
                kept2.append((v, f))
        assert len(kept2) > n_tags, 'nothing to spill'
        i = len(kept2) - 1 - (self.rng.randrange(min(3, len(kept2) - n_tags)))
        rel = kept2.pop(i)
        self.release(rel, kept2)
        self.spilled.append(rel[0])
        self.n_spill += 1

    # recomputed values repeat earlier ones: the final rows use the first copy of each
    def final_rows(self):
        ce = CombEch()
        keep = []
        for v, f in self.computed:
            if ce.add(v, 1 << len(keep)) is None:
                keep.append((v, f))
        orig, self.computed = self.computed, keep
        try:
            return super().final_rows()
        finally:
            self.computed = orig

    # same as Builder.compute_coset, with a bounded number of random trials
    def compute_coset(self, r, trials=20000):
        from build import ints_annih, par
        elems = self.L_elems()
        vecs = [v for v, _ in elems]
        ann = ints_annih(vecs, self.ny)
        rhs = [par(a & r) for a in ann]
        m = len(elems)
        ech = Ech(vecs)
        sb = self.span_basis(elems)
        for trial in range(trials):
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

    # ---- recompute a spilled value from the factors of the products that made it
    def recompute(self, r, depth=0):
        elems = self.L_elems()
        live = Ech([v for v, _ in elems])
        if live.reduce(r) == 0:
            return
        # cheapest case first: a single product of live values reaches r
        while Ech([x for x, _ in self.L_elems()]).n >= self.capacity():
            self.release_one(list(self.cur_needed) + [r])
        try:
            self.compute_coset(r, trials=300)
            self.n_remat += 1
            return
        except RuntimeError:
            pass
        elems = self.L_elems()
        live = Ech([v for v, _ in elems])
        # express r over live + products ever computed, preferring the most recently computed
        ce = CombEch()
        basis = []
        for v, _ in elems:
            if ce.add(v, 1 << len(basis)) is None:
                basis.append((v, None))
        for v, f in reversed(self.computed):
            if f in self.factors and ce.add(v, 1 << len(basis)) is None:
                basis.append((v, f))
        c = ce.solve(r)
        assert c is not None, 'value cannot be rematerialised'
        todo = [basis[i] for i in range(len(basis)) if (c >> i) & 1 and basis[i][1] is not None]
        assert depth < 12, 'rematerialisation too deep'
        self.remat_calls = getattr(self, 'remat_calls', 0) + 1
        assert self.remat_calls < 400, 'rematerialisation loop'
        for v, f in todo:
            if Ech([x for x, _ in self.L_elems()]).reduce(v) == 0:
                continue
            u, w = self.factors[f]
            self.recompute(u, depth + 1)
            self.recompute(w, depth + 1)
            while Ech([x for x, _ in self.L_elems()]).n >= self.capacity():
                self.release_one(list(self.cur_needed) + [u, w])
                self.recompute(u, depth + 1)
                self.recompute(w, depth + 1)
            el = self.L_elems()
            sb = self.span_basis(el)
            fu = self.express(el, sb, u)
            fv = self.express(el, sb, w)
            assert fu is not None and fv is not None
            sym = self.ev_compute(fu, fv)
            self.add_live(v, sym)
            self.n_remat += 1

    def run_rest(self, order, verbose=True, t0=None):
        import time
        t0 = t0 or time.time()
        self.chipsym = {}
        dimH = Ech(self.H).n
        self.cur_needed = []
        for t, i in enumerate(order):
            needed = []
            for j in order[t:]:
                needed += [self.zrows[2 * j], self.zrows[2 * j + 1]]
            self.cur_needed = needed
            for r in (self.zrows[2 * i], self.zrows[2 * i + 1]):
                if not self.in_live(r):
                    if Ech([v for v, _ in self.computed]).reduce(r) == 0:
                        self.recompute(r)
                    else:
                        while Ech([v for v, _ in self.L_elems()]).n >= self.capacity():
                            self.release_one(needed)
                        try:
                            self.compute_coset(r)
                        except RuntimeError:
                            # no single product reaches r from what is live: bring spilled values back first
                            assert self.spilled, 'compute failed'
                            for v in list(reversed(self.spilled))[:6]:
                                self.recompute(v)
                            while Ech([v for v, _ in self.L_elems()]).n >= self.capacity():
                                self.release_one(needed)
                            self.compute_coset(r)
                    assert self.in_live(r)
            # a later step may have spilled the first row of this chip again
            for r in (self.zrows[2 * i], self.zrows[2 * i + 1]):
                if not self.in_live(r):
                    self.recompute(r)
            while Ech([v for v, _ in self.L_elems()]).n > self.capacity(extra_chip=1):
                before = [self.zrows[2 * i], self.zrows[2 * i + 1]]
                self.release_one(needed)
                for r in before:
                    if not self.in_live(r):
                        self.recompute(r)
            self.chipsym[i] = self.chip_event(i)
            self.chips_done += 1
            if self.eager_tail and Ech([v for v, _ in self.computed]).n == dimH:
                nd = []
                for j in order[t + 1:]:
                    nd += [self.zrows[2 * j], self.zrows[2 * j + 1]]
                self.release_eagerly(nd)
        while Ech([v for v, _ in self.computed]).n < dimH:
            while Ech([v for v, _ in self.L_elems()]).n >= self.capacity():
                self.release_one([])
            ec = Ech([v for v, _ in self.computed])
            target = next(v for v in self.H if ec.reduce(v))
            self.compute_coset(target)
        assert Ech([v for v, _ in self.computed] + self.H).n == dimH
        self.final_releases()
        self.low_release()
        return order

    # ---- final closure; when stuck, bring in one value through a conditional CCZ
    def final_releases(self):
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
            inter = intersect_vecs(Z, list(clo.piv.values()), self.ny)
            cand = [v for v in inter if Sech.reduce(v)]
            if not cand:
                # final_mode 0: CCZ only; 1: free releases first; 2: one-term CCZ, then free releases
                mode = self.final_mode
                v = None
                if mode == 2 and self.allow_ccz:
                    v = self.cubic_step(S, Sech, Z, clo, max_terms=1)
                if v is None and mode >= 1 and self.peel_step(added, Sech):
                    elems = self.L_elems()
                    ce = self.span_basis(elems)
                    Z = [v for v, _ in elems]
                    full = Ech(Z).n
                    continue
                if v is None and self.allow_ccz:
                    v = self.cubic_step(S, Sech, Z, clo)
                if v is not None:
                    v = self.best_gain(v, S, Sech, Z, clo)
                    cand = [v]
                else:
                    m = self.remat_step(S, Sech, Z, clo)
                    if m is None:
                        raise RuntimeError(f'closure stuck (cubic) at {Sech.n} of {full}')
                    # recompute one value from the closure order; it joins the live set and the closure
                    for (a, _) in S:
                        clo.add(a & m[0])
                    clo.add(m[0])
                    S.append(m)
                    Sech.add(m[0])
                    added.append(m)
                    elems = self.L_elems()
                    ce = self.span_basis(elems)
                    Z = [v for v, _ in elems]
                    full = Ech(Z).n
                    continue
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

    def peel_step(self, added, Sech):
        """release, right now and for free, a live value outside the closure whose phase is quadratic in the other
        live values (a legal first erasure from the top; no extra gate)."""
        elems = self.L_elems()
        ce = self.span_basis(elems)
        vals = [v for v, _ in self.live]
        cands = [v for v in vals if Sech.reduce(v)]
        for _ in range(40):
            if len(vals) < 2:
                break
            a, b = self.rng.sample(vals, 2)
            if Sech.reduce(a ^ b):
                cands.append(a ^ b)
        self.rng.shuffle(cands)
        target = Ech([v for v, _ in elems]).n - 1
        for x in cands[:60]:
            ech = Ech([v for v, _ in self.free] + [v for v, _ in added])
            if not ech.reduce(x):
                continue
            kept = list(added)
            pool = list(self.live)
            self.rng.shuffle(pool)
            for v, f in pool:
                if ech.n >= target:
                    break
                e2 = ech.copy()
                if e2.add(v) and e2.reduce(x):
                    ech = e2
                    kept.append((v, f))
            if ech.n != target or not self.expressible(x, self.free + kept):
                continue
            fx = self.express(elems, ce, x)
            self.release((x, fx), kept)
            self.n_peel += 1
            return True
        return False

    def reach(self, clo2, Sech, m):
        """how many earlier products would become computable from the closure once m is added (progress)."""
        s2 = Sech.copy()
        s2.add(m)
        return sum(1 for u, w in self.factors.values()
                   if not s2.reduce(u) and not s2.reduce(w) and s2.reduce(u & w))

    def gain_of(self, v, S, Sech, Z, clo):
        c2 = clo.copy()
        for (a, _) in S:
            c2.add(a & v)
        c2.add(v)
        s2 = Sech.copy()
        s2.add(v)
        return sum(1 for x in intersect_vecs(Z, list(c2.piv.values()), self.ny) if s2.add(x))

    def best_gain(self, first, S, Sech, Z, clo):
        """among several values reachable with as few cubic terms, take the one that opens the closure furthest."""
        best = (self.gain_of(first, S, Sech, Z, clo), -len(self.cubic_for[first]), first)
        tries = int(os.environ.get('CUBTRIES', '24'))
        for _ in range(tries):
            v = self.cubic_step(S, Sech, Z, clo)
            if v is None:
                break
            if len(self.cubic_for[v]) > len(self.cubic_for[best[2]]):
                continue
            key = (self.gain_of(v, S, Sech, Z, clo), -len(self.cubic_for[v]), v)
            if key[:2] > best[:2]:
                best = key
        return best[2]

    def remat_step(self, S, Sech, Z, clo):
        """one product of values already in span(S), preferably one the loader computed before, whose arrival lets
        the most live values become quadratic.  Returns (value, form) after emitting the CCX, or None."""
        assert self.n_remat_final < 12, 'too many recomputations in the final releases'
        if Ech([v for v, _ in self.L_elems()]).n >= self.capacity():
            return None                       # no free wire for another value
        elems = self.L_elems()
        sb = self.span_basis(elems)
        live = Ech([v for v, _ in elems])
        cands = []
        for val, (u, w) in [(None, f) for f in self.factors.values()]:
            m = u & w
            if Sech.reduce(u) or Sech.reduce(w) or live.reduce(m) == 0:
                continue
            cands.append((m, u, w))
        if len(cands) < 8:
            vals = [v for v, _ in S[1:]]
            for _ in range(400):
                u = 0
                w = 0
                for v in self.rng.sample(vals, self.rng.randint(1, 2)):
                    u ^= v
                for v in self.rng.sample(vals, self.rng.randint(1, 2)):
                    w ^= v
                m = u & w
                if u and w and u != w and live.reduce(m):
                    cands.append((m, u, w))
        self.rng.shuffle(cands)
        best = None
        for m, u, w in cands[:60]:
            c2 = clo.copy()
            for (a, _) in S:
                c2.add(a & m)
            c2.add(m)
            inter = intersect_vecs(Z + [m], list(c2.piv.values()), self.ny)
            s2 = Sech.copy()
            s2.add(m)
            gain = sum(1 for v in inter if s2.add(v))
            if best is None or gain > best[0][0] or (gain == best[0][0] and self.reach(c2, Sech, m) > best[0][1]):
                best = ((gain, self.reach(c2, Sech, m)), m, u, w)
        if best is None or (not best[0][0] and (self.n_remat_final >= 6 or not best[0][1])):
            return None
        _, m, u, w = best
        fu = self.express(elems, sb, u)
        fv = self.express(elems, sb, w)
        assert fu is not None and fv is not None
        sym = self.ev_compute(fu, fv)
        self.add_live(m, sym)
        self.n_remat += 1
        self.n_remat_final += 1
        return (m, sym)

    def cubic_step(self, S, Sech, Z, clo, max_terms=3):
        """a live value v outside S with v = quadratic(S) + (1, 2 or 3 cubic terms of S); fewest terms first."""
        piv = clo.piv
        wc = CombEch()          # span of the live values modulo the quadratic closure
        zb = []
        zred = Ech()
        for z in Z:
            rz = full_reduce(piv, z)
            wc.add(rz, 1 << len(zb))
            zb.append(z)
            zred.add(rz)
        zpiv = zred.piv
        vals = [v for v, _ in S]

        def lift(rsum):
            comb = wc.solve(rsum)
            if comb is None:
                return None
            v = 0
            for i, z in enumerate(zb):
                if (comb >> i) & 1:
                    v ^= z
            return v

        tri = [(a, b, c) for a in range(1, len(vals)) for b in range(a + 1, len(vals)) for c in range(b + 1, len(vals))]
        self.rng.shuffle(tri)
        tri = tri[:40000]
        seen = {}                  # residual modulo (closure + live) -> (reduced cubic, triple)
        items = []
        for t in tri:
            rt = full_reduce(piv, vals[t[0]] & vals[t[1]] & vals[t[2]])
            if not rt:
                continue
            key = full_reduce(zpiv, rt)
            combos = None
            if not key:
                combos = (rt, [t])
            elif key in seen and seen[key][0] != rt:
                combos = (rt ^ seen[key][0], [seen[key][1], t])
            if combos and len(combos[1]) <= max_terms:
                v = lift(combos[0])
                if v is not None and Sech.reduce(v):
                    self.cubic_for[v] = [(S[a], S[b], S[c]) for a, b, c in combos[1]]
                    return v
            seen.setdefault(key, (rt, t))
            items.append((key, rt, t))
        # three terms
        for i in range(min(len(items), 1500) if max_terms >= 3 else 0):
            ki, ri, ti = items[i]
            for j in range(i + 1, len(items)):
                kj, rj, tj = items[j]
                hit = seen.get(ki ^ kj)
                if hit and hit[1] not in (ti, tj):
                    v = lift(ri ^ rj ^ hit[0])
                    if v is not None and Sech.reduce(v):
                        self.cubic_for[v] = [(S[a], S[b], S[c]) for a, b, c in (ti, tj, hit[1])]
                        return v
        return None


def intersect_vecs(A, B, ny):
    from build import intersect
    return intersect(A, B, ny)
