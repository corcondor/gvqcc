#!/usr/bin/env python3
"""Reproduce the exact canonical-tag versus actual-batch control-state check."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import kickmix as km
import numpy as np

from chemistry_affine_span_resynthesis import parse_line
from chemistry_joint_product_resynthesis import extract
from chemistry_relation_screen import initial_values, advance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--loaders", required=True, type=Path)
    parser.add_argument("--table", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError("Use a fresh report path")
    with np.load(args.table, allow_pickle=False) as data:
        words = data["angle_words"].astype(np.uint64)
    assert words.shape == (1220, 75)
    rows = []
    valid_mask = (1 << 1220) - 1
    for k in range(1, 15):
        source = args.loaders / f"angle_k_{k}.kmb"
        circuit = km.Circuit.from_file(source)
        ex = extract(circuit)
        actual, actual_one = initial_values(
            circuit, words[:, 5*(k-1):5*k], words[:, 5*k:5*(k+1)]
        )
        canonical = [0] * circuit.num_qubits
        one = (1 << 2048) - 1
        for q in range(11):
            canonical[q] = sum(1 << a for a in range(2048) if a >> q & 1)
        for j, (a, b) in enumerate([(0, 1), (0, 2), (1, 2), (0, 3), (1, 3)]):
            canonical[11 + 8*j + 7] = canonical[a] & canonical[b]
        for line in ex["lines"][:ex["first"]]:
            gate, qs, condition = parse_line(line)
            advance(actual, gate, qs, actual_one)
            advance(canonical, gate, qs, one)
        for q in ex["pool"]:
            valid = canonical[q] & valid_mask
            assert actual[q] == valid | (valid << 1220), (k, q)
        rows.append({
            "k": k,
            "control_wires_checked": len(ex["pool"]),
            "actual_address_direction_cases": 2440,
            "canonical_control_state_equals_both_actual_batches": True,
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        })
    report = {
        "status": "EXACT_CANONICAL_INPUT_MODEL_PASS",
        "table_sha256": hashlib.sha256(args.table.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "method": "Independently propagate the circuit prefix on the exact previous/current word batches and on the canonical five-tag input; compare every entry control wire for all valid addresses and both directions. No random samples.",
        "checks": rows,
        "total_address_direction_cases": 34160,
        "source_files_modified": False,
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "circuits": len(rows),
                      "address_direction_cases": 34160,
                      "control_wires_per_circuit": rows[0]["control_wires_checked"]}))


if __name__ == "__main__":
    main()
