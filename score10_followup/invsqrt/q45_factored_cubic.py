#!/usr/bin/env python3
"""Test a single affine factor times a quadratic, plus a quadratic remainder."""
import argparse
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path


def reduce_vector(value, basis):
    while value:
        pivot = value.bit_length() - 1
        row = basis.get(pivot)
        if row is None:
            break
        value ^= row
    return value


def form_basis(values):
    basis = {}
    for value in values:
        reduced = reduce_vector(value, basis)
        if reduced:
            basis[reduced.bit_length() - 1] = reduced
    return basis


def screen(snapshot, sample_count, factor_width):
    constant = (1 << sample_count) - 1
    values = {q: value for q, value in enumerate(snapshot)
              if q != 45 and value not in (0, constant)}
    quadratics = list({constant, *values.values(),
                       *(a & b for a, b in combinations(values.values(), 2))})
    quadratic_basis = form_basis(quadratics)
    delta = reduce_vector(snapshot[45], quadratic_basis)
    hits = []
    checked = 0
    if not delta:
        return {"quadratic_rank": len(quadratic_basis),
                "quadratic_match_on_samples": True, "factors_checked": checked,
                "factored_cubic_matches_on_samples": hits}
    for width in range(1, factor_width + 1):
        for factor_wires in combinations(values, width):
            first_factor = 0
            for q in factor_wires:
                first_factor ^= values[q]
            basis = dict(quadratic_basis)
            for quadratic in quadratics:
                reduced = reduce_vector(first_factor & quadratic, basis)
                if reduced:
                    basis[reduced.bit_length() - 1] = reduced
            checked += 1
            if not reduce_vector(delta, basis):
                hits.append(factor_wires)
    return {"quadratic_rank": len(quadratic_basis),
            "quadratic_match_on_samples": False, "factors_checked": checked,
            "factored_cubic_matches_on_samples": hits}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--kmx", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--factor-width", type=int, choices=(1, 2), default=1)
    args = parser.parse_args()
    data = json.loads(args.snapshot.read_text())
    raw = args.kmx.read_bytes()
    assert data["source_sha256"] in {
        sha256(raw).hexdigest(), sha256(raw.removesuffix(b"\n")).hexdigest(),
    }
    assert len(set(data["samples"])) == data["shots"]
    results = {}
    for line, values in data["states_hex"].items():
        snapshot = [int(value, 16) for value in values]
        results[line] = screen(snapshot, data["shots"], args.factor_width)
        print(line, results[line], flush=True)
    args.out.write_text(json.dumps({"source_sha256": data["source_sha256"],
                                    "sample_inputs_sha256": data["sample_inputs_sha256"],
                                    "shots": data["shots"], "factor_width": args.factor_width,
                                    "results": results}, indent=2) + "\n")


if __name__ == "__main__":
    main()
