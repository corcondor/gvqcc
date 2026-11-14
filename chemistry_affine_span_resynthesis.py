#!/usr/bin/env python3
"""Exact, domain-aware CCX-to-linear replacement for the fixed ANGLE loaders.

Each qubit is tracked as a Boolean polynomial of the arbitrary 40-bit output
register, with complete address truth tables as its coefficients. A CCX is replaced only if its control
product is already in the linear span of other live wires and the constant.
The supplied source circuits are never changed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import resource
import time

import kickmix as km


def basis_expression(values, wanted, excluded, one):
    basis = {}
    for wire, value in [(len(values), one)] + list(enumerate(values)):
        if wire == excluded or not value:
            continue
        expression = 1 << wire
        while value:
            pivot = value.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = (value, expression)
                break
            old, support = basis[pivot]
            value ^= old
            expression ^= support
    expression = 0
    while wanted:
        pivot = wanted.bit_length() - 1
        if pivot not in basis:
            return None
        old, support = basis[pivot]
        wanted ^= old
        expression ^= support
    return expression


def parse_line(line):
    parts = line.split()
    if not parts or parts[0] in {"APPEND_TO_REGISTER", "REGISTER"}:
        return parts[0] if parts else "", (), None
    condition = int(parts[-1][1:]) if "if" in parts else None
    operands = tuple(int(p[1:]) for p in parts[1:] if p.startswith("q"))
    return parts[0], operands, condition


def xor_poly(left, right):
    result = dict(left)
    for term, coefficient in right.items():
        result[term] = result.get(term, 0) ^ coefficient
        if not result[term]:
            del result[term]
    return result


def mul_poly(left, right):
    result = {}
    for a, va in left.items():
        for b, vb in right.items():
            term, coefficient = a | b, va & vb
            result[term] = result.get(term, 0) ^ coefficient
    return {term: coefficient for term, coefficient in result.items() if coefficient}


def optimize(path, address_count=2048):
    circuit = km.Circuit.from_file(path)
    lines = str(circuit).splitlines()
    one = (1 << address_count) - 1
    polynomials = [{} for _ in range(circuit.num_qubits)]
    term_ids = {0: 0}
    def pack(poly):
        result = 0
        for term, coefficient in poly.items():
            if term not in term_ids:
                if len(term_ids) >= 4096:
                    raise ValueError("Symbolic-term memory limit reached")
                term_ids[term] = len(term_ids)
            result |= coefficient << (address_count * term_ids[term])
        return result
    for q in range(11):
        polynomials[q] = {0: sum(1 << a for a in range(address_count) if (a >> q) & 1)}
    for q in range(11, 51):
        polynomials[q] = {1 << (q-11): one}
    values = [pack(p) for p in polynomials]
    initial_polynomials = [dict(p) for p in polynomials]
    rewritten, hits = [], []
    measurement_phase = {}
    measurement_count = 0
    counts = {"CCX": 0, "nonlinear_products_representable": 0, "arbitrary_output_controls": 0}
    for pos, line in enumerate(lines):
        name, qubits, condition = parse_line(line)
        replacement = [line]
        if name in {"CX", "X", "CCX", "R", "HMR"} and condition is not None:
            raise ValueError("Classically conditioned state mutation requires an explicit branch proof")
        if name == "X":
            polynomials[qubits[0]] = xor_poly(polynomials[qubits[0]], {0:one})
            values[qubits[0]] ^= one
        elif name == "CX":
            a, b = qubits
            polynomials[b] = xor_poly(polynomials[b], polynomials[a])
            values[b] ^= values[a]
        elif name == "CCX":
            a, b, target = qubits
            counts["CCX"] += 1
            if (values[a] | values[b]) >> address_count:
                counts["arbitrary_output_controls"] += 1
            product_poly = mul_poly(polynomials[a], polynomials[b])
            product = pack(product_poly)
            expression = basis_expression(values, product, target, one)
            if expression is not None:
                controls = [q for q in range(len(values)) if expression >> q & 1]
                constant = bool(expression >> len(values) & 1)
                reconstructed = one if constant else 0
                for q in controls:
                    reconstructed ^= values[q]
                assert reconstructed == product and target not in controls
                replacement = ([f"X q{target}"] if constant else []) + [f"CX q{q} q{target}" for q in controls]
                counts["nonlinear_products_representable"] += 1
                hits.append({"line_index": pos, "original": line, "replacement": replacement,
                             "coefficient_vector_sha256": hashlib.sha256(product.to_bytes((product.bit_length() + 7)//8, "little")).hexdigest()})
            polynomials[target] = xor_poly(polynomials[target], product_poly)
            values[target] ^= product
        elif name == "CZ":
            if condition != 0:
                raise ValueError("Only measurement-conditioned CZ is supported")
            measurement_phase = xor_poly(measurement_phase, mul_poly(polynomials[qubits[0]], polynomials[qubits[1]]))
        elif name == "HMR":
            assert not measurement_phase, ("uncancelled previous measurement phase", pos)
            measurement_phase = dict(polynomials[qubits[0]])
            measurement_count += 1
            polynomials[qubits[0]] = {}
            values[qubits[0]] = 0
        elif name == "R":
            assert not polynomials[qubits[0]], ("reset of a nonzero function", pos)
            polynomials[qubits[0]] = {}
            values[qubits[0]] = 0
        elif name not in {"", "APPEND_TO_REGISTER", "REGISTER"}:
            raise ValueError("Unsupported gate: " + name)
        rewritten.extend(replacement)
    for q in range(51, len(values)):
        assert values[q] == 0, ("dirty scratch", q)
    assert not measurement_phase, "uncancelled final measurement phase"
    for q in range(11):
        assert polynomials[q] == initial_polynomials[q], ("selection changed", q)
    changed_output_wires = [q for q in range(11, 51)
                            if {term:v for term,v in polynomials[q].items() if term}
                            != initial_polynomials[q]]
    counts["output_monomials_seen"] = len(term_ids)
    counts["all_measurement_phases_cancelled"] = measurement_count
    counts["selection_restored"] = True
    counts["workspace_clean_for_all_output_symbols"] = True
    counts["arbitrary_output_xor_structure"] = not changed_output_wires
    counts["arbitrary_output_structure_changed_wires"] = changed_output_wires
    return "\n".join(rewritten) + "\n", counts, hits


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--loaders", required=True, type=Path)
    ap.add_argument("--output-dir", required=True, type=Path)
    ap.add_argument("--report", required=True, type=Path)
    ap.add_argument("--addresses", type=int, default=2048, choices=[1220,2048])
    args=ap.parse_args()
    if args.report.exists() or args.output_dir.exists():
        raise FileExistsError("Use fresh output paths")
    started=time.monotonic()
    report={"status":"COMPLETE", "address_count":args.addresses, "output_symbols":40,
            "script_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "scope":"Single CCX control products in the GF(2) linear span of currently live wires, on the complete selected address domain and arbitrary 40-bit output symbols. Not joint nonlinear resynthesis.",
            "contract_diagnostic":"Arbitrary-output XOR structure is recorded independently of the replacement search. A false value is not itself a claim about current competition validity.",
            "loaders":[]}
    candidates=[]
    for k in range(15):
        source=args.loaders/f"angle_k_{k}.kmb"
        text, counts, hits=optimize(source, args.addresses)
        row={"k":k,"source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
             **counts,"hits":hits}
        report["loaders"].append(row)
        if hits:
            candidates.append((k,text))
        print(json.dumps({"k":k, **counts}),flush=True)
    report["total_ccx_reduction"]=sum(r["nonlinear_products_representable"] for r in report["loaders"])
    report["seconds"]=time.monotonic()-started
    report["peak_rss_mib"]=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024
    report["candidate_semantic_verification"]="NOT_PERFORMED" if candidates else "NO_CANDIDATE"
    report["source_files_modified"]=False
    if candidates:
        args.output_dir.mkdir()
        for k,text in candidates:
            (args.output_dir/f"angle_k_{k}.kmx").write_text(text)
    args.report.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({key:report[key] for key in ["total_ccx_reduction","seconds","peak_rss_mib"]}))


if __name__ == "__main__":
    main()
