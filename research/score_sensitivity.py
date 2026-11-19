#!/usr/bin/env python3
"""Recompute GVQCC composite score and cost/width tradeoffs.

Historical numeric baseline is the archived Round48 local official-default
cost triple. This tool does NOT run a circuit/verifier, does NOT certify
correctness, and never claims Kaggle online submission.
"""
from __future__ import annotations

import argparse
import json
from math import isclose

REFERENCE = {
    "invsqrt": 2076774.233715282,
    "dqi": 24439463583672.93,
    "chemistry": 3355599588.3155375,
}
ROUND48 = {
    "invsqrt": 73870.22470522957,
    "dqi": 344465952282.9805,
    "chemistry": 294637907.186498,
}
ROUND48_Q = 890
ROUND48_MEAN_TOFFOLI = 365056.0579199219
ROUND48_REPETITION = 1.1912604648115832


def score(invsqrt: float, dqi: float, chemistry: float) -> float:
    """Official composite arithmetic, not an empirical verification."""
    if min(invsqrt, dqi, chemistry) <= 0:
        raise ValueError("Costs must be positive")
    return (
        REFERENCE["invsqrt"] / invsqrt
        * REFERENCE["dqi"] / dqi
        * REFERENCE["chemistry"] / chemistry
    ) ** (1.0 / 3.0)


def dqi_cost(qubits: int, mean_toffoli: float, repetition: float) -> float:
    if qubits <= 0 or mean_toffoli <= 0 or repetition < 1:
        raise ValueError("Require Q>0, T>0 and R>=1")
    return repetition * qubits**2 * mean_toffoli


def compare(
    invsqrt: float,
    dqi: float,
    chemistry: float,
    q: int,
    mean_t: float,
    r: float,
    target: float,
    widths: list[int],
) -> dict:
    if target <= 0:
        raise ValueError("Target score must be positive")
    s = score(invsqrt, dqi, chemistry)
    cost_factor = (s / target) ** 3
    threshold_dqi = dqi * cost_factor
    nominal = dqi_cost(q, mean_t, r)
    return {
        "status": "HYPOTHETICAL_COST_SENSITIVITY_ONLY_NOT_VALIDATED_CIRCUIT",
        "baseline_composite_local_numeric": s,
        "baseline_costs": {"invsqrt": invsqrt, "dqi": dqi, "chemistry": chemistry},
        "target_composite": target,
        "required_cost_product_reduction_fraction": 1 - cost_factor,
        "dqi_cost_at_target_if_other_costs_fixed": threshold_dqi,
        "dqi_mean_t_at_target_if_q_and_r_fixed": threshold_dqi / (r * q**2),
        "dqi_mean_t_reduction_at_target": mean_t - threshold_dqi / (r * q**2),
        "input_dqi_cost_vs_q2_t_r_check": {
            "input": dqi,
            "recomputed": nominal,
            "matches_with_tolerance": isclose(nominal, dqi, rel_tol=1e-10, abs_tol=1e-3),
        },
        "qubit_only_counterfactuals": [
            {
                "qubits": new_q,
                "hypothetical_dqi_cost": dqi_cost(new_q, mean_t, r),
                "hypothetical_score": score(invsqrt, dqi_cost(new_q, mean_t, r), chemistry),
                "strict_contract_proven": False,
            }
            for new_q in widths
        ],
        "warning": (
            "Q reduction is not free: preserving mean T, repetition, "
            "correctness, ancilla/phase, and chemistry contracts is unproven."
        ),
    }


def self_test() -> None:
    baseline = score(**ROUND48)
    assert isclose(baseline, 28.32145634974874, abs_tol=2e-12)
    c = dqi_cost(ROUND48_Q, ROUND48_MEAN_TOFFOLI, ROUND48_REPETITION)
    assert isclose(c, ROUND48["dqi"], rel_tol=1e-12)
    z = compare(
        ROUND48["invsqrt"], ROUND48["dqi"], ROUND48["chemistry"],
        ROUND48_Q, ROUND48_MEAN_TOFFOLI, ROUND48_REPETITION,
        28.5, [889, 881]
    )
    assert isclose(z["required_cost_product_reduction_fraction"], 0.01867657531066, abs_tol=1e-11)
    assert isclose(z["qubit_only_counterfactuals"][-1]["hypothetical_score"], 28.5140110846526, abs_tol=1e-10)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--invsqrt", type=float, default=ROUND48["invsqrt"])
    parser.add_argument("--dqi", type=float, default=ROUND48["dqi"])
    parser.add_argument("--chemistry", type=float, default=ROUND48["chemistry"])
    parser.add_argument("--q", type=int, default=ROUND48_Q)
    parser.add_argument("--mean-t", type=float, default=ROUND48_MEAN_TOFFOLI)
    parser.add_argument("--r", type=float, default=ROUND48_REPETITION)
    parser.add_argument("--target", type=float, default=28.5)
    parser.add_argument("--what-if-widths", type=int, nargs="*", default=[889, 885, 881])
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    out = compare(
        args.invsqrt, args.dqi, args.chemistry,
        args.q, args.mean_t, args.r, args.target, args.what_if_widths
    )
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
