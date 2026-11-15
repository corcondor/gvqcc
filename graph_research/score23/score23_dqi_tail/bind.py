"""Bind and splice closed segmented zero-checks into the extractor callers."""

from argparse import ArgumentParser
from bisect import bisect_left
from collections import defaultdict
from csv import DictReader
import json
from pathlib import Path
import sys

import numpy as np


def move_boundary(index, splices):
    assert not any(s["start"] < index < s["end"] for s in splices)
    return index + sum((s["new_end"] - s["new_start"]) - (s["end"] - s["start"])
                       for s in splices if s["end"] <= index)


def bind_inside(base, template, callers, match):
    before = list(template.operations(0, len(template.opcodes)))
    ret = []
    for caller, start, stop in callers:
        pos = start
        while (i := base.opcodes.find(template.opcodes, pos, stop)) >= 0:
            pos = i + 1
            end = i + len(template.opcodes)
            if (maps := match(before, base.operations(i, end))) is not None:
                ret.append((caller, i, end, maps))
    return ret


def first_access(base, b_ids):
    data = np.frombuffer(base.opcodes, dtype=np.uint8)
    references = defaultdict(list)
    for column, flag, writes in ((8, 64, True), (9, 128, False)):
        packet = base.packets[column]
        values = np.frombuffer(base.data, dtype="<u4", count=packet["payload_bytes"] // 4,
                               offset=packet["payload_offset"])
        positions = np.flatnonzero(data & flag)
        assert len(values) == len(positions)
        for selector in np.flatnonzero(np.isin(values, list(b_ids))):
            references[int(values[selector])].append((int(positions[selector]), writes))
        del values
    starts, ends, parents, stack = [], [], [], []
    for pos in np.flatnonzero((data == 0x81) | (data == 0x01)):
        if data[pos] == 0x81:
            parents.append(stack[-1] if stack else -1)
            stack.append(len(starts))
            starts.append(int(pos))
            ends.append(-1)
        else:
            ends[stack.pop()] = int(pos)
    assert not stack
    starts = np.array(starts, dtype=np.int64)

    def path(pos):
        scope = int(np.searchsorted(starts, pos)) - 1
        while scope >= 0 and ends[scope] <= pos:
            scope = parents[scope]
        seen = []
        while scope >= 0:
            seen.append(scope)
            scope = parents[scope]
        return seen[::-1]

    for bit in references:
        references[bit].sort()
    return references, path


def never_stale_at_read(opcodes, values, path, end):
    """Prove all executed-arm reads follow a dominating ordinary write."""
    pending = True
    ambient = []
    skipped = []
    for index, writes in values:
        if index < end:
            continue
        current = path(index)
        common = 0
        while common < min(len(current), len(ambient)) and current[common] == ambient[common]:
            common += 1
        while len(skipped) > common:
            pending |= skipped.pop()
        skipped.extend([pending] * (len(current) - common))
        ambient = current
        if writes and opcodes[index] in (0x40, 0x41, 0x50):
            pending = False
        elif pending:
            # A read or a read-modify-write of the old version could escape.
            return False
        if not pending and not any(skipped):
            return True
    return True


