"""Classify every peak position by operand-bound source calling ranges."""

from argparse import ArgumentParser
from collections import Counter, defaultdict
from csv import DictReader
import json
from pathlib import Path


def load(path):
    return json.loads(path.read_text())


def relocated(ranges, splices):
    """Preserve the entire updated range when nested component edits lie inside."""
    def cut(position):
        delta = 0
        for site in splices:
            if position <= site["old_start"]:
                break
            if position < site["old_end"]:
                raise ValueError(f"source boundary {position} intersects replacement")
            delta = site["new_end"] - site["old_end"]
        return position + delta

    return [(cut(lo), cut(hi), label, priority) for lo, hi, label, priority in ranges]


def source_ranges(source, crt):
    bindings = {scope["label"]: scope["e4"] for scope in source["scopes"] if "e4" in scope}
    spans = [(*scope["e4"], scope["label"], scope["depth"] + 1)
             for scope in source["scopes"] if "e4" in scope]
    first_return = bindings["pipeline.emit_key_closing"][0]
    last_return = bindings["scalar_seed.close_padded"][0]
    spans.append((first_return, last_return, "crt.emit_closing", 3))
    # The 34 forward calls are independently matched in their entirety.
    spans.extend((row["start"],row["end"],"crt.emit_prefix",3) for row in crt["matches"])
    return spans


def report(peaks, spans, inner, idle):
    cuts = sorted({cut for lo,hi,_ in peaks for cut in (lo,hi)}
                  | {cut for a,b,_,_ in spans+inner for cut in (a,b)})
    groups = defaultdict(lambda: dict(positions=0, peak_intervals=set(), idle_intersection=None))
    family_totals = Counter()
    rows = []
    position = 0
    unlabeled = 0
    for left, right in zip(cuts, cuts[1:]):
        while position < len(peaks) and peaks[position][1] <= left:
            position += 1
        if position == len(peaks):
            break
        if not peaks[position][0] <= left < right <= peaks[position][1]:
            continue
        active = [(priority,label) for a,b,label,priority in spans if a <= left < right <= b]
        label = max(active)[1] if active else "UNBOUND"
        deepest = sorted({name for a,b,name,_ in inner if a <= left < right <= b})
        amount = right-left
        if not deepest:
            unlabeled += amount
        for each in deepest:
            family_totals[each] += amount
        g = groups[label]
        g["positions"] += amount
        g["peak_intervals"].add(position)
        avail = idle[peaks[position][:2]]
        g["idle_intersection"] = (avail if g["idle_intersection"] is None
                                  else g["idle_intersection"] & avail)
        record = [left,right,label,deepest]
        if rows and rows[-1][1] == left and rows[-1][2:] == record[2:]:
            rows[-1][1] = right
        else:
            rows.append(record)
    for group in groups.values():
        group["peak_intervals"] = len(group["peak_intervals"])
        group["idle_intersection"] = sorted(group["idle_intersection"])
    return rows, dict(callers=groups, inner_membership_totals=dict(family_totals),
                      not_bound_to_exact_inner_template=unlabeled,
                      caller_count=len(groups), total_positions=sum(r[1]-r[0] for r in rows))


def main():
    p = ArgumentParser(description=__doc__)
    for name in ("source","crt","phase","combined","combined-census","virtual","peaks","operands","out"):
        p.add_argument("--"+name, type=Path, required=True)
    a = p.parse_args()
    splices82 = load(a.phase)["output"]["sites"]
    splices34 = load(a.combined)["splices"]
    original = source_ranges(load(a.source), load(a.crt))
    stage_ranges = relocated(relocated(original, splices82), splices34)
    inner = [(lo,hi,family,0) for family, spans in load(a.combined_census)["family_ranges"].items()
             for lo,hi in spans]
    inner += [(row["start"], row["end"],"gauge_park_virtual.products",0)
              for family in load(a.virtual)["families"] for row in family["matches"]]
    peaks = [tuple(map(int, line.split())) for line in a.peaks.read_text().splitlines()]
    with a.operands.open() as stream:
        idle = {
            (int(row["start"]),int(row["stop_exclusive"])): set(map(int,row["scratch_idle"].split(",")))
            if row["scratch_idle"] else set() for row in DictReader(stream, delimiter="\t")
        }
    rows, stats = report(peaks, stage_ranges, inner, idle)
    assert stats["total_positions"] == 3_978_150
    (a.out/"families.json").write_text(json.dumps(stats, indent=2) + "\n")
    with (a.out/"peak_membership.tsv").open("w") as stream:
        stream.write("start\tstop_exclusive\tcaller\texact_inner_families\n")
        for left,right,caller,exact in rows:
            stream.write(f"{left}\t{right}\t{caller}\t{','.join(exact)}\n")
    with (a.out/"caller_ranges.tsv").open("w") as stream:
        for lo,hi,label,_ in sorted(stage_ranges):
            stream.write(f"{lo}\t{hi}\t{label}\n")
    print(json.dumps(stats))


if __name__ == "__main__":
    main()
