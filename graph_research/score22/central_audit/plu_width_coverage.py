"""Compare active wire spans for the exact PLU compute/return pair."""

from argparse import ArgumentParser
import json
from pathlib import Path

from census import intersection, read_width, size, union


def load(path):
    return json.loads(path.read_text())


def count_width(segments, threshold, scope=None):
    ready = union([(start, stop) for start, stop, width in segments if width >= threshold])
    return size(ready if scope is None else intersection(ready, [scope]))


def main():
    cli = ArgumentParser(description=__doc__)
    cli.add_argument("prior", type=Path, help="Directory containing lifetimes_all.json/tsv")
    cli.add_argument("candidate", type=Path, help="Directory containing plu_dqi_all receipts")
    cli.add_argument("output", type=Path)
    args = cli.parse_args()
    before = load(args.prior / "lifetimes_all.json")
    after = load(args.candidate / "plu_dqi_all_lifetimes.json")
    old_width = read_width(args.prior / "lifetimes_all.tsv", before["num_ops"])
    new_width = read_width(args.candidate / "plu_dqi_all_lifetimes.tsv", after["num_ops"])
    regions = load(args.candidate / "plu_dqi_all_bind.json")["matches"]
    rows = []
    for region in regions:
        row = {}
        for key, widths in (("old", old_width), ("new", new_width)):
            bounds = (region[f"{key}_start"], region[f"{key}_end"])
            row[key] = dict(interval=bounds,
                            max_width=max(w for a, b, w in widths if a < bounds[1] and b > bounds[0]),
                            cut_counts={q: count_width(widths, q, bounds) for q in (881, 889)})
        rows.append(row)
    result = dict(whole_peak_before=before["peak"], whole_peak_after=after["peak"],
                  q889_total_before=count_width(old_width, 889),
                  q889_total_after=count_width(new_width, 889), paired_splice_scope=rows)
    args.output.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
