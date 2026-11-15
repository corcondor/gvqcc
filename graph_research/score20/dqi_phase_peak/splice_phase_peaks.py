#!/usr/bin/env python3
"""Splice exact GF4096 masked inverse phases and certify local boundaries."""
from argparse import ArgumentParser
from bisect import bisect_left
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HEADER_COUNTS = (
    ("num_ops", 1, 1),
    ("num_ops_with_3_target_qubits", 2, 4),
    ("num_ops_with_2_target_qubits", 5, 4),
    ("num_ops_with_1_target_qubits", 7, 4),
    ("num_ops_with_1_target_bit", 8, 4),
    ("num_ops_with_1_condition_bit", 9, 4),
    ("num_ops_with_angle", 10, 16),
)


def condition_scopes(ops):
    positions = np.flatnonzero(np.isin(ops, [0x01, 0x81]))
    stack = []
    parents = {-1: -1}
    top_after = np.full(len(positions), -1, dtype=np.int32)
    for i, position in enumerate(positions):
        position = int(position)
        if ops[position] == 0x81:
            parents[position] = stack[-1] if stack else -1
            stack.append(position)
        else:
            stack.pop()
        if stack:
            top_after[i] = stack[-1]
    assert not stack

    def top(position):
        i = int(positions.searchsorted(position)) - 1
        return int(top_after[i]) if i >= 0 else -1

    def dominates(ancestor, descendant):
        while descendant != -1 and ancestor != descendant:
            descendant = parents[descendant]
        return ancestor == descendant

    return top, dominates


def bit_accesses(circuit, ops, affected):
    results = defaultdict(list)
    for column, flag in ((8, 0x40), (9, 0x80)):
        packet = circuit.packets[column]
        operands = np.frombuffer(circuit.data, dtype="<u4",
                                 count=packet["payload_bytes"] // 4,
                                 offset=packet["payload_offset"])
        positions = np.flatnonzero(ops & flag)
        assert len(positions) == len(operands)
        for i in np.flatnonzero(np.isin(operands, sorted(affected))):
            results[int(operands[i])].append((int(positions[i]), flag))
        del operands
    for accesses in results.values():
        accesses.sort()
    return results


def lifetimes(path):
    intervals = defaultdict(list)
    with path.open() as source:
        for row in csv.DictReader(source, delimiter="\t"):
            intervals[int(row["q"])].append((int(row["first"]), int(row["last"])))
    for spans in intervals.values():
        spans.sort()
    return intervals


def clean_at(intervals, q, position):
    spans = intervals[q]
    i = bisect_left(spans, (position, 0))
    return i == 0 or spans[i - 1][1] <= position


def select(circuit, old, records, life):
    ops = np.frombuffer(circuit.opcodes, dtype=np.uint8)
    top, dominates = condition_scopes(ops)
    old_internal = {op.bit for op in old.operations(0, len(old.opcodes))
                    if op.bit is not None}
    assert all(bit >= 12 for bit in old_internal)
    for site in records:
        site["affected"] = sorted(int(site["bmap"][str(b)]) for b in old_internal)
    accesses = bit_accesses(circuit, ops, {b for site in records for b in site["affected"]})
    inputs = defaultdict(list)
    modified = defaultdict(list)
    from bisect import bisect_right
    from functools import lru_cache
    top = lru_cache(maxsize=100000)(top)
    for site in records:
        assert top(site["start"]) == top(site["end"])
        assert all(clean_at(life, q, site["start"]) for q in site["helpers"])
        mask = {site["bmap"][str(b)] for b in range(12)}
        assert not set(site["affected"]) & mask
        for b in mask:
            inputs[b].append((site["start"], 0))
        for b in site["affected"]:
            modified[b].append(site["start"])
    rejects = []
    skipped = set()
    while True:
        failures = {}
        active = [site for site in records if site["start"] not in skipped]
        records_by_start = {site["start"]: site for site in active}
        active_starts = sorted(records_by_start)
        for bit, all_modifications in modified.items():
            modifies = [position for position in all_modifications if position in records_by_start]
            if not modifies:
                continue
            external = accesses[bit]
            virtual = [row for row in inputs[bit] if row[0] in records_by_start]
            if virtual:
                external = sorted(external + virtual)
            for i, start in enumerate(modifies):
                end = records_by_start[start]["end"]
                limit = modifies[i + 1] if i + 1 < len(modifies) else len(ops)
                written_scopes = set()
                k = bisect_left(external, (end, 0))
                while k < len(external):
                    position, flag = external[k]
                    if position >= limit:
                        break
                    k += 1
                    if flag:
                        at = bisect_right(active_starts, position) - 1
                        if at >= 0 and position < records_by_start[active_starts[at]]["end"]:
                            continue
                    scope = top(position)
                    opcode = ops[position]
                    if flag == 0x40 and opcode in (0x40, 0x41, 0x50):
                        if scope == -1:
                            break
                        written_scopes.add(scope)
                    elif not any(dominates(writer, scope) for writer in written_scopes):
                        failures.setdefault(start, dict(bit=bit, next_position=position,
                            next_opcode=hex(opcode), flag=flag, next_scope=scope))
                        break
        if not failures:
            break
        skipped.update(failures)
        rejects.extend(dict(start=start, failure=failure) for start, failure in failures.items())
    selected = [site for site in records if site["start"] not in skipped]
    return selected, rejects


