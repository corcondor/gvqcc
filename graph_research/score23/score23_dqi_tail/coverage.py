"""Count region-level changes after the 24-input checkpoint replacements."""

from argparse import ArgumentParser
from collections import Counter
import json
from pathlib import Path
import sys


def measure(segments, start, stop):
    cuts = Counter()
    for a, b, w in segments:
        left, right = max(a, start), min(b, stop)
        if left < right:
            cuts[w] += right - left
    return dict(max=max(cuts), q881=sum(n for w, n in cuts.items() if w >= 881),
                q888=sum(n for w, n in cuts.items() if w >= 888), q889=cuts[889])


def main():
    cli = ArgumentParser(description=__doc__)
    cli.add_argument("--central", type=Path, required=True)
    cli.add_argument("--source", type=Path, required=True)
    cli.add_argument("--candidate", type=Path, required=True)
    cli.add_argument("--out", type=Path, required=True)
    args = cli.parse_args()
    sys.path.insert(0, str(args.central))
    from census import read_width

    def load_json(path):
        return json.loads(path.read_text())

    old = load_json(args.source / "loans_lifetime.json")
    new = load_json(args.candidate / "lifetime.json")
    bound = load_json(args.candidate / "bind_full.json")
    left = read_width(args.source / "loans_lifetime.tsv", old["num_ops"])
    right = read_width(args.candidate / "lifetimes.tsv", new["num_ops"])
    traces = []
    for row in bound["selected"]:
        before = measure(left, row["old_start"], row["old_end"])
        after = measure(right, row["new_start"], row["new_end"])
        traces.append(dict(caller=row["caller"], kind=row["kind"],
                           old_start=row["old_start"], new_start=row["new_start"],
                           before=before, after=after))
    report = dict(
        source_sha256=bound["source_sha256"], candidate_sha256=bound["candidate_sha256"],
        whole_before=measure(left, 0, old["num_ops"]), whole_after=measure(right, 0, new["num_ops"]),
        local_deltas=Counter(row["before"]["max"] - row["after"]["max"] for row in traces),
        region_count=len(traces),
        caller_counts=Counter(row["caller"] for row in traces),
        cuts_inside={name: {key: sum(row[name][key] for row in traces)
                           for key in ("q881", "q888", "q889")}
                     for name in ("before", "after")}, regions=traces,
    )
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print({k: v for k, v in report.items() if k != "regions"}, flush=True)


if __name__ == "__main__":
    main()
