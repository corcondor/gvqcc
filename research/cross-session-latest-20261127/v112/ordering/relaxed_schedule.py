"""Schedule commuting gates with certified zero cuts and independent HMR order.

Unlike V111's strict graph, X/X and Z/Z events may commute on a shared qubit.
Independent HMR outcomes may be permuted (the outcome identities, classical
read/write edges, and guarded scopes are preserved). Rotation order remains
fixed because external angles are assigned in rotation order. Zero cuts are
explicit barriers on their logical wire, never inferred from probabilistic
simulation. The lower bound is for this fixed graph and zero-cut model only.
"""
from pathlib import Path
from collections import Counter, defaultdict
from dataclasses import replace
import argparse
import bisect
import hashlib
import heapq
import json
import random
import struct
import time
from native_kmb import NativeKMB, Op


def public(c):
    out = set()
    for k, s in c.sections:
        if k == 0:
            n, w = struct.unpack_from("<II", s)
            out.update(x & 0x7fffffff for x in struct.unpack_from("<" + "I" * w, s, 8+n) if x >> 31)
    return out


def roles(o):
    k, w = o.raw & 127, o.wires
    if k in (16, 19, 32, 48):
        return {q: 2 for q in w}
    if k == 17:
        return {w[0]: 1}
    if k in (33, 49):
        return {**{q: 2 for q in w[:-1]}, w[-1]: 1}
    if k == 34:
        return {q: 3 for q in w}
    if k == 50:
        return {w[0]: 2, w[1]: 3, w[2]: 3}
    if k in (18, 80):
        return {w[0]: 3}
    if k in (0, 1, 64, 65, 66):
        return {}
    raise ValueError(("unknown opcode", o))


def model(c, intervals):
    rows = [tuple(map(int, l.split()[1:])) for l in Path(intervals).read_text().splitlines() if l.startswith("I ")]
    by = defaultdict(list)
    for e, (s, t, q) in enumerate(rows):
        by[q].append((s, t, e))
    for q in by:
        by[q].sort()
    starts = {q: [r[0] for r in a] for q, a in by.items()}
    uses = []
    ending = []
    n = len(c.ops)
    for i, o in enumerate(c.ops):
        es = []
        ends = []
        for q in o.wires:
            j = bisect.bisect_right(starts[q], i) - 1
            a, b, e = by[q][j]
            assert a <= i <= b, (i, q, a, b)
            es.append(e)
            if b == i and i < n-1:
                ends.append(e)
        uses.append(tuple(es))
        ending.append(tuple(ends))
    init = {e for e, (s, _, q) in enumerate(rows) if s == 0 and q in public(c)}
    tail = {e for e, (_, t, _) in enumerate(rows) if t == n-1}
    return rows, uses, ending, init, tail


def graph(c, m, mode, measurement_order):
    rows, uses, ending, init, tail = m
    n = len(c.ops)
    successors = [set() for _ in range(n)]
    predecessor = [set() for _ in range(n)]
    frontier = set()
    last = {}
    scope_bar = None
    last_rotation = None
    last_hmr = None
    epoch_events = defaultdict(list)
    zero_bar = {}
    for i, o in enumerate(c.ops):
        k = o.raw & 127
        pre = set()
        if scope_bar is not None:
            pre.add(scope_bar)
        if k == 1:
            pre.update(frontier)
            last.clear()
            scope_bar = i
        else:
            types = roles(o)
            if mode == "strict":
                types = {q: 3 for q in types}
            if o.condition is not None:
                types[("b", o.condition)] = 2
            if o.measurement is not None:
                types[("b", o.measurement)] = 3
            for q, typ in types.items():
                if q in last:
                    pt, group, prev = last[q]
                    if typ == pt and typ != 3:
                        pre.update(prev)
                        group.append(i)
                    else:
                        pre.update(group)
                        last[q] = (typ, [i], tuple(group))
                else:
                    last[q] = (typ, [i], ())
        # A zero certificate refers to a logical wire boundary. Preserve that
        # boundary even when individual X/X or Z/Z operations commute.
        for q, e in zip(o.wires, uses[i]):
            if q in zero_bar:
                pre.add(zero_bar[q])
            if e in ending[i]:
                pre.update(epoch_events[e])
            epoch_events[e].append(i)
        for e in ending[i]:
            zero_bar[rows[e][2]] = i
        if k == 19:
            if last_rotation is not None:
                pre.add(last_rotation)
            last_rotation = i
        if measurement_order and k in (18, 80):
            if last_hmr is not None:
                pre.add(last_hmr)
            last_hmr = i
        assert all(j < i for j in pre)
        predecessor[i] = pre
        for j in pre:
            successors[j].add(i)
        frontier.difference_update(pre)
        frontier.add(i)
    return successors, predecessor


def bound(m, succ):
    rows, uses, ending, init, tail = m
    n = len(succ)
    mask = lambda es: sum(1 << e for e in set(es))
    a, z = mask(init), mask(tail)
    fw = [0]*n
    bw = [0]*n
    for i in range(n):
        fw[i] |= a | mask(uses[i])
        for j in succ[i]:
            fw[j] |= fw[i]
    for i in range(n-1, -1, -1):
        bw[i] |= z | mask(ending[i])
        for j in succ[i]:
            bw[i] |= bw[j]
    widths = [(a & b).bit_count() for a, b in zip(fw, bw)]
    w = max(widths)
    i = widths.index(w)
    return {"lower_bound": w, "first_anchor": i, "anchor_count": widths.count(w),
            "anchor_epochs": [e for e in range(len(rows)) if (fw[i] & bw[i]) >> e & 1]}


