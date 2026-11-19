#!/usr/bin/env python3
"""Reproduce DF-THC-SOS PHYSICS acceptance gates; no Kickmix circuit simulation.

This guard deliberately applies the fixed S/beta shifts from the official
verifier, ignoring submitted Hsym_lower/H1_I. Its only claim is that the
chemical score's physical constraints pass or fail. It does NOT check ANGLE
circuit correctness or DQI/invsqrt and is not sufficient for submission.

Usage:
  python research/chemistry_fixed_shift_score_gate.py factorization.npz \
    --verifier-root /path/to/official_verifiers --output receipt.json
Dependencies: numpy, scipy.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("npz", type=Path)
    ap.add_argument("--verifier-root", type=Path, required=True)
    ap.add_argument("--output", type=Path)
    ns = ap.parse_args()
    sys.path.insert(0, str(ns.verifier_root.resolve()))

    from dfthcsos.scoreinfra.reference import (
        load_reference, load_fixed_shifts, PACKAGED_FCIDUMP, UPPER_ENERGY
    )
    from dfthcsos.scoreinfra.dfthc_math import (
        evaluate_dfthc_angle_words, symmetric_from_lower
    )

    with np.load(ns.npz, allow_pickle=False) as z:
        data = {k: z[k].copy() for k in z.files}

    # Mandatory: the original verifier overwrites these submitted fields.
    data.update(load_fixed_shifts())
    ref = load_reference(PACKAGED_FCIDUMP)
    S = symmetric_from_lower(data["Hsym_lower"], ref["orbitals"])
    beta = float(data["H1_I"]) - 0.5 * float(np.trace(S))
    W_native = data["H2_I"] - data["W"].sum(axis=1)
    metrics = evaluate_dfthc_angle_words(
        data["angle_words"], data["W"], W_native, S, beta, ref,
        brot=int(data["brot"]), tree_edges=data["tree_edges"],
        energy_upper=UPPER_ENERGY,
    )

    reasons = []
    if not metrics["error_1"] <= 0.020:
        reasons.append("error_1 > 0.020")
    if not metrics["error_2"] <= 0.020:
        reasons.append("error_2 > 0.020")
    if not metrics["gap_in_domain"] or not np.isfinite(metrics["lambda_eff"]):
        reasons.append("gap outside domain")
    if not metrics["Lambda"] > 49.0:
        reasons.append("Lambda <= strict floor 49.0")
    if not metrics["E_gap"] > 3.914898:
        reasons.append("E_gap <= strict floor 3.914898")
    result = {
        "scope": "OFFICIAL_SCOREINFRA_PHYSICS_ONLY_NOT_FULL_KICKMIX_VERIFICATION",
        "source_sha256": digest(ns.npz),
        "fixed_shifts_applied": ["H1_I", "Hsym_lower"],
        "passes_physical_gates": not reasons,
        "rejection_reasons": reasons,
        "metrics": metrics,
        "dqi_verified": False,
        "invsqrt_verified": False,
        "angle_circuits_verified": False,
    }
    content = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if ns.output:
        ns.output.parent.mkdir(parents=True, exist_ok=True)
        ns.output.write_text(content, encoding="utf-8")
    print(content, end="")


if __name__ == "__main__":
    main()
