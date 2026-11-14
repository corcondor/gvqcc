"""Regression for the concrete mistakes found in the uploaded v4 scanner."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

import kmb_profile as kp

HERE = Path(__file__).resolve().parent


def write_small_kmb(path, operations, num_qubits=4, num_bits=2):
    """Create a tiny documented KMB-v2 fixture; no Kickmix dependency."""
    columns = {i: bytearray() for i in range(1, 12)}
    qcounts = [0] * 4
    bit_count = condition_count = 0
    for opcode, qubits, bit, condition in operations:
        columns[1].append(opcode)
        arity = (opcode >> 4) & 3
        assert len(qubits) == arity
        qcounts[arity] += 1
        for j, q in enumerate(qubits):
            column = 2 + j if arity == 3 else 5 + j if arity == 2 else 7
            columns[column] += struct.pack("<I", q)
        if opcode & 0x40:
            columns[8] += struct.pack("<I", bit)
            bit_count += 1
        if opcode & 0x80:
            columns[9] += struct.pack("<I", condition)
            condition_count += 1
    columns[11] += struct.pack("<Q", 0)
    with path.open("wb") as output:
        output.write(kp.HEADER.pack(
            kp.MAGIC, 2, num_qubits, num_bits, 0, len(operations),
            qcounts[3], qcounts[2], qcounts[1], bit_count, condition_count, 0, 0, 0))
        for column in range(1, 12):
            output.write(kp.PACKET.pack(column, len(columns[column])))
            output.write(columns[column])


OPS = [
    (0x10, [1], None, None),             # Z on known zero: still zero.
    (0x21, [1, 2], None, None),          # Zero CX control: both remain zero.
    (0x31, [1, 0, 2], None, None),       # One zero CCX control: target remains zero.
    (0x20, [1, 3], None, None),          # CZ does not change data.
    (0x21, [0, 1], None, None),          # Unknown input copied to scratch 1.
    (0xD0, [1], 0, 1),                  # Conditional HMR may be skipped.
    (0x81, [], None, 1),                # PUSH unknown classical condition.
    (0x12, [1], None, None),             # R inside condition stack may be skipped.
    (0x01, [], None, None),              # POP.
    (0x22, [1, 2], None, None),          # SWAP transfers possible nonzero to q2.
    (0x32, [1, 2, 3], None, None),       # Zero control: CSWAP has no effect.
    (0xA2, [2, 3], None, 1),             # Conditional swap: both may be nonzero.
    (0x50, [2], 0, None),                # Unconditional HMR establishes zero.
    (0x12, [3], None, None),             # Unconditional R establishes zero.
    (0x11, [1], None, None),
    (0x11, [1], None, None),             # Cancellation intentionally not inferred.
    (0x12, [1], None, None),
]
EXPECTED_BEFORE = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 2, 1, 0, 1, 1, 0]


class ScratchAuditTests(unittest.TestCase):
    def test_conditions_controls_swaps_and_indices(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            circuit = root / "known_cases.kmb"
            write_small_kmb(circuit, OPS)
            for mode in ("kmb", "legacy-v4"):
                out = root / mode
                result = subprocess.run([
                    sys.executable, str(HERE / "gvqcc_dqi_audit.py"),
                    "--circuit", str(circuit), "--scratch-start", "1",
                    "--scratch-initial", "zero", "--index-mode", mode,
                    "--snapshots", ",".join(map(str, range(18))),
                    "--window", "0:100", "--region", "12:13",
                    "--out-dir", str(out),
                ], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                scan = json.loads((out / "scan.json").read_text())
                events = [json.loads(line) for line in (out / "events.jsonl").read_text().splitlines()]
                window = [e for e in events if e["event"] == "window"]
                self.assertEqual([e["kmb_index"] for e in window], list(range(17)))
                self.assertIn("CX", [e["opcode"] for e in window])
                self.assertIn("PUSH_CONDITION", [e["opcode"] for e in window])
                self.assertEqual(scan["peak_possibly_nonzero_scratch"], 2)
                self.assertEqual(scan["num_kmb_operations"], 17)
                self.assertEqual(scan["num_legacy_v4_gate_operations"], 15)
                self.assertEqual(window[7]["active_pushed_conditions"],
                                 [{"source_bit_id": 1, "push_kmb_index": 6}])
                self.assertEqual(window[9]["active_pushed_conditions"], [])
                if mode == "kmb":
                    snapshots = [e for e in events if e["event"] == "snapshot"]
                    self.assertEqual([e["scratch"]["possibly_nonzero_count"] for e in snapshots],
                                     EXPECTED_BEFORE)
                    self.assertEqual(snapshots[10]["scratch"]["possibly_nonzero_qubits"], [2])
                    self.assertEqual(snapshots[12]["scratch"]["possibly_nonzero_qubits"], [2, 3])
                    # Region starts with a reset: its pre-reset state must count.
                    self.assertEqual(scan["region"]["peak_possibly_nonzero"], 2)
                self.assertEqual(scan["final_scratch"]["possibly_nonzero_count"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
