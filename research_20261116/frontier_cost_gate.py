#!/usr/bin/env python3
"""Conservative, source-pinned cost/score gate for GVQCC research.

Calculates conditional frontier for C=41..44, full official score arithmetic,
and DQI Q/T trade-offs. Does NOT infer physical feasibility from costs.
Reference figures from official competition, public maoxin123 28.09 notebook,
and user-owned, official-local 562-CCX proof receipt.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

REF = {
    "invsqrt": 2076774.233715,
    "dqi": 24439463583672.93,
    "dfthcsos": 3355599588.3155375,
}
PUBLIC = {
    "invsqrt": 75006.38,
    "dqi": 347375470571.73,
    "dfthcsos": 294762732.98,
}
LOCAL = {"invsqrt": 75170.13631745959,
         "dqi": 347373921975.41064,
         "dfthcsos": 294763061.58129317}
Q_CHEM = 427
T_CHEM = {44: 14712, 43: 14634, 42: 14555, 41: 14477}


def score(costs: dict[str, float]) -> float:
    if set(costs) != set(REF) or not all(math.isfinite(v) and v > 0 for v in costs.values()):
        raise ValueError("exactly three finite positive costs are required")
    return math.exp(sum(math.log(REF[t] / costs[t]) for t in REF) / 3)


def eligible_chemistry(receipt: dict) -> bool:
    """Only the complete official receipt, not an error2-only checkpoint, is eligible."""
    if receipt.get("status") != "PASS":
        return False
    m = receipt.get("metrics", {})
    try:
        return (receipt.get("verified_shots", 0) >= 78080
                and float(m["error_1"]) <= 0.020
                and float(m["error_2"]) <= 0.020
                and float(m["Lambda"]) > 49.0
                and float(m["E_gap"]) > 3.914898
                and math.isfinite(float(receipt["score"]))
                and float(receipt["score"]) > 0
                and int(receipt["num_qubits"]) > 0)
    except (KeyError, ValueError, TypeError, OverflowError):
        return False


def matrix(base: dict, target: float = 28.3, qchem: int = Q_CHEM,
           t_rank: dict[int, int] = T_CHEM):
    """Conditional shape table; all rows marked UNVERIFIED until verified receipts exist."""
    if target <= 0 or not math.isfinite(target):
        raise ValueError("target must be finite and positive")
    lam = base["dfthcsos"] / (t_rank[44] * qchem)
    required_product = math.exp(3 * (math.log(score(base)) - math.log(target)))
    chem_needed = base["dfthcsos"] * required_product
    out = []
    for c, t in sorted(t_rank.items(), reverse=True):
        held = {**base, "dfthcsos": lam * t * qchem}
        out.append({
            "C": c,
            "T_if_same_loaders": t,
            "Q_if_same_workspaces": qchem,
            "assumed_lambda_eff": lam,
            "score_if_feasible_and_same_lambda": score(held),
            "lambda_eff_needed_for_target": chem_needed / (t * qchem),
            "relative_lambda_drop_needed_pct": 100 * (1 - chem_needed / (t * qchem) / lam),
            "verification": "NOT_A_CIRCUIT; NOT_PROOF_OF_FEASIBILITY",
        })
    return {"baseline_score": score(base), "target": target,
            "required_product_ratio": required_product,
            "cost_needed_if_only_one_component_changes": {k:v*required_product for k,v in base.items()},
            "rows": out}


def dqi_tradeoff(q_old=890, t_old=368137.8485742187, q_values=(889,888,885,880,875,870)):
    return [{"Q": q,"max_T_at_same_DQI_cost":t_old*(q_old/q)**2,
             "extra_T_allowance":t_old*((q_old/q)**2-1),
             "assumption":"unchanged repetition factor and error rate"} for q in q_values]


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--target", type=float, default=28.3)
    ap.add_argument("--out", type=Path)
    args=ap.parse_args()
    composite={**PUBLIC,"dqi": LOCAL["dqi"]}
    data={"reference_costs":REF,"public_costs":PUBLIC,"local_receipt_costs":LOCAL,
          "public_score_recalculated":score(PUBLIC),
          "ours_public_compatible_predicted_score":score(composite),
          "compatibility_validation":"UNVERIFIED_COMPOSITE: combine bytes and run all official verifiers before submission",
          "chemistry_rank_scenarios":matrix(composite,args.target),
          "dqi_Q_T_scenarios":dqi_tradeoff(),
          "attribution":{
           "public":"maoxin123/qcc-v27-a-44-qubit-invsqrt-on-the-28-09-frontier (Apache-2.0); marculera/boristown (CC0/Apache-2.0)",
           "local":"submission_graph562.zip official local receipt (no public server score claim)",
           "competition":"https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation"}}
    encoded=json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+"\n"
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(encoded)
    else:print(encoded,end='')

if __name__=="__main__":main()
