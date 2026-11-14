#!/usr/bin/env python3
"""Exact final-output dependence on five preserved coded-word tags."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import resource
import time

import kickmix as km

from chemistry_affine_span_resynthesis import parse_line, xor_poly, mul_poly


def analyze(path, count=1220):
    circuit = km.Circuit.from_file(path)
    one = (1 << count)-1
    state = [{} for _ in range(circuit.num_qubits)]
    for q in range(11):
        state[q] = {0:sum(1 << a for a in range(count) if a >> q & 1)}
    for q in range(11,51):
        state[q] = {1 << (q-11):one}
    for line in str(circuit).splitlines():
        name, qs, condition = parse_line(line)
        if name in {"X","CX","CCX","HMR","R"} and condition is not None:
            raise ValueError("Unsupported state mutation")
        if name == "X":
            state[qs[0]] = xor_poly(state[qs[0]], {0:one})
        elif name == "CX":
            state[qs[1]] = xor_poly(state[qs[1]],state[qs[0]])
        elif name == "CCX":
            state[qs[2]] = xor_poly(state[qs[2]],mul_poly(state[qs[0]],state[qs[1]]))
        elif name in {"HMR","R"}:
            state[qs[0]] = {}
        elif name not in {"", "REGISTER", "APPEND_TO_REGISTER", "CZ"}:
            raise ValueError(name)
    expansions_checked = 0
    for i, polynomial in enumerate(state[11:51]):
        update = xor_poly(polynomial,{1 << i:one})
        compressed = {}
        for monomial, coefficient in update.items():
            tagmask = 0
            for bit in range(40):
                if monomial >> bit & 1:
                    assert bit % 8 in {6,7}
                    assert not tagmask >> (bit//8) & 1
                    tagmask |= 1 << (bit//8)
            if tagmask in compressed:
                assert compressed[tagmask] == coefficient
            compressed[tagmask] = coefficient
        expanded = {}
        for tagmask, coefficient in compressed.items():
            tags = [j for j in range(5) if tagmask >> j & 1]
            for choices in itertools.product([6,7],repeat=len(tags)):
                monomial = sum(1 << (8*j+bit) for j,bit in zip(tags,choices))
                expanded[monomial] = coefficient
        assert expanded == update
        expansions_checked += 1
    tag_differences = []
    for j in range(5):
        difference = xor_poly(state[11+8*j+6],state[11+8*j+7])
        difference = xor_poly(difference,{1 << (8*j+6):one,1 << (8*j+7):one})
        assert all(term == 0 for term in difference)
        tag_differences.append(difference.get(0,0))
    terms = {term for polynomial in state[11:51] for term in polynomial}
    return {
        "circuit_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
        "max_initial_z_degree":max(term.bit_count() for term in terms),
        "quadratic_z_monomials":sum(term.bit_count() == 2 for term in terms),
        "output_update_depends_only_on_five_tags": True,
        "exact_output_polynomial_expansions_checked": expansions_checked,
        "five_tags_preserved":not any(tag_differences),
        "tag_change_independent_of_initial_z":True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--loaders",type=Path,required=True)
    parser.add_argument("--report",type=Path,required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError("Use a fresh report path")
    started = time.monotonic()
    rows = []
    for k in range(15):
        row = {"k":k,**analyze(args.loaders/f"angle_k_{k}.kmb")}
        if k:
            assert row["five_tags_preserved"]
        rows.append(row)
    report = {
        "status":"EXACT_TAG_DEPENDENCE_PROVED",
        "domain":"all 1220 addresses and arbitrary 40-bit initial word register",
        "tag_definition":"s[j] = z[8*j+6] XOR z[8*j+7]",
        "script_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "loaders":rows,
        "phase_proof":"See chemistry_affine_contract_1220.json; this script checks output polynomials only.",
        "seconds":time.monotonic()-started,
        "peak_rss_mib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
    }
    args.report.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__ == "__main__":
    main()
