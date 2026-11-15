"""Bind consuming GF24 sites and intersect a fixed-order DQI lifetime profile."""

from argparse import ArgumentParser
from bisect import bisect_left, bisect_right
from collections import Counter
from csv import DictReader
from hashlib import file_digest
import json
from pathlib import Path
import sys


PIN = "e4e110436080b8538f50511dc7064185e1708c2bd386ea0e36322d7791311355"


def digest(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def open_columns(path, binary, format):
    with path.open("rb") as stream:
        magic, *fields = format.HEADER.unpack(stream.read(format.HEADER.size))
        header = dict(zip(format.HEADER_FIELDS, fields))
        assert magic == format.MAGIC and header["version"] == 2
        assert not header["num_info_tags"]
        for _ in range(header["num_registers"]):
            id, size = format.PACKET.unpack(stream.read(format.PACKET.size))
            assert id == 0
            stream.seek(size, 1)
        packets = []
        for expected in range(1, 12):
            id, size = format.PACKET.unpack(stream.read(format.PACKET.size))
            assert id == expected
            packets.append(dict(type=id, payload_offset=stream.tell(), payload_bytes=size))
            stream.seek(size, 1)
        assert stream.tell() == path.stat().st_size
    return binary(path, dict(header=header, storage=dict(operation_packets=packets)))


def emit_templates(directory, sources):
    for rel in ("after_c5/extractor_width", "night_c27/arithmetic"):
        sys.path.insert(0, str(sources / rel))
    import kickmix as km
    import direct_carry_arithmetic as direct
    from tower_inverse import xor_product

    paths = {}
    for label in ("adjoint_99", "ordinary_99", "scalar_42"):
        builder = km.CircuitBuilder()
        u = builder.create_quantum_register(24, "source")
        v = builder.create_quantum_register(24, "target")
        if label == "adjoint_99":
            direct._adjoint_consume(builder, u, v, direct.A.DEFAULT_DELTA)
        elif label == "ordinary_99":
            direct.A.emit_prefix(builder, u, v, direct.A.DEFAULT_DELTA)
        else:
            temp = builder.alloc_qubits(12)
            xor_product(builder, v[:12], u[:12], temp)
            builder.swap(v[:12], temp)
            builder.hmr(temp, builder.alloc_bits(12))
            builder.free(temp)
        path = directory / (label + ".kmb")
        builder.finish_circuit().to_file(path, format="kmb")
        paths[label] = path
    return paths


def match_sites(base, template, match):
    pattern = template.opcodes
    before = list(template.operations(0, len(pattern)))
    sites = []
    offset = 0
    while (i := base.opcodes.find(pattern, offset)) >= 0:
        offset = i + 1
        if match(before, base.operations(i, i + len(pattern))) is not None:
            sites.append((i, i + len(pattern)))
    return sites


def read_width(path, operation_count):
    events = Counter()
    fixed_abi = set()
    with path.open() as stream:
        for row in DictReader(stream, delimiter="\t"):
            q, start, end = (int(row[key]) for key in ("q", "first", "last"))
            if int(row["abi"]):
                assert start == 0 and end == operation_count
                fixed_abi.add(q)
            else:
                events[start] += 1
                events[end] -= 1
    width = len(fixed_abi)
    end = 0
    segments = []
    for i, diff in sorted(events.items()):
        if end < i:
            segments.append((end, i, width))
        width += diff
        end = i
    if end < operation_count:
        segments.append((end, operation_count, width))
    return segments


def union(segments):
    merged = []
    for start, end in sorted(segments):
        if merged and start <= merged[-1][1]:
            p, q = merged[-1]
            merged[-1] = (p, max(q, end))
        else:
            merged.append((start, end))
    return merged


def intersection(a, b):
    i = j = 0
    matches = []
    while i < len(a) and j < len(b):
        p, q = a[i]
        r, s = b[j]
        start, end = max(p, r), min(q, s)
        if start < end:
            matches.append((start, end))
        if q <= s:
            i += 1
        else:
            j += 1
    return matches


def subtract(a, b):
    output = []
    j = 0
    for l, r in a:
        while j < len(b) and b[j][1] <= l:
            j += 1
        k = j
        while k < len(b) and b[k][0] < r:
            p, q = b[k]
            if p > l:
                output.append((l, p))
            l = max(l, q)
            k += 1
        if l < r:
            output.append((l, r))
    return output


def size(segments):
    return sum(end - start for start, end in segments)


def coverage(hot, sites):
    starts, ends = zip(*hot) if hot else ((), ())
    counts = {}
    for label, intervals in sites.items():
        eligible = [i for i in intervals if bisect_right(ends, i[0]) < bisect_left(starts, i[1])]
        counts[label] = dict(intersecting_sites=len(eligible),
                             covered_positions=size(intersection(hot, union(intervals))))
    both_99 = union(sites["adjoint_99"] + sites["ordinary_99"])
    total = union([*both_99, *sites["scalar_42"]])
    remainder = subtract(hot, both_99)
    remaining_all = subtract(hot, total)
    return dict(positions=size(hot), disjoint_hot_intervals=len(hot), by_family=counts,
                covered_by_any_99=size(intersection(hot, both_99)),
                outside_any_99=size(remainder), intervals_outside_any_99=len(remainder),
                outside_all_three_families=size(remaining_all),
                intervals_outside_all_three_families=len(remaining_all),
                first_remainder_after_any_99=remainder[:10])


def main():
    cli = ArgumentParser(description=__doc__)
    cli.add_argument("circuit", type=Path)
    cli.add_argument("intervals", type=Path)
    cli.add_argument("out", type=Path)
    cli.add_argument("--prior-code", type=Path, required=True)
    cli.add_argument("--dqi-source", type=Path, required=True)
    args = cli.parse_args()
    assert digest(args.circuit) == PIN
    sys.path.insert(0, str(args.prior_code))
    from dqi_ccx_peephole import BinaryCircuit
    import kmb_profile
    from outcome_dqi_chart_match import match

    base = open_columns(args.circuit, BinaryCircuit, kmb_profile)
    templates = emit_templates(args.out.parent, args.dqi_source)
    sites = {}
    details = {}
    for label, path in templates.items():
        reference = open_columns(path, BinaryCircuit, kmb_profile)
        sites[label] = match_sites(base, reference, match)
        details[label] = dict(length=len(reference.opcodes), sites=len(sites[label]),
                              template_sha256=digest(path), ranges=sites[label])
        print(label, details[label]["sites"], sites[label][:5], flush=True)
        reference.close()
    segments = read_width(args.intervals, len(base.opcodes))
    central = [(17126975, 54178104)]
    summary = {}
    for threshold in (889, 888, 885, 881):
        hot = union([(l, r) for l, r, width in segments if width >= threshold])
        summary[str(threshold)] = dict(all=coverage(hot, sites),
                                       central=coverage(intersection(hot, central), sites))
    result = dict(source_sha256=PIN, interval_tsv_sha256=digest(args.intervals),
                  operations=len(base.opcodes), central=central, details=details,
                  thresholds=summary)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)
    base.close()


if __name__ == "__main__":
    main()
