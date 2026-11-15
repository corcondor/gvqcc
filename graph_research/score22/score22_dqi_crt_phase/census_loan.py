#!/usr/bin/env python3
"""Measure actual width after restoring the dirty borrowed lanes."""
from argparse import ArgumentParser
from pathlib import Path
import json
import sys


def main(args):
    sys.path.insert(0,str(args.central))
    from census import read_width, union, intersection, size, subtract, digest
    from census_combined import gap_map, shifted, stage_hot
    reference = json.loads((args.root/"splice.json").read_text())
    change = json.loads((args.root/"loan_splice.json").read_text())
    assert reference["output_sha256"] == change["input_sha256"]
    baseline_ops = reference["header"]["num_ops"]
    optimized_ops = change["header"]["num_ops"]
    old = read_width(args.root/"lifetimes.tsv",baseline_ops)
    new = read_width(args.root/"loans_lifetime.tsv",optimized_ops)
    spans = [(x["start"],x["end"],x["new_start"],x["new_end"]) for x in change["splice"]]
    untouched = gap_map(baseline_ops,spans)
    result = {}
    for width in (889,888,881):
        old_hot = stage_hot(old,width,union)
        new_hot = stage_hot(new,width,union)
        old_spliced = intersection(old_hot,union([(a,b) for a,b,_,_ in spans]))
        new_spliced = intersection(new_hot,union([(a,b) for _,_,a,b in spans]))
        visible = union(shifted(old_hot,untouched))
        gained = subtract(new_hot,union([*visible,*new_spliced]))
        lost = subtract(visible,new_hot)
        result[width]=dict(old_total=size(old_hot),new_total=size(new_hot),
                           old_spliced=size(old_spliced),new_spliced=size(new_spliced),
                           new_total_runs=len(new_hot),outside_new=size(gained),outside_removed=size(lost))
    output=dict(output_sha256=change["output_sha256"],counts=result,
                old_lifetime_sha=digest(args.root/"lifetimes.tsv"),
                new_lifetime_sha=digest(args.root/"loans_lifetime.tsv"))
    args.out.write_text(json.dumps(output,indent=2)+"\n")
    print(json.dumps(output,indent=2))


if __name__=="__main__":
    parser=ArgumentParser(description=__doc__)
    for key in ("central","root","out"):
        parser.add_argument("--"+key,type=Path,required=True)
    main(parser.parse_args())
