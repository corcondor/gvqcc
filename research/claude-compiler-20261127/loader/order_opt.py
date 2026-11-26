# Register-pressure scheduling of the chips (compiler "instruction ordering").
# pressure(t) = dim F + rank_F(C_t) + rank_F(N_t) - rank_F(C_t + N_t), the dimension that must stay live after chip t,
# with C_t = live space after phase 1 + rows of chips 1..t, N_t = rows of the later chips.  We also charge the
# new directions chip t+1 still has to compute.  Simulated annealing over the order of the non-early chips.
import math, random
from gf2 import Ech


def full_basis(vecs):
    e = Ech()
    for v in vecs:
        e.add(v)
    return e


class Pressure:
    def __init__(self, zrows, free_vals, start_vals, cap, early):
        self.z = zrows
        self.cap = cap
        self.F = full_basis(free_vals)
        self.dimF = self.F.n
        # work modulo F: reduce every row once (Ech.reduce is leading-bit only, so use a full reduction)
        piv = sorted(self.F.piv.items(), reverse=True)

        def red(v):
            for h, p in piv:
                if (v >> h) & 1:
                    v ^= p
            return v
        self.rows = [(red(zrows[2 * i]), red(zrows[2 * i + 1])) for i in range(len(zrows) // 2)]
        self.start = [red(v) for v in start_vals]
        self.early = early

    def profile(self, order):
        n = len(order)
        # N_t basis built from the back
        suffix = [None] * (n + 1)
        e = Ech()
        suffix[n] = []
        for t in range(n - 1, -1, -1):
            added = []
            for v in self.rows[order[t]]:
                if e.add(v):
                    added.append(v)
            suffix[t] = suffix[t + 1] + added
        c = Ech(self.start)
        total = c.copy()
        for v in suffix[0]:
            total.add(v)
        prof = []
        for t in range(n):
            need = 0
            for v in self.rows[order[t]]:
                need += c.add(v)
            # C_t + N_t is the same space for every t, so the held dimension is rank C_t + rank N_t - const
            keep = c.n + len(suffix[t + 1]) - total.n
            prof.append((self.dimF + keep, need))
        return prof

    def cost(self, order):
        prof = self.profile(order)
        over = 0.0
        peak = 0
        for t in range(self.early - 1, len(order) - 1):
            after = prof[t][0] + prof[t + 1][1]     # keep after chip t plus what chip t+1 must add
            if after > self.cap:
                over += after - self.cap
            peak = max(peak, after)
        soft = sum(max(0, p[0] - (self.cap - 4)) for p in prof[self.early - 1:])
        return over * 1000 + soft + peak * 0.01, over, peak


def anneal(P, order, iters, seed, fixed_head):
    rng = random.Random(seed)
    cur = list(order)
    cc, over, peak = P.cost(cur)
    best = (cc, over, peak, list(cur))
    T = 30.0
    for it in range(iters):
        i = rng.randrange(fixed_head, len(cur))
        j = rng.randrange(fixed_head, len(cur))
        if i == j:
            continue
        new = list(cur)
        if rng.random() < 0.5:
            new[i], new[j] = new[j], new[i]
        else:
            x = new.pop(i)
            new.insert(j, x)
        nc, no, npk = P.cost(new)
        if nc <= cc or rng.random() < math.exp((cc - nc) / T):
            cur, cc, over, peak = new, nc, no, npk
            if cc < best[0]:
                best = (cc, over, peak, list(cur))
        T = max(0.5, T * 0.999)
    return best
