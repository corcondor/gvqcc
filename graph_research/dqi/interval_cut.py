#!/usr/bin/env python3
"""Exact interval-graph deletion bounds for an unchanged pinned DQI tape.

Deleting a lifetime is a relaxation of valid phase-safe rematerialization.
This program does not emit a circuit or infer a score change.
"""

import argparse
from collections import Counter
import csv
import hashlib
import heapq
import json
from pathlib import Path


BASE_SHA = "e4e110436080b8538f50511dc7064185e1708c2bd386ea0e36322d7791311355"
INTERVAL_SHA = "4aaf31122c1fff471c2fd9bb148ee80fd8900796eb55038d11e2eda028ff74bd"


def load_intervals(path):
    with path.open() as source:
        return [
            (int(row["first"]), int(row["last"]) + 1, int(row["q"]), bool(int(row["abi"])))
            for row in csv.DictReader(source, delimiter="\t")
        ]


def overlaps(rows):
    """Return maximal occupancy and half-open maximal cliques by sweep."""
    events = Counter()
    for first, stop, _, _ in rows:
        events[first] += 1
        events[stop] -= 1
    last = current = peak = 0
    peaks = []
    for time, change in sorted(events.items()):
        if time > last:
            if current > peak:
                peak = current
                peaks = []
            if current == peak:
                if peaks and peaks[-1][1] == last:
                    peaks[-1][1] = time
                else:
                    peaks.append([last, time])
        current += change
        last = time
    return peak, peaks


def single_width_step_certificate(rows, peaks):
    """Choose latest-ending optional lifetime at the first uncovered peak point.

    Each choice certifies that no optional interval covers two witnesses.
    Its chosen interval covers the peak points until the next witness.
    """
    optional = [r for r in rows if not r[3]]
    witnesses = []
    selected = []
    covered_until = 0
    for first, stop in peaks:
        point = max(first, covered_until)
        while point < stop:
            crossing = [r for r in optional if r[0] <= point < r[1]]
            if not crossing:
                return {"status": "NO_MUTABLE_INTERVAL_AT_PEAK", "point": point}
            item = max(crossing, key=lambda r: r[1])
            selected.append(item)
            witnesses.append(point)
            covered_until = item[1]
            point = item[1]

    for item in optional:
        assert sum(item[0] <= time < item[1] for time in witnesses) <= 1
    for first, stop in peaks:
        while first < stop:
            first = max(r[1] for r in selected if r[0] <= first < r[1])
    return dict(
        status="EXACT_MINIMUM_COMPLETE_LIFETIME_DELETIONS_FOR_WIDTH_888",
        minimum=len(witnesses), witnesses=witnesses, selected_lifetimes=selected,
    )


def min_deleted(rows, width):
    """Latest-deadline greedy deletion; ABI rows are compulsory.

    At first overload any feasible solution must discard one active optional
    interval. Exchanging that choice for the active interval ending latest
    cannot harm any later occupancy constraint. Prior points were feasible
    before this choice. Repeat for optimal cardinality.
    """
    ordered = sorted(rows)
    active = {}
    oldest = []
    longest_optional = []
    dropped = []
    for identity, row in enumerate(ordered):
        first, last, wire, pinned = row
        while oldest and oldest[0][0] <= first:
            _, idx = heapq.heappop(oldest)
            active.pop(idx, None)
        active[identity] = True
        heapq.heappush(oldest, (last, identity))
        if not pinned:
            heapq.heappush(longest_optional, (-last, identity))
        while len(active) > width:
            while longest_optional and longest_optional[0][1] not in active:
                heapq.heappop(longest_optional)
            if not longest_optional:
                return {"width": width, "status": "PINNED_OVERFLOW", "first": first}
            _, remove = heapq.heappop(longest_optional)
            active.pop(remove)
            dropped.append(remove)
    drop_set = set(dropped)
    kept = [row for idx, row in enumerate(ordered) if idx not in drop_set]
    observed, _ = overlaps(kept)
    assert observed <= width
    return dict(
        width=width, exact_minimum_deleted=len(dropped), kept_peak=observed,
        dropped_by_qubit=dict(Counter(ordered[idx][2] for idx in dropped)),
    )


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--tape", type=Path, required=True)
    cli.add_argument("--intervals", type=Path, required=True)
    cli.add_argument("--interval-audit", type=Path, required=True)
    cli.add_argument("--out", type=Path, required=True)
    args = cli.parse_args()
    with args.tape.open("rb") as file:
        tape_sha = hashlib.file_digest(file, "sha256").hexdigest()
    if tape_sha != BASE_SHA:
        raise ValueError(f"tape must be frozen e4; got {tape_sha}")
    interval_sha = hashlib.sha256(args.intervals.read_bytes()).hexdigest()
    if interval_sha != INTERVAL_SHA:
        raise ValueError(f"interval table must come from frozen e4; got {interval_sha}")
    raw = json.loads(args.interval_audit.read_text())
    rows = load_intervals(args.intervals)
    assert raw["intervals"] == len(rows)
    peak, peaks = overlaps(rows)
    assert peak == raw["global_peak"] == 889
    immutable_peak, _ = overlaps([r for r in rows if r[3]])
    certificate = single_width_step_certificate(rows, peaks)
    targets = [min_deleted(rows, width) for width in (888, 887, 884, 880, 872, 864, 857)]
    assert certificate["minimum"] == targets[0]["exact_minimum_deleted"]
    report = dict(
        status="GRAPH_RELAXATION_ONLY_NO_REWRITE",
        input_sha256=tape_sha,
        source_ops=raw["num_ops"],
        interval_file_sha256=interval_sha,
        reset_separated_intervals=len(rows),
        peak=peak, peak_span_count=len(peaks),
        peak_span_operations=sum(b-a for a,b in peaks),
        fixed_abi_peak=immutable_peak,
        q888_certificate=certificate,
        target_deletions=targets,
        scope=("ABI lifetimes compulsory; optional reset-separated lifetimes may be omitted "
               "at unit cost. Real removal may require phase debt repayment, cheaper splits, "
               "relayout or algebraic replacement. Counts are exact in this relaxation only."),
    )
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k,v in report.items() if k not in ("q888_certificate", "target_deletions")}))
    print([(r["width"], r.get("exact_minimum_deleted")) for r in targets])


if __name__ == "__main__":
    main()
