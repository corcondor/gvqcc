"""Bound simultaneous release using the certified quadratic transport gaps."""

from argparse import ArgumentParser
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from csv import DictReader
from dataclasses import dataclass
from functools import cache
import json
from pathlib import Path


@dataclass(frozen=True)
class Gap:
    start: int
    stop: int
    target: int
    sources: frozenset[int]
    cost: int


def csv_rows(path):
    with path.open() as stream:
        yield from DictReader(stream, delimiter="\t")


def read_gaps(path):
    for row in csv_rows(path):
        target = int(row["q"])
        support = frozenset(int(x) for name in ("initial_terms", "final_terms")
                            for term in row[name].split(";") if term
                            for x in term.split(",") if x != "65535")
        assert target not in support
        start, end, cost = (int(row[key]) for key in ("begin","end","quadratics"))
        yield Gap(start, end, target, support, cost)


@cache
def independent(adjacency, active):
    if not active:
        return 0
    members = [i for i, _ in enumerate(adjacency) if active >> i & 1]
    v = max(members,key=lambda i:(adjacency[i] & active).bit_count())
    if not adjacency[v] & active:
        return active.bit_count()
    reduced = active & ~(1<<v)
    return max(independent(adjacency,reduced),
               1 + independent(adjacency,reduced & ~adjacency[v]))


def release_capacity(gaps):
    gaps = tuple(sorted(gaps,key=lambda g:g.target))
    adjacency = tuple(sum(1<<j for j,v in enumerate(gaps) if j != i and (
        v.target == u.target or v.target in u.sources or u.target in v.sources))
        for i,u in enumerate(gaps))
    return independent(adjacency,(1<<len(gaps))-1)


def audit_runs(peaks, gaps):
    starts = [begin for begin,_,_ in peaks]
    ends = [end for _,end,_ in peaks]
    inbox = [[] for _ in peaks]
    for gap in gaps:
        a, b = bisect_right(ends,gap.start), bisect_left(starts,gap.stop)
        for i in range(a,b):
            inbox[i].append(gap)
    exact = []
    for (start,stop,label), use in zip(peaks,inbox):
        lines = [g for g in use if g.start <= start < stop <= g.stop]
        inside = defaultdict(list)
        for gap in use:
            l,r = max(start,gap.start),min(stop,gap.stop)
            if l<r:
                inside[l].append((True,gap))
                inside[r].append((False,gap))
        inside[start]
        inside[stop]
        runs = Counter()
        current = set()
        earlier = start
        for at,events in sorted(inside.items()):
            if at>earlier:
                runs[release_capacity(current)] += at-earlier
            for add,gap in events:
                if add:
                    current.add(gap)
                else:
                    current.remove(gap)
            earlier = at
        exact.append(dict(start=start,end=stop,caller=label,
                          continuous_release_capacity=release_capacity(lines),
                          per_cut_release_histogram=dict(sorted(runs.items()))))
    return exact


def best_partition(peaks,gaps,parts):
    """Optimize the weakest contiguous cluster with one release gap per wire."""
    start = [p[0] for p in peaks]
    stop = [p[1] for p in peaks]
    n = len(peaks)
    # Each certified gap covers an interval of contiguous peak runs.
    covered = []
    for gap in gaps:
        left,right = bisect_left(start,gap.start),bisect_right(stop,gap.stop)
        if left<right:
            covered.append((left,right,gap))
    spans = [[] for _ in range(n)]
    for l,r,gap in covered:
        for i in range(l,r):
            spans[i].append((r,gap))
    table = [[None]*(n+1) for _ in range(parts+1)]
    table[0][0] = (49,())
    for end in range(1,n+1):
        for begin in range(end):
            per_span = release_capacity(gap for right,gap in spans[begin] if right>=end)
            for k in range(1,parts+1):
                previous = table[k-1][begin]
                if previous is None:
                    continue
                score = min(previous[0],per_span)
                next_entry = (score,(*previous[1],(start[begin],stop[end-1],per_span)))
                if table[k][end] is None or next_entry > table[k][end]:
                    table[k][end] = next_entry
    return table[parts][n]


def main():
    p = ArgumentParser(description=__doc__)
    for n in ("peaks","gaps","out"):
        p.add_argument("--"+n,type=Path,required=True)
    a = p.parse_args()
    peaks = [(int(r["start"]),int(r["stop_exclusive"]),r["caller"]) for r in csv_rows(a.peaks)]
    gaps = tuple(read_gaps(a.gaps))
    rows = audit_runs(peaks,gaps)
    callers = {}
    for label in dict.fromkeys(p[2] for p in peaks):
        site = [r for r in rows if r["caller"]==label]
        histogram = Counter()
        for row in site:
            histogram.update(row["per_cut_release_histogram"])
        continuous = [row["continuous_release_capacity"] for row in site]
        callers[label] = dict(peak_intervals=len(site),positions=sum(histogram.values()),
                              full_interval_capacity_range=[min(continuous),max(continuous)],
                              interval_capacity_histogram=dict(sorted(Counter(continuous).items())),
                              per_cut_histogram=dict(sorted(histogram.items())))
        if label.startswith("extractor."):
            selected = [p for p in peaks if p[2]==label]
            callers[label]["partitions"] = {
                k:best_partition(selected,gaps,k) for k in range(2,5)}
    output = dict(callers=callers,individual_intervals=rows,
                  scope="Exact independent sets of the audited quadratic recovery candidates "
                        "with fixed scheduling, without phased layout or arithmetic rewriting.")
    a.out.write_text(json.dumps(output,indent=2)+"\n")
    print(json.dumps(callers))


if __name__=="__main__":
    main()