def prepare(site, fixture, fresh, operation):
    qmap = {i: site["qmap"][str(i)] for i in range(12)}
    helper_ids = sorted(site["helpers"])
    assert len(helper_ids) == 12
    qmap.update(zip(range(19, 30), helper_ids[:-1]))
    bmap = {i: site["bmap"][str(i)] for i in range(12)}
    bmap.update({old: fresh + old - 12 for old in range(12, fixture.profile["header"]["num_bits"])})
    operations = [operation(0x40, bit=bmap[i]) for i in bmap if i >= 12]
    for op in fixture.operations(0, len(fixture.opcodes)):
        operations.append(operation(op.opcode, tuple(qmap[q] for q in op.qubits),
                                    bmap[op.bit] if op.bit is not None else None,
                                    bmap[op.condition] if op.condition is not None else None,
                                    op.angle))
    return operations


def write(circuit, fixture, selected, output, kp, binary, encode):
    fresh = circuit.profile["header"]["num_bits"]
    fresh_count = fixture.profile["header"]["num_bits"] - 12
    columns = {k: [] for k in range(1, 11)}
    receipts = []
    offset = 0
    for site in selected:
        start, end = site["start"], site["end"]
        replacement = prepare(site, fixture, fresh, binary.Operation)
        encoded = encode(replacement)
        for k in columns:
            lo, hi = circuit.column_range(k, start, end)
            columns[k].append((lo, hi, encoded[k]))
        receipts.append(dict(old_start=start, old_end=end, new_start=start + offset,
                             new_end=start + offset + len(replacement),
                             dropped_helper=site["max_helper"],
                             old_scratch_bits_dead=len(site["affected"])))
        offset += len(replacement) - (end - start)
    header = dict(circuit.profile["header"])
    header["num_bits"] += fresh_count
    sizes = {k: circuit.packets[k]["payload_bytes"] for k in circuit.packets}
    for k, patches in columns.items():
        sizes[k] += sum(len(payload) - (hi - lo) for lo, hi, payload in patches)
    for field, k, width in HEADER_COUNTS:
        header[field] = sizes[k] // width
    assert header["num_ops_with_3_target_qubits"] == circuit.profile["header"]["num_ops_with_3_target_qubits"]
    created = False
    try:
        with output.open("xb") as target:
            created = True
            target.write(kp.HEADER.pack(kp.MAGIC, *(header[k] for k in kp.HEADER_FIELDS)))
            binary.copy_range(circuit.data, target, kp.HEADER.size, circuit.packets[1]["header_offset"])
            for k, size in sizes.items():
                pkt = circuit.packets[k]
                target.write(kp.PACKET.pack(k, size))
                base, head = pkt["payload_offset"], 0
                for lo, hi, payload in columns.get(k, ()):
                    assert head <= lo <= hi
                    binary.copy_range(circuit.data, target, base + head, base + lo)
                    target.write(payload)
                    head = hi
                binary.copy_range(circuit.data, target, base + head, base + pkt["payload_bytes"])
    except BaseException:
        if created:
            output.unlink(missing_ok=True)
        raise
    with output.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    return dict(header=header, sha256=digest, sites=receipts)


def main(args):
    sys.path.insert(0, str(args.repo))
    import kmb_splice as ks
    import kmb_profile as kp
    import dqi_ccx_peephole as binary
    from outcome_dqi_chart_splice_norm import encode

    baseline = ks.open_circuit(args.baseline, args.profile)
    records = json.loads(args.bindings.read_text())["records"]
    sites = next(r["matches"] for r in records if r["name"] == "masked")
    old = ks.open_circuit(args.pieces / "masked_original.kmb")
    new = ks.open_circuit(args.pieces / "masked_phase11.kmb")
    try:
        assert all(a["end"] <= b["start"] for a, b in zip(sites, sites[1:]))
        selected, rejected = select(baseline, old, sites, lifetimes(args.life))
        report = dict(status="NO_SELECTED_REPLACEMENTS", selected=len(selected),
                      dropped_helper_histogram=dict(Counter(s["max_helper"] for s in selected)),
                      rejected=rejected)
        print(json.dumps({k: v for k, v in report.items() if k != "rejected"}), flush=True)
        if rejected:
            print(json.dumps(rejected[:4]), flush=True)
        if selected:
            report["output"] = write(baseline, new, selected, args.output, kp, binary, encode)
            report["status"] = "EXACT_MASKED_COMPONENT_SPLICE"
    finally:
        new.close()
        old.close()
        baseline.close()
    args.receipt.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    for name in ("repo", "baseline", "profile", "pieces", "life", "bindings", "output", "receipt"):
        parser.add_argument("--" + name, type=Path, required=True)
    main(parser.parse_args())
