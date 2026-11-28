#!/usr/bin/env python3
"""Audit all FeMoCo Givens sign-frame GF(2) constraints across every address.

Independent full-row extension of signed6_constraint_rank.py. No Toffoli, score,
or official-verifier claim is made. This script checks the 70 inter-bank
signed6 constraints and obtains an exact nullspace for each legal address.
"""
import argparse
import hashlib
import json
from pathlib import Path
from collections import Counter
import numpy as np
from signed6_constraint_rank import vectors, nullspace


def audit(npz_path):
    with np.load(npz_path) as z:
        w = z['angle_words'].astype(np.uint8)
        edges = z['tree_edges']
    if w.shape[1] != 75:
        raise ValueError(f'Expected 75 Givens angles, got {w.shape}')
    expr, slots = vectors(edges)
    nvar = len(slots)
    if nvar != 74:
        raise ValueError(f'Expected 74 frame freedoms, got {nvar}')
    high = ((w >> 6) ^ (w >> 5)) & 1
    baseline_broken = int(np.count_nonzero(high[:, 5:] != high[:, :-5]))
    rank_hist = Counter()
    null_hist = Counter()
    bases = []
    for addr in range(len(w)):
        row = w[addr]
        masks = [expr[k][int(int(row[k]) in (32, 96))] for k in range(75)]
        constraints = [masks[k] ^ masks[k - 5] for k in range(5, 75)]
        null, rank = nullspace(constraints, nvar)
        if not all(((c & v).bit_count() & 1) == 0 for c in constraints for v in null):
            raise AssertionError(f'Invalid nullspace at address {addr}')
        rank_hist[rank] += 1
        null_hist[len(null)] += 1
        if addr < 8:
            bases.append({'address': addr,
                          'rank': rank, 'basis_hex': [hex(v) for v in null]})
    return {
        'kind': 'exact_GF2_row_by_row_sign_frame_constraints',
        'source_file_sha256': hashlib.sha256(Path(npz_path).read_bytes()).hexdigest(),
        'rows': len(w), 'angles_per_row': int(w.shape[1]),
        'variables': nvar, 'inter_bank_constraints_per_row': 70,
        'existing_signed6_invariant_mismatches': baseline_broken,
        'rank_histogram': dict(sorted(rank_hist.items())),
        'nullity_histogram': dict(sorted(null_hist.items())),
        'first_8_certificates': bases,
        'official_kickmix_executed': False,
        'scored_improvement': False,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--npz', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--expect-rank', type=int, default=None)
    args = ap.parse_args()
    result = audit(args.npz)
    if args.expect_rank is not None:
        rank_counts = result['rank_histogram']
        if rank_counts != {args.expect_rank: result['rows']}:
            raise AssertionError(f'Unexpected ranks: {rank_counts}')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print('audited', result['rows'], 'addresses; rank', result['rank_histogram'],
          'nullity', result['nullity_histogram'],
          'baseline signed6 invariant mismatches', result['existing_signed6_invariant_mismatches'])


if __name__ == '__main__':
    main()