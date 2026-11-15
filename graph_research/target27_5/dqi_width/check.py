"""Construct paired inverse and third-pivot fixtures and verify their original phase contract."""
import argparse
import json
from pathlib import Path

import numpy as np
import kickmix as km

import score5_dqi_width_check as checks
import outcome_dqi_chart_inverse_norm as reference
import inverse
import borrow_inverse


def validate_scalar():
    field = km.GF2Field(12)
    mul = field.mul

    def maps(left, right, factor, reciprocal):
        left, right = right, left
        left ^= mul(factor, right)
        right ^= mul(reciprocal, left)
        left ^= mul(factor, right)
        return left, right

    def squaring(x):
        return mul(x, x)

    def root(x):
        return field.pow(x, 2048)

    for factor in range(1, 4096):
        reciprocal = field.invert(factor)
        for left, right in [(1 << i, 0) for i in range(12)] + [(0, 1 << i) for i in range(12)]:
            output_left, output_right = maps(left, root(right), reciprocal, factor)
            output_right = squaring(output_right)
            output_left, output_right = maps(root(output_left), output_right, factor, reciprocal)
            output_left = squaring(output_left)
            assert (output_left, output_right) == (mul(left, factor), mul(right, factor))
    assert maps(0, 0, 0, 0) == (0, 0)
    return 4095 * 24 + 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    scalar_cases = validate_scalar()
    rng = np.random.default_rng(20261115)
    values = np.array([0, 1, 4095, 4096, (1 << 24) - 1,
                       *rng.integers(0, 1 << 24, 4091)], dtype=np.uint32)
    flags = np.arange(len(values)) & 1
    masks = rng.integers(0, 1 << 24, len(values), dtype=np.uint32)
    rows = {}
    for label, module in [("original", reference), ("frobenius", inverse), ("borrow_norm", borrow_inverse)]:
        circuit, row = checks.single_pair(module, args.out, label)
        row["native_tests"] = [checks.simulate_pair(circuit, values, flags, masks, seed)
                              for seed in (20261115, 15202611)]
        row["third_pivot_chart"] = checks.chart_pair(module, args.out, label)
        rows[label] = row
    assert rows["original"]["Q"] == 73
    assert rows["frobenius"]["Q"] == 67
    assert rows["frobenius"]["T"] - rows["original"]["T"] == 336
    assert rows["original"]["third_pivot_chart"]["Q"] == 889
    assert rows["frobenius"]["third_pivot_chart"]["Q"] == 883
    assert (rows["frobenius"]["third_pivot_chart"]["T"]
            - rows["original"]["third_pivot_chart"]["T"]) == 1008
    assert rows["borrow_norm"]["Q"] == 61
    assert rows["borrow_norm"]["T"] - rows["original"]["T"] == 60
    assert rows["borrow_norm"]["third_pivot_chart"]["Q"] == 877
    assert (rows["borrow_norm"]["third_pivot_chart"]["T"]
            - rows["original"]["third_pivot_chart"]["T"]) == 180
    result = dict(scalar_cases=scalar_cases, rows=rows)
    (args.out / "component.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
