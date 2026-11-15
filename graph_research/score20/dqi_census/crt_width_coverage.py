"""Compare branch-lifetime cut counts across the exact CRT splice."""

from argparse import ArgumentParser
import json
from pathlib import Path

from census import intersection, read_width, size, union


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path,
                        help="Directory containing binding, stage receipt and branch interval profiles")
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    root = args.directory

    def read(name):
        return json.loads((root / name).read_text())

    binding = read("crt_e4_bind.json")
    assert binding["exact_sites"] == 1
    prior = read("branch_lifetimes.json")
    updated = read("crt_branch_lifetimes.json")
    interval = binding["matches"][0]
    marks = next(row["marks"] for row in read("crt_native_last/result.json")["rows"]
                 if row["case"] == "split_prefix")
    bounds = [(interval["new_start"] + marks[mark]["operation"])
              for mark in ("begin_residue", "end_residue")]
    residue = [tuple(bounds)]
    stages = [[(interval["start"], interval["end"])],
              [(interval["new_start"], interval["new_end"])]]
    original_segments = read_width(root / "branch_lifetimes.tsv", prior["num_ops"])
    new_segments = read_width(root / "crt_branch_lifetimes.tsv", updated["num_ops"])
    comparisons = {}
    for threshold in (889, 888, 885, 881):
        before, after = [union([(a, b) for a, b, width in segments if width >= threshold])
                         for segments in (original_segments, new_segments)]
        before_stage = intersection(before, stages[0])
        after_stage = intersection(after, stages[1])
        residual_positions = intersection(after_stage, residue)
        assert size(after_stage) == size(residual_positions)
        comparisons[threshold] = dict(
            old_whole=size(before), new_whole=size(after),
            old_block=size(before_stage), new_block=size(after_stage),
            new_block_inside_residue=size(residual_positions),
            new_block_peak_intervals=after_stage if threshold == 889 else None,
        )
    report = dict(whole_width_before=prior["peak"], whole_width_after=updated["peak"],
                  stages=stages, residue=residue, measure=comparisons,
                  stock_dqi_verifier_ran=False)
    args.report.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
