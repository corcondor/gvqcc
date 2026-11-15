#!/usr/bin/env python3
"""Compute resource targets and the chemistry normalization floor.

This is an accounting/proof calculation, not a score submission. The lower
bound uses only the official fixed-shift definitions and the triangle
inequality; it is valid for all factorization shapes and all encoded angles.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scorecard", type=Path, required=True)
    p.add_argument("--verifiers", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    sys.path.insert(0, str(a.verifiers))
    import numpy as np
    from dfthcsos.scoreinfra.dfthc_math import symmetric_from_lower
    from dfthcsos.scoreinfra.reference import (
        ELECTRONS, ORBITALS, UPPER_ENERGY, PACKAGED_FCIDUMP,
        PACKAGED_FIXED_SHIFTS, load_fixed_shifts, load_reference,
    )

    sc = json.loads(a.scorecard.read_text())
    current = math.prod(sc["reference_costs"][t] / c for t, c in sc["candidate_costs"].items()) ** (1 / 3)
    target = 28.0
    factor = (current / target) ** 3
    shifts = load_fixed_shifts()
    sym = np.asarray(symmetric_from_lower(shifts["Hsym_lower"], ORBITALS), dtype=np.float64)
    beta = float(shifts["H1_I"]) - 0.5 * float(np.trace(sym))
    ref = load_reference(PACKAGED_FCIDUMP)
    const = UPPER_ENERGY - ref["ecore"] + ELECTRONS * beta
    gap_floor = 3.914898
    assert const < 0
    normalization_floor = math.sqrt(-const * gap_floor)
    lam = sc["chemistry_metrics"]["lambda_eff"]
    hypothetical_best_score = current * (lam / normalization_floor) ** (1 / 3)
    result = {
        "baseline_scorecard_sha256": sha(a.scorecard),
        "local_score": current, "target": target,
        "required_cost_product_factor": factor,
        "required_product_reduction_percent": 100 * (1 - factor),
        "equal_per_task_cost_factor": current / target,
        "single_task_cost_targets": {t: c * factor for t, c in sc["candidate_costs"].items()},
        "conditional_targets": {
            "dqi_Q_at_fixed_R_and_T": 889 * math.sqrt(factor),
            "chemistry_lambda_at_fixed_T_and_Q": lam * factor,
            "chemistry_total_T_at_fixed_lambda_and_Q": 14728 * factor,
            "invsqrt_Q_at_fixed_mean_T_and_rotation_price": 46 * factor,
        },
        "chemistry_universal_normalization_floor": {
            "constant_c": const, "gap_floor": gap_floor,
            "lambda_eff_strictly_greater_than": normalization_floor,
            "lambda_only_score_ceiling_with_other_costs_fixed": hypothetical_best_score,
            "lambda_only_cannot_reach_28": hypothetical_best_score < target,
            "proof": [
                "Let P be the sum of positive eigenvalues of h1_prime and N the absolute sum of its negative eigenvalues.",
                "Let d be the official generator offsets (H2_I - sum_b W_rbc in NPZ coordinates).",
                "Triangle inequality gives lambda_h2 >= ||d||_2^2 / 4, independently of the factorization and angle table.",
                "E_gap = c + 2N + ||d||_2^2 / 2 and Lambda = P+N+lambda_h2.",
                "Therefore 2Lambda-E_gap >= 2P-c >= -c > 0.",
                "lambda_eff^2 = E_gap (2Lambda-E_gap) >= -c E_gap > -c * gap_floor.",
            ],
            "reference_py_sha256": sha(a.verifiers / "dfthcsos/scoreinfra/reference.py"),
            "dfthc_math_py_sha256": sha(a.verifiers / "dfthcsos/scoreinfra/dfthc_math.py"),
            "fixed_shifts_sha256": sha(PACKAGED_FIXED_SHIFTS),
            "forum_lead": "https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation/discussion/753633",
            "attribution": "Lynn Langit's public bound; rederived and evaluated independently against the local official code.",
        },
        "submission_performed": False,
    }
    a.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
