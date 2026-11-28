#!/usr/bin/env python3
"""QCC official component-cost arithmetic; conditional, not verified score.

Rounding in leaderboard badges is separate from the underlying official
verifier receipts. No C43 or C42 row is a valid circuit until official PASS.
"""
from __future__ import annotations
import argparse
import json
import math

REF = {
    "invsqrt": 2076774.233715,
    "dqi": 24439463583672.93,
    "dfthcsos": 3355599588.3155375,
}
PUBLIC_28_09 = {
    "invsqrt": 75006.38,
    "dqi": 347375470571.73,
    "dfthcsos": 294762732.98,
}
OUR_VERIFIED_LOCAL = {
    "invsqrt": 75170.13631745959,
    "dqi": 347373921975.41064,
    "dfthcsos": 294763061.58129317,
}
CHEM_T = {44: 14712, 43: 14634, 42: 14555}
CHEM_Q = 427


def gm(costs):
    if set(costs) != set(REF) or not all(
        math.isfinite(x) and x > 0 for x in costs.values()
    ):
        raise ValueError("Need all three positive finite component costs")
    return math.exp(sum(math.log(REF[k] / costs[k]) for k in REF) / 3)


def c_scenarios(costs=None, target=28.3):
    base = dict(PUBLIC_28_09 if costs is None else costs)
    if not (math.isfinite(target) and target > 0):
        raise ValueError("Bad target score")
    old = gm(base)
    m = base["dfthcsos"] / (CHEM_T[44] * CHEM_Q)
    required_factor = (old / target)**3
    chemistry_target = base["dfthcsos"] * required_factor
    rows = []
    for c, t in CHEM_T.items():
        conditional = {**base, "dfthcsos": m * t * CHEM_Q}
        rows.append({
            "C": c,
            "T_same_loaders": t,
            "Q_same_workspace": CHEM_Q,
            "lambda_held_fixed": m,
            "score_if_numeric_and_native_pass": gm(conditional),
            "lambda_needed_for_target": chemistry_target / (t * CHEM_Q),
            "lambda_drop_needed_percent": 100 * (1 - chemistry_target / (t * CHEM_Q) / m),
            "status": "COST_ONLY_NOT_VERIFIED",
        })
    return {"baseline_score": old, "target": target,
            "chemistry_cost_needed_if_other_components_held": chemistry_target,
            "rows": rows}


def dqi_qubit_tradeoff(q_old, t_old, r_ratio=1.0, q_new=880):
    """Maximum Toffoli with new width, holding R*Q^2*T <= old cost."""
    if min(q_old, q_new) <= 0 or not all(
        math.isfinite(x) and x > 0 for x in (t_old, r_ratio)
    ):
        raise ValueError("Bad Q/T/R values")
    tmax = t_old * (q_old / q_new)**2 / r_ratio
    return {
        "Q_old": q_old, "Q_new": q_new, "T_old": t_old,
        "R_new_over_old": r_ratio,
        "T_new_max_to_not_worsen_DQI": tmax,
        "extra_T_budget": tmax - t_old,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--target", type=float, default=28.3)
    args = p.parse_args()
    hybrid = {**PUBLIC_28_09, "dqi": OUR_VERIFIED_LOCAL["dqi"]}
    print(json.dumps({
        "public_reported_score_model": gm(PUBLIC_28_09),
        "our_local_official_score": gm(OUR_VERIFIED_LOCAL),
        "hybrid_source_cost_score_if_reverified": gm(hybrid),
        "hybrid_verification": "NOT_YET_REBUILT_OR_REVERIFIED",
        "C43_C42_cost_only": c_scenarios(hybrid, args.target),
        "DQI_Q_T_tradeoffs_if_R_FIXED": [
            dqi_qubit_tradeoff(890, 368137.84857421875, q_new=q)
            for q in (889, 885, 880, 875, 870)
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
