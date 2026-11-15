#!/usr/bin/env python3
"""Audit local parity-only T synthesis against actual invsqrt phase blocks.

For a fixed classical branch with cubic Boolean sign phase C, write A for
the matrix whose columns are odd parity rotations in units of pi/4. The
zero linear and quadratic parity syndromes imply A A^T = 0. The flattening
of C, including its three symmetric slots and zero repeated-index entries,
is a matrix product with A^T and therefore has rank <= rank(A). If m is the
number of columns of A, self-orthogonality gives m >= 2 rank(A). In the
equality case the row space is self-dual and contains the all-ones vector.
Contracting C by a preimage of that vector gives A A^T = 0, so rank(C) is
strictly below rank(A). Hence m >= 2 rank(C) + 1 for nonzero cubic phase.

The result is for independent entry variables and parity-only Clifford/T
gates. An actual circuit may use correlated entry variables, other angles,
or nonlinear data gates. Quantum data, scratch, and classical lifetimes
are checked independently before the bound is applied.
"""

import argparse
import collections
import itertools
import json
from pathlib import Path
import sys
import tempfile

import kickmix


def multiply(left, right):
    result = set()
    for a in left:
        for b in right:
            term = a | b
            if term in result:
                result.remove(term)
            else:
                result.add(term)
    return result


def update_values(operation, wires, values, xor, product, zero, one):
    if operation == "X":
        target, = wires
        values[target] = xor(values[target], one)
    elif operation == "CX":
        control, target = wires
        values[target] = xor(values[target], values[control])
    elif operation == "CCX":
        control_a, control_b, target = wires
        values[target] = xor(values[target], product(values[control_a], values[control_b]))
    elif operation == "CSWAP":
        control, left, right = wires
        delta = product(values[control], xor(values[left], values[right]))
        values[left] = xor(values[left], delta)
        values[right] = xor(values[right], delta)
    elif operation == "SWAP":
        left, right = wires
        values[left], values[right] = values[right], values[left]
    elif operation == "HMR":
        target, = wires
        values[target] = zero


def track_constants(lines, operations, starts):
    """Use only identities visible from a sound three-valued propagation."""
    snapshots = {}
    values = [None] * 22 + [0] * 24
    stack = []

    def xor(left, right):
        return None if left is None or right is None else left ^ right

    def product(left, right):
        if left == 0 or right == 0:
            return 0
        return None if left is None or right is None else left & right

    def join(left, right):
        return [a if a == b else None for a, b in zip(left, right)]

    for index, (operation, wires) in enumerate(operations):
        if index in starts:
            snapshots[index] = values[:]
        if operation == "PUSH_CONDITION":
            stack.append(values[:])
        elif operation == "POP_CONDITION":
            values = join(values, stack.pop())
        elif operation in {"X", "CX", "CCX", "CSWAP", "SWAP", "HMR"}:
            before = values[:]
            update_values(operation, wires, values, xor, product, 0, 1)
            if " if " in lines[index]:
                values = join(values, before)
        else:
            assert operation in {
                "APPEND_TO_REGISTER", "REGISTER", "BIT_STORE0", "BIT_STORE1", "BIT_INVERT",
                "Z", "CZ", "CCZ", "Z_POW", "NEG",
            }, operation
    assert not stack
    return snapshots


def block_phases(operations, block, symbols, constants):
    values = [set() if c == 0 else {0} if c == 1 else {1 << q}
              for q, c in enumerate(constants)]
    phase_by_index = {j: key for key, indices in symbols["terms"].items() for j in indices}
    stack = []
    phases = collections.defaultdict(set)

    for index in range(block["start"], block["end"] + 1):
        operation, wires = operations[index]
        if index in phase_by_index:
            term = {0}
            for wire in wires:
                term = multiply(term, values[wire])
            phases[phase_by_index[index]] ^= term
        if operation == "PUSH_CONDITION":
            stack.append(values[:])
        elif operation == "POP_CONDITION":
            if values != stack.pop():
                return None, "DATA_RELATION_REQUIRES_REACHABLE_INPUT"
        else:
            update_values(operation, wires, values, set.__xor__, multiply, set(), {0})

    if any(poly and any(key.startswith("measurement_") for key in guard)
           for guard, poly in phases.items()):
        return None, "MEASUREMENT_RELATION_REQUIRES_REACHABLE_INPUT"
    return {guard: poly for guard, poly in phases.items() if poly}, None


