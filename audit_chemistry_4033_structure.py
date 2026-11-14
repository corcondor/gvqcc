#!/usr/bin/env python3
"""Read-only audit of the pinned 4033 chemistry word codes and loader counts.

This does not generate or optimize a loader and does not verify its semantics.
It reads the original arrays and KMB files; only the requested JSON is written.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import resource

import numpy as np

from kmb_profile import profile

FACTOR_SHA = "3f864a7aeaa4d78984c8822761782b63be2d553b229f487e79640a73be147c44"
SOURCE = "https://www.kaggle.com/code/maoxin123/qcc-v27-4033-toffoli-coded-word-chemistry"


def audit(factorization: Path, loaders: Path) -> dict:
    digest = hashlib.sha256(factorization.read_bytes()).hexdigest()
    if digest != FACTOR_SHA:
        raise ValueError("Expected the pinned original 4033 factorization")
    with np.load(factorization, allow_pickle=False) as data:
        words = data["angle_words"].copy()
        shape = tuple(data["W"].shape)
    if words.shape != (1220, 75) or shape != (8, 143, 44):
        raise ValueError("Unexpected original factorization dimensions")

    # Mobius transform in the four low address bits, independently for each
    # complete 16-address block. The last four rows have no full truth table.
    ncomplete = len(words) // 16
    anf = words[:ncomplete * 16].reshape(ncomplete, 16, 75).copy()
    for bit in range(4):
        for mask in range(16):
            if mask & (1 << bit):
                anf[:, mask, :] ^= anf[:, mask ^ (1 << bit), :]
    degrees = np.array([mask.bit_count() for mask in range(16)])
    batches = []
    for k in range(15):
        a = anf[:, :, 5*k:5*k+5]
        bit0 = a & 1
        xor5 = np.bitwise_xor.reduce(a, axis=2)
        counts = {
            "individual_word_bit0_degree_gt1": int(np.count_nonzero(bit0[:, degrees > 1, :])),
            "xor5_bit1_degree_gt1": int(np.count_nonzero((xor5[:, degrees > 1] >> 1) & 1)),
            "xor5_bit2_degree_gt2": int(np.count_nonzero((xor5[:, degrees > 2] >> 2) & 1)),
        }
        batches.append({
            "batch": k,
            "violating_anf_coefficients": counts,
            "distinct_bit0_affine_coefficient_sets_per_word": [
                int(len(np.unique(bit0[:, degrees <= 1, j], axis=0)))
                for j in range(5)
            ],
        })
    if any(any(b["violating_anf_coefficients"].values()) for b in batches[3:]):
        raise ValueError("Original words do not satisfy the published RM constraints")

    # A full block is eligible for a label permutation within one rho only
    # when it neither touches the first 76 rows nor crosses a rho boundary.
    safe_blocks = []
    for block in range(ncomplete):
        first, last = 16 * block, 16 * block + 15
        if first < 76:
            continue
        rho = (first - 76) // 143
        if (last - 76) // 143 == rho:
            safe_blocks.append({"address_first": first, "address_last": last, "rho": rho})

    loader_reports = []
    for k in range(15):
        p = profile(loaders / f"angle_k_{k}.kmb", max_register_summaries=0)
        loader_reports.append({
            "k": k, "sha256": p["raw_kmb_sha256"],
            "num_qubits": p["header"]["num_qubits"],
            "num_ops": p["header"]["num_ops"],
            "CCX": p["raw_gate_families"]["CCX"],
            "CCZ": p["raw_gate_families"]["CCZ"],
            "CSWAP": p["raw_gate_families"]["CSWAP"],
        })
    return {
        "schema": "gvqcc-4033-structure-audit-v1",
        "status": "READ_ONLY_STRUCTURE_AUDIT_COMPLETE",
        "source_notebook": SOURCE,
        "factorization_sha256": digest,
        "angle_words_shape": list(words.shape),
        "complete_16_address_blocks_audited": ncomplete,
        "partial_tail_rows_excluded_from_RM_claim": [1216, 1217, 1218, 1219],
        "batches": batches,
        "within_rho_complete_blocks": safe_blocks,
        "within_rho_complete_block_count": len(safe_blocks),
        "rows_in_these_blocks": 16 * len(safe_blocks),
        "rows_fixed_if_only_these_blocks_are_permuted": len(words) - 16 * len(safe_blocks),
        "loaders": loader_reports,
        "static_CCX_total": sum(p["CCX"]["total"] for p in loader_reports),
        "generator_found": False,
        "generator_reproduction_performed": False,
        "row_permutation_experiments_performed": False,
        "input_files_modified": False,
        "limitations": [
            "Static gate counts are not an official measured resource score.",
            "No circuit semantic or phase verification was performed by this audit.",
            "Known RM degrees survive a common invertible affine low-four-bit substitution within each block; this does not prove unchanged loader cost.",
            "The pinned release notebook and dataset contain completed circuits, not the generator.",
        ],
        "peak_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--factorization", required=True, type=Path)
    parser.add_argument("--loaders", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = audit(args.factorization, args.loaders)
    with args.output.open("x") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps({k: report[k] for k in [
        "status", "static_CCX_total", "within_rho_complete_block_count",
        "peak_rss_mib", "generator_reproduction_performed",
    ]}))


if __name__ == "__main__":
    main()
