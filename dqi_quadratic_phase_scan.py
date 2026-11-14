#!/usr/bin/env python3
"""Read-only exact phase-polynomial scan of bounded affine/CCZ blocks.

Measurements, resets, nonlinear permutations, explicit classical conditions,
and every condition-stack change are barriers. Within one block the implicit
classical condition is fixed. Arbitrary coherent block inputs are allowed.
No KMB is rewritten. A certificate compares the complete Boolean ANF phase
and the complete affine output map, not only sampled classical outcomes.
"""
from __future__ import annotations

import argparse
from collections import Counter
from itertools import product
import json
from pathlib import Path
import re
import time

import dqi_ccx_peephole as shared


ALLOWED = {0x00, 0x10, 0x11, 0x20, 0x21, 0x22, 0x30}
BARRIER = re.compile(rb"[^\x00\x10\x11\x20\x21\x22\x30]")
CCZ = re.compile(rb"\x30")
NAMES = {0x00: "NEG", 0x10: "Z", 0x11: "X", 0x20: "CZ",
         0x21: "CX", 0x22: "SWAP", 0x30: "CCZ"}


def bits(mask):
    while mask:
        bit = mask & -mask
        yield bit.bit_length() - 1
        mask ^= bit


def mul(a, b):
    """Boolean polynomial multiplication in GF(2)[x]/(x_i^2-x_i)."""
    out = set()
    for u in a:
        for v in b:
            term = u | v
            out.symmetric_difference_update((term,))
    return out


def linear_poly(mask, n):
    return {0 if i == n else 1 << i for i in bits(mask)}


def symbolic(ops, wire_ids, max_terms=100000):
    """Exact affine map plus complete degree<=3 ANF phase at block input."""
    n = len(wire_ids)
    indexes = {q: i for i, q in enumerate(wire_ids)}
    rows = [1 << i for i in range(n)]
    phase = set()
    for op in ops:
        if op.opcode not in ALLOWED or op.condition is not None:
            raise ValueError("Unsupported gate inside certified block")
        q = [indexes[x] for x in op.qubits]
        if op.opcode == 0x11:
            rows[q[0]] ^= 1 << n
        elif op.opcode == 0x21:
            rows[q[1]] ^= rows[q[0]]
        elif op.opcode == 0x22:
            rows[q[0]], rows[q[1]] = rows[q[1]], rows[q[0]]
        else:
            term = {0}
            for index in q:
                term = mul(term, linear_poly(rows[index], n))
            phase.symmetric_difference_update(term)
            if len(phase) > max_terms:
                raise OverflowError("ANF term budget exceeded")
    return rows, phase


def independent_rows(rows):
    pivots = {}
    for row in rows:
        while row:
            i = row.bit_length() - 1
            if i not in pivots:
                pivots[i] = row
                break
            row ^= pivots[i]
    return len(pivots)


def linear_factor_basis(cubic, n):
    """Kernel of L -> L wedge cubic, the full space of possible linear factors.

    The highest-degree Boolean ANF transforms as an alternating 3-form.
    For nonzero L, L wedge F=0 iff a linear coordinate change makes all cubic
    terms contain L. Characteristic two removes signs, not repeated-index
    cancellation. Each degree-four coefficient is a homogeneous linear
    equation in the n coefficients of L.
    """
    constraints = {}
    for monomial in cubic:
        for i in range(n):
            bit = 1 << i
            if not monomial & bit:
                key = monomial | bit
                constraints[key] = constraints.get(key, 0) ^ bit
    pivots = {}
    for row in constraints.values():
        while row:
            p = (row & -row).bit_length() - 1
            if p not in pivots:
                pivots[p] = row
                break
            row ^= pivots[p]
    answer = []
    for free in range(n):
        if free in pivots:
            continue
        vector = 1 << free
        for p in sorted(pivots, reverse=True):
            if (pivots[p] & vector).bit_count() & 1:
                vector ^= 1 << p
        assert all(not ((row & vector).bit_count() & 1) for row in constraints.values())
        answer.append(vector)
    return answer


