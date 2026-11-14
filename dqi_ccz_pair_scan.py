#!/usr/bin/env python3
"""Read-only scan for a distinct exact two-CCZ factoring rule.

For distinct a,b,c,d and an identical unchanged classical condition:
    CCZ(a,b,c); CCZ(a,b,d)
      = CX(c,d); CCZ(a,b,d); CX(c,d).

This does not rewrite a KMB or load a kickmix Circuit. Only unitary intervening
operations proven to commute with one endpoint may be crossed. All classical
writes, measurements, resets, condition-stack changes and unknown operations
are barriers. Overlapping opportunities are not additive savings.
"""
from __future__ import annotations

import argparse
from collections import defaultdict, deque
from itertools import combinations, product
import json
from pathlib import Path
import re
import time

import dqi_ccx_peephole as shared


def identity_check():
    cases = 0
    for a, b, c, d, condition, stack_active in product((0, 1), repeat=6):
        active = condition & stack_active
        original = (a, b, c, d)
        phase = active & ((a & b & c) ^ (a & b & d))
        rewritten = list(original)
        if active:
            rewritten[3] ^= rewritten[2]
        phase_rewritten = active & (rewritten[0] & rewritten[1] & rewritten[3])
        if active:
            rewritten[3] ^= rewritten[2]
        assert tuple(rewritten) == original
        assert phase_rewritten == phase
        cases += 1
    return {
        "status": "PASS", "quantum_basis_states": 16,
        "explicit_condition_cases": 2, "implicit_condition_stack_cases": 2,
        "state_and_phase_cases": cases,
        "conditional_off": "identity including phase",
        "coherent_scope": "Exact phased-permutation equality on every basis state",
    }


def commutes_with_ccz(ccz, other):
    """Conservative sufficient rule, valid for arbitrary coherent inputs.

    Diagonal gates commute; reversible bit flips commute if they never write
    one of the three CCZ arguments. SWAP/CSWAP commute when both swapped bits
    belong to the CCZ support, or both are outside it. This preserves the
    symmetric cubic monomial, irrespective of the swap control.
    """
    assert (ccz.opcode & 0x7F) == 0x30
    support = set(ccz.qubits)
    base = other.opcode & 0x7F
    if base in (0x00, 0x10, 0x13, 0x20, 0x30):
        return True
    if base in (0x11, 0x21, 0x31):
        return other.qubits[-1] not in support
    if base in (0x22, 0x32):
        return (other.qubits[-2] in support) == (other.qubits[-1] in support)
    return False


def condition_stack_audit(opcodes):
    """Audit depth using opcode events only; never evaluate or alter conditions."""
    depth = 0
    empty_pops = 0
    ccz_depths = defaultdict(int)
    for match in re.finditer(rb"[\x01\x81\x30\xb0]", opcodes):
        opcode = opcodes[match.start()]
        if opcode == 0x81:
            depth += 1
        elif opcode == 0x01:
            if depth:
                depth -= 1
            else:
                empty_pops += 1
        else:
            ccz_depths[depth] += 1
    return {"ccz_by_condition_stack_depth": dict(sorted(ccz_depths.items())),
            "final_stack_depth": depth, "empty_stack_pops": empty_pops,
            "condition_truth_values": "not evaluated"}


