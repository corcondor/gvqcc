#!/usr/bin/env python3
"""Exhaustive Boolean/phase analysis of an explicitly grounded pure KMX block.

All wire values at block entry MUST be supplied as independent inputs, known
zeros, or known ones. No measurements, resets, classical conditions, metadata,
or unknown instructions are silently ignored. This analyzes a subspace specified
by that entry context; it does not prove that the surrounding circuit reaches it.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

ARITY = {"X": 1, "CX": 2, "CCX": 3, "SWAP": 2, "CSWAP": 3,
         "Z": 1, "CZ": 2, "CCZ": 3, "NEG": 0}


def qubit_list(text: str) -> list[str]:
    values = [s.strip() for s in text.split(",") if s.strip()]
    if any(re.fullmatch(r"q(?:0|[1-9][0-9]*)", q) is None for q in values):
        raise ValueError("wire lists must contain comma-separated q0, q1, ...")
    if len(set(values)) != len(values):
        raise ValueError("duplicate wire in a declaration")
    return values


def parse_block(text: str, grounded: set[str]):
    gates = []
    for line_number, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        # An operation index printed by a dump is a label, not an instruction.
        line = re.sub(r"^[0-9]+\s*:\s*", "", line)
        tokens = line.split()
        op, args = tokens[0], tokens[1:]
        if op not in ARITY:
            raise ValueError(f"line {line_number}: unsupported instruction {op}; "
                             "only pure reversible gates and sign phases are accepted")
        if len(args) != ARITY[op]:
            raise ValueError(f"line {line_number}: {op} requires exactly {ARITY[op]} "
                             "qubit operands; classical conditions are not supported")
        if len(set(args)) != len(args):
            raise ValueError(f"line {line_number}: repeated wire operand")
        missing = [q for q in args if q not in grounded]
        if missing:
            raise ValueError(f"line {line_number}: ungrounded wires {missing}; "
                             "declare their entry values explicitly")
        gates.append((op, *args))
    return gates


def apply_gate(values: dict[str, int], phase: int, gate: tuple,
               full_mask: int) -> int:
    op, *q = gate
    if op == "X":
        values[q[0]] ^= full_mask
    elif op == "CX":
        values[q[1]] ^= values[q[0]]
    elif op == "CCX":
        values[q[2]] ^= values[q[0]] & values[q[1]]
    elif op == "SWAP":
        values[q[0]], values[q[1]] = values[q[1]], values[q[0]]
    elif op == "CSWAP":
        delta = values[q[0]] & (values[q[1]] ^ values[q[2]])
        values[q[1]] ^= delta
        values[q[2]] ^= delta
    elif op == "Z":
        phase ^= values[q[0]]
    elif op == "CZ":
        phase ^= values[q[0]] & values[q[1]]
    elif op == "CCZ":
        phase ^= values[q[0]] & values[q[1]] & values[q[2]]
    elif op == "NEG":
        phase ^= full_mask
    else:
        raise ValueError(f"unrecognized gate {op}")
    return phase


def anf(mask: int, inputs: list[str], cases: int) -> dict:
    coeff = [(mask >> x) & 1 for x in range(cases)]
    for i in range(len(inputs)):
        bit = 1 << i
        for x in range(cases):
            if x & bit:
                coeff[x] ^= coeff[x ^ bit]
    support = [x for x, c in enumerate(coeff) if c]
    return {
        "degree": max((x.bit_count() for x in support), default=-1),
        "term_count": len(support),
        "monomial_masks": support,
        "terms": [[q for i, q in enumerate(inputs) if x & (1 << i)]
                  for x in support],
        "convention": "[] is the constant 1; zero polynomial has degree -1",
    }


def affine_compression(output_masks: list[int], outputs: list[str], full_mask: int):
    offset = [v & 1 for v in output_masks]  # output at independent input 0
    rows = [v ^ (full_mask if c else 0) for v, c in zip(output_masks, offset)]
    basis_rows = [1 << i for i in range(len(outputs))]
    network = [("X", q) for q, c in zip(outputs, offset) if c]
    rank = 0
    cases = full_mask.bit_length()
    for column in range(cases):
        pivot = next((i for i in range(rank, len(rows)) if rows[i] & (1 << column)), None)
        if pivot is None:
            continue
        if pivot != rank:
            rows[rank], rows[pivot] = rows[pivot], rows[rank]
            basis_rows[rank], basis_rows[pivot] = basis_rows[pivot], basis_rows[rank]
            # Emit only X and CX in the coordinate-change network. A row swap
            # uses three CX gates so it needs no special synthesis support.
            a, b = outputs[rank], outputs[pivot]
            network.extend([("CX", a, b), ("CX", b, a), ("CX", a, b)])
        for i in range(len(rows)):
            if i != rank and rows[i] & (1 << column):
                rows[i] ^= rows[rank]
                basis_rows[i] ^= basis_rows[rank]
                network.append(("CX", outputs[rank], outputs[i]))
        rank += 1
        if rank == len(rows):
            break
    # Verify the emitted network on every input, including constants.
    actual = dict(zip(outputs, output_masks))
    for gate in network:
        apply_gate(actual, 0, gate, full_mask)
    assert [actual[q] for q in outputs] == rows
    assert all(v == 0 for v in rows[rank:])
    inverse = list(reversed(network))  # X, CX, SWAP are self inverse
    for gate in inverse:
        apply_gate(actual, 0, gate, full_mask)
    assert [actual[q] for q in outputs] == output_masks
    return {
        "rank": rank,
        "offset_at_input_zero": sum(c << i for i, c in enumerate(offset)),
        "linear_basis_rows_bitmasks": basis_rows,
        "retained_output_wires": outputs[:rank],
        "zero_output_wires_after_network": outputs[rank:],
        "network_kmx": [" ".join(g) for g in network],
        "inverse_network_kmx": [" ".join(g) for g in inverse],
        "network_exhaustively_verified": True,
        "scope": "An invertible change of output coordinates on this declared entry "
                 "subspace. It does not reduce the original computation's peak qubits "
                 "or automatically rewrite subsequent consumers.",
    }


def analyze(text: str, inputs: list[str], outputs: list[str],
            zeros: list[str], ones: list[str]) -> dict:
    if len(inputs) > 12:
        raise ValueError("at most 12 independent inputs (4096 assignments) are supported")
    if not outputs:
        raise ValueError("at least one output wire is required")
    groups = [inputs, outputs, zeros, ones]
    if any(len(g) != len(set(g)) for g in groups):
        raise ValueError("duplicate wire within declaration")
    declared = inputs + zeros + ones
    if len(declared) != len(set(declared)):
        raise ValueError("inputs, known-zero wires and known-one wires must be disjoint")
    if any(re.fullmatch(r"q(?:0|[1-9][0-9]*)", q) is None for q in declared + outputs):
        raise ValueError("invalid qubit identifier")
    if not set(outputs) <= set(declared):
        raise ValueError("every output's entry value must also be explicitly declared")
    cases = 1 << len(inputs)
    full_mask = (1 << cases) - 1
    values = {q: sum(((x >> i) & 1) << x for x in range(cases))
              for i, q in enumerate(inputs)}
    values.update({q: 0 for q in zeros})
    values.update({q: full_mask for q in ones})
    initial = values.copy()
    gates = parse_block(text, set(declared))
    phase = 0
    for gate in gates:
        phase = apply_gate(values, phase, gate, full_mask)
    output_masks = [values[q] for q in outputs]
    output_values = [sum(((v >> x) & 1) << j for j, v in enumerate(output_masks))
                     for x in range(cases)]
    image_size = len(set(output_values))
    compression = affine_compression(output_masks, outputs, full_mask)
    compression["output_wires_disjoint_from_inputs"] = not bool(set(outputs) & set(inputs))
    return {
        "format": "boolean-block-analysis-v1",
        "block_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "context": {"inputs": inputs, "outputs": outputs, "known_zero": zeros,
                    "known_one": ones, "independent_input_count": len(inputs)},
        "assignments_checked": cases,
        "gate_counts": dict(sorted(Counter(g[0] for g in gates).items())),
        "input_restoration": {q: values[q] == initial[q] for q in inputs},
        "all_inputs_restored": all(values[q] == initial[q] for q in inputs),
        "other_wire_restoration": {q: values[q] == initial[q]
                                   for q in declared if q not in inputs and q not in outputs},
        "image_count": image_size,
        "output_map_injective": image_size == cases,
        "image_information_lower_bound_bits": (image_size - 1).bit_length(),
        "output_anf": {q: anf(values[q], inputs, cases) for q in outputs},
        "phase_anf": anf(phase, inputs, cases),
        "affine_compression": compression,
        "truth_table": [{"input": x, "output": y,
                         "phase_sign": -1 if (phase >> x) & 1 else 1}
                        for x, y in enumerate(output_values)],
        "bit_order": "bit i corresponds to the ith wire in the respective declared list",
        "limitations": [
            "The stated entry values and independent-input assumption must be justified externally.",
            "Image size is not affine-span rank: six independent inputs can have output affine rank twelve.",
            "No claim of optimal gate synthesis, lower peak workspace, or validity in a surrounding DQI circuit.",
        ],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--file", required=True, type=Path)
    p.add_argument("--inputs", required=True, help="comma-separated independent entry wires")
    p.add_argument("--outputs", required=True, help="comma-separated output wires in desired bit order")
    p.add_argument("--zero", default="", help="comma-separated wires proven zero at entry")
    p.add_argument("--ones", default="", help="comma-separated wires proven one at entry")
    p.add_argument("--json", type=Path, help="write the complete report here instead of stdout")
    args = p.parse_args()
    try:
        result = analyze(args.file.read_text(), qubit_list(args.inputs), qubit_list(args.outputs),
                         qubit_list(args.zero), qubit_list(args.ones))
        result["source_file"] = str(args.file.resolve())
        encoded = json.dumps(result, indent=2) + "\n"
        if args.json:
            args.json.parent.mkdir(parents=True, exist_ok=True)
            args.json.write_text(encoded)
            print(json.dumps({"report": str(args.json.resolve()),
                              "assignments": result["assignments_checked"],
                              "inputs_restored": result["all_inputs_restored"],
                              "image_count": result["image_count"],
                              "output_affine_rank": result["affine_compression"]["rank"]}))
        else:
            print(encoded, end="")
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
