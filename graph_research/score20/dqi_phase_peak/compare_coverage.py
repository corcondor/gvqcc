#!/usr/bin/env python3
"""Compare branch-lifetime census on exact splice ranges and untouched ranges."""
from argparse import ArgumentParser
from csv import DictReader
import json
from pathlib import Path

import numpy as np


def census(path, operations, regions):
    counters = np.zeros(operations + 1, np.int16)
    with path.open() as file:
        for row in DictReader(file, delimiter="\t"):
            counters[int(row["first"])] += 1
            counters[int(row["last"])] -= 1
    np.cumsum(counters, dtype=np.int16, out=counters)
    peak = int(counters.max())
    positions = int(np.count_nonzero(counters == 889))
    inside = [int(np.count_nonzero(counters[s:e] == 889)) for s, e in regions]
    return counters, dict(operations=operations, width=peak, cuts_at_889=positions,
                cuts_in_replaced_spans=sum(inside),
                cuts_outside_replaced_spans=positions-sum(inside),
                per_span_max=int(max(counters[s:e].max() for s, e in regions)),
                span_count_with_peak=sum(v > 0 for v in inside))


def main(args):
    receipt = json.loads(args.splices.read_text())["output"]
    old_sites = [(s["old_start"], s["old_end"]) for s in receipt["sites"]]
    new_sites = [(s["new_start"], s["new_end"]) for s in receipt["sites"]]
    original, old = census(args.old_life, 58_868_734, old_sites)
    replacement, new = census(args.new_life, receipt["header"]["num_ops"], new_sites)
    outside = []
    original_start = new_start = 0
    for (original_end, original_next), (new_end, new_next) in zip(
            old_sites + [(len(original)-1, len(original)-1)],
            new_sites + [(len(replacement)-1, len(replacement)-1)]):
        assert original_end - original_start == new_end - new_start
        before = original[original_start:original_end] == 889
        after = replacement[new_start:new_end] == 889
        disappeared = np.flatnonzero(np.diff((before & ~after).astype(np.int8),
                                              prepend=np.int8(0), append=np.int8(0)))
        added = int(np.count_nonzero(after & ~before))
        assert added == 0
        outside.extend((int(a)+original_start, int(b)+original_start)
                       for a, b in zip(disappeared[::2], disappeared[1::2]))
        original_start, new_start = original_next, new_next
    output = dict(old=old, new=new,
                  changed_q889_cut_count=old["cuts_at_889"] - new["cuts_at_889"],
                  global_width_reduction=old["width"] - new["width"],
                  retired_unchanged_ranges_e4_coordinates=outside,
                  retired_unchanged_cut_count=sum(b-a for a,b in outside))
    args.out.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({k: v for k, v in output.items() if k != "retired_unchanged_ranges_e4_coordinates"}))


if __name__ == "__main__":
    p = ArgumentParser(description=__doc__)
    for name in ("splices", "old-life", "new-life", "out"):
        p.add_argument("--" + name, type=Path, required=True)
    main(p.parse_args())