def decompose_quadratic(poly, n):
    """Eliminate one alternating pivot edge, retaining all linear corrections.

    For edge ab, (a+N_b)(b+N_a) removes every edge incident to a or b.
    N_a and N_b omit a,b. The exact XOR residual is checked directly.
    """
    remaining = set(poly)
    pairs = []
    while True:
        edge = next((m for m in sorted(remaining) if m.bit_count() == 2), None)
        if edge is None:
            break
        a, b = list(bits(edge))
        na = nb = 0
        for monomial in remaining:
            if monomial.bit_count() != 2 or monomial == edge:
                continue
            if monomial & (1 << a):
                na ^= monomial ^ (1 << a)
            if monomial & (1 << b):
                nb ^= monomial ^ (1 << b)
        left, right = (1 << a) ^ nb, (1 << b) ^ na
        pairs.append((left, right))
        remaining.symmetric_difference_update(mul(linear_poly(left, n), linear_poly(right, n)))
        assert all(m.bit_count() <= 2 for m in remaining)
    assert all(m.bit_count() <= 1 for m in remaining)
    reconstruction = set(remaining)
    for left, right in pairs:
        reconstruction.symmetric_difference_update(mul(linear_poly(left, n), linear_poly(right, n)))
    assert reconstruction == poly
    matrix = [0] * n
    for term in poly:
        if term.bit_count() == 2:
            a, b = list(bits(term))
            matrix[a] ^= 1 << b
            matrix[b] ^= 1 << a
    rank = independent_rows(matrix)
    assert rank == 2 * len(pairs)
    return pairs, remaining, rank


def synth_network(matrix):
    """CNOT network carrying x to the invertible linear map matrix*x."""
    n = len(matrix)
    a = list(matrix)
    eliminate = []
    for col in range(n):
        pivot = next(r for r in range(col, n) if a[r] >> col & 1)
        if pivot != col:
            for source, target in ((pivot, col), (col, pivot), (pivot, col)):
                a[target] ^= a[source]
                eliminate.append((source, target))
        for r in range(n):
            if r != col and a[r] >> col & 1:
                a[r] ^= a[col]
                eliminate.append((col, r))
    assert a == [1 << i for i in range(n)]
    network = list(reversed(eliminate))
    rows = [1 << i for i in range(n)]
    for source, target in network:
        rows[target] ^= rows[source]
    assert rows == matrix
    return network


def optimize(ops, wire_ids, search_linear=True):
    n = len(wire_ids)
    rows, phase = symbolic(ops, wire_ids)
    cubic = {m for m in phase if m.bit_count() == 3}
    if cubic:
        common = (1 << n) - 1
        for term in cubic:
            common &= term
        if not common:
            factors = linear_factor_basis(cubic, n) if search_linear else []
            if not factors:
                return {"status": "no_common_linear_control", "cubic_terms": len(cubic),
                        "linear_factor_space_dimension": 0,
                        "factor_test": "kernel of L -> L wedge cubic ANF"}
            best = None
            for factor in factors:
                pivot = min(bits(factor))
                network = [shared.Operation(0x21, (wire_ids[i], wire_ids[pivot]))
                           for i in bits(factor) if i != pivot]
                trial = optimize(network + ops + list(reversed(network)), wire_ids, False)
                if "ccz_after" not in trial:
                    raise AssertionError("A nonzero wedge kernel vector failed the coordinate test")
                trial["linear_factor_space_dimension"] = len(factors)
                trial["common_linear_control_qubits"] = [wire_ids[i] for i in bits(factor)]
                if trial["status"] == "proved_saving":
                    by_name = {name: opcode for opcode, name in NAMES.items()}
                    middle = [shared.Operation(by_name[x["name"]], tuple(x["qubits"]))
                              for x in trial["replacement"]]
                    replacement = network + middle + list(reversed(network))
                    new_rows, new_phase = symbolic(replacement, wire_ids)
                    assert new_rows == rows and new_phase == phase
                    trial["source_operations"] = [
                        {"name": NAMES[op.opcode], "qubits": list(op.qubits), "source_index": op.source_index}
                        for op in ops]
                    trial["replacement"] = [{"name": NAMES[op.opcode], "qubits": list(op.qubits)}
                                             for op in replacement]
                if best is None or trial["ccz_after"] < best["ccz_after"]:
                    best = trial
            return best
        control = min(bits(common))
        q = {m ^ (1 << control) for m in cubic}
        pairs, residual, rank = decompose_quadratic(q, n)
    else:
        control, pairs, residual, rank = None, [], set(), 0
    cost_before = sum(op.opcode == 0x30 for op in ops)
    info = {"status": "rank_evaluated", "ccz_before": cost_before,
            "ccz_after": len(pairs), "static_ccz_saving": cost_before - len(pairs),
            "cubic_terms": len(cubic), "quadratic_polar_rank": rank,
            "control_qubit": None if control is None else wire_ids[control]}
    if len(pairs) >= cost_before:
        return info
    replacement = []
    def emit(opcode, q=()):
        replacement.append(shared.Operation(opcode, tuple(wire_ids[i] for i in q)))
    low = phase - cubic
    if control is not None:
        low.symmetric_difference_update({m | (1 << control) for m in residual})
    for term in sorted(low):
        emit({0: 0x00, 1: 0x10, 2: 0x20}[term.bit_count()], tuple(bits(term)))
    if pairs:
        others = [i for i in range(n) if i != control]
        def compress(mask):
            return sum(((mask >> original) & 1) << j for j, original in enumerate(others))
        matrix = [compress(row) for pair in pairs for row in pair]
        assert independent_rows(matrix) == len(matrix)
        for j in range(len(others)):
            test = matrix + [1 << j]
            if independent_rows(test) > len(matrix):
                matrix.append(1 << j)
        assert len(matrix) == len(others)
        network = synth_network(matrix)
        for source, target in network:
            emit(0x21, (others[source], others[target]))
        for j in range(len(pairs)):
            emit(0x30, (control, others[2 * j], others[2 * j + 1]))
        for source, target in reversed(network):
            emit(0x21, (others[source], others[target]))
    replacement += [op for op in ops if op.opcode in (0x11, 0x21, 0x22)]
    new_rows, new_phase = symbolic(replacement, wire_ids)
    assert new_rows == rows and new_phase == phase
    info.update({"status": "proved_saving", "phase_anf_equal": True,
                 "affine_output_equal": True,
                 "proof_scope": "all coherent inputs; inactive shared condition is identity",
                 "input_wires": wire_ids,
                 "source_operations": [{"name": NAMES[op.opcode], "qubits": list(op.qubits),
                                        "source_index": op.source_index} for op in ops],
                 "replacement": [{"name": NAMES[op.opcode], "qubits": list(op.qubits)}
                                 for op in replacement]})
    return info


