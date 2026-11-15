"""List all high-width slices and intersect physical wire and lifetime IDs."""

from argparse import ArgumentParser
from bisect import bisect_right
from collections import Counter, defaultdict
from csv import DictReader
from hashlib import file_digest
from pathlib import Path
from struct import unpack
import json


KNOWN_TAPES = {
    "9d97cda71833e8ae4776355b9c39d3b90fba6f778bf4e869345feff477892d1d": 8_607_724,
    "9cb3f1baf125912fc48c22813cb34e375de71b0741c02e9846aa95a4b1b04789": 3_978_150,
}


def header_and_ports(path):
    ports = {}
    with path.open("rb") as stream:
        header = stream.read(104)
        version, nq, _, nr, ops = unpack("<IIIIQ", header[16:40])
        if version != 2:
            raise ValueError("Expected KMB version 2")
        for _ in range(nr):
            kind, size = unpack("<QQ", stream.read(16))
            if kind:
                raise ValueError("Expected a register packet")
            data = stream.read(size)
            names, count = unpack("<II", data[:8])
            name = data[8:8+names].decode()
            addresses = unpack("<" + "I" * count, data[8+names:])
            wires = [x & 0x7FFFFFFF for x in addresses if x & 0x80000000]
            if wires:
                if len(wires) != count:
                    raise ValueError("Unexpected mixed input port")
                ports[name] = wires
    return nq, ops, ports


def read_lifetimes(path, n):
    lifetimes = defaultdict(list)
    events = defaultdict(list)
    with path.open() as stream:
        for row in DictReader(stream, delimiter="\t"):
            q, start, stop = (int(row[k]) for k in ("q", "first", "last"))
            if not 0 <= start <= stop <= n:
                raise ValueError(f"Invalid lifetime of q{q}")
            if stop == start:
                continue
            identity = len(lifetimes[q])
            lifetimes[q].append((start, stop))
            events[start].append((q, identity, True))
            events[stop].append((q, identity, False))
    return lifetimes, events


def profile(events, n, threshold):
    positions = Counter()
    physical = persistent = None
    active = {}
    spans = []
    earlier = 0
    for now, updates in sorted(events.items()):
        width = len(active)
        if now > earlier:
            positions[width] += now - earlier
            if width >= threshold:
                if spans and spans[-1][1] == earlier and spans[-1][2] == width:
                    spans[-1][1] = now
                else:
                    spans.append([earlier, now, width])
            if width == threshold:
                wires = set(active)
                ids = set(active.items())
                physical = wires if physical is None else physical & wires
                persistent = ids if persistent is None else persistent & ids
        for q, identity, born in sorted(updates, key=lambda update: update[2]):
            if born:
                assert q not in active
                active[q] = identity
            else:
                assert active.pop(q) == identity
        earlier = now
    assert earlier == n
    return positions, spans, physical, persistent


def main():
    cli = ArgumentParser(description=__doc__)
    cli.add_argument("kmb", type=Path)
    cli.add_argument("lifetimes", type=Path)
    cli.add_argument("out", type=Path)
    args = cli.parse_args()
    with args.kmb.open("rb") as file:
        digest = file_digest(file, "sha256").hexdigest()
    if digest not in KNOWN_TAPES:
        raise ValueError(f"Unrecognized phase-spliced member {digest}")
    nq, n, ports = header_and_ports(args.kmb)
    input_wires = {q for wires in ports.values() for q in wires}
    lifetimes, changes = read_lifetimes(args.lifetimes, n)
    positions, spans, physical, persistent = profile(changes, n, nq)
    assert nq == 889 and positions[889] == KNOWN_TAPES[digest]
    q0, q1 = spans[0][0], spans[-1][1]
    all_scratch = sorted(set(range(nq)) - input_wires)
    peak_lives = defaultdict(set)
    ends = [end for _, end, _ in spans]
    for q in all_scratch:
        for identity, (begin, stop) in enumerate(lifetimes[q]):
            index = bisect_right(ends, begin)
            if index < len(spans) and spans[index][0] < stop:
                peak_lives[q].add(identity)
    result = dict(source_sha256=digest, positions=positions[889],
                  width=nq, intervals=len(spans), cut_range=[q0,q1],
                  positions_at_or_above={
                      width:sum(n for w,n in positions.items() if w >= width)
                      for width in range(870, 890)},
                  register_ports=ports, quantum_input_wires=len(input_wires),
                  physical_intersection=sorted(physical),
                  same_lifetime_intersection={
                      q:lifetimes[q][identity] for q,identity in sorted(persistent)
                  },
                  shared_scratch_lifetimes={
                      q:lifetimes[q][identity] for q,identity in sorted(persistent)
                      if q in all_scratch
                  },
                  scratch_epochs_touching_any_peak={
                      q:len(peak_lives[q]) for q in all_scratch
                  })
    args.out.mkdir(exist_ok=True, parents=True)
    (args.out / "intersections.json").write_text(json.dumps(result, indent=2) + "\n")
    with (args.out / "peak889.tsv").open("w") as stream:
        for first, last, width in spans:
            stream.write(f"{first}\t{last}\t{width}\n")
    upper_widths = [
        (width, sum(n for w,n in positions.items() if w >= width)) for width in (880,889)]
    print(dict(width=nq, intervals=len(spans), common_physical=len(physical),
               common_abi=len(persistent)-len(result["shared_scratch_lifetimes"]),
               common_scratch=result["shared_scratch_lifetimes"],
               ranges=upper_widths, cut_range=[q0,q1]))


if __name__ == "__main__":
    main()
