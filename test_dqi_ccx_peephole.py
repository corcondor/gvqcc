"""Regressions for the v13 line-loss bug and exact, condition-safe CCX rewrites."""

import io
import json
from pathlib import Path
import random
import struct
import tempfile
import unittest

import dqi_ccx_peephole as pp
import kmb_profile as kp


HERE = Path(__file__).resolve().parent


def fixture_bytes(operations, registers=()):
    """Independent small KMB encoder, including condition and classical columns."""
    payloads = {kind: bytearray() for kind in range(1, 12)}
    max_q = max_b = -1
    for op in operations:
        payloads[1].append(op.opcode)
        columns = {0: (), 1: (7,), 2: (5, 6), 3: (2, 3, 4)}[len(op.qubits)]
        for column, q in zip(columns, op.qubits):
            payloads[column].extend(struct.pack("<I", q))
            max_q = max(max_q, q)
        if op.bit is not None:
            payloads[8].extend(struct.pack("<I", op.bit))
            max_b = max(max_b, op.bit)
        if op.condition is not None:
            payloads[9].extend(struct.pack("<I", op.condition))
            max_b = max(max_b, op.condition)
        payloads[10].extend(op.angle)
    payloads[11].extend(struct.pack("<Q", 0))
    register_bytes = bytearray()
    for name, targets in registers:
        name = name.encode()
        payload = struct.pack("<II", len(name), len(targets)) + name
        for target in targets:
            payload += struct.pack("<I", target)
            if target & (1 << 31):
                max_q = max(max_q, target & 0x7FFFFFFF)
            else:
                max_b = max(max_b, target)
        register_bytes.extend(kp.PACKET.pack(0, len(payload)) + payload)
    result = bytearray(kp.HEADER.pack(
        kp.MAGIC, 2, max_q + 1, max_b + 1, len(registers), len(operations),
        len(payloads[2]) // 4, len(payloads[5]) // 4, len(payloads[7]) // 4,
        len(payloads[8]) // 4, len(payloads[9]) // 4, len(payloads[10]) // 16, 0, 0,
    ))
    result.extend(register_bytes)
    for kind, payload in payloads.items():
        result.extend(kp.PACKET.pack(kind, len(payload)))
        result.extend(payload)
    return bytes(result)


def op(base, *qubits, condition=None, bit=None):
    return pp.Operation(base | (0x80 if condition is not None else 0), tuple(qubits), bit, condition)


def simulate(operations, state, classical):
    """Exact monomial simulation: basis permutation plus sign, not just values."""
    sign = 1
    stack = []
    for operation in operations:
        base = operation.opcode & 0x7F
        q = operation.qubits
        if base == 1:
            if operation.opcode & 0x80:
                stack.append(bool((classical >> operation.condition) & 1))
            else:
                stack.pop()
            continue
        active = all(stack) and (operation.condition is None or
                                 bool((classical >> operation.condition) & 1))
        if not active:
            continue
        values = [(state >> x) & 1 for x in q]
        if base == 0:
            sign *= -1
        elif base in (0x11, 0x21, 0x31):
            if all(values[:-1]):
                state ^= 1 << q[-1]
        elif base in (0x10, 0x20, 0x30):
            if all(values):
                sign *= -1
        elif base in (0x22, 0x32):
            if (base == 0x22 or values[0]) and values[-2] != values[-1]:
                state ^= (1 << q[-2]) | (1 << q[-1])
        elif base == 0x40:
            classical &= ~(1 << operation.bit)
        elif base == 0x41:
            classical |= 1 << operation.bit
        elif base == 0x42:
            classical ^= 1 << operation.bit
        else:
            raise AssertionError(f"Unsupported independent simulator opcode {base:#x}")
    return state, classical, sign, stack


def reproduce_v13(text):
    """The original worker's pending-CCX fallback, isolated without Kaggle I/O."""
    previous = None
    output = io.StringIO()
    for line in text.splitlines(keepends=True):
        parts = line.split()
        current = line if len(parts) == 4 and parts[0] == "CCX" else None
        if previous is not None:
            output.write(previous)
            previous = current
            continue  # Original bug: a non-CCX current line disappears.
        if current is not None:
            previous = current
        else:
            output.write(line)
    if previous is not None:
        output.write(previous)
    return output.getvalue()


class PeepholeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.serial = 0

    def tearDown(self):
        self.temp.cleanup()

    def rewrite(self, operations=None, data=None, window=256, registers=()):
        self.serial += 1
        source = self.root / f"source{self.serial}.kmb"
        target = self.root / f"target{self.serial}.kmb"
        source.write_bytes(data if data is not None else fixture_bytes(operations, registers))
        original = source.read_bytes()
        report = pp.optimize(source, target, window)
        self.assertEqual(source.read_bytes(), original, "The source must remain untouched")
        profile = kp.profile(target)
        reader = pp.BinaryCircuit(target, profile, checkpoint=8)
        try:
            output = list(reader.operations(0, profile["header"]["num_ops"]))
        finally:
            reader.close()
        return output, report, original, target.read_bytes()

    def assert_equivalent(self, before, after, qubits=6, bits=2):
        for state in range(1 << qubits):
            for classical in range(1 << bits):
                self.assertEqual(simulate(before, state, classical), simulate(after, state, classical),
                                 (state, classical, before, after))

    def test_v13_drops_following_gate_and_condition_pop(self):
        source = "PUSH_CONDITION b0\nCCX q0 q1 q2\nPOP_CONDITION\nX q3\n"
        damaged = reproduce_v13(source)
        self.assertNotIn("POP_CONDITION", damaged)
        self.assertNotEqual(source, damaged)
        for following in (op(0x11, 3), op(1)):
            before = [op(1, condition=0), op(0x31, 0, 1, 2), following]
            if following.opcode != 1:
                before.append(op(1))
            after, report, original, rewritten = self.rewrite(before)
            self.assertEqual(report["static_ccx_reduction"], 0)
            self.assertEqual(original, rewritten)
            self.assert_equivalent(before, after)

    def test_all_official_format_fixtures_copy_byte_exactly(self):
        fixtures = json.loads((HERE / "kmb_official_fixtures.json").read_text())["examples"]
        for fixture in fixtures:
            with self.subTest(name=fixture["name"]):
                _, report, before, after = self.rewrite(data=bytes.fromhex(fixture["hex"]), window=1)
                self.assertEqual(report["static_ccx_reduction"], 0)
                self.assertEqual(before, after)  # Includes rotations, tags, registers, resets, measurements.

    def test_adjacent_reversed_controls_and_grouped_binary_operations(self):
        before = [op(0x31, 0, 1, 2), op(0x31, 1, 0, 3), op(0x11, 4)]
        after, report, _, _ = self.rewrite(before, window=1)
        self.assertEqual(report["static_ccx_reduction"], 1)
        self.assertEqual([gate.opcode for gate in after], [0x21, 0x31, 0x21, 0x11])
        self.assert_equivalent(before, after)

    def test_interleaved_twelve_word_outputs_all_merge(self):
        # Same arrangement as the actual 96-CCX opportunity: 12 then 12 gates.
        before = [op(0x31, 0, k + 1, k + 13) for k in range(12)]
        before += [op(0x31, 0, k + 1, k + 25) for k in range(12)]
        after, report, _, _ = self.rewrite(before)
        self.assertEqual(report["discovery"]["adjacent_same_control_pairs"], 0)
        self.assertEqual(report["static_ccx_reduction"], 12)
        self.assertEqual(report["rewritten_blocks"], 1)
        rng = random.Random(842)
        for _ in range(2000):
            state = rng.randrange(1 << 37)
            self.assertEqual(simulate(before, state, 0), simulate(after, state, 0))
        # Exhaustive smaller overlapping block checks all amplitudes/signs.
        small = [op(0x31, 0, k + 1, k + 4) for k in range(3)]
        small += [op(0x31, 0, k + 1, k + 7) for k in range(3)]
        optimized, certificate = pp.optimize_block(small, 256)
        self.assertEqual(len(certificate), 3)
        self.assert_equivalent(small, optimized, qubits=10, bits=0)

    def test_commuting_unitaries_preserve_basis_and_phase(self):
        middles = [op(0), op(0x11, 4), op(0x10, 2), op(0x20, 0, 2),
                   op(0x30, 0, 1, 2), op(0x21, 4, 5), op(0x31, 4, 5, 2),
                   op(0x22, 4, 5), op(0x21, 4, 2, condition=1)]
        for middle in middles:
            with self.subTest(middle=middle):
                before = [op(0x31, 0, 1, 2, condition=0), middle,
                          op(0x31, 0, 1, 3, condition=0)]
                after, report, _, _ = self.rewrite(before)
                self.assertEqual(report["static_ccx_reduction"], 1)
                self.assert_equivalent(before, after)

    def test_first_right_fallback_preserves_phase(self):
        before = [op(0x31, 0, 1, 2), op(0x10, 3), op(0x31, 0, 1, 3)]
        after, report, _, _ = self.rewrite(before)
        self.assertEqual(report["blocks"][0]["rewrites"][0]["direction"], "first_right")
        self.assert_equivalent(before, after)

    def test_noncommuting_middle_is_rejected(self):
        for middle in (op(0x11, 0), op(0x20, 2, 3), op(0x21, 4, 1), op(0x22, 0, 4)):
            before = [op(0x31, 0, 1, 2), middle, op(0x31, 0, 1, 3)]
            _, report, original, rewritten = self.rewrite(before)
            self.assertEqual(report["static_ccx_reduction"], 0)
            self.assertEqual(original, rewritten)

    def test_condition_stack_and_explicit_condition_preserved(self):
        before = [op(1, condition=0), op(0x31, 0, 1, 2, condition=1),
                  op(0x11, 4), op(0x31, 0, 1, 3, condition=1), op(1), op(0x11, 5)]
        after, report, _, _ = self.rewrite(before, registers=(("output", (0x80000003, 1)),))
        self.assertEqual(report["static_ccx_reduction"], 1)
        self.assertEqual(sum(gate.opcode == 1 for gate in after), 1)
        self.assertEqual(sum(gate.opcode == 0x81 for gate in after), 1)
        self.assert_equivalent(before, after)

    def test_classical_write_reset_measurement_and_stack_are_barriers(self):
        middles = [op(0x42, bit=0), op(0x12, 4), op(0x50, 4, bit=1),
                   op(1, condition=1), op(1)]
        for middle in middles:
            before = [op(0x31, 0, 1, 2, condition=0), middle,
                      op(0x31, 0, 1, 3, condition=0)]
            _, report, original, rewritten = self.rewrite(before)
            self.assertEqual(report["static_ccx_reduction"], 0)
            self.assertEqual(original, rewritten)

    def test_mismatched_explicit_conditions_never_merge(self):
        for condition in (None, 1):
            before = [op(0x31, 0, 1, 2, condition=0), op(0x31, 0, 1, 3, condition=condition)]
            _, report, original, rewritten = self.rewrite(before)
            self.assertEqual(report["static_ccx_reduction"], 0)
            self.assertEqual(original, rewritten)

    def test_rank_checkpoint_boundary(self):
        before = [op(0x11, 4)] * 4095 + [op(0x31, 0, 1, 2), op(0x31, 0, 1, 3)]
        after, report, _, _ = self.rewrite(before, window=1)
        self.assertEqual(report["static_ccx_reduction"], 1)
        self.assert_equivalent(before, after, qubits=5, bits=0)

    def test_separate_blocks_insert_at_same_operand_offset_in_order(self):
        before = [op(0x31, 0, 1, 2), op(0x31, 0, 1, 3), op(0x11, 4),
                  op(0x31, 0, 1, 4), op(0x31, 0, 1, 5)]
        after, report, _, _ = self.rewrite(before, window=1)
        self.assertEqual(report["static_ccx_reduction"], 2)
        self.assertEqual(report["rewritten_blocks"], 2)
        self.assert_equivalent(before, after)

    def test_existing_outputs_and_in_place_edits_rejected(self):
        source = self.root / "source.kmb"
        source.write_bytes(fixture_bytes([op(0x11, 0)]))
        with self.assertRaises(FileExistsError):
            pp.optimize(source, source)
        target = self.root / "target.kmb"
        target.write_bytes(b"keep")
        with self.assertRaises(FileExistsError):
            pp.optimize(source, target)
        self.assertEqual(target.read_bytes(), b"keep")

    def test_kmx_conversion_via_real_kickmix_when_available(self):
        try:
            import kickmix
        except ImportError:
            self.skipTest("Optional real-Kickmix KMX-to-KMB round trip")
        source = self.root / "grouped.kmx"
        binary = self.root / "grouped.kmb"
        # Use Kickmix's parser to expand text; the optimizer never guesses
        # whether a text line contains one gate, a group, or an annotation.
        source.write_text("CCX q0 q1 q2\nCCX q0 q1 q3\nX q4\n")
        kickmix.Circuit.from_file(str(source), format="kmx").to_file(str(binary), format="kmb")
        after, report, _, _ = self.rewrite(data=binary.read_bytes(), window=1)
        self.assertEqual(report["static_ccx_reduction"], 1)
        self.assert_equivalent([op(0x31, 0, 1, 2), op(0x31, 0, 1, 3), op(0x11, 4)], after)


if __name__ == "__main__":
    unittest.main()
