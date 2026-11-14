#!/usr/bin/env python3
"""Measure a strict arbitrary-z XOR fallback without running a scoring verifier.

Builds the mirror's ordinary QROM reference on the unchanged submitted words.
No source circuit or submission archive is changed. Circuits are kept in memory.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, required=True)
    parser.add_argument("--table", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError("Use a fresh report path")
    started = time.monotonic()
    spec = importlib.util.spec_from_file_location("angle_reference", args.generator)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    words = module.load_angle_words(args.table)
    rows = []
    for k, delta in enumerate(module.batch_deltas(words, 5)):
        circuit = module.build_angle_k_circuit(delta, 8)
        info = module.circuit_costs([circuit])[0]
        info["k"] = k
        # This construction proves arbitrary output behavior structurally:
        # every output use is a CX target, never a control or a measured wire.
        output = set(range(11, 51))
        unexpected = []
        for i, line in enumerate(str(circuit).splitlines()):
            parts = line.split()
            if not parts or parts[0] in {"REGISTER", "APPEND_TO_REGISTER"}:
                continue
            qubits = [int(p[1:]) for p in parts[1:] if p.startswith("q")]
            touched = output.intersection(qubits)
            if touched and not (parts[0] == "CX" and len(qubits) == 2
                                and qubits[1] in output and qubits[0] not in output):
                unexpected.append(i)
        if unexpected:
            raise AssertionError(unexpected[:5])
        info["output_only_used_as_xor_target"] = True
        rows.append(info)
        print(json.dumps(info), flush=True)
    loader_t = sum(row["max_magic"] for row in rows)
    loader_q = max(row["num_qubits"] for row in rows)
    report = {
        "status": "COST_MEASURED_NOT_OFFICIAL_SCORE",
        "table_sha256": hashlib.sha256(args.table.read_bytes()).hexdigest(),
        "generator_sha256": hashlib.sha256(args.generator.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "generator": str(args.generator),
        "loaders": rows,
        "loader_ccx_per_pass": loader_t,
        "loader_qubits": loader_q,
        "loader_scratch_qubits": loader_q - 51,
        "reference_geometry_heuristic_toffoli": 6662,
        "derived_total_toffoli_same_geometry": 6662 + 2 * loader_t,
        "derived_total_qubits_same_geometry": 84 + 40 + max(303, loader_q - 51),
        "cost_ratio_to_4033_same_geometry": (6662 + 2 * loader_t) / 14728,
        "note": "This is a fallback cost, not an optimal strict XOR synthesis. Same-geometry totals use the existing 4033 receipt's heuristic resource terms. Numerical factorization is unchanged.",
        "candidate_files_written": False,
        "seconds": time.monotonic() - started,
        "peak_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "loaders"}, indent=2))


if __name__ == "__main__":
    main()
