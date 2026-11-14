#!/usr/bin/env python3
"""Exact sparse Boolean ANF propagation for an explicitly grounded pure KMX block.

No exhaustive input enumeration. Limits abort, never truncate the polynomial.
Run from the same directory as boolean_block_analyze.py (parser dependency).
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from boolean_block_analyze import parse_block, qubit_list


class Algebra:
    def __init__(self, max_terms=50000, max_degree=8, max_products=5000000):
        if min(max_terms, max_degree, max_products) < 1:
            raise ValueError("resource limits must be positive")
        self.max_terms, self.max_degree, self.max_products = max_terms, max_degree, max_products
        self.peak_terms = 0
        self.peak_degree = -1

    def check(self, p):
        degree = max((m.bit_count() for m in p), default=-1)
        self.peak_terms = max(self.peak_terms, len(p))
        self.peak_degree = max(self.peak_degree, degree)
        if len(p) > self.max_terms:
            raise ValueError(f"exact analysis aborted: polynomial term limit {self.max_terms} exceeded")
        if degree > self.max_degree:
            raise ValueError(f"exact analysis aborted: degree {degree} exceeds limit {self.max_degree}")
        return p

    def xor(self, a, b):
        return self.check(a ^ b)

    def mul(self, a, b):
        if len(a) * len(b) > self.max_products:
            raise ValueError(f"exact analysis aborted: multiplication pair limit {self.max_products} exceeded")
        out = set()
        for ma in a:
            for mb in b:
                m = ma | mb  # Boolean ring: x_i squared equals x_i.
                if m in out:
                    out.remove(m)
                else:
                    out.add(m)
                if len(out) > self.max_terms or m.bit_count() > self.max_degree:
                    self.check(out)
        return self.check(out)

    def gate(self, values, phase, gate):
        op, *q = gate
        if op == "X":
            values[q[0]] = self.xor(values[q[0]], {0})
        elif op == "CX":
            values[q[1]] = self.xor(values[q[1]], values[q[0]])
        elif op == "CCX":
            values[q[2]] = self.xor(values[q[2]], self.mul(values[q[0]], values[q[1]]))
        elif op == "SWAP":
            values[q[0]], values[q[1]] = values[q[1]], values[q[0]]
        elif op == "CSWAP":
            d = self.mul(values[q[0]], self.xor(values[q[1]], values[q[2]]))
            values[q[1]] = self.xor(values[q[1]], d)
            values[q[2]] = self.xor(values[q[2]], d)
        elif op in {"Z", "CZ", "CCZ", "NEG"}:
            p = {0}
            for wire in q:
                p = self.mul(p, values[wire])
            phase = self.xor(phase, p)
        else:
            raise ValueError(f"unsupported instruction {op}")
        return phase


def polynomial(p, inputs):
    support = sorted(p)
    return {"degree": max((m.bit_count() for m in p), default=-1),
            "term_count": len(p), "monomial_masks": support,
            "terms": [[q for i, q in enumerate(inputs) if m & (1 << i)] for m in support],
            "convention": "[] is the constant 1; zero polynomial has degree -1"}


def compress(polys, outputs, algebra):
    rows = [p - {0} for p in polys]
    offset = [int(0 in p) for p in polys]
    basis = [1 << i for i in range(len(outputs))]
    net = [("X", q) for q, c in zip(outputs, offset) if c]
    rank = 0
    while rank < len(rows):
        pivot_row = next((i for i in range(rank, len(rows)) if rows[i]), None)
        if pivot_row is None:
            break
        if pivot_row != rank:
            rows[rank], rows[pivot_row] = rows[pivot_row], rows[rank]
            basis[rank], basis[pivot_row] = basis[pivot_row], basis[rank]
            a, b = outputs[rank], outputs[pivot_row]
            net.extend([("CX", a, b), ("CX", b, a), ("CX", a, b)])
        pivot = min(rows[rank])
        for i in range(len(rows)):
            if i != rank and pivot in rows[i]:
                rows[i] = algebra.xor(rows[i], rows[rank])
                basis[i] ^= basis[rank]
                net.append(("CX", outputs[rank], outputs[i]))
        rank += 1
    actual = dict(zip(outputs, polys))
    for gate in net:
        algebra.gate(actual, set(), gate)
    if [actual[q] for q in outputs] != rows or any(rows[rank:]):
        raise AssertionError("coordinate network failed exact polynomial verification")
    for gate in reversed(net):
        algebra.gate(actual, set(), gate)
    if [actual[q] for q in outputs] != polys:
        raise AssertionError("inverse coordinate network failed exact polynomial verification")
    return {"rank": rank, "coefficient_matrix": "nonconstant ANF monomials as columns",
            "offset_at_input_zero": sum(c << i for i, c in enumerate(offset)),
            "linear_basis_rows_bitmasks": basis,
            "retained_output_wires": outputs[:rank],
            "zero_output_wires_after_network": outputs[rank:],
            "network_kmx": [" ".join(g) for g in net],
            "inverse_network_kmx": [" ".join(g) for g in reversed(net)],
            "network_exactly_verified": True,
            "scope": "Exact affine span over the entire declared independent-input cube; "
                     "does not prove lower peak qubits or a valid rewrite of downstream consumers."}


def analyze(text, inputs, outputs, zeros, ones, max_terms=50000, max_degree=8,
            max_products=5000000):
    declarations = inputs + zeros + ones
    if not outputs:
        raise ValueError("at least one output required")
    if len(declarations) != len(set(declarations)) or len(outputs) != len(set(outputs)):
        raise ValueError("entry declarations must be disjoint and every list duplicate-free")
    qubit_list(",".join(declarations))
    qubit_list(",".join(outputs))
    if not set(outputs) <= set(declarations):
        raise ValueError("every output's entry value must be explicitly declared")
    gates = parse_block(text, set(declarations))
    values = {q: {1 << i} for i, q in enumerate(inputs)}
    values.update({q: set() for q in zeros})
    values.update({q: {0} for q in ones})
    initial = values.copy()
    algebra = Algebra(max_terms, max_degree, max_products)
    phase = set()
    for index, gate in enumerate(gates):
        try:
            phase = algebra.gate(values, phase, gate)
        except ValueError as exc:
            raise ValueError(f"gate {index} ({' '.join(gate)}): {exc}") from exc
    outputs_anf = {q: polynomial(values[q], inputs) for q in outputs}
    compression = compress([values[q] for q in outputs], outputs, algebra)
    return {"format": "symbolic-boolean-block-analysis-v1", "exact": True,
            "block_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "context": {"inputs": inputs, "outputs": outputs, "known_zero": zeros,
                        "known_one": ones, "independent_input_count": len(inputs)},
            "gate_counts": dict(sorted(Counter(g[0] for g in gates).items())),
            "input_restoration": {q: values[q] == initial[q] for q in inputs},
            "all_inputs_restored": all(values[q] == initial[q] for q in inputs),
            "other_wire_restoration": {q: values[q] == initial[q] for q in declarations
                                       if q not in inputs and q not in outputs},
            "output_anf": outputs_anf, "phase_anf": polynomial(phase, inputs),
            "max_output_degree": max(v["degree"] for v in outputs_anf.values()),
            "outputs_above_degree_two": [q for q, p in outputs_anf.items() if p["degree"] > 2],
            "affine_compression": compression,
            "limits": {"max_terms": max_terms, "max_degree": max_degree,
                       "max_products": max_products, "peak_terms": algebra.peak_terms,
                       "peak_degree": algebra.peak_degree},
            "limitations": ["Entry values and independent input context must be justified externally.",
                            "No truth-table enumeration, image-size or injectivity claim is made.",
                            "The rank is exact for the declared cube; correlations in actual inputs may lower it.",
                            "Output compression does not establish a lower computation peak or resynthesis."]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--file", required=True, type=Path)
    for name in ["inputs", "outputs"]:
        p.add_argument("--" + name, required=True)
    for name in ["zero", "ones"]:
        p.add_argument("--" + name, default="")
    p.add_argument("--max-terms", type=int, default=50000)
    p.add_argument("--max-degree", type=int, default=8)
    p.add_argument("--max-products", type=int, default=5000000)
    p.add_argument("--json", type=Path)
    a = p.parse_args()
    try:
        r = analyze(a.file.read_text(), qubit_list(a.inputs), qubit_list(a.outputs),
                    qubit_list(a.zero), qubit_list(a.ones), a.max_terms, a.max_degree, a.max_products)
        r["source_file"] = str(a.file.resolve())
        encoded = json.dumps(r, indent=2) + "\n"
        if a.json:
            a.json.parent.mkdir(parents=True, exist_ok=True)
            a.json.write_text(encoded)
            print(json.dumps({"report": str(a.json.resolve()), "exact": True,
                              "inputs": len(qubit_list(a.inputs)),
                              "max_output_degree": r["max_output_degree"],
                              "output_affine_rank": r["affine_compression"]["rank"],
                              "inputs_restored": r["all_inputs_restored"]}))
        else:
            print(encoded, end="")
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
