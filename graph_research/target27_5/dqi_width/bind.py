"""Exact opcode/operand binding and fixed-schedule coverage on frozen score19 DQI."""
import argparse
import csv
import json
from pathlib import Path

import kmb_splice as splice
from outcome_dqi_chart_match import match

PINNED = "e4e110436080b8538f50511dc7064185e1708c2bd386ea0e36322d7791311355"


def matches(base, template_path, start, stop):
    template = splice.open_circuit(template_path)
    pattern = template.opcodes[start:stop]
    before = list(template.operations(start, stop))
    assert len(before) == len(pattern) == stop - start
    pos = 0
    hits = []
    while (found := base.opcodes.find(pattern, pos)) >= 0:
        pos = found + 1
        updated = match(before, base.operations(found, found + len(pattern)))
        if updated is not None:
            hits.append((found, found + len(pattern)))
    template.close()
    return hits


def active_ranges(table, threshold):
    events = {}
    with table.open() as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            if row["abi"] == "1":
                continue
            lo, hi = int(row["first"]), int(row["last"])
            events[lo] = events.get(lo, 0) + 1
            events[hi] = events.get(hi, 0) - 1
    width = 840
    last = 0
    for pos, update in sorted(events.items()):
        if width >= threshold and last < pos:
            yield last, pos
        width += update
        last = pos


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("intervals", type=Path)
    parser.add_argument("native", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--pre-hmr", type=Path)
    parser.add_argument("--hmr-patch", type=Path)
    args = parser.parse_args()
    base = splice.open_circuit(args.source)
    assert base.profile["raw_kmb_sha256"] == PINNED
    chart = json.loads((args.native / "component.json").read_text())["rows"]["original"]["third_pivot_chart"]
    paired = json.loads((args.native / "paired.json").read_text())["gauge_park_paired-prefix"]
    path = args.native / "original_chart.kmb"
    found = {}
    found["chart_prefix"] = matches(base, path, 0, chart["prefix_ops"])
    found["chart_return"] = matches(base, path, chart["prefix_ops"], chart["operations"])
    path = args.native / "gauge_park_paired-prefix.kmb"
    found["paired_divide_prefix"] = matches(base, path, 0, paired["length"] - 12)
    paired_total = json.loads((args.native / "paired_closed.json").read_text())["gauge_park_paired-paired"]
    path = args.native / "gauge_park_paired-paired.kmb"
    found["paired_divide_closing"] = matches(base, path, paired["length"] - 12 + 13,
                                             paired_total["length"])
    if args.pre_hmr is not None:
        assert args.hmr_patch is not None
        old = splice.open_circuit(args.pre_hmr)
        patch = json.loads(args.hmr_patch.read_text())
        assert old.profile["raw_kmb_sha256"] == patch["source_sha256"]
        assert base.profile["raw_kmb_sha256"] == patch["candidate_sha256"]
        edits = {e["index"]: e for e in patch["edits"]}

        def operation(row):
            return (row["opcode"], row["qubits"], row["bit"], row["condition"], row["angle_hex"])

        def observed(row):
            return (row.opcode, list(row.qubits), row.bit, row.condition, (row.angle or b"").hex())

        def offset(index):
            return sum(len(edit["new"]) - 1 for i, edit in edits.items() if i < index)

        path = args.native / "original_chart.kmb"
        for name, start, end in (
            ("chart_prefix", 0, chart["prefix_ops"]),
            ("chart_return", chart["prefix_ops"], chart["operations"]),
        ):
            found_in_old = matches(old, path, start, end)
            for a, b in found_in_old:
                expected = []
                for row in old.operations(a, b):
                    edit = edits.get(row.source_index)
                    if edit is None:
                        expected.append(observed(row))
                    else:
                        assert observed(row) == operation(edit["old"])
                        expected.extend(operation(x) for x in edit["new"])
                lo, hi = a + offset(a), b + offset(b)
                assert expected == [observed(x) for x in base.operations(lo, hi)]
                found[name].append((lo, hi))
        old.close()
    base.close()
    ranges = [(a, b, key) for key, intervals in found.items() for a, b in intervals]
    coverage = {}
    for target in (889, 886, 883, 881):
        hot = list(active_ranges(args.intervals, target))
        coverage[str(target)] = {
            "hot_operation_count": sum(b - a for a, b in hot),
            "hot_operations_in_portions_eligible_for_local_substitution": sum(
                max(0, min(y, b) - max(x, a)) for x, y in hot for a, b, key in ranges),
        }
    result = dict(source_sha256=PINNED, binding_intervals=found, hot_coverage=coverage)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
