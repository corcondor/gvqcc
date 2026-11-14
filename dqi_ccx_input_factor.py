#!/usr/bin/env python3
"""Bounded input-side CCX factorization scan, preserving all existing artifacts.

For distinct a,b,c,t:
  CCX(a,b,t); CCX(a,c,t) == CX(b,c); CCX(a,c,t); CX(b,c).
This is the input-side dual of the same-control output fanout identity.
"""
from __future__ import annotations

import argparse
from collections import deque
import json
from pathlib import Path
import resource
import time

import dqi_ccx_peephole as shared


def identity_check():
    checks = 0
    for state in range(16):
        for enabled in (False, True):
            a, b, c, target = [(state >> bit) & 1 for bit in range(4)]
            original = [a, b, c, target ^ ((a & b) if enabled else 0) ^ ((a & c) if enabled else 0)]
            updated = [a, b, c, target]
            if enabled:
                updated[2] ^= updated[1]
                updated[3] ^= updated[0] & updated[2]
                updated[2] ^= updated[1]
            assert original == updated
            checks += 1
    return {"status": "PASS", "basis_states": 16, "classical_conditions": 2,
            "checks": checks, "phase": "Both sides are identical basis permutations with no phase gates."}


def pair_operands(first, second):
    if not first.is_ccx or not second.is_ccx or first.condition != second.condition:
        return None
    if first.qubits[2] != second.qubits[2]:
        return None
    common = set(first.qubits[:2]) & set(second.qubits[:2])
    if len(common) != 1 or len(set(first.qubits + second.qubits)) != 4:
        return None
    control = next(iter(common))
    left = next(q for q in first.qubits[:2] if q != control)
    right = next(q for q in second.qubits[:2] if q != control)
    return control, left, right, first.qubits[2]


def discover(circuit, window=256, seconds=110):
    started = time.monotonic()
    latest, pending, hits = {}, deque(), []
    counts = {"ccx_scanned": 0, "signature_pairs": 0,
              "four_distinct_qubit_pairs": 0, "barrier_free_pairs": 0,
              "proved_commuting_pairs": 0}
    complete = True
    for rank, match in enumerate(shared.THREE_QUBIT.finditer(circuit.opcodes)):
        position = match.start()
        if (circuit.opcodes[position] & 0x7F) != 0x31:
            continue
        counts["ccx_scanned"] += 1
        if counts["ccx_scanned"] % 4096 == 0 and time.monotonic() - started > seconds:
            complete = False
            break
        current = circuit.ccx_at(position, rank)
        while pending and pending[0][0] < position - window:
            expired_position, signature = pending.popleft()
            if latest.get(signature, current).source_index == expired_position:
                latest.pop(signature, None)
        signatures = [(current.qubits[2], control, current.condition) for control in current.qubits[:2]]
        for signature in signatures:
            previous = latest.get(signature)
            if previous is None:
                continue
            counts["signature_pairs"] += 1
            operands = pair_operands(previous, current)
            if operands is None:
                continue
            counts["four_distinct_qubit_pairs"] += 1
            start = previous.source_index + 1
            if shared.BARRIER.search(circuit.opcodes, start, position):
                continue
            counts["barrier_free_pairs"] += 1
            middle = list(circuit.operations(start, position))
            if all(shared.commutes_with_ccx(current, op) for op in middle):
                direction = "second_left"
            elif all(shared.commutes_with_ccx(previous, op) for op in middle):
                direction = "first_right"
            else:
                continue
            counts["proved_commuting_pairs"] += 1
            hits.append({"first_source_op": previous.source_index,
                         "second_source_op": position, "qubits_a_b_c_t": list(operands),
                         "explicit_condition_bit": current.condition,
                         "direction": direction, "crossed_operations": len(middle)})
        for signature in signatures:
            latest[signature] = current
            pending.append((position, signature))
    ranges = []
    for hit in sorted(hits, key=lambda h: h["first_source_op"]):
        start, end = hit["first_source_op"], hit["second_source_op"] + 1
        if ranges and start < ranges[-1][1]:
            ranges[-1] = (ranges[-1][0], max(end, ranges[-1][1]))
        else:
            ranges.append((start, end))
    return ranges, hits, counts, complete, time.monotonic() - started


def optimize_block(operations, window):
    result, certificate = list(operations), []
    while True:
        changed = False
        for i, first in enumerate(result):
            if not first.is_ccx:
                continue
            for j in range(i + 1, min(len(result), i + window + 1)):
                second = result[j]
                operands = pair_operands(first, second)
                if operands is None:
                    continue
                middle = result[i + 1:j]
                if all(shared.commutes_with_ccx(second, op) for op in middle):
                    direction = "second_left"
                elif all(shared.commutes_with_ccx(first, op) for op in middle):
                    direction = "first_right"
                else:
                    continue
                control, left, right, target = operands
                cx = shared.Operation(0x21 | (second.opcode & 0x80), (left, right),
                                      condition=second.condition)
                replacement = [cx, second, cx]
                result[i:j+1] = replacement + middle if direction == "second_left" else middle + replacement
                certificate.append({"first_source_op": first.source_index,
                                    "second_source_op": second.source_index,
                                    "qubits_a_b_c_t": list(operands), "direction": direction,
                                    "explicit_condition_bit": first.condition,
                                    "crossed_current_operations": len(middle)})
                changed = True
                break
            if changed:
                break
        if not changed:
            return result, certificate


