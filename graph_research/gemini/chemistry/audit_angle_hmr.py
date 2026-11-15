#!/usr/bin/env python3
"""Verify clean-AND erasure and screen redundant CCX for the ANGLE family."""
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path

import kickmix as km
import numpy as np


def xor_tuple(left, right):
    return left[0] ^ right[0], left[1] ^ right[1]


def solve_affine(state, target, function, full):
    """Express a function using exactly the currently live clean data lanes."""
    basis = {}
    for wire in [-1, *range(len(state))]:
        if wire == -1:
            row = full
        elif wire == target or state[wire][1]:
            continue
        else:
            row = state[wire][0]
        comb = 1 << (wire + 1)
        while row:
            pivot = row.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = (row, comb)
                break
            head, predecessor = basis[pivot]
            row ^= head
            comb ^= predecessor
    ans = 0
    while function:
        pivot = function.bit_length() - 1
        if pivot not in basis:
            return None
        row, comb = basis[pivot]
        function ^= row
        ans ^= comb
    return [i - 1 for i in range(len(state) + 1) if (ans >> i) & 1]


def audit(path, incoming=None, expected=None):
    circuit = km.Circuit.from_file(path)
    n_addresses = 2048 if incoming is None else incoming.shape[0]
    full = (1 << n_addresses) - 1
    address_values = [sum(1 << a for a in range(n_addresses) if (a >> q) & 1)
                      for q in range(11)]
    state = [(v, 0) for v in address_values]
    def packed_bit(words, k):
        q, r = divmod(k, 8)
        return sum(1 << a for a in range(n_addresses) if (int(words[a, q]) >> r) & 1)
    state += [(0 if incoming is None else packed_bit(incoming, q),
               1 << (q - 1 if incoming is not None and q % 8 == 7 else q))
              for q in range(40)]
    state += [(0, 0)] * (circuit.num_qubits - 51)
    pristine_delta = tuple(state)
    active_workspace = {}
    reset = set()
    pending = None
    counts = Counter()
    affine = []
    output_products = defaultdict(list)
    phase_pair_assertions = []
    for pos, line in enumerate(str(circuit).splitlines(), 1):
        gate, *parts = line.split()
        counts[gate] += 1
        if gate in {"REGISTER", "APPEND_TO_REGISTER"}:
            continue
        if pending is not None:
            assert gate == "CZ", (path.name, pos, gate, pending)
        wires = [int(p[1:]) for p in parts if p.startswith("q")]
        if gate == "X":
            assert len(parts) == 1
            q, = wires
            state[q] = xor_tuple(state[q], (full, 0))
        elif gate == "CX":
            assert len(parts) == 2
            a, b = wires
            assert not state[a][1] or 11 <= b < 51, (path, pos, line)
            state[b] = xor_tuple(state[b], state[a])
        elif gate == "CCX":
            assert len(parts) == 3
            a, b, dst = wires
            assert dst >= 11
            assert not state[a][1] and not state[b][1], (path, pos, line, state[a][1], state[b][1])
            function = state[a][0] & state[b][0]
            if dst >= 51:
                assert dst in reset and dst not in active_workspace and state[dst] == (0, 0)
                active_workspace[dst] = (pos, frozenset((a, b)), function)
                reset.remove(dst)
                counts["work_ccx"] += 1
            else:
                output_products[min(function, function ^ full)].append(pos)
                counts["word_ccx"] += 1
            recipe = solve_affine(state, dst, function, full)
            if recipe is not None:
                affine.append({"line": pos, "target": dst, "xor_of": recipe})
            state[dst] = xor_tuple(state[dst], (function, 0))
        elif gate == "R":
            q, = wires
            assert len(parts) == 1
            assert q >= 51 and state[q] == (0, 0) and q not in reset and q not in active_workspace
            reset.add(q)
        elif gate == "HMR":
            q, = wires
            assert q in active_workspace and parts[1] == "b0" and len(parts) == 2
            launch, controls, function = active_workspace.pop(q)
            assert state[q] == (function, 0)
            pending = (q, controls, function, launch, pos)
            state[q] = (0, 0)
        elif gate == "CZ":
            a, b = wires
            assert parts[-2:] == ["if", "b0"] and len(parts) == 4
            assert pending is not None
            q, controls, function, launch, measured = pending
            assert not state[a][1] and not state[b][1], (path, pos, line, state[a][1], state[b][1])
            assert function == state[a][0] & state[b][0]
            assert controls == frozenset((a, b))
            phase_pair_assertions.append((launch, measured, pos, a, b, q))
            pending = None
        else:
            raise ValueError((path, pos, gate))
    assert not active_workspace and not reset and pending is None
    assert tuple(state[:11]) == pristine_delta[:11]
    assert all(state[q][1] == pristine_delta[q][1] for q in range(11, 51))
    if expected is not None:
        assert all(state[q][0] == packed_bit(expected, q - 11) for q in range(11, 51))
    assert all(record == (0, 0) for record in state[51:])
    assert counts["CCX"] == counts["work_ccx"] + counts["word_ccx"]
    exact_delta = b"".join((state[q][0] ^ pristine_delta[q][0]).to_bytes((n_addresses + 7) // 8, "little")
                           for q in range(11, 51))
    return {
        "sha256": sha256(path.read_bytes()).hexdigest(),
        "independent_arbitrary_word_bits": 40 if incoming is None else 35,
        "addresses": n_addresses,
        "q": circuit.num_qubits,
        "histogram": dict(counts),
        "matched_clean_ands": len(phase_pair_assertions),
        "first_compute_hmr_cz_control1_control2_target": phase_pair_assertions[0],
        "arbitrary_target_xor_delta_sha256": sha256(exact_delta).hexdigest(),
        "simply_redundant_ccx": affine,
        "repeated_output_products_up_to_complement":
            [lines for lines in output_products.values() if len(lines) > 1],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("loaders", type=Path)
    parser.add_argument("--table", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with np.load(args.table, allow_pickle=False) as f:
        words = f["angle_words"].astype(np.uint8)
    assert words.shape == (1220, 75)
    parts = [words[:, 5*k:5*(k+1)] for k in range(15)]
    results = [audit(args.loaders / "angle_k_0.kmb")]
    for k in range(1,15):
        results.append(audit(args.loaders / f"angle_k_{k}.kmb", parts[k-1], parts[k]))
    totals = Counter()
    for result in results:
        totals.update(result["histogram"])
    receipt = {
        "matched_clean_ands": sum(row["matched_clean_ands"] for row in results),
        "simply_redundant_ccx": sum(len(row["simply_redundant_ccx"]) for row in results),
        "duplicate_output_product_classes": sum(
            len(row["repeated_output_products_up_to_complement"]) for row in results),
        "totals": dict(totals),
        "loaders": results,
    }
    args.out.write_text(json.dumps(receipt, indent=2) + "\n")
    print({k: v for k, v in receipt.items() if k != "loaders"})


if __name__ == "__main__":
    main()
