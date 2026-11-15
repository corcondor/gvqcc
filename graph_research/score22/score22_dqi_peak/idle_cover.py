"""An exact interval-level operand-idle hitting set, before semantic checks."""

from argparse import ArgumentParser
from collections import Counter
from csv import DictReader
from functools import cache
import json
from pathlib import Path


def reduce_subsets(sets):
    minimal = []
    for subset in sorted(set(sets), key=lambda row: (len(row), sorted(row))):
        if not any(prior <= subset for prior in minimal):
            minimal.append(subset)
    return frozenset(minimal)


@cache
def cover(sets):
    if not sets:
        return frozenset()
    required = min(sets, key=lambda row: (len(row), sorted(row)))
    if not required:
        raise ValueError("An interval has every scratch operand in use")
    solutions = []
    for wire in sorted(required):
        remaining = frozenset(row for row in sets if wire not in row)
        solutions.append(cover(remaining) | {wire})
    return min(solutions, key=lambda row: (len(row), sorted(row)))


def main():
    cli = ArgumentParser(description=__doc__)
    cli.add_argument("operands", type=Path)
    cli.add_argument("out", type=Path)
    args = cli.parse_args()
    with args.operands.open() as stream:
        rows = list(DictReader(stream, delimiter="\t"))
    idle = [frozenset(map(int,r["scratch_idle"].split(","))) if r["scratch_idle"] else frozenset()
            for r in rows]
    histogram = Counter(map(len,idle))
    forced = set().union(*(subset for subset in idle if len(subset) == 1))
    solution = sorted(cover(reduce_subsets(idle))) if 0 not in histogram else None
    result = dict(peak_intervals=len(idle),
                  common_idle_wires=sorted(frozenset.intersection(*idle)),
                  interval_counts_by_idle_wire_count=dict(sorted(histogram.items())),
                  forced_wires=sorted(forced), minimum_pool=solution,
                  minimum_pool_size=len(solution) if solution is not None else None,
                  peak_intervals_with_fewer_than_8_idle_wires=sum(histogram[i] for i in range(8)),
                  scope="Idle operands throughout each contiguous peak interval, without "
                        "proof of clean state, reversible recovery or dirty-safe use.")
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(result)


if __name__ == "__main__":
    main()