def main():
    cli = ArgumentParser(description=__doc__)
    cli.add_argument("--source", type=Path, required=True)
    cli.add_argument("--source-lifetime", type=Path, required=True)
    cli.add_argument("--loan-receipt", type=Path, required=True)
    cli.add_argument("--callers", type=Path, required=True)
    cli.add_argument("--prior-code", type=Path, required=True)
    cli.add_argument("--central", type=Path, required=True)
    cli.add_argument("--native", type=Path, required=True)
    cli.add_argument("--out", type=Path, required=True)
    cli.add_argument("--output-kmb", type=Path)
    cli.add_argument("--schedule-helpers", action="store_true")
    args = cli.parse_args()
    sys.path[:0] = [str(args.central), str(args.prior_code)]
    import dqi_ccx_peephole as binary
    import kmb_profile
    from outcome_dqi_chart_match import match
    from outcome_dqi_chart_splice_norm import encode
    from census import digest, intersection, open_columns, read_width, size, union
    from splice_plu_crt import write_patches

    loan = json.loads(args.loan_receipt.read_text())
    assert digest(args.source) == loan["output_sha256"]
    base = open_columns(args.source, binary.BinaryCircuit, kmb_profile)
    callers = []
    for row in args.callers.read_text().splitlines():
        lo, hi, label = row.split("\t")
        if label.startswith("extractor."):
            callers.append((label, move_boundary(int(lo), loan["splice"]),
                            move_boundary(int(hi), loan["splice"])))
    lifetimes = read_width(args.source_lifetime, len(base.opcodes))
    starts, finishes = defaultdict(list), defaultdict(list)
    if args.schedule_helpers:
        with args.source_lifetime.open() as stream:
            for row in DictReader(stream, delimiter="\t"):
                wire = int(row["q"])
                starts[wire].append(int(row["first"]))
                finishes[wire].append(int(row["last"]))

    def crossing(wire, point):
        k = bisect_left(starts[wire], point) - 1
        return k >= 0 and finishes[wire][k] > point
    hot = {threshold: union([(a, b) for a, b, w in lifetimes if w >= threshold])
           for threshold in (881, 888, 889)}
    fixtures = {}
    hits = []
    for kind in ("xor", "phase"):
        old = open_columns(args.native / f"{kind}_original.kmb", binary.BinaryCircuit, kmb_profile)
        new = open_columns(args.native / f"{kind}_narrow.kmb", binary.BinaryCircuit, kmb_profile)
        exported = set() if kind == "xor" else {0}
        before = {op.bit for op in old.operations(0, len(old.opcodes)) if op.bit is not None}
        regions = bind_inside(base, old, callers, match)
        print(kind, len(regions), flush=True)
        fixtures[kind] = (old, new, exported, before - exported)
        hits.extend((i, end, caller, kind, maps) for caller, i, end, maps in regions)
    hits.sort(key=lambda item: item[0])
    assert all(a[1] <= b[0] for a, b in zip(hits, hits[1:]))
    retired_ids = {maps["bits"][bit]
                   for _, _, _, kind, maps in hits for bit in fixtures[kind][3]}
    references, path = first_access(base, retired_ids)
    patches = []
    scopes = []
    rejected = []
    offset = 0
    next_bit = base.profile["header"]["num_bits"]
    for i, end, caller, kind, maps in hits:
        if path(i) != path(end):
            raise ValueError("The matched clause modifies its caller condition")
        old, new, exported, removed = fixtures[kind]
        unsafe = []
        for bit in removed:
            actual = maps["bits"][bit]
            if not never_stale_at_read(base.opcodes, references[actual], path, end):
                unsafe.append(actual)
        if unsafe:
            rejected.append(dict(kind=kind, start=i, end=end, would_keep_classical=unsafe))
            continue
        remap = {idx: maps["bits"][idx] for idx in exported}
        quantum = maps["qubits"].copy()
        if args.schedule_helpers:
            first_helper = 25 if kind == "xor" else 24
            owned = [maps["qubits"][q] for q in range(first_helper,
                                                        old.profile["header"]["num_qubits"])]
            # The original module allocates these 22 clean. Choose 14 of its
            # owned physical names, prioritizing carried lifetimes.
            owned.sort(key=lambda physical: not crossing(physical, i))
            for q in range(first_helper, new.profile["header"]["num_qubits"]):
                quantum[q] = owned[q - first_helper]

        def bit_index(idx):
            nonlocal next_bit
            if idx is None:
                return None
            if idx not in remap:
                remap[idx] = next_bit
                next_bit += 1
            return remap[idx]

        replacement = [binary.Operation(op.opcode, tuple(quantum[q] for q in op.qubits),
                                        bit_index(op.bit), bit_index(op.condition), op.angle)
                       for op in new.operations(0, len(new.opcodes))]
        patches.append((i, end, replacement))
        scopes.append(dict(caller=caller, kind=kind, old_start=i, old_end=end,
                           new_start=i + offset, new_end=i + offset + len(replacement),
                           old_width_counts={w: size(intersection(ranges, [(i, end)]))
                                             for w, ranges in hot.items()}))
        offset += len(replacement) - (end - i)
    report = dict(source_sha256=loan["output_sha256"], exact_matches=len(hits), selected=scopes,
                  rejected_classical=rejected, static_t_delta=len(scopes) * 8,
                  rescheduled_owned_helpers=args.schedule_helpers)
    if args.output_kmb is not None:
        header = write_patches(base, args.output_kmb, patches, binary, encode, next_bit)
        report.update(candidate_sha256=digest(args.output_kmb), header=header)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print({k: len(v) if isinstance(v, list) else v for k, v in report.items()}, flush=True)
    for old, new, *_ in fixtures.values():
        old.close()
        new.close()
    base.close()


if __name__ == "__main__":
    main()