def scan(circuit, window=4096, seconds=80):
    started = time.monotonic()
    previous = defaultdict(deque)
    opportunities = []
    counts = {
        "ccz_seen": 0, "explicitly_conditional_ccz_seen": 0,
        "same_pair_and_condition_within_window": 0,
        "four_distinct_qubit_pairs": 0, "blocked_by_ordering_barrier": 0,
        "blocked_by_noncommuting_unitary": 0, "proved_legal_pairs": 0,
        "barrier_segment_restarts": 0, "maximum_candidate_separation": 0,
    }
    completed = True
    last_position = -1
    for index, match in enumerate(shared.THREE_QUBIT.finditer(circuit.opcodes)):
        position = match.start()
        if (circuit.opcodes[position] & 0x7F) != 0x30:
            continue
        if time.monotonic() - started >= seconds:
            completed = False
            break
        if window == 0 and shared.BARRIER.search(circuit.opcodes, last_position + 1, position):
            previous.clear()
            counts["barrier_segment_restarts"] += 1
        last_position = position
        current = circuit.ccx_at(position, index)  # generic 3-qubit operand read
        counts["ccz_seen"] += 1
        counts["explicitly_conditional_ccz_seen"] += current.condition is not None
        for common in combinations(sorted(current.qubits), 2):
            key = (*common, current.condition)
            older = previous[key]
            while window and older and position - older[0].source_index > window:
                older.popleft()
            for first in older:
                counts["same_pair_and_condition_within_window"] += 1
                if len(set(first.qubits).union(current.qubits)) != 4:
                    continue
                counts["four_distinct_qubit_pairs"] += 1
                counts["maximum_candidate_separation"] = max(
                    counts["maximum_candidate_separation"], position - first.source_index)
                start = first.source_index + 1
                if shared.BARRIER.search(circuit.opcodes, start, position):
                    counts["blocked_by_ordering_barrier"] += 1
                    continue
                middle = list(circuit.operations(start, position))
                if all(commutes_with_ccz(current, op) for op in middle):
                    direction = "second_left"
                elif all(commutes_with_ccz(first, op) for op in middle):
                    direction = "first_right"
                else:
                    counts["blocked_by_noncommuting_unitary"] += 1
                    continue
                counts["proved_legal_pairs"] += 1
                c = next(q for q in first.qubits if q not in common)
                d = next(q for q in current.qubits if q not in common)
                opportunities.append({
                    "start": first.source_index, "end_exclusive": position + 1,
                    "first_source_op": first.source_index, "second_source_op": position,
                    "common_qubits": list(common), "first_extra_qubit": c,
                    "second_extra_qubit": d, "explicit_condition_bit": current.condition,
                    "condition_stack": "unchanged; all PUSH/POP are barriers",
                    "direction": direction, "crossed_operations": len(middle),
                    "replacement": [
                        {"name": "CX", "qubits": [c, d], "condition": current.condition},
                        {"name": "CCZ", "qubits": [*common, d], "condition": current.condition},
                        {"name": "CX", "qubits": [c, d], "condition": current.condition},
                    ],
                })
            older.append(current)
    intervals = []
    for item in sorted(opportunities, key=lambda p: (p["start"], p["end_exclusive"])):
        start, end = item["start"], item["end_exclusive"]
        if intervals and start < intervals[-1][1]:
            intervals[-1][1] = max(end, intervals[-1][1])
        else:
            intervals.append([start, end])
    independent = []
    end = -1
    for item in sorted(opportunities, key=lambda p: (p["end_exclusive"], p["start"])):
        if item["start"] >= end:
            independent.append([item["start"], item["end_exclusive"]])
            end = item["end_exclusive"]
    return {
        "scan_completed": completed, "window_operations": window,
        "search_scope": ("all CCZ pairs inside each barrier-free unitary segment"
                         if window == 0 else "same-pair candidates within bounded operation distance"),
        "time_budget_seconds": seconds, "scan_seconds": time.monotonic() - started,
        "last_ccz_source_op": last_position, "counts": counts,
        "legal_blocks_union": intervals, "opportunities": opportunities,
        "nonoverlapping_intervals": independent,
        "nonoverlapping_static_ccz_savings": len(independent),
        "execution_count_scope": (
            "Each rewrite saves one conditional CCZ only when its shared condition "
            "and condition stack are true; static counts are not official mean Toffolis."
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--window", type=int, default=4096)
    parser.add_argument("--seconds", type=float, default=80)
    args = parser.parse_args()
    started = time.monotonic()
    proof = identity_check()
    profile = json.loads(args.profile.read_text())
    circuit = shared.BinaryCircuit(args.input, profile)
    try:
        result = scan(circuit, args.window, args.seconds)
        result["condition_stack_audit"] = condition_stack_audit(circuit.opcodes)
    finally:
        circuit.close()
    result.update({
        "schema": "dqi-ccz-pair-read-only-v1", "identity_check": proof,
        "input": str(args.input), "input_sha256_from_cached_profile": profile["raw_kmb_sha256"],
        "input_sha256_recomputed_this_run": False,
        "binary_modified": False, "candidate_or_pipeline_modified": False,
        "total_seconds": time.monotonic() - started,
        "peak_rss_mib": shared.kp.peak_rss_mib(),
    })
    args.report.write_text(json.dumps(result, indent=2) + "\n")
    summary = {k: v for k, v in result.items() if k not in (
        "opportunities", "legal_blocks_union", "nonoverlapping_intervals")}
    summary["legal_blocks_count"] = len(result["legal_blocks_union"])
    summary["legal_blocks_first_8"] = result["legal_blocks_union"][:8]
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