def exact_polynomial_check(before, after):
    """Independent Boolean-polynomial proof for unconditional X/CX/CCX blocks.

    A monomial is a bit mask of input variables; a polynomial is a set of
    monomials with coefficients in GF(2). Bitwise OR multiplies monomials
    because Boolean variables obey x*x=x. No basis-state sampling is used.
    """
    wires = sorted({q for op in before + after for q in op.qubits})
    positions = {q: i for i, q in enumerate(wires)}

    def evaluate(operations):
        values = {q: {1 << positions[q]} for q in wires}
        for op in operations:
            if op.condition is not None:
                raise ValueError("Symbolic block proof expects unconditional instructions")
            if op.opcode == 0x11:
                values[op.qubits[0]] ^= {0}
            elif op.opcode == 0x21:
                control, target = op.qubits
                values[target] ^= values[control]
            elif op.opcode == 0x31:
                left, right, target = op.qubits
                product = set()
                for a in values[left]:
                    for b in values[right]:
                        term = a | b
                        if term in product:
                            product.remove(term)
                        else:
                            product.add(term)
                values[target] ^= product
            else:
                raise ValueError("Symbolic block proof supports X/CX/CCX only")
        return values

    original, transformed = evaluate(before), evaluate(after)
    if original != transformed:
        raise AssertionError("Independent exact polynomial comparison failed")
    return {"status": "PASS", "input_variables": len(wires),
            "all_basis_states_covered": 1 << len(wires),
            "maximum_output_degree": max(term.bit_count() for p in original.values() for term in p),
            "phase": "Identical basis permutation; no phase gates on either side."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--cached-profile", type=Path)
    parser.add_argument("--window", type=int, default=256)
    parser.add_argument("--seconds", type=float, default=110)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, help="Optional new candidate; default is read-only")
    args = parser.parse_args()
    started = time.monotonic()
    proof = identity_check()
    if args.output and (args.output.resolve() == args.input.resolve() or args.output.exists()):
        raise FileExistsError("Candidate output must be new and separate from the input")
    profile = (json.loads(args.cached_profile.read_text()) if args.cached_profile and not args.output
               else shared.kp.profile(args.input, max_register_summaries=0))
    circuit = shared.BinaryCircuit(args.input, profile)
    try:
        ranges, hits, counts, complete, scan_seconds = discover(circuit, args.window, args.seconds)
        blocks, replacements = [], []
        for start, end in ranges:
            before = list(circuit.operations(start, end))
            after, certificate = optimize_block(before, args.window)
            stack_depth = circuit.opcodes[:start].count(0x81) - circuit.opcodes[:start].count(0x01)
            polynomial_proof = (exact_polynomial_check(before, after)
                                if all(op.condition is None and op.opcode in (0x11, 0x21, 0x31)
                                       for op in before + after) else None)
            blocks.append({"start_op": start, "end_op_exclusive": end,
                           "before_operations": len(before), "after_operations": len(after),
                           "condition_stack_depth": stack_depth,
                           "exact_polynomial_proof": polynomial_proof,
                           "verified_rewrite_count": len(certificate), "rewrites": certificate})
            if certificate:
                replacements.append((start, end, before, after))
        if args.output:
            if not complete:
                raise RuntimeError("Refusing to write a candidate after a time-bounded partial scan")
            shared.write_rewritten(circuit, args.output, replacements)
    finally:
        circuit.close()
    result = {"status": "COMPLETE" if complete else "TIME_BOUNDED_PARTIAL",
              "input": str(args.input), "input_sha256": profile["raw_kmb_sha256"],
              "scope": ("Candidate written; full decoder verification is still required."
                        if args.output else "Read-only scan. No candidate written; no full decoder validation implied."),
              "identity_proof": proof, "window": args.window, "counts": counts,
              "proved_pairs": hits, "blocks": blocks,
              "total_current_block_rewrites": sum(b["verified_rewrite_count"] for b in blocks),
              "scan_seconds": scan_seconds, "total_seconds": time.monotonic() - started,
              "max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    if args.output:
        after_profile = shared.kp.profile(args.output, max_register_summaries=0)
        observed = (profile["raw_gate_families"]["CCX"]["total"] -
                    after_profile["raw_gate_families"]["CCX"]["total"])
        assert observed == result["total_current_block_rewrites"]
        result.update(output=str(args.output), output_sha256=after_profile["raw_kmb_sha256"],
                      after_header=after_profile["header"], binary_layout_validation="passed",
                      static_ccx_reduction=observed, static_cx_added=2*observed,
                      total_seconds=time.monotonic() - started,
                      max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    args.report.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k:v for k,v in result.items() if k not in ("proved_pairs", "blocks")}, indent=2))


if __name__ == "__main__":
    main()
