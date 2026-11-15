"""Intersect exact scratch-wire gaps with every maximum-width slice."""
from argparse import ArgumentParser
from collections import defaultdict
from csv import DictReader
from pathlib import Path
import json


def data(path):
    with path.open() as stream:
        yield from DictReader(stream, delimiter="\t")


def union(intervals):
    out = []
    for start, stop in sorted(intervals):
        if out and start <= out[-1][1]:
            out[-1][1] = max(out[-1][1], stop)
        else:
            out.append([start, stop])
    return out


def intersection(left, right):
    i = j = 0
    while i < len(left) and j < len(right):
        a, b = left[i]
        c, d = right[j]
        if max(a, c) < min(b, d):
            yield [max(a, c), min(b, d)]
        i += b <= d
        j += d <= b


def subtract(intervals, removed):
    changes = defaultdict(int)
    for begin, end in intervals:
        changes[begin] += 1
        changes[end] -= 1
    for begin, end in removed:
        changes[begin] -= 2
        changes[end] += 2
    last = level = 0
    for now, change in sorted(changes.items()):
        if level == 1 and last < now:
            yield [last, now]
        last = now
        level += change


def measure(intervals):
    return sum(stop - start for start, stop in intervals)


def profiles(rows):
    changes = defaultdict(int)
    for row in rows:
        changes[int(row["first"])] += 1
        changes[int(row["last"])] -= 1
    last = width = 0
    out = defaultdict(list)
    for now, delta in sorted(changes.items()):
        if now > last:
            out[width].append([last, now])
        width += delta
        last = now
    return width, out


def main():
    p = ArgumentParser(description=__doc__)
    p.add_argument("lifetimes", type=Path)
    p.add_argument("gaps", type=Path)
    p.add_argument("out", type=Path)
    p.add_argument("--peak-intervals", type=Path)
    args = p.parse_args()
    _, widths = profiles(data(args.lifetimes))
    peak = max(widths)
    hot = union(widths[peak])
    if args.peak_intervals:
        with args.peak_intervals.open("w") as stream:
            stream.write("start\tstop_exclusive\twidth\n")
            for start, stop in hot:
                stream.write(f"{start}\t{stop}\t{peak}\n")
    gaps = [{key: int(row[key]) for key in ("begin", "end", "q", "quadratics")}
            for row in data(args.gaps)]
    budget_rows = {}
    for budget in (0, 1, 2, 4, 8, 24):
        eligible = [row for row in gaps if row["quadratics"] <= budget]
        covered = list(intersection(hot, union((r["begin"], r["end"]) for r in eligible)))
        remainder = union(subtract(hot, covered))
        budget_rows[str(budget)] = dict(covered_positions=measure(covered),
                                        remaining_positions=measure(remainder),
                                        remaining_intervals=len(remainder),
                                        first_remaining=remainder[:5])
    result = dict(peak=peak, peak_positions=measure(hot), peak_intervals=len(hot),
                  gaps=len(gaps), cumulative_quadratic_cost=budget_rows)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
