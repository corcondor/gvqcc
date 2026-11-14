#!/usr/bin/env python3
"""Compare DQI resource changes using R * Q**2 * T and the three-task GM.

T must come from the same official verification setup for both candidates.
A static gate histogram alone is not an official score. This tool performs
arithmetic only; it does not validate a circuit or query Kaggle.
"""
import argparse
import json
import math


def positive_float(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("must be finite and positive")
    return number


def positive_int(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def compare(old_q, old_t, old_score, new_q, new_t, r_ratio=1.0, target=28.0):
    cost_ratio = r_ratio * (new_q / old_q) ** 2 * new_t / old_t
    break_even_t = old_t * (old_q / new_q) ** 2 / r_ratio
    target_t = break_even_t * (old_score / target) ** 3
    return {
        "assumptions": {
            "other_two_task_costs": "unchanged",
            "new_R_over_old_R": r_ratio,
            "score_formula": "old_score * (old_DQI_cost / new_DQI_cost)**(1/3)",
            "validation": "arithmetic only, not an official verification or submission",
        },
        "baseline": {"qubits": old_q, "toffolis": old_t, "overall_score": old_score},
        "candidate": {"qubits": new_q, "toffolis": new_t},
        "new_DQI_cost_over_old": cost_ratio,
        "DQI_cost_reduction_percent": 100 * (1 - cost_ratio),
        "predicted_overall_score": old_score / cost_ratio ** (1 / 3),
        "break_even_toffolis": break_even_t,
        "toffoli_increase_budget": break_even_t - old_t,
        "target_overall_score": target,
        "max_toffolis_for_target": target_t,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-q", type=positive_int, default=889)
    parser.add_argument("--old-t", type=positive_float, default=382600.0)
    parser.add_argument("--old-score", type=positive_float, default=27.30683)
    parser.add_argument("--new-q", type=positive_int, required=True)
    parser.add_argument("--new-t", type=positive_float, required=True)
    parser.add_argument("--r-ratio", type=positive_float, default=1.0,
                        help="new repetition overhead divided by baseline; default assumes equal overhead")
    parser.add_argument("--target", type=positive_float, default=28.0)
    args = parser.parse_args()
    print(json.dumps(compare(args.old_q, args.old_t, args.old_score,
                             args.new_q, args.new_t, args.r_ratio, args.target),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
