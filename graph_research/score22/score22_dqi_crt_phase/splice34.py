#!/usr/bin/env python3
"""Splice all 34 checked CRT prefixes over the verified masked-phase tape."""
from argparse import ArgumentParser
from collections import Counter
import csv
import json
from pathlib import Path
import sys

import numpy as np


PHASE_SHA = "9d97cda71833e8ae4776355b9c39d3b90fba6f778bf4e869345feff477892d1d"
E4_SHA = "e4e110436080b8538f50511dc7064185e1708c2bd386ea0e36322d7791311355"
HEADER_COUNTS = (
    ("num_ops", 1, 1),
    ("num_ops_with_3_target_qubits", 2, 4),
    ("num_ops_with_2_target_qubits", 5, 4),
    ("num_ops_with_1_target_qubits", 7, 4),
    ("num_ops_with_1_target_bit", 8, 4),
    ("num_ops_with_1_condition_bit", 9, 4),
    ("num_ops_with_angle", 10, 16),
)


def fixture_registers(args, r):
    rng = np.random.default_rng(502531991 + r)
    return {name: rng.integers(0, 2, (12*n, args.shots), dtype=np.uint8).astype(bool)
            for name, n in (("N", r), ("D", r+1), ("P", 2), ("probe", r+2))}


def classical_trace(sequence):
    return [(op.opcode, op.bit, op.condition) for op in sequence
            if op.bit is not None or op.condition is not None]


def change(circuit, directory, prior_code, args, sites):
    for rel in ("night_c27/synthesis", "night_c27/arithmetic", "after_c5/extractor_width"):
        sys.path.insert(0, str(args.source / rel))
    import ew_paths  # noqa: F401
    import kickmix as km
    import fused_crt_synthesis as source
    import split_crt as split
    import dqi_ccx_peephole as binary
    from census import open_columns
    import kmb_profile
    from outcome_dqi_chart_match import match
    from outcome_dqi_chart_splice_norm import encode

    columns = {kind: [] for kind in range(1, 11)}
    receipts = []
    offset = 0
    for site in sites:
        r, node = site["r"], site["node"]
        start, end = site["start"], site["end"]
        rng = fixture_registers(args, r)
        expected = split.formula(source, rng, r, node)
        path = directory / "fixture.kmb"
        fixtures = []
        for changed in (False, True):
            for closed in (False, True):
                template, _, component_marks, helper_peak = split.build(km, source, r, node, changed, closed)
                split.check_case(km, source, rng, r, node, template, expected, (3719, 11845), closed)
                if not closed:
                    template.to_file(path, format="kmb")
                    compact = open_columns(path, binary.BinaryCircuit, kmb_profile)
                    try:
                        fixtures.append(list(compact.operations(0, len(compact.opcodes))))
                    finally:
                        compact.close()
                    if changed:
                        marks = component_marks
        path.unlink()
        old, new = fixtures
        assert end - start == len(old)
        production = list(circuit.operations(start, end))
        maps = match(old, production)
        assert maps is not None, site
        assert classical_trace(old) == classical_trace(new), site
        qubits, bits = maps["qubits"], maps["bits"]
        physical = [binary.Operation(op.opcode, tuple(qubits[q] for q in op.qubits),
                                    bits[op.bit] if op.bit is not None else None,
                                    bits[op.condition] if op.condition is not None else None,
                                    op.angle) for op in new]
        old_columns, new_columns = encode(production), encode(physical)
        for kind in columns:
            a, b = circuit.column_range(kind, start, end)
            base = circuit.packets[kind]["payload_offset"]
            assert circuit.data[base+a:base+b] == old_columns[kind]
            columns[kind].append((a, b, new_columns[kind]))
        old_t = sum((op.opcode & 0x30) == 0x30 for op in old)
        new_t = sum((op.opcode & 0x30) == 0x30 for op in new)
        assert old_t == site["original_static_t"] and new_t - old_t == 15
        assert sum(op.is_ccx for op in new) - sum(op.is_ccx for op in old) == 15
        assert all(not (op.opcode & 0x80) for op in new if op.is_ccx)
        receipt = dict(r=r, node=node, old_start=start, old_end=end,
                       new_start=start+offset, new_end=start+offset+len(physical),
                       old_static_paid=old_t, new_static_paid=new_t,
                       native_shots_per_fixture=2*args.shots)
        receipt.update({key: value["operation"] + start + offset for key, value in marks.items()})
        receipts.append(receipt)
        offset += len(physical) - (end-start)
        print(json.dumps(receipt), flush=True)
    return columns, receipts


def write(circuit, output, columns, binary, kp):
    packet_lengths = {kind: packet["payload_bytes"] for kind, packet in circuit.packets.items()}
    for kind, changes in columns.items():
        packet_lengths[kind] += sum(len(payload) - (b-a) for a,b,payload in changes)
    header = dict(circuit.profile["header"])
    header.update({key: packet_lengths[kind] // width for key,kind,width in HEADER_COUNTS})
    assert header["num_ops_with_3_target_qubits"] - circuit.profile["header"]["num_ops_with_3_target_qubits"] == 510
    temporary = output.with_suffix(".pending")
    created = False
    try:
        with temporary.open("xb") as target:
            created = True
            target.write(kp.HEADER.pack(kp.MAGIC, *(header[key] for key in kp.HEADER_FIELDS)))
            first = circuit.packets[1]["payload_offset"] - kp.PACKET.size
            binary.copy_range(circuit.data, target, kp.HEADER.size, first)
            for kind, size in packet_lengths.items():
                packet = circuit.packets[kind]
                base = packet["payload_offset"]
                target.write(kp.PACKET.pack(kind, size))
                cursor = 0
                for a,b,payload in columns.get(kind, ()):
                    assert cursor <= a <= b
                    binary.copy_range(circuit.data, target, base+cursor, base+a)
                    target.write(payload)
                    cursor = b
                binary.copy_range(circuit.data, target, base+cursor, base+packet["payload_bytes"])
        assert not output.exists()
        temporary.rename(output)
    finally:
        if created:
            temporary.unlink(missing_ok=True)
    return header


def main(args):
    sys.path.insert(0, str(args.central))
    sys.path.insert(0, str(args.repo))
    from census import open_columns, digest
    import dqi_ccx_peephole as binary
    import kmb_profile as kp

    assert digest(args.input) == PHASE_SHA
    phase = json.loads(args.phase_splices.read_text())["output"]
    assert phase["sha256"] == PHASE_SHA
    crts = json.loads(args.crt_sites.read_text())
    assert crts["source_sha256"] == E4_SHA
    sites = crts["matches"]
    assert len(sites) == 34 and all(a["end"] == b["start"] for a, b in zip(sites, sites[1:]))
    assert (sites[-1]["end"] < min(s["old_start"] for s in phase["sites"]))

    circuit = open_columns(args.input, binary.BinaryCircuit, kp)
    try:
        columns, receipts = change(circuit, args.receipt.parent, args.repo, args, sites)
        header = write(circuit, args.output, columns, binary, kp)
    finally:
        circuit.close()
    report = dict(status="PHASE_AND_ALL_CRT_SPLICED", input_sha256=PHASE_SHA,
                  output_sha256=digest(args.output), static_paid_delta=510,
                  native_shots_per_case=2*args.shots,
                  native_cases=136, header=header, splices=receipts)
    args.receipt.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    for arg in ("repo", "central", "source", "input", "phase-splices", "crt-sites", "output", "receipt"):
        parser.add_argument("--" + arg, required=True, type=Path)
    parser.add_argument("--shots", type=int, default=128)
    main(parser.parse_args())