def measure(order, m):
    rows, uses, ending, init, tail = m
    live = set(init)
    hist = Counter()
    for i in order:
        live.update(uses[i])
        hist[len(live)] += 1
        live.difference_update(ending[i])
    peak = max(hist)
    return (peak, hist[peak], sum(k*v for k, v in hist.items())), dict(sorted(hist.items()))


def greedy(m, succ, pred, seed):
    rows, uses, ending, init, tail = m
    n = len(succ)
    degree = [len(p) for p in pred]
    ready = {i for i, d in enumerate(degree) if not d}
    remaining = Counter(e for u in uses for e in u)
    rng = random.Random(seed)
    tie = [rng.random() for _ in range(n)]
    live = set(init)
    order = []
    while ready:
        def key(i):
            alloc = sum(e not in live for e in uses[i])
            release = len(ending[i])
            urgency = sum(1 / max(1, remaining[e]) for e in uses[i] if e in live)
            t = i if seed % 2 == 0 else tie[i]
            if seed % 6 < 2:
                return (alloc, -release, -urgency, t)
            if seed % 6 < 4:
                return (alloc-release, alloc, -urgency, t)
            return (max(0, len(live)+alloc-36), alloc-release, -urgency, t)
        i = min(ready, key=key)
        ready.remove(i)
        order.append(i)
        for e in uses[i]:
            live.add(e)
            remaining[e] -= 1
        for e in ending[i]:
            assert remaining[e] == 0
            live.remove(e)
        for j in succ[i]:
            degree[j] -= 1
            if degree[j] == 0:
                ready.add(j)
    assert len(order) == n
    return order


def verify_permutation(c, m, order, succ):
    assert sorted(order) == list(range(len(c.ops)))
    pos = [0]*len(order)
    for j, i in enumerate(order):
        pos[i] = j
    assert all(pos[i] < pos[j] for i, s in enumerate(succ) for j in s)
    # Independently check all conflicting events per resource in original order.
    # Consecutive equal role batches may reorder internally, never across the
    # next conflicting batch. Scope and rotation checks use original identities.
    events = defaultdict(list)
    scopes = []
    rotations = []
    for i, o in enumerate(c.ops):
        if (o.raw & 127) == 1:
            scopes.append(i)
        if (o.raw & 127) == 19:
            rotations.append(i)
        for q, typ in roles(o).items():
            events[("q", q)].append((i, typ))
        if o.condition is not None:
            events[("b", o.condition)].append((i, 2))
        if o.measurement is not None:
            events[("b", o.measurement)].append((i, 3))
    for ev in events.values():
        groups = []
        for i, typ in ev:
            if groups and typ != 3 and groups[-1][0] == typ:
                groups[-1][1].append(i)
            else:
                groups.append((typ, [i]))
        for (_, a), (_, b) in zip(groups, groups[1:]):
            assert max(pos[i] for i in a) < min(pos[i] for i in b)
    assert [i for i in order if (c.ops[i].raw & 127) == 19] == rotations
    for i in order:
        assert bisect.bisect_left(scopes, i) == sum(pos[s] < pos[i] for s in scopes)
    rows, uses, ending, init, tail = m
    epoch_events = defaultdict(list)
    for i, es in enumerate(uses):
        for e in es:
            epoch_events[e].append(i)
    for q in range(c.header[1]):
        epochs = sorted((r[0], e) for e, r in enumerate(rows) if r[2] == q)
        for (_, a), (_, b) in zip(epochs, epochs[1:]):
            assert max(pos[i] for i in epoch_events[a]) < min(pos[i] for i in epoch_events[b])
    return True


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("intervals", type=Path)
    p.add_argument("out", type=Path)
    p.add_argument("--tries", type=int, default=12)
    p.add_argument("--modes", nargs="+", choices=("strict_fixed", "strict_free", "commute_fixed", "commute_free"),
                   default=["strict_fixed", "strict_free", "commute_fixed", "commute_free"])
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    c = NativeKMB.read(a.source)
    assert c.to_bytes() == a.source.read_bytes()
    m = model(c, a.intervals)
    base, hist = measure(list(range(len(c.ops))), m)
    result = {"source_sha256": hashlib.sha256(a.source.read_bytes()).hexdigest(),
              "zero_intervals_sha256": hashlib.sha256(a.intervals.read_bytes()).hexdigest(),
              "base_score": base, "base_histogram": hist, "modes": [],
              "scope": "Exact commuting permutations and specified zero cuts; no global quantum-width lower bound."}
    for selected_mode in a.modes:
        mode, meas_text = selected_mode.split("_")
        meas = meas_text == "fixed"
        t = time.monotonic()
        s, p = graph(c, m, mode, meas)
        row = {"mode": mode, "preserve_all_measurement_order": meas, "bound": bound(m, s), "trials": []}
        best = (base, list(range(len(c.ops))), hist)
        for seed in range(a.tries):
            order = greedy(m, s, p, seed)
            score, h = measure(order, m)
            row["trials"].append({"seed": seed, "score": score})
            if score < best[0]:
                best = (score, order, h)
        assert verify_permutation(c, m, best[1], s)
        row.update(best_score=best[0], histogram=best[2], seconds=time.monotonic()-t,
                   permutation_check="PASS", edge_count=sum(len(x) for x in s))
        tag = mode + ("_fixed_hmr" if meas else "_free_hmr")
        (a.out / (tag + "_order.json")).write_text(json.dumps(best[1]))
        result["modes"].append(row)
        (a.out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        print(tag, "bound", row["bound"]["lower_bound"], "best", best[0], flush=True)


if __name__ == "__main__":
    main()