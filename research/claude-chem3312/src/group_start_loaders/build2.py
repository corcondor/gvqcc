# Builder with free partial columns: phase 1 computed on the constrained columns, free-column values lifted afterwards.
import os, subprocess, random, time, hashlib
from common import *
from frame import *
from gf2 import *
from solve import needed_rows, h_vec
from solve2 import relation_functionals, restricted_solve
from build import Builder, ints_annih

HERE = os.path.dirname(os.path.abspath(__file__))


class Builder2(Builder):
    def __init__(self, k, F, cov, sol, seed=1):
        super().__init__(k, F, cov, sol, seed=seed)
        self.free_cols = list(sol['free'])
        self.annH = relation_functionals(sol)
        self.C1 = self.cap - len(self.free)      # non-free live dimension at the end of phase 1
        self.fmask = 0
        for y in self.free_cols:
            self.fmask |= 1 << y

    def phase1(self, order, e, p1seed=1, limit=0):
        Erows = []
        Ej = []
        for i in order[:e]:
            Ej += [2 * i, 2 * i + 1]
        Erows = [self.zrows[j] for j in Ej]
        start = self.L_elems()                    # free, plus products already live (loader 0 tags)
        fv = [v for v, _ in start]
        total = len(self.free) + self.C1
        eE = Ech([1 << y for y in self.free_cols] + fv)
        rk = sum(1 for v in Erows if eE.add(v))
        p = total - len(start) - rk
        assert p >= 0, ('p', p)
        M = (1 << 64) - 1

        def s3(v):
            return f'{v & M} {(v >> 64) & M} {(v >> 128) & M}'

        txt = [f'{self.ny} {len(fv)} {len(self.annH)} {len(Erows)} {total} {p} {len(self.free_cols)}']
        txt += [s3(v) for v in fv] + [s3(v) for v in self.annH] + [s3(v) for v in Erows]
        txt += [' '.join(map(str, self.free_cols))]
        body = '\n'.join(txt)
        tag = hashlib.sha256(body.encode()).hexdigest()[:12]
        inp = os.path.join(HERE, f'p1_k{self.k}_s{p1seed}_{tag}.in')
        outp = os.path.join(HERE, f'p1_k{self.k}_s{p1seed}_{tag}.out')
        errp = os.path.join(HERE, f'p1_k{self.k}_s{p1seed}_{tag}.err')
        print(f'  phase1: p={p} rank(E)={rk} m_start={len(start) + p} (id {tag})', flush=True)
        if os.path.exists(outp):
            stdout = open(outp).read()
            print('  phase1: reusing cached search result', flush=True)
        else:
            open(inp, 'w').write(body)
            with open(inp) as fi, open(errp, 'w') as fe:
                prg = os.path.join(HERE, f'p1_k{self.k}_s{p1seed}_{tag}.prog')
                exe = os.environ.get('P1EXE', 'phase1bs5.exe')
                out = subprocess.run([os.path.join(HERE, exe), str(p1seed), str(limit), prg, os.environ.get('P1THREADS', '3')], stdin=fi, stdout=subprocess.PIPE, stderr=fe, text=True)
            if out.returncode:
                raise RuntimeError(f'phase1 failed ({out.returncode}): ' + open(errp).read()[-2000:])
            stdout = out.stdout
            open(outp, 'w').write(stdout)
        tok = stdout.split()
        n = int(tok[0])
        assert n == total - len(start)
        basis = list(start)
        for t in range(n):
            a, b, c, d = map(int, tok[1 + 4 * t:5 + 4 * t])
            um = a | (b << 64)
            vm = c | (d << 64)
            u = 0; fu = 0; v = 0; fv_ = 0
            for j, (val, form) in enumerate(basis):
                if um >> j & 1:
                    u ^= val; fu ^= form
                if vm >> j & 1:
                    v ^= val; fv_ ^= form
            sym = self.ev_compute(fu, fv_)
            el = (u & v, sym)
            basis.append(el)
            self.add_live(*el)
        assert Ech([v for v, _ in self.L_elems()]).n == total
        for a in self.annH:
            assert all(((v & a).bit_count() & 1) == 0 for v, _ in basis), 'product violates a relation'
        if self.post_seed is not None:
            self.rng = random.Random(self.post_seed)
        self.lift(Ej)
        self.place_anchors(order, e)

    def place_anchors(self, order, e):
        from anchors import find_anchors
        nonE = order[e:]
        slots = len(order) - 57          # positions where anchor supports are free of cost
        base = self.free + [(v, None) for v in self.keep_always]
        if self.set_anchors:
            from anchors import anchor_set
            size, want = self.set_anchors
            best, _, _ = find_anchors(self.zrows, nonE, base, self.ny, count=2, tries=2000)
            start = best[2] if best else []
            res, got = anchor_set(self.zrows, nonE, base, size, want, start, random.Random(self.rng.random()))
            assert res is not None, f'anchor set: only {got} combinations in {size} chips'
            vals, union = res
            order[e:] = [i for i in nonE if i not in union] + [i for i in nonE if i in union]
            self.anchors = vals
            print(f'  anchors: {len(vals)} closable combinations inside {len(union)} chips ({got} available)', flush=True)
            return
        best, minw, n = find_anchors(self.zrows, nonE, base, self.ny, count=self.nanchors, tries=getattr(self, "anchor_tries", 12000))
        if best is None or best[0] > slots:
            best, minw, n = find_anchors(self.zrows, nonE, base, self.ny, count=max(1, self.nanchors - 1), tries=3000)
        assert best is not None and best[0] <= slots, f'no anchor fits: {best and best[0]} > {slots}'
        union = best[2]
        self.last_count = len(union)
        chosen = [c[2] for c in best[1]]
        for h in range(self.hier_anchors):
            # one more anchor, closable over the free set plus the anchors found so far, preferably inside their support
            base2 = base + [(v, None) for v in chosen]
            more, _, n2 = find_anchors(self.zrows, nonE, base2, self.ny, count=1, tries=3000, seed=11 + h, prior=frozenset(union))
            if more is None or len(more[2]) > slots:
                print(f'  extra anchor {h}: none within {slots} chips', flush=True)
                break
            union = set(more[2])
            chosen.append(more[1][0][2])
            print(f'  extra anchor {h}: support now {len(union)} chips', flush=True)
        rest = [i for i in nonE if i not in union]
        last = [i for i in nonE if i in union]
        order[e:] = rest + last
        self.anchors = chosen
        print(f'  anchors: {len(self.anchors)} sparse closable combinations, supports on the last {len(last)} chips ({n} candidates, min support {minw})', flush=True)

    def lift(self, Ej):
        F = self.F
        sol = self.sol
        elems = self.L_elems()
        keep = ~self.fmask
        ce = CombEch()
        for i, (v, _) in enumerate(elems):
            d = ce.add(v & keep, 1 << i)
            assert d is None, 'live basis not injective on constrained columns'
        z = list(sol['z'])
        newrow = {}
        for j in Ej:
            row = self.zrows[j] & keep
            c = ce.solve(row)
            assert c is not None, 'early row not in span'
            full = 0
            i = 0
            while c:
                if c & 1:
                    full ^= elems[i][0]
                c >>= 1; i += 1
            assert (full & keep) == row
            newrow[j] = full
        rng = random.Random(self.rng.random())
        for y in self.free_cols:
            fixed = {j: (newrow[j] >> y) & 1 for j in Ej}
            zy = restricted_solve(F, sol['coef'], y, fixed, rng)
            assert zy is not None, f'free column {y} cannot be completed'
            z[y] = zy
            sol['h'][y] = h_vec(F, y, zy, sol['s'])
        sol['z'] = z
        rows, hrows, lin = needed_rows(F, sol)
        self.zrows = rows
        self.hrows = hrows
        self.H = rows + hrows + lin
        for j in Ej:
            assert self.zrows[j] == newrow[j]
            assert self.in_live(self.zrows[j])
        for a in self.annH:
            assert all(((v & a).bit_count() & 1) == 0 for v in self.H), 'needed row violates a relation'
        print(f'  lifted free columns; rank of needed high functions {Ech(self.H).n}', flush=True)