def flatten_rank(cubic):
    columns = collections.defaultdict(int)
    for monomial in cubic:
        for wire in range(monomial.bit_length()):
            mask = 1 << wire
            if monomial & mask:
                columns[monomial ^ mask] ^= mask
    basis = {}
    for column in columns.values():
        while column:
            pivot = column.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = column
                break
            column ^= basis[pivot]
    return len(basis)


def analyze(blocks, symbols, operations, constants):
    rows = []
    for block in blocks:
        start = block["start"]
        phases, reason = block_phases(operations, block, symbols[start], constants[start])
        row = dict(block)
        if phases is None:
            row["status"] = reason
            rows.append(row)
            continue
        guards = sorted(set().union(*map(set, phases)))
        if len(guards) > 10:
            row["status"] = "TOO_MANY_EXTERNAL_BRANCHES"
            rows.append(row)
            continue
        row["branches"] = []
        for assignment in itertools.product([0, 1], repeat=len(guards)):
            true_guards = {guard for guard, bit in zip(guards, assignment) if bit}
            polynomial = set()
            for guard, part in phases.items():
                if true_guards.issuperset(guard):
                    polynomial ^= part
            degree = max((term.bit_count() for term in polynomial), default=0)
            entry = {"true_external_guards": sorted(true_guards), "phase_degree": degree}
            if degree > 3:
                entry["status"] = "NOT_A_CLIFFORD_T_PARITY_PHASE"
            elif degree <= 2:
                entry["status"] = "CLIFFORD_PHASE"
            else:
                rank = flatten_rank(term for term in polynomial if term.bit_count() == 3)
                min_t = 2 * rank + 1
                entry |= {"cubic_rank": rank, "t_lower_bound": min_t,
                          "effective_toffoli_lower_bound": min_t / 4}
                entry["status"] = ("NO_STRICT_GAIN_OVER_STATIC_PAID" if min_t >= 4 * block["paid"]
                                   else "BOUND_INCONCLUSIVE")
            row["branches"].append(entry)
        rows.append(row)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.repo))
    import score8_invsqrt_phase_quadratic as prior

    assert flatten_rank([0b111]) == 3
    assert flatten_rank([0b00111, 0b11001]) == 5
    source = args.repo / "score3_invsqrt_cache.kmx"
    assert prior.sha(source) == prior.PIN
    expected_kmb_hash = "684106f101730ca193627229920a0501bef9ea10ccfb34aa453fcf63edadb50a"
    circuit = kickmix.Circuit(source.read_text())
    with tempfile.TemporaryDirectory() as directory:
        rebound = Path(directory) / "rebound.kmb"
        circuit.to_file(rebound, format="kmb")
        assert prior.sha(rebound) == expected_kmb_hash
    lines, operations = prior.R.instructions(source)
    all_blocks, depth, uses = prior.shape(lines, operations)
    eligible = []
    symbols = {}
    for block in all_blocks:
        symbol, _ = prior.symbols(lines, operations, block, depth, uses)
        if symbol:
            eligible.append(block)
            symbols[block["start"]] = symbol
    constants = track_constants(lines, operations, symbols.keys())
    rows = analyze(eligible, symbols, operations, constants)
    summary = collections.Counter(
        branch["status"] for row in rows for branch in row.get("branches", [row])
    )
    output = {"status": "ANALYSIS_ONLY", "source_kmx_sha256": prior.PIN,
              "native_recompiled_kmb_sha256": expected_kmb_hash,
              "source_qubits": circuit.num_qubits,
              "source_static_toffoli_like": circuit.operation_statistics().num_toffoli_like,
              "all_paid_conditional_blocks": len(all_blocks), "eligible_blocks": len(eligible),
              "branch_status_counts": summary, "rows": rows,
              "scope": "Independent live entry values, sound known constants, no reachable domain correlations. "
                       "The source static paid count is an upper bound, not a modeled average. "
                       "No replacement circuit or verifier run."}
    args.output.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({key: value for key, value in output.items() if key != "rows"}, indent=2))


if __name__ == "__main__":
    main()
