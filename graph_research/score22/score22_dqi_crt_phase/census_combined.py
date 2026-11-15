#!/usr/bin/env python3
"""Trace every hot cut through the complete CRT and inverse phase splice map."""
from argparse import ArgumentParser
from collections import Counter
import json
from pathlib import Path
import sys


def shifted(ranges, blocks):
    result = []
    for start, stop in ranges:
        for prior, bound, offset in blocks:
            lo, hi = max(start, prior), min(stop, bound)
            if lo < hi:
                result.append((lo+offset, hi+offset))
    return result


def stage_hot(widths, threshold, union):
    return union([(a, b) for a, b, width in widths if width >= threshold])


def gap_map(num_ops, splices):
    result = []
    old_prev = new_prev = 0
    for old_start, old_end, new_start, new_end in splices:
        assert old_start - old_prev == new_start - new_prev
        result.append((old_prev, old_start, new_prev-old_prev))
        old_prev, new_prev = old_end, new_end
    result.append((old_prev, num_ops, new_prev-old_prev))
    return result


def main(args):
    sys.path.insert(0, str(args.central))
    import census as c

    crt = json.loads((args.combined/"splice.json").read_text())
    phase = json.loads((args.phase/"splice_all.json").read_text())["output"]
    baseline = json.loads((args.central/"census.json").read_text())
    assert crt["input_sha256"] == phase["sha256"]
    e4_ops = baseline["operations"]
    phase_ops = phase["header"]["num_ops"]
    crt_ops = crt["header"]["num_ops"]
    combined_widths = c.read_width(args.combined/"lifetimes.tsv", crt_ops)
    phase_widths = c.read_width(args.phase/"lifetimes_all.tsv", phase_ops)
    crt_delta = crt_ops-phase_ops
    assert crt["splices"][-1]["new_end"] - crt["splices"][-1]["old_end"] == crt_delta

    CRT = [(s["old_start"], s["old_end"], s["new_start"], s["new_end"]) for s in crt["splices"]]
    Phase = [(s["old_start"], s["old_end"], s["new_start"]+crt_delta, s["new_end"]+crt_delta)
             for s in phase["sites"]]
    e4_map = gap_map(e4_ops, CRT + Phase)
    phase_map = gap_map(phase_ops, CRT)
    families = {
        "new_CRT_residue_GF24": [(s["begin_residue"], s["end_residue"]) for s in crt["splices"]],
        "new_CRT_scalar_updates": [(s["begin_scalar_updates"], s["end_scalar_updates"]) for s in crt["splices"]],
        "new_masked_inverse_phase": [(s["new_start"]+crt_delta, s["new_end"]+crt_delta) for s in phase["sites"]],
    }
    inside_crt = [(s["new_start"], s["new_end"]) for s in crt["splices"]]
    families["new_CRT_linear_views"] = c.subtract(c.union(inside_crt),
        c.union(families["new_CRT_residue_GF24"]+families["new_CRT_scalar_updates"]))
    for name, info in baseline["details"].items():
        families["e4_"+name] = shifted(info["ranges"], e4_map)
    nested = json.loads(args.nested.read_text())
    assert nested["input_sha256"] == baseline["source_sha256"]
    families["e4_nested_divide_prefix"] = shifted([(m["start"], m["end"]) for m in nested["matched"]], e4_map)
    if args.other.exists():
        extra = json.loads(args.other.read_text())
        assert extra["input_sha256"] == phase["sha256"]
        for name, info in extra["bindings"].items():
            if info["matched"]:
                family = "_".join(name.split("_")[:2])
                families.setdefault(family, []).extend(shifted(info["matched"], phase_map))
    virtual = args.combined/"virtual_bind.json"
    if virtual.exists():
        binds = json.loads(virtual.read_text())
        assert binds["tape_sha256"] == crt["output_sha256"]
        families["virtual_source_products"] = [
            (row["start"],row["end"])
            for group in binds["families"]
            for row in group["matches"]
        ]
    families = {name: c.union(ranges) for name, ranges in families.items()}
    result = {}
    for threshold in (889, 888, 881):
        hot = stage_hot(combined_widths, threshold, c.union)
        earlier_hot = stage_hot(phase_widths, threshold, c.union)
        old_sites = [(s["old_start"], s["old_end"]) for s in crt["splices"]]
        old_crt = c.intersection(earlier_hot, c.union(old_sites))
        new_crt = c.intersection(hot, c.union(inside_crt))
        before_unchanged = c.union(shifted(earlier_hot, phase_map))
        retained = c.intersection(hot, before_unchanged)
        covered = c.intersection(hot, c.union([r for spans in families.values() for r in spans]))
        unclassified = c.subtract(hot, covered)
        overlap = {name: c.size(c.intersection(hot, ranges)) for name, ranges in families.items()}
        result[threshold] = dict(phase_only_total=c.size(earlier_hot),
            combined_total=c.size(hot), combined_disjoint_runs=len(hot),
            old_CRT_spans=c.size(old_crt), new_CRT_spans=c.size(new_crt),
            disappeared_unchanged=c.size(before_unchanged)-c.size(retained),
            added_unchanged=c.size(hot)-c.size(new_crt)-c.size(retained),
            independently_covered_by_family=overlap, union_bound=c.size(covered),
            unclassified=c.size(unclassified), unclassified_runs=len(unclassified),
            ten_longest_unclassified=sorted(unclassified, key=lambda p:p[0]-p[1])[:10])
    receipt = dict(input_sha256=crt["output_sha256"], operation_count=crt_ops,
                   family_ranges=families, thresholds=result)
    args.out.write_text(json.dumps(receipt, indent=2)+"\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    p = ArgumentParser(description=__doc__)
    for name in ("phase", "central", "combined", "nested", "other", "out"):
        p.add_argument("--"+name, type=Path, required=True)
    main(p.parse_args())
