#!/usr/bin/env python3
"""Independently check the scope of the two invsqrt phase-only edits.

This checks source identity, unchanged nonphase gates, unconditional insertion
points, and the claimed measurement-outcome independence of the phase wires.
It does not rerun the official 200,540,928-shot evaluation.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIAGONAL = {"Z", "CZ", "CCZ", "Z_POW", "NEG"}
CLASSICAL = {"BIT_STORE0", "BIT_STORE1", "BIT_INVERT"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    original = (ROOT / "invsqrt_structural_e46.kmx").read_text().splitlines()
    plans = json.loads((ROOT / "invsqrt_structural_build_plans.json").read_text())
    latest = max(max(p["candidate"]["line"] for p in plans),
                 max(i for i, line in enumerate(original, 1) if line.startswith("Z_POW ")))
    stack = 0
    conditional = {}
    insertion_depths = {}
    points = {p["candidate"]["line"] for p in plans}
    for line_number, line in enumerate(original, 1):
        if line_number in points:
            insertion_depths[line_number] = stack
        words = line.split()
        if not words:
            continue
        op = words[0]
        if op == "PUSH_CONDITION":
            stack += 1
            continue
        if op == "POP_CONDITION":
            stack -= 1
            assert stack >= 0
            continue
        if op == "Z_POW":
            assert stack == 0 and "if" not in words, (line_number, line)
        if line_number <= latest and (stack or "if" in words) and op not in CLASSICAL:
            conditional[op] = conditional.get(op, 0) + 1
            assert op in DIAGONAL, (line_number, op)
    assert stack == 0
    assert all(depth == 0 for depth in insertion_depths.values())

    native = json.loads((ROOT / "invsqrt_structural_native.json").read_text())
    native_by_name = {r["name"]: r for r in native["records"]}
    records = []
    for plan in plans:
        path = ROOT / Path(plan["kmx"]).name
        actual = path.read_text().splitlines()
        qs = plan["candidate"]["qubits"]
        extra = [f"CX q{qs[0]} q{qs[1]}"] * 2 if len(qs) == 2 else []
        expected = []
        for line_number, line in enumerate(original, 1):
            if line_number == plan["candidate"]["line"]:
                expected.extend(extra)
            if not line.startswith("Z_POW "):
                expected.append(line)
        without_rotations = [line for line in actual if not line.startswith("Z_POW ")]
        assert without_rotations == expected, plan["name"]
        # The two added CXs surround just one diagonal rotation, so their
        # product restores all qubit values for every input, even without
        # assuming either control is zero.
        if len(qs) == 2:
            # Earlier rotations can be deleted, so locate the unique edit via
            # its neighboring inserted CX/rotation/CX sequence instead.
            matches = [i for i in range(len(actual) - 2)
                       if actual[i] == extra[0] and actual[i + 1].startswith("Z_POW ")
                       and actual[i + 2] == extra[1]]
            assert len(matches) == 1, (plan["name"], matches)
        result = native_by_name[plan["name"]]
        binary = ROOT / Path(result["kmb"]).name
        assert sha(binary) == result["sha256"]
        assert result["restoration_failures"] == result["exact_phase_mismatches"] == 0
        assert result["static_generic_rotations"] == plan["generic_rotations"]
        records.append({"name": plan["name"], "kmx_sha256": sha(path),
                        "kmb_sha256": sha(binary),
                        "nonphase_edit": "one CX/diagonal-rotation/CX conjugation",
                        "all_other_nonphase_lines_identical": True,
                        "classically_unconditional_insertion": True,
                        "delta_phase_independent_of_measurement_outcomes": True,
                        "native_result_and_file_hash_match": True})
    report = {"status": "PASS_STRUCTURAL_EDIT_AUDIT", "records": records,
              "conditional_quantum_opcodes_before_latest_modified_rotation": conditional,
              "latest_modified_rotation_line": latest,
              "all_original_rotations_unconditional": True,
              "insertion_condition_depths": insertion_depths,
              "source_kmx_sha256": sha(ROOT / "invsqrt_structural_e46.kmx"),
              "limitations": [
                  "Phase-wire independence follows because all preceding conditionally executed quantum operations are diagonal; unconditional HMR resets do not depend on their recorded outcome.",
                  "The original baseline's correctness is not reproved here. The audit proves that the new edits add only a deterministic input-dependent diagonal phase to it.",
                  "Full-domain integer-oracle results and finite native checks remain separate evidence; this is not an official 200M-shot run or a global optimality proof."
              ]}
    (ROOT / "invsqrt_structural_independent_audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
