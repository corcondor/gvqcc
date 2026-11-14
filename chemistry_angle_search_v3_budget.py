"""Compute the strict chemistry loader budget for an independently valid table.

This is a resource comparison, not a chemistry or circuit correctness test.
The candidate lambda must be recomputed from the quantized angle words.
"""
import argparse
import json
import math
from pathlib import Path


def loader_budget(base_lambda, base_t, base_q, old_loader, candidate_lambda,
                  candidate_q, nonloader_t=None):
    if min(base_lambda, base_t, base_q, candidate_lambda, candidate_q) <= 0:
        raise ValueError("Costs and lambda values must be positive")
    fixed_t = base_t - 2 * old_loader if nonloader_t is None else nonloader_t
    if fixed_t < 0:
        raise ValueError("The non-loader Toffoli count cannot be negative")
    base_cost = base_lambda * base_t * base_q
    strict_bound = (base_cost / (candidate_lambda * candidate_q) - fixed_t) / 2
    max_integer = math.ceil(strict_bound) - 1

    def cost(loader):
        return candidate_lambda * (fixed_t + 2 * loader) * candidate_q

    # Check the strict inequality directly at the computed integer boundary.
    while max_integer >= 0 and cost(max_integer) >= base_cost:
        max_integer -= 1
    while cost(max_integer + 1) < base_cost:
        max_integer += 1
    return {
        "candidate_lambda_if_numerically_valid": candidate_lambda,
        "candidate_qubits": candidate_q,
        "nonloader_t": fixed_t,
        "per_pass_loader_strict_upper_bound": strict_bound,
        "max_improving_integer_loader": max_integer if max_integer >= 0 else None,
        "cost_ratio_with_original_loader": cost(old_loader) / base_cost,
        "boundary_cost_ratio": cost(max_integer) / base_cost if max_integer >= 0 else None,
        "next_integer_cost_ratio": cost(max_integer + 1) / base_cost,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lambda-values", type=float, nargs="+", default=[44.17, 45.3, 46.4])
    parser.add_argument("--candidate-qubits", type=int, default=427)
    parser.add_argument("--nonloader-t", type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    summary_path = Path(__file__).with_name("chemistry_polish_v2_summary.json")
    base = json.loads(summary_path.read_text())["baseline"]
    base_lambda = base["official_numerical_metrics"]["lambda_eff"]
    rows = [loader_budget(base_lambda, base["toffoli_count"], base["qubits"],
                          4033, value, args.candidate_qubits, args.nonloader_t)
            for value in args.lambda_values]
    result = {
        "scope": "Conditional break-even calculation; no candidate validity or score claim",
        "baseline_npz_sha256": base["sha256"],
        "baseline_lambda": base_lambda,
        "baseline_t": base["toffoli_count"],
        "baseline_qubits": base["qubits"],
        "original_per_pass_loader_t": 4033,
        "formula": "lambda_new * Q_new * (T_nonloader_new + 2*L_new) < lambda_old * Q_old * T_old",
        "rows": rows,
    }
    text = json.dumps(result, indent=2) + "\n"
    print(text, end="")
    if args.output:
        args.output.write_text(text)


if __name__ == "__main__":
    main()
