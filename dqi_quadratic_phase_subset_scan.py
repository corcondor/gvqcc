#!/usr/bin/env python3
"""Bounded exact extension: test all subsets of the nine-CCZ affine blocks.

The whole block need not have one common control: its selected phase terms
may still factor. Selected gates are removed only after their complete ANF
has been moved to the block input and independently compared algebraically.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import time

import dqi_quadratic_phase_scan as core


def contributions(ops, wires):
    n = len(wires)
    ix = {q: i for i, q in enumerate(wires)}
    rows = [1 << i for i in range(n)]
    result = []
    for index, op in enumerate(ops):
        q = [ix[x] for x in op.qubits]
        if op.opcode == 0x11:
            rows[q[0]] ^= 1 << n
        elif op.opcode == 0x21:
            rows[q[1]] ^= rows[q[0]]
        elif op.opcode == 0x22:
            rows[q[0]], rows[q[1]] = rows[q[1]], rows[q[0]]
        elif op.opcode == 0x30:
            term = {0}
            for i in q:
                term = core.mul(term, core.linear_poly(rows[i], n))
            result.append((index, term))
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path)
    p.add_argument("--profile", type=Path, required=True)
    p.add_argument("--whole-report", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--seconds", type=float, default=90)
    args = p.parse_args()
    started = time.monotonic()
    profile = json.loads(args.profile.read_text())
    blocks = json.loads(args.whole_report.read_text())["evaluated_blocks"]
    circuit = core.shared.BinaryCircuit(args.input, profile)
    stats = Counter()
    candidates = []
    completed = True
    block_reports = []
    opcode_by_degree = {0: 0x00, 1: 0x10, 2: 0x20, 3: 0x30}
    try:
        for block in blocks:
            if block["block_operations"] != 145:
                continue
            ops = list(circuit.operations(block["start"], block["end_exclusive"]))
            wires = sorted({q for op in ops for q in op.qubits})
            parts = contributions(ops, wires)
            assert len(parts) == 9
            counts = Counter()
            for selection in range(1, 1 << len(parts)):
                number = selection.bit_count()
                if number < 2:
                    continue
                if time.monotonic() - started >= args.seconds:
                    completed = False
                    break
                phase = set()
                indexes = set()
                for i in core.bits(selection):
                    index, term = parts[i]
                    indexes.add(index)
                    phase.symmetric_difference_update(term)
                cubic = {m for m in phase if m.bit_count() == 3}
                counts["subsets_checked"] += 1
                factors = core.linear_factor_basis(cubic, len(wires)) if cubic else [1]
                if not factors:
                    counts["no_common_linear_factor"] += 1
                    continue
                counts["factorable_subsets"] += 1
                synthetic = [core.shared.Operation(opcode_by_degree[m.bit_count()],
                             tuple(wires[i] for i in core.bits(m))) for m in sorted(phase)]
                if not cubic:
                    trial = {"status": "proved_saving", "ccz_after": 0,
                             "replacement": [{"name": core.NAMES[op.opcode],
                                              "qubits": list(op.qubits)} for op in synthetic]}
                else:
                    trial = core.optimize(synthetic, wires)
                if trial.get("ccz_after", number) >= number:
                    counts["no_rank_saving"] += 1
                    continue
                # optimize() also creates a witness when the ANF has more
                # monomials than source CCZs; compare against the source count.
                assert trial["status"] == "proved_saving"
                by_name = {name: opcode for opcode, name in core.NAMES.items()}
                new_phase_ops = [core.shared.Operation(by_name[x["name"]], tuple(x["qubits"]))
                                 for x in trial["replacement"]]
                replacement = new_phase_ops + [op for i, op in enumerate(ops) if i not in indexes]
                assert core.symbolic(ops, wires) == core.symbolic(replacement, wires)
                counts["proved_saving"] += 1
                candidates.append({"start": block["start"], "end_exclusive": block["end_exclusive"],
                    "selected_source_ops": [ops[i].source_index for i in sorted(indexes)],
                    "original_ccz": len(parts), "replaced_ccz": number,
                    "replacement_ccz": trial["ccz_after"], "static_ccz_saving": number-trial["ccz_after"],
                    "phase_anf_and_affine_output_equal": True,
                    "replacement": [{"name": core.NAMES[op.opcode], "qubits": list(op.qubits)}
                                    for op in replacement]})
            stats.update(counts)
            block_reports.append({"start": block["start"], "counts": dict(counts)})
            if not completed:
                break
    finally:
        circuit.close()
    report = {"schema": "dqi-common-control-quadratic-subset-scan-v1",
              "input_sha256_from_cached_profile": profile["raw_kmb_sha256"],
              "scan_completed": completed, "scope": "all size2..9 subsets of each nine-CCZ affine block",
              "stats": dict(stats), "blocks": block_reports, "candidates": candidates,
              "candidate_count": len(candidates), "candidate_or_worker_modified": False,
              "binary_modified": False, "seconds": time.monotonic()-started,
              "peak_rss_mib": core.shared.kp.peak_rss_mib(),
              "limitation": "Does not combine different controls jointly or cross any original barrier; overlapping savings cannot be added."}
    args.report.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k not in ("blocks","candidates")},indent=2))


if __name__ == "__main__":
    main()
