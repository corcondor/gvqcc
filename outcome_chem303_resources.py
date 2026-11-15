#!/usr/bin/env python3
"""Evaluate allowed DFTHC resource knobs using the unmodified official model.

This does not synthesize or validate a candidate. Holding the loader cost or
lambda fixed is a break-even calculation, not a prediction for a new shape.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=Path(__file__).resolve().parents[1] / "official_sources/Inzainos/verifiers/dfthcsos/scoreinfra/costs_prepare.py")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_suffix(".json"))
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location("official_chem303_costs", args.model)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    reference_qt = 14722 * 427

    def row(**kwargs):
        cfg = dict(R=8, B=143, C=44, brot=8, J=5)
        cfg.update(kwargs)
        r, b, c, brot, j = (cfg[k] for k in ("R", "B", "C", "brot", "J"))
        model = mod.SpinFreeData_V1(R=r, B=b, C=c, N=76, chi=10, beta=brot)
        outer = model.outer_state_prep_qubit_cost()
        inner = model.inner_state_prep_qubit_cost()
        qubits = outer["persistent"] + inner["persistent"] + j*brot + max(outer["temporary"], inner["temporary"])
        heuristic = model.outer_state_prep() + model.inner_state_prep() + model.givens_rotations()
        return {
            **cfg,
            "number_of_angle_circuits": math.ceil(75/j),
            "inner_qroam_block_log2": model.find_qroam_size_to_minimize_global_temp_ancilla(math.ceil(math.log2(b))+11),
            "outer_toffoli": model.outer_state_prep(),
            "inner_toffoli": model.inner_state_prep(),
            "givens_toffoli": model.givens_rotations(),
            "heuristic_toffoli": heuristic,
            "inner_temporary_qubits": inner["temporary"],
            "total_qubits": qubits,
            "max_angle_workspace_at_minimal_selection_width": 128-math.ceil(math.log2(76+r*b))-j*brot,
            "total_toffoli_assuming_unchanged_4030_perpass_loader": heuristic+8060,
            "QT_assuming_unchanged_4030_perpass_loader": qubits*(heuristic+8060),
            "loader_perpass_break_even_at_v27_lambda": (reference_qt/qubits-heuristic)/2,
            "same_loader_and_lambda_cost_reduction_percent": 100*(1-qubits*(heuristic+8060)/reference_qt),
        }

    rows = [row()]
    rows += [row(brot=v) for v in (7,6,5,4,3,9)]
    rows += [row(J=v) for v in (1,3,4,6,7)]
    rows += [row(C=v) for v in (43,42,40,36,32,24,16)]
    rows += [row(B=v) for v in (142,128,127,120,64)]
    rows += [row(R=v) for v in (7,6,4)]
    result = {
        "status": "OFFICIAL_RESOURCE_MODEL_AUDIT_ONLY_NO_CANDIDATE",
        "model_file": str(args.model.resolve()),
        "model_sha256": hashlib.sha256(args.model.read_bytes()).hexdigest(),
        "baseline": {"source":"public v27 reported metrics", "R":8,"B":143,"C":44,"brot":8,"J":5,"angle_toffoli_per_pass":4030,"Q":427,"T":14722,"lambda_eff":46.909726478631555,"cost":294888332.1042627},
        "constraints": {
            "submitted_circuits": "ANGLE_k only; inner and outer state preparation are heuristic estimates",
            "angle_circuit_qubit_cap":128,
            "fixed_chi":10,
            "fixed_orbitals":76,
            "inner_qroam_customization_available":False,
            "fixed_symmetry_shifts":"H1_I and Hsym_lower are replaced with baseline values",
            "new_shapes_or_precision_require_new_numerical_and_circuit_verification":True,
            "same_words_rebatching_preserves_lambda_and_errors_if_exactly_verified":True,
        },
        "prior_experiments_not_repeated": {
            "original_B142_prefix_span_error2_necessary_lower_bound":0.027380151644545478,
            "bound_scope":"Original fixed word prefix, applies also to its smaller prefixes; not arbitrary new words",
            "C43_fixed_words_local_optimization_error2":0.021121775043258892,
            "C43_scope":"Failed local fit, not proof of global infeasibility",
        },
        "rows": rows,
        "no_new_submission_or_validated_improvement":True,
    }
    args.output.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({"output":str(args.output),"rows":len(rows),"baseline_reproduced":rows[0]["total_qubits"]==427 and rows[0]["total_toffoli_assuming_unchanged_4030_perpass_loader"]==14722}))


if __name__ == "__main__":
    main()
