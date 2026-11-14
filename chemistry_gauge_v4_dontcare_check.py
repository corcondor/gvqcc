#!/usr/bin/env python3
"""Find exact zero-parent Givens don't-cares; validate one canonical table.

Only exact integer quadrants establish zeros. No floating epsilon is used to
decide that an amplitude/angle is inactive. No reduced-cost circuit is claimed.
"""
from pathlib import Path
import hashlib
import json
import sys
import time
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'official_sources/Inzainos/verifiers'))
from dfthcsos.scoreinfra.dfthc_math import reconstruct_u_vectors, symmetric_from_lower, evaluate_dfthc_angle_words
from dfthcsos.scoreinfra.reference import check_fcidump, load_reference, load_fixed_shifts, UPPER_ENERGY


def inactive_angles(words, edges):
    """Exact structural zeros for a legal parent-before-new-child tree."""
    live = np.zeros((len(words), words.shape[1] + 1), dtype=bool)
    live[:, 0] = True
    inactive = np.zeros_like(words, dtype=bool)
    seen = {0}
    for j, (parent, child) in enumerate(edges):
        assert parent in seen and child not in seen
        seen.add(int(child))
        active = live[:, parent].copy()
        inactive[:, j] = ~active
        # theta = pi*word/128. These are exact sin/cos zeros.
        live[:, parent] = active & ((words[:, j] % 128) != 64)
        live[:, child] = active & ((words[:, j] % 128) != 0)
    return inactive


def main():
    start = time.monotonic()
    source = ROOT / 'dqi_inputs/chemistry_4033/submission_asterios_full.npz'
    baseline = dict(np.load(source, allow_pickle=False))
    w, edges = baseline['angle_words'], baseline['tree_edges']
    inactive = inactive_angles(w, edges)
    changed = w.copy()
    changed[inactive] &= 192  # preserve bits6/7; choose zero for low six bits.
    assert np.array_equal(inactive, inactive_angles(changed, edges))
    u = reconstruct_u_vectors(w / 128, edges)
    v = reconstruct_u_vectors(changed / 128, edges)
    outer_difference = np.einsum('ip,iq->ipq', u, u) - np.einsum('ip,iq->ipq', v, v)
    before = json.loads((OUT / 'chemistry_gauge_v4_results.json').read_text())
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    assert before['source_sha256'] == source_hash
    shifts = load_fixed_shifts()
    s = np.asarray(symmetric_from_lower(shifts['Hsym_lower'], 76), dtype=float)
    beta = float(shifts['H1_I']) - .5 * np.trace(s)
    ref = load_reference(check_fcidump())
    metrics = evaluate_dfthc_angle_words(changed, baseline['W'], baseline['H2_I'] - baseline['W'].sum(1),
        s, beta, ref, brot=8, tree_edges=edges, energy_upper=UPPER_ENERGY)
    valid = bool(metrics['gap_in_domain'] and metrics['error_1'] <= .020 and metrics['error_2'] <= .020
        and metrics['E_gap'] > 3.914898 and metrics['Lambda'] > 49)
    tags = lambda a: ((a >> 6) ^ (a >> 7)) & 1
    result = {
        'source': str(source.relative_to(ROOT)), 'source_sha256': source_hash,
        'zero_detection': 'integer word%128==0 => sin=0; word%128==64 => cos=0; exact tree propagation',
        'inactive_angle_entries': int(inactive.sum()),
        'inactive_entries_by_column': inactive.sum(0).tolist(),
        'inactive_entries_by_batch': inactive.reshape(1220, 15, 5).sum((0, 2)).tolist(),
        'independent_low_bit_dont_care_positions': int(inactive.sum() * 6),
        'changed_words': int(np.count_nonzero(w != changed)),
        'changed_low_bits': sum(int(np.sum(inactive & (((w >> bit) & 1) != 0))) for bit in range(6)),
        'unchanged_high_bits': bool(np.array_equal(w & 192, changed & 192)),
        'unchanged_loader_tags': bool(np.array_equal(tags(w), tags(changed))),
        'unchanged_exact_inactive_set': True,
        'max_abs_vector_difference': float(np.max(np.abs(u - v))),
        'max_abs_outer_product_difference': float(np.max(np.abs(outer_difference))),
        'baseline_official_metrics': before['baseline_metrics'],
        'canonical_official_metrics': metrics,
        'numerically_valid': valid,
        'scope': 'Only a physics-equivalent target table; no matching loader synthesized, no T/Q gain, no full circuit check or submission.',
        'elapsed_seconds': time.monotonic() - start,
    }
    assert result['max_abs_vector_difference'] < 1e-12
    assert result['max_abs_outer_product_difference'] < 1e-12
    assert valid
    (OUT / 'chemistry_gauge_v4_dontcare_results.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
