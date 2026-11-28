# Register-pressure list scheduling of the chips after the window search (compiler "instruction scheduling").
# Held dimension after a chip = rank_F(C) + rank_F(N) - const, C = live+computed rows, N = rows of later chips.
# Choose, one at a time, the next chip that keeps the held dimension (plus what it must compute) lowest.
import random
from gf2 import Ech


def install(B, e, seed):
    orig = B.run_rest

    def run_rest(order, verbose=True, t0=None):
        order[:] = reorder(B, list(order), e + B.extra_rows, seed)
        return orig(order, verbose, t0)
    B.run_rest = run_rest


def reorder(B, order, head, seed):
    rng = random.Random(seed)
    F = Ech([v for v, _ in B.free] + list(B.keep_always))
    piv = sorted(F.piv.items(), reverse=True)

    def red(v):
        for h, p in piv:
            if (v >> h) & 1:
                v ^= p
        return v
    rows = {i: (red(B.zrows[2 * i]), red(B.zrows[2 * i + 1])) for i in order}
    C = Ech()
    for v, _ in B.L_elems():
        C.add(red(v))
    total = C.copy()
    for i in order:
        for v in rows[i]:
            total.add(v)
    cap = B.capacity() - F.n
    last = getattr(B, 'last_count', 0)
    n = len(order)
    out = order[:head]
    for i in out:
        for v in rows[i]:
            C.add(v)
    segments = [order[head:n - last], order[n - last:]]
    worst = 0
    for seg_index, seg in enumerate(segments):
        todo = list(seg)
        while todo:
            later = [i for s in segments[seg_index + 1:] for i in s]
            best = None
            for i in todo:
                c2 = C.copy()
                need = sum(1 for v in rows[i] if c2.add(v))
                N = Ech()
                for j in todo + later:
                    if j != i:
                        for v in rows[j]:
                            N.add(v)
                keep = c2.n + N.n - total.n
                before = keep_now(C, todo + later, rows, total) + need
                key = (max(0, before - cap), max(before, keep), need, keep, rng.random())
                if best is None or key < best[0]:
                    best = (key, i, c2, before)
            _, i, C, before = best
            worst = max(worst, before + F.n)
            todo.remove(i)
            out.append(i)
    print(f'  greedy order: worst held+need {worst} (capacity {B.capacity()})', flush=True)
    return out


def keep_now(C, chips, rows, total):
    N = Ech()
    for j in chips:
        for v in rows[j]:
            N.add(v)
    return C.n + N.n - total.n
