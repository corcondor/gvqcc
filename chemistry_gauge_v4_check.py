#!/usr/bin/env python3
"""Check a sign gauge of the pinned integer Givens tree; no score claim.

Run with the scientific Python environment for vector and official-metric checks.
Run with Kickmix Python and --loader-check for the existing wrapper rejection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / 'chemistry_gauge_v4_results.json'
SOURCE = ROOT / 'dqi_inputs/chemistry_4033/submission_asterios_full.npz'


def loader_check():
    from chemistry_affine_loader_v3_build import build_affine_family, tag_profile_sufficient
    coefficients = np.zeros((75, 8), dtype=np.uint16)
    coefficients[0, 7] = 1  # Whole-vector sign flip at every address.
    result = {'constant_root_msb_patch': True,
              'tag_profile_sufficient': tag_profile_sufficient(coefficients)}
    try:
        _, _, proof = build_affine_family(coefficients)
    except Exception as error:
        result.update(accepted=False, exception_type=type(error).__name__, message=str(error))
    else:
        result.update(accepted=True, proof=proof)
    data = json.loads(OUT.read_text())
    data['existing_affine_wrapper_check'] = result
    OUT.write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps(result), flush=True)


def main():
    start = time.monotonic()
    sys.path.insert(0, str(ROOT / 'official_sources/Inzainos/verifiers'))
    from dfthcsos.scoreinfra.dfthc_math import (
        reconstruct_u_vectors, reconstruct_x, symmetric_from_lower,
        evaluate_dfthc_angle_words,
    )
    from dfthcsos.scoreinfra.reference import (
        check_fcidump, load_reference, load_fixed_shifts, UPPER_ENERGY,
    )
    data = dict(np.load(SOURCE, allow_pickle=False))
    words, edges = data['angle_words'], data['tree_edges']
    assert tuple(edges[0]) == (0, 1)
    changed = words.copy()
    changed[:, 0] &= 127
    sign_bits = (words[:, 0] >> 7) & 1
    signs = 1 - 2 * sign_bits
    original_u = reconstruct_u_vectors(words / 128, edges)
    gauge_u = reconstruct_u_vectors(changed / 128, edges)
    vector_residual = gauge_u - signs[:, None] * original_u
    outer_a = np.einsum('ip,iq->ipq', original_u, original_u)
    outer_b = np.einsum('ip,iq->ipq', gauge_u, gauge_u)
    n = original_u.shape[1]
    r, b, _ = data['W'].shape
    x_a = reconstruct_x(original_u[n:].reshape(r, b, n), data['W'])
    x_b = reconstruct_x(gauge_u[n:].reshape(r, b, n), data['W'])
    addresses = np.arange(len(words))
    constant = int(sign_bits[0])
    affine_coeffs = [int(sign_bits[1 << bit]) ^ constant for bit in range(11)]
    prediction = np.full(len(words), constant, dtype=np.int64)
    for bit, coefficient in enumerate(affine_coeffs):
        if coefficient:
            prediction ^= (addresses >> bit) & 1
    tags_before = ((words >> 6) ^ (words >> 7)) & 1
    tags_after = ((changed >> 6) ^ (changed >> 7)) & 1
    shifts = load_fixed_shifts()
    s = np.asarray(symmetric_from_lower(shifts['Hsym_lower'], n), dtype=float)
    beta = float(shifts['H1_I']) - .5 * np.trace(s)
    reference = load_reference(check_fcidump())
    kwargs = dict(brot=8, tree_edges=edges, energy_upper=UPPER_ENERGY)
    d = data['H2_I'] - data['W'].sum(axis=1)
    metrics_before = evaluate_dfthc_angle_words(words, data['W'], d, s, beta, reference, **kwargs)
    metrics_after = evaluate_dfthc_angle_words(changed, data['W'], d, s, beta, reference, **kwargs)
    def valid(metrics):
        return bool(metrics['gap_in_domain'] and metrics['error_1'] <= .020
                    and metrics['error_2'] <= .020 and metrics['E_gap'] > 3.914898
                    and metrics['Lambda'] > 49)
    metrics_delta = {k: float(metrics_after[k]) - float(metrics_before[k])
                     for k in metrics_before if not isinstance(metrics_before[k], (bool, np.bool_))}
    result = {
        'source': str(SOURCE.relative_to(ROOT)),
        'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'operation': 'angle_words[:,0] &= 127; all other arrays unchanged',
        'angle_words_changed': int(np.count_nonzero(words != changed)),
        'vectors_tested': len(words), 'dimensions': n,
        'max_abs_signed_vector_difference': float(np.max(np.abs(vector_residual))),
        'max_abs_outer_product_difference': float(np.max(np.abs(outer_a - outer_b))),
        'max_abs_weighted_x_difference': float(np.max(np.abs(x_a - x_b))),
        'baseline_metrics': metrics_before, 'gauge_metrics': metrics_after,
        'metric_differences': metrics_delta,
        'baseline_numerically_valid': valid(metrics_before),
        'gauge_numerically_valid': valid(metrics_after),
        'gauge_fix_mask_is_address_affine': bool(np.array_equal(prediction, sign_bits)),
        'unique_affine_interpolant_mismatch_count': int(np.count_nonzero(prediction != sign_bits)),
        'original_tags_repeated_across_batches': bool(np.all(tags_before.reshape(-1, 15, 5) == tags_before[:, None, :5])),
        'gauge_tags_repeated_across_batches': bool(np.all(tags_after.reshape(-1, 15, 5) == tags_after[:, None, :5])),
        'limits': ['No matching reduced-cost loader has been synthesized.',
                   'The gauge changes the preserved loader tag for batch0, slot0.',
                   'Deleting writes to q18 or reusing old loaders is not validated.',
                   'Floating-point metric differences are rounding effects, not an optimization result.',
                   'No full circuit verification or Kaggle submission.'],
        'elapsed_seconds': time.monotonic() - start,
    }
    assert result['max_abs_signed_vector_difference'] < 1e-12
    assert result['max_abs_outer_product_difference'] < 1e-12
    assert result['baseline_numerically_valid'] and result['gauge_numerically_valid']
    OUT.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--loader-check', action='store_true')
    args = parser.parse_args()
    loader_check() if args.loader_check else main()
