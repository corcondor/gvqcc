"""Evaluate a normalization-only lower bound from the official FeMoCo reference."""
from __future__ import annotations

import argparse
import json
from math import sqrt
from pathlib import Path

import numpy as np
from dfthcsos.verify import E_GAP_FLOOR, ERROR_2_THRESHOLD, load_inputs


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("factorization", type=Path)
    p.add_argument("chemistry_receipt", type=Path)
    p.add_argument("scorecard", type=Path)
    p.add_argument("out", type=Path)
    args = p.parse_args()

    inputs = load_inputs(args.factorization)
    data = inputs.ref
    n = inputs.num_orbitals
    trace_shift = float(np.trace(inputs.S))
    trace_target = float(np.einsum("iijj->", data["tei"])) + n*trace_shift
    trace_h0 = float(np.trace(data["h1_thc"])) - (data["electrons"]/2)*trace_shift + inputs.beta_1*n
    gap_offset = inputs.energy_upper - data["ecore"] + data["electrons"]*inputs.beta_1
    trace_lower = trace_target - ERROR_2_THRESHOLD*n
    double_trace_partner = 2*trace_lower + 2*trace_h0 - gap_offset
    # Input-identity residual d obeys |d_rc| <= sum_b |w_rbc| + |H2_I_rc|.
    # With g=gap_offset+||h'||_*-tr(h')+||d||^2/2, this gives
    # 2*Lambda-g >= -gap_offset + ||h'||_*+tr(h') >= -gap_offset.
    identity_partner = -gap_offset
    partner_lower = max(double_trace_partner, identity_partner)
    assert partner_lower > 0
    bound = sqrt(E_GAP_FLOOR*partner_lower)

    baseline = json.loads(args.scorecard.read_text())
    receipt = json.loads(args.chemistry_receipt.read_text())
    prior_cost = receipt["score"]
    tq = receipt["toffoli_count"]*receipt["num_qubits"]
    capped_portfolio = baseline["local_score"]*(prior_cost/(bound*tq))**(1/3)
    target_cost = prior_cost*(baseline["local_score"]/28)**3

    w = inputs.w
    source = np.concatenate((w, (inputs.W + w.sum(axis=1))[:,None,:]),axis=1)
    gram = source @ np.swapaxes(source,1,2)
    data_h2 = float(np.sum(np.square(np.abs(source).sum(axis=1)))/4)
    gram_lower = float(np.abs(gram).sum()/4)
    gauge_lcu = receipt["metrics"]["Lambda"] - data_h2 + gram_lower
    gap = receipt["metrics"]["E_gap"]
    gauge_effective = sqrt(gap*(2*gauge_lcu-gap))
    report = {
        "normalization_only": {
            "scope": "All factorizations under the official fixed shift and SOS gap floor, with the two-body error cap used only by the weaker double-trace bound",
            "orbitals": n,
            "gap_floor": E_GAP_FLOOR,
            "two_body_error_cap": ERROR_2_THRESHOLD,
            "shifted_two_body_reference_double_trace": trace_target,
            "submitted_double_trace_floor": trace_lower,
            "h0_trace": trace_h0,
            "gap_offset": gap_offset,
            "double_trace_partner_floor": double_trace_partner,
            "identity_partner_floor": identity_partner,
            "partner_2Lambda_minus_gap_floor": partner_lower,
            "lambda_eff_floor": bound,
            "local_score_ceiling_at_unchanged_T_Q_and_other_tasks": capped_portfolio,
            "max_TQ_for_score_28_holding_other_tasks": target_cost/bound,
            "actual_TQ": tq,
            "max_T_with_same_Q":target_cost/(bound*receipt["num_qubits"]),
            "max_ANGLE_T_per_pass_with_same_Q_and_other_chemistry_T":
                (target_cost/(bound*receipt["num_qubits"])
                 - (receipt["toffoli_count"]-receipt["resources"]["angles_toffoli"]))/2,
        },
        "exact_group_gram": {
            "baseline_lambda_h2": data_h2,
            "lambda_h2_floor": gram_lower,
            "lambda_eff_floor": gauge_effective,
            "local_score_ceiling_at_unchanged_T_Q_and_other_tasks": baseline["local_score"]*(prior_cost/(gauge_effective*tq))**(1/3),
            "input_stacked_block_smallest_singular_values": [float(s[-1]) for s in (np.linalg.svd(x,compute_uv=False) for x in source)]
        }
    }
    args.out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report),flush=True)


if __name__ == "__main__":
    main()
