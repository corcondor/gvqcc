#!/usr/bin/env python3
"""Read-only screen of whole-word repetition suggested by Gu et al. (2026).

Uses the pinned 4033 angle words and the actual XOR-difference ANGLE contract.
Counts only data redundancy; does not synthesize circuits or estimate score.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import resource
import time

import numpy as np


PIN = "3f864a7aeaa4d78984c8822761782b63be2d553b229f487e79640a73be147c44"


def audit(path):
    started = time.monotonic()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != PIN:
        raise ValueError("Expected original pinned 4033 factorization")
    with np.load(path, allow_pickle=False) as data:
        words = data["angle_words"].astype(np.uint64)
    if words.shape != (1220, 75) or int(words.max()) > 255:
        raise ValueError("Unexpected angle-word dimensions or precision")
    previous = np.zeros((1220, 5), dtype=np.uint64)
    reports = []
    shifts = np.arange(5, dtype=np.uint64) * np.uint64(8)
    for k in range(15):
        current = words[:, 5 * k:5 * k + 5]
        differences = current ^ previous
        packed = np.bitwise_or.reduce(differences << shifts, axis=1)
        _, counts = np.unique(packed, return_counts=True)
        blocks = {}
        for exp in range(1, 11):
            width = 1 << exp
            equal = []
            for first in range(0, len(packed) - width + 1, width):
                middle = first + width // 2
                if np.array_equal(packed[first:middle], packed[middle:first + width]):
                    equal.append(first)
            blocks[str(width)] = equal
        reports.append({
            "angle_k": k, "valid_rows": len(packed), "distinct_40bit_difference_words": len(counts),
            "duplicate_row_redundancy": int(len(packed) - len(counts)),
            "maximum_word_multiplicity": int(counts.max()),
            "zero_difference_rows": int(np.count_nonzero(packed == 0)),
            "equal_adjacent_row_pairs": int(np.count_nonzero(packed[0:1220:2] == packed[1:1220:2])),
            "equal_halves_of_complete_aligned_blocks": blocks,
        })
        previous = current
    return {
        "schema": "anthropic-whole-word-repetition-screen-v1",
        "factorization_sha256": digest,
        "target": "f_k(a) = g_(k-1)(a) XOR g_k(a), first previous batch zero",
        "source_idea": "https://arxiv.org/html/2610.22367v1",
        "rows_are_unchanged": True, "circuit_generated": False,
        "candidate_modified": False, "score_improvement_claim": False,
        "batches": reports,
        "total_duplicate_row_redundancy": sum(x["duplicate_row_redundancy"] for x in reports),
        "total_equal_adjacent_row_pairs": sum(x["equal_adjacent_row_pairs"] for x in reports),
        "total_equal_half_blocks": sum(len(v) for x in reports
                                       for v in x["equal_halves_of_complete_aligned_blocks"].values()),
        "limitations": [
            "Whole 40-bit difference words only; partial-word, affine, RM and shared-product structure are not screened out.",
            "A pure row permutation cannot create additional duplicate complete words, but joint retraining can alter the table.",
            "Incomplete blocks extending beyond valid address 1219 are excluded; behavior outside the promised domain is not assumed.",
            "Data redundancy is not a Toffoli-count certificate or a quantum-circuit correctness result.",
        ],
        "seconds": time.monotonic() - started,
        "peak_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("factorization", type=Path)
    p.add_argument("--report", required=True, type=Path)
    args = p.parse_args()
    result = audit(args.factorization)
    args.report.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "batches"}, indent=2))


if __name__ == "__main__":
    main()
