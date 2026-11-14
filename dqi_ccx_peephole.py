#!/usr/bin/env python3
"""Lossless KMB v2 same-control Toffoli optimization, without a Circuit object.

For distinct a,b,x,y, CCX(a,b,x); CCX(a,b,y) is replaced exactly by
CX(x,y); CCX(a,b,x); CX(x,y). A bounded search can commute one CCX through
intervening unitary gates only when a conservative, explicit rule proves that
the gates commute. Condition-stack changes, classical writes, measurement,
reset, information tags and debugging operations are barriers.

The original file is read-only. Registers and untouched operand bytes are
copied verbatim. Working memory holds compact opcode bytes and rank indexes,
not millions of Python gate objects. Operand columns are memory-mapped.

Binary format: https://github.com/quantumlib/Qualtran/blob/main/docs/kickmix/
kickmix_binary_format.md
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import mmap
from pathlib import Path
import re
import struct
import sys
import time

import kmb_profile as kp


U32 = struct.Struct("<I")
THREE_QUBIT = re.compile(rb"[\x30-\x32\xb0-\xb2]")
# Any other operation is an ordering barrier, including PUSH/POP_CONDITION.
BARRIER = re.compile(
    rb"[^\x00\x80\x10\x90\x11\x91\x13\x93"
    rb"\x20-\x22\xa0-\xa2\x30-\x32\xb0-\xb2]"
)
QUANTUM_COLUMNS = {3: (2, 3, 4), 2: (5, 6), 1: (7,), 0: ()}
COUNT_TABLES = {
    "q1": bytes(int(((x & 0x30) >> 4) == 1) for x in range(256)),
    "q2": bytes(int(((x & 0x30) >> 4) == 2) for x in range(256)),
    "q3": bytes(int(((x & 0x30) >> 4) == 3) for x in range(256)),
    "bit": bytes(int(bool(x & 0x40)) for x in range(256)),
    "condition": bytes(int(bool(x & 0x80)) for x in range(256)),
    "angle": bytes(int((x & 0x7F) == 0x13) for x in range(256)),
}
COLUMN_RANKS = {
    2: ("q3", 4), 3: ("q3", 4), 4: ("q3", 4),
    5: ("q2", 4), 6: ("q2", 4), 7: ("q1", 4),
    8: ("bit", 4), 9: ("condition", 4), 10: ("angle", 16),
}


@dataclass(frozen=True)
class Operation:
    opcode: int
    qubits: tuple[int, ...] = ()
    bit: int | None = None
    condition: int | None = None
    angle: bytes = b""
    source_index: int | None = None

    @property
    def is_ccx(self):
        return (self.opcode & 0x7F) == 0x31

    @property
    def signature(self):
        if not self.is_ccx:
            return None
        return (*sorted(self.qubits[:2]), self.condition)


class BinaryCircuit:
    """Random access to compact operand columns, with small rank checkpoints."""

    def __init__(self, path, profile, checkpoint=4096):
        self.path = Path(path)
        self.profile = profile
        self.packets = {p["type"]: p for p in profile["storage"]["operation_packets"]}
        self.file = self.path.open("rb")
        self.data = mmap.mmap(self.file.fileno(), 0, access=mmap.ACCESS_READ)
        packet = self.packets[1]
        self.opcodes = self.data[
            packet["payload_offset"]:packet["payload_offset"] + packet["payload_bytes"]
        ]
        self.checkpoint = checkpoint
        self.prefixes = {name: [0] for name in COUNT_TABLES}
        for start in range(0, len(self.opcodes), checkpoint):
            block = self.opcodes[start:start + checkpoint]
            for name, table in COUNT_TABLES.items():
                prefix = self.prefixes[name]
                prefix.append(prefix[-1] + block.translate(table).count(1))

    def close(self):
        self.data.close()
        self.file.close()

    def rank(self, name, position):
        checkpoint = position // self.checkpoint
        tail = self.opcodes[checkpoint * self.checkpoint:position]
        return self.prefixes[name][checkpoint] + tail.translate(COUNT_TABLES[name]).count(1)

    def uint32(self, column, index):
        return U32.unpack_from(self.data, self.packets[column]["payload_offset"] + 4 * index)[0]

    def ccx_at(self, position, three_qubit_index):
        opcode = self.opcodes[position]
        condition = self.uint32(9, self.rank("condition", position)) if opcode & 0x80 else None
        return Operation(
            opcode, tuple(self.uint32(k, three_qubit_index) for k in (2, 3, 4)),
            condition=condition, source_index=position,
        )

    def operations(self, start, end):
        ranks = {name: self.rank(name, start) for name in COUNT_TABLES}
        for position in range(start, end):
            opcode = self.opcodes[position]
            nq = (opcode & 0x30) >> 4
            qubits = tuple(self.uint32(k, ranks[f"q{nq}"]) for k in QUANTUM_COLUMNS[nq])
            bit = self.uint32(8, ranks["bit"]) if opcode & 0x40 else None
            condition = self.uint32(9, ranks["condition"]) if opcode & 0x80 else None
            angle = b""
            if (opcode & 0x7F) == 0x13:
                offset = self.packets[10]["payload_offset"] + 16 * ranks["angle"]
                angle = self.data[offset:offset + 16]
                ranks["angle"] += 1
            if nq:
                ranks[f"q{nq}"] += 1
            ranks["bit"] += bool(opcode & 0x40)
            ranks["condition"] += bool(opcode & 0x80)
            yield Operation(opcode, qubits, bit, condition, angle, position)

    def column_range(self, kind, start, end):
        if kind == 1:
            return start, end
        name, width = COLUMN_RANKS[kind]
        return self.rank(name, start) * width, self.rank(name, end) * width


def commutes_with_ccx(ccx, other):
    """Sufficient commutation rules, valid for arbitrary quantum states.

    Conditions may differ: each controlled gate either applies or is the
    identity, and all supported intermediate gates leave classical bits fixed.
    Stack changes and bit writes are never supported intermediate gates.
    """
    assert ccx.is_ccx
    controls = ccx.qubits[:2]
    target = ccx.qubits[2]
    base = other.opcode & 0x7F
    q = other.qubits
    if base == 0x00:  # Global (possibly classically controlled) phase.
        return True
    if base == 0x11:  # X commutes unless it flips a Toffoli control.
        return q[0] not in controls
    if base in (0x10, 0x13, 0x20, 0x30):  # Diagonal Z family.
        return target not in q
    if base in (0x21, 0x31):  # Neither gate writes a control of the other.
        return q[-1] not in controls and target not in q[:-1]
    if base in (0x22, 0x32):  # Conservative disjoint SWAP / CSWAP rule.
        return not set(q).intersection(ccx.qubits)
    return False


def discover_blocks(circuit, window):
    last = {}
    intervals = []
    counts = {"adjacent_ccx_pairs": 0, "adjacent_same_control_pairs": 0,
              "nearby_same_control_pairs": 0, "proved_commuting_pairs": 0}
    previous_ccx = None
    for index, match in enumerate(THREE_QUBIT.finditer(circuit.opcodes)):
        position = match.start()
        if (circuit.opcodes[position] & 0x7F) != 0x31:
            continue
        current = circuit.ccx_at(position, index)
        if previous_ccx is not None and previous_ccx.source_index + 1 == position:
            counts["adjacent_ccx_pairs"] += 1
            if previous_ccx.signature == current.signature:
                counts["adjacent_same_control_pairs"] += 1
        previous_ccx = current
        previous = last.get(current.signature)
        last[current.signature] = current
        if previous is None or position - previous.source_index > window:
            continue
        if previous.qubits[2] == current.qubits[2]:
            continue  # This pass performs fanout merges, not cancellation.
        counts["nearby_same_control_pairs"] += 1
        start = previous.source_index + 1
        if BARRIER.search(circuit.opcodes, start, position):
            continue
        if all(commutes_with_ccx(current, op) for op in circuit.operations(start, position)):
            allowed = True
        else:
            allowed = all(commutes_with_ccx(previous, op) for op in circuit.operations(start, position))
        if allowed:
            counts["proved_commuting_pairs"] += 1
            intervals.append((previous.source_index, position + 1))
    blocks = []
    for start, end in sorted(intervals):
        if blocks and start < blocks[-1][1]:
            blocks[-1] = (blocks[-1][0], max(end, blocks[-1][1]))
        else:
            blocks.append((start, end))
    return blocks, counts


def optimize_block(operations, window):
    """Recheck every rewrite against the CURRENT block, including new CNOTs."""
    result = list(operations)
    certificate = []
    while True:
        change = None
        for i, first in enumerate(result):
            if not first.is_ccx:
                continue
            for j in range(i + 1, min(len(result), i + window + 1)):
                second = result[j]
                if first.signature != second.signature or first.qubits[2] == second.qubits[2]:
                    continue
                middle = result[i + 1:j]
                if all(commutes_with_ccx(second, op) for op in middle):
                    direction, kept, removed = "second_left", first, second
                elif all(commutes_with_ccx(first, op) for op in middle):
                    direction, kept, removed = "first_right", second, first
                else:
                    continue
                cx = Operation(0x21 | (kept.opcode & 0x80),
                               (kept.qubits[2], removed.qubits[2]), condition=kept.condition)
                replacement = [cx, kept, cx]
                result[i:j + 1] = replacement + middle if direction == "second_left" else middle + replacement
                certificate.append({
                    "first_source_op": first.source_index,
                    "second_source_op": second.source_index,
                    "controls": list(first.qubits[:2]),
                    "first_target": first.qubits[2], "second_target": second.qubits[2],
                    "explicit_condition_bit": first.condition,
                    "direction": direction, "crossed_current_operations": len(middle),
                })
                change = True
                break
            if change:
                break
        if not change:
            return result, certificate


def encode_columns(operations):
    columns = {kind: bytearray() for kind in range(1, 11)}
    for op in operations:
        if BARRIER.fullmatch(bytes([op.opcode])):
            raise ValueError("A proposed rewrite contains an ordering barrier")
        columns[1].append(op.opcode)
        for kind, qubit in zip(QUANTUM_COLUMNS[len(op.qubits)], op.qubits):
            columns[kind].extend(U32.pack(qubit))
        if op.bit is not None:
            columns[8].extend(U32.pack(op.bit))
        if op.condition is not None:
            columns[9].extend(U32.pack(op.condition))
        columns[10].extend(op.angle)
    return {kind: bytes(value) for kind, value in columns.items()}


def copy_range(source, output, start, end, chunk_bytes=1 << 20):
    for offset in range(start, end, chunk_bytes):
        output.write(source[offset:min(end, offset + chunk_bytes)])


def write_rewritten(circuit, output_path, blocks):
    splices = {kind: [] for kind in range(1, 12)}
    for start, end, before, after in blocks:
        old_columns = encode_columns(before)
        new_columns = encode_columns(after)
        for kind in range(1, 11):
            low, high = circuit.column_range(kind, start, end)
            base = circuit.packets[kind]["payload_offset"]
            if circuit.data[base + low:base + high] != old_columns[kind]:
                raise AssertionError(f"Column {kind} does not match the original operation block")
            if old_columns[kind] != new_columns[kind]:
                splices[kind].append((low, high, new_columns[kind]))
    sizes = {kind: p["payload_bytes"] for kind, p in circuit.packets.items()}
    for kind, changes in splices.items():
        sizes[kind] += sum(len(new) - (high - low) for low, high, new in changes)
    header = dict(circuit.profile["header"])
    for field, kind, width in (
        ("num_ops", 1, 1), ("num_ops_with_3_target_qubits", 2, 4),
        ("num_ops_with_2_target_qubits", 5, 4), ("num_ops_with_1_target_qubits", 7, 4),
        ("num_ops_with_1_target_bit", 8, 4), ("num_ops_with_1_condition_bit", 9, 4),
        ("num_ops_with_angle", 10, 16),
    ):
        header[field] = sizes[kind] // width
    created = False
    try:
        with Path(output_path).open("xb") as output:
            created = True
            output.write(kp.HEADER.pack(kp.MAGIC, *(header[name] for name in kp.HEADER_FIELDS)))
            copy_range(circuit.data, output, kp.HEADER.size, circuit.packets[1]["header_offset"])
            for kind in range(1, 12):
                packet = circuit.packets[kind]
                base = packet["payload_offset"]
                output.write(kp.PACKET.pack(kind, sizes[kind]))
                cursor = 0
                for low, high, replacement in splices[kind]:
                    if low < cursor:
                        raise AssertionError("Overlapping binary column splices")
                    copy_range(circuit.data, output, base + cursor, base + low)
                    output.write(replacement)
                    cursor = high
                copy_range(circuit.data, output, base + cursor, base + packet["payload_bytes"])
    except BaseException:
        if created:
            Path(output_path).unlink(missing_ok=True)
        raise


def optimize(input_path, output_path, window=256, progress=False):
    input_path, output_path = Path(input_path).resolve(), Path(output_path).resolve()
    if not 1 <= window <= 4096:
        raise ValueError("The operation window must be between 1 and 4096")
    if input_path == output_path or output_path.exists():
        raise FileExistsError("The output must be a new file, separate from the input")
    started = time.monotonic()
    before_profile = kp.profile(input_path, progress=progress, max_register_summaries=0)
    circuit = BinaryCircuit(input_path, before_profile)
    try:
        ranges, counts = discover_blocks(circuit, window)
        rewrites, certificates = [], []
        for start, end in ranges:
            before = list(circuit.operations(start, end))
            after, certificate = optimize_block(before, window)
            if certificate:
                rewrites.append((start, end, before, after))
                certificates.append({"start_op": start, "end_op_exclusive": end,
                                     "merges": len(certificate), "rewrites": certificate})
        write_rewritten(circuit, output_path, rewrites)
    finally:
        circuit.close()
    after_profile = kp.profile(output_path, progress=progress, max_register_summaries=0)
    merges = sum(block["merges"] for block in certificates)
    if (before_profile["raw_gate_families"]["CCX"]["total"] -
            after_profile["raw_gate_families"]["CCX"]["total"]) != merges:
        raise AssertionError("The output CCX reduction disagrees with its rewrite certificate")
    return {
        "schema": "dqi-ccx-peephole-v1", "input": str(input_path), "output": str(output_path),
        "input_sha256": before_profile["raw_kmb_sha256"],
        "output_sha256": after_profile["raw_kmb_sha256"],
        "window_operations": window, "discovery": counts, "rewritten_blocks": len(certificates),
        "static_ccx_reduction": merges, "static_cx_added": 2 * merges,
        "before_header": before_profile["header"], "after_header": after_profile["header"],
        "binary_layout_validation": "passed",
        "official_verification": "not_run_by_this_tool",
        "qubit_count_unchanged": before_profile["header"]["num_qubits"] == after_profile["header"]["num_qubits"],
        "preservation": "All register bytes, non-rewritten operations and their operands are copied verbatim; condition-stack operations are barriers.",
        "proof": "Each moved CCX commutes with every crossed current operation; the two same-control CCXs then use the exact CX-CCX-CX identity under identical classical conditions.",
        "blocks": certificates, "elapsed_seconds": time.monotonic() - started,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--window", type=int, default=256,
                        help="Maximum original/current operation separation (1 means adjacent only)")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--progress", action="store_true")
    args = parser.parse_args(argv)
    report_path = args.report or args.output.with_suffix(".report.json")
    if report_path.resolve() in (args.input.resolve(), args.output.resolve()) or report_path.exists():
        parser.error("The report must be a new file separate from input/output")
    try:
        result = optimize(args.input, args.output, args.window, args.progress)
        with report_path.open("x", encoding="utf-8") as output:
            json.dump(result, output, indent=2)
            output.write("\n")
    except (OSError, ValueError, AssertionError) as ex:
        print(f"Error: {ex}", file=sys.stderr)
        return 1
    print(json.dumps({key: result[key] for key in (
        "static_ccx_reduction", "static_cx_added", "rewritten_blocks", "discovery",
        "output_sha256", "binary_layout_validation", "official_verification", "elapsed_seconds",
    )}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
