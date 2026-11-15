"""Exact lifetime-event census for fixed and replaced chart segments."""
from argparse import ArgumentParser
from collections import defaultdict
import csv
import json
from pathlib import Path


def census(path, ranges):
    events=defaultdict(int)
    with path.open() as stream:
        for row in csv.DictReader(stream,delimiter="\t"):
            events[int(row["first"])]+=1
            events[int(row["last"])]-=1
    peaks={881:0,888:0,889:0}
    local=[dict(max_width=0,Q889_positions=0,above_Q881_positions=0) for lo,hi in ranges]
    active=0
    maximum=0
    last=0
    for pos,delta in sorted(events.items()):
        if last<pos:
            for level in peaks:
                if active>=level:
                    peaks[level]+=pos-last
            for j,(start,end) in enumerate(ranges):
                length=max(0,min(pos,end)-max(last,start))
                if length:
                    local[j]["max_width"]=max(local[j]["max_width"],active)
                    local[j]["Q889_positions"]+=length*(active>=889)
                    local[j]["above_Q881_positions"]+=length*(active>881)
            maximum=max(maximum,active)
        active+=delta
        last=pos
    return dict(Q=maximum,global_positions_at_or_above=peaks,sites=local)


def main():
    p=ArgumentParser(description=__doc__)
    p.add_argument("source_lives",type=Path)
    p.add_argument("new_lives",type=Path)
    p.add_argument("splice",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    changes=json.loads(a.splice.read_text())["sites"]
    report={}
    for label,paths in (("old",a.source_lives),("new",a.new_lives)):
        report[label]=census(paths,[(site[label+"_start"],site[label+"_end"]) for site in changes])
    a.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report))


if __name__=="__main__":
    main()