def self_check():
    # The two CCZ terms have no common pair after the intervening CNOT changes
    # the target, but the complete phased permutation still simplifies.
    op = shared.Operation
    examples = [
        [op(0x30, (0, 1, 2)), op(0x30, (0, 1, 3))],
        [op(0x21, (1, 2)), op(0x30, (0, 2, 3)), op(0x21, (1, 2)),
         op(0x30, (0, 1, 3)), op(0x30, (0, 2, 3))],
        [op(0x11, (1,)), op(0x30, (0, 1, 2)), op(0x11, (1,)), op(0x30, (0, 1, 2))],
        [op(0x21, (4, 0)), op(0x30, (0, 1, 2)), op(0x30, (0, 1, 3)),
         op(0x30, (0, 2, 3)), op(0x21, (4, 0))],
    ]
    checks = []
    basis_cases = 0
    def run(gates, x, active):
        phase = 0
        if not active:
            return x, phase
        for gate in gates:
            q = gate["qubits"]
            name = gate["name"]
            if name == "X":
                x ^= 1 << q[0]
            elif name == "CX":
                x ^= ((x >> q[0]) & 1) << q[1]
            elif name == "SWAP":
                change = ((x >> q[0]) ^ (x >> q[1])) & 1
                x ^= (change << q[0]) | (change << q[1])
            else:
                phase ^= all(x >> i & 1 for i in q)
        return x, phase
    for example in examples:
        wire_count = max(4, 1 + max(q for op in example for q in op.qubits))
        result = optimize(example, list(range(wire_count)))
        assert result["status"] == "proved_saving"
        for x, active in product(range(1 << wire_count), (False, True)):
            assert run(result["source_operations"], x, active) == run(result["replacement"], x, active)
            basis_cases += 1
        checks.append({k: result[k] for k in ("ccz_before", "ccz_after", "phase_anf_equal", "affine_output_equal")})
    # Exhaust all nonzero cubic ANFs on five variables. Check the wedge-kernel
    # test against direct substitution for every nonzero candidate linear form.
    from itertools import combinations
    monomials = [sum(1 << i for i in c) for c in combinations(range(5), 3)]
    factor_cases = 0
    for encoded in range(1, 1 << len(monomials)):
        cubic = {m for i, m in enumerate(monomials) if encoded >> i & 1}
        basis = linear_factor_basis(cubic, 5)
        span = {0}
        for vector in basis:
            span |= {x ^ vector for x in list(span)}
        for factor in range(1, 32):
            pivot = min(bits(factor))
            transformed = set()
            for monomial in cubic:
                if monomial >> pivot & 1:
                    transformed.symmetric_difference_update(
                        mul({monomial ^ (1 << pivot)}, linear_poly(factor, 5)))
                else:
                    transformed.symmetric_difference_update((monomial,))
            direct = all(m >> pivot & 1 for m in transformed if m.bit_count() == 3)
            assert direct == (factor in span)
            factor_cases += 1
    return {"status": "PASS", "synthetic_examples": checks,
            "independent_bit_simulation_cases": basis_cases,
            "exhaustive_5variable_factor_substitution_cases": factor_cases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=270)
    parser.add_argument("--max-ops", type=int, default=4096)
    parser.add_argument("--max-wires", type=int, default=64)
    args = parser.parse_args()
    started = time.monotonic()
    proof = self_check()
    profile = json.loads(args.profile.read_text())
    circuit = shared.BinaryCircuit(args.input, profile)
    stats = Counter()
    histogram = Counter()
    candidates, evaluated = [], []
    completed = True
    try:
        positions = [m.start() for m in CCZ.finditer(circuit.opcodes)]
        groups = []
        for p in positions:
            if not groups or BARRIER.search(circuit.opcodes, groups[-1][-1] + 1, p):
                groups.append([p])
            else:
                groups[-1].append(p)
        for group in groups:
            histogram[len(group)] += 1
            stats["ccz_seen"] += len(group)
            if len(group) < 2:
                stats["single_ccz_blocks"] += 1
                continue
            if time.monotonic() - started > args.seconds:
                completed = False
                break
            first, end = group[0], group[-1] + 1
            if end - first > args.max_ops:
                stats["skipped_operation_budget"] += 1
                continue
            ops = list(circuit.operations(first, end))
            wires = sorted({q for op in ops for q in op.qubits})
            if len(wires) > args.max_wires:
                stats["skipped_wire_budget"] += 1
                continue
            try:
                result = optimize(ops, wires)
            except OverflowError:
                stats["skipped_polynomial_budget"] += 1
                continue
            result.update({"start": first, "end_exclusive": end,
                           "block_operations": len(ops), "block_wires": len(wires),
                           "implicit_condition": "unchanged inside block; PUSH/POP are barriers"})
            stats[result["status"]] += 1
            evaluated.append({k: v for k, v in result.items() if k not in ("source_operations", "replacement", "input_wires")})
            if result["status"] == "proved_saving":
                candidates.append(result)
    finally:
        circuit.close()
    report = {
        "schema": "dqi-common-control-quadratic-phase-scan-v1",
        "scope": "all consecutive CCZ groups bounded by non-affine/conditional/measurement barriers; max4096ops/64wires",
        "input": str(args.input), "input_sha256_from_cached_profile": profile["raw_kmb_sha256"],
        "input_sha256_recomputed_this_run": False,
        "scan_completed": completed, "stats": dict(stats),
        "ccz_count_per_block_histogram": dict(sorted(histogram.items())),
        "evaluated_blocks": evaluated, "candidates": candidates,
        "nonoverlapping_static_ccz_savings": sum(x["static_ccz_saving"] for x in candidates),
        "static_savings_not_official_average": True,
        "self_check": proof, "binary_modified": False,
        "candidate_or_worker_modified": False,
        "seconds": time.monotonic() - started, "peak_rss_mib": shared.kp.peak_rss_mib(),
        "limitations": [
            "Common linear factors of the whole cubic ANF are tested exactly; sums of separately factored subsets are not optimized jointly.",
            "All classical writes, explicit conditional opcodes, PUSH/POP, measurement/reset, CCX/CSWAP, and unknown gates are barriers.",
            "Single-CCZ blocks, >4096 operations, >64 wires, and >100000 ANF terms are excluded.",
            "Candidates are isolated exact local proofs, not a new whole-circuit verification or score.",
        ],
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in ("evaluated_blocks", "candidates")}, indent=2))


if __name__ == "__main__":
    main()
