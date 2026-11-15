#!/usr/bin/env python3
"""Hash-bound resource gate for exact-physics J4 chemistry candidates.

Usage (Kickmix/numpy environment):
  python score10_official_gate.py --candidate FAMILY --review REVIEW.json \
      --baseline-zip score8_local_candidate.zip --scorecard score8_scorecard.json \
      --verifiers OFFICIAL/verifiers --out gate.json

Only candidates with an independently proved unchanged physical model can
reuse score8's numeric metrics. The actual KMB hashes and counts must match
the exact review. A cheaper candidate is passed to the unmodified official
verifier with its default shots, salt and seed. A more expensive one stops
at the resource gate; no official PASS is inferred from that calculation.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import tempfile
import time
import zipfile

import numpy as np


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4 << 20), b''):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--review', type=Path, required=True)
    parser.add_argument('--baseline-zip', type=Path, required=True)
    parser.add_argument('--scorecard', type=Path, required=True)
    parser.add_argument('--verifiers', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    sys.path.insert(0, str(args.verifiers.resolve()))
    import kickmix as km
    import dfthcsos.verify as official
    from dfthcsos.scoreinfra.circuits import recover_words_from_circuits
    from dfthcsos.scoreinfra.dfthc_math import reconstruct_u_vectors

    scorecard = json.loads(args.scorecard.read_text())
    accepted_hash = scorecard['zip']['sha256']
    assert digest(args.baseline_zip) == accepted_hash, 'accepted archive mismatch'
    review = json.loads(args.review.read_text())
    assert review['status'] == 'INDEPENDENT_REORDER_KMB_AND_PHYSICS_PROOF_PASS'
    assert review['native_decoded_vectors_bitwise_identical']
    assert review['parent_before_child_tree_valid']
    assert review['arbitrary_target_bits'] == 32
    assert review['required_addresses'] == 1220

    factor = args.candidate / 'submission.npz'
    factor_hash = digest(factor)
    assert factor_hash == review['candidate_factorization_sha256']
    with zipfile.ZipFile(args.baseline_zip) as archive:
        base_bytes = archive.read('dfthcsos/submission.npz')
    assert hashlib.sha256(base_bytes).hexdigest() == review['source_factorization_sha256']
    base = dict(np.load(io.BytesIO(base_bytes), allow_pickle=False))
    candidate = dict(np.load(factor, allow_pickle=False))
    assert base.keys() == candidate.keys()
    for key in base.keys() - {'angle_words', 'tree_edges'}:
        assert base[key].dtype == candidate[key].dtype
        assert base[key].shape == candidate[key].shape
        assert base[key].tobytes() == candidate[key].tobytes(), key

    circuits, members = [], []
    assert len(review['rows']) == 19
    for k, row in enumerate(review['rows']):
        path = args.candidate / f'angle_k_{k}.kmb'
        sha = digest(path)
        assert sha == row['sha256'], (k, 'review not bound to candidate bytes')
        circuit = km.Circuit.from_file(path)
        count = int(circuit.operation_statistics().num_toffoli_like)
        assert count == row['static_and_executed_toffolis']
        assert circuit.num_qubits == row['circuit_qubits']
        # The independent proof accepts unconditional CCX and conditioned CZ
        # only; static CCX counts therefore equal the counts of every branch.
        circuits.append(circuit)
        members.append(dict(batch=k, sha256=sha, toffoli=count, qubits=circuit.num_qubits))
    loader = sum(row['toffoli'] for row in members)
    # Bind the retained numeric metrics to the real accepted loaders, whose
    # NPZ angle_words declaration is stale in 473 entries. This is a native
    # recovery check, not a default-shot full numeric verification.
    with tempfile.TemporaryDirectory(prefix='score10_gate_') as temp:
        root = Path(temp)
        baseline_circuits = []
        with zipfile.ZipFile(args.baseline_zip) as archive:
            for k in range(15):
                name = f'angle_k_{k}.kmb'
                path = root / name
                path.write_bytes(archive.read('dfthcsos/' + name))
                baseline_circuits.append(km.Circuit.from_file(path))
        old_words, old_layout, old_t = recover_words_from_circuits(
            baseline_circuits, num_vectors=1220, num_angles=75,
            shots_per_address=1, seed=2026111510)
    new_words, new_layout, new_t = recover_words_from_circuits(
        circuits, num_vectors=1220, num_angles=75,
        shots_per_address=1, seed=2026111510)
    assert old_t == 8060 and new_t == 2 * loader
    assert old_layout.brot == new_layout.brot == 8
    assert np.array_equal(new_words, candidate['angle_words'])
    assert hashlib.sha256(old_words.astype(np.uint8).tobytes()).hexdigest() == (
        '8caf7416de79102103757e3ab7ab4b6bbebfad9b1bf1ecd564c20eb948dbfcea')
    old_vectors = reconstruct_u_vectors(old_words.astype(float) / 128, base['tree_edges'])
    new_vectors = reconstruct_u_vectors(new_words.astype(float) / 128, candidate['tree_edges'])
    assert old_vectors.tobytes() == new_vectors.tobytes(), 'physical vectors changed'
    inputs = official.load_inputs(factor)
    resources = official.resource_costs(inputs, circuits, 8, 2 * loader)
    assert resources['angles_within_cap']
    chemistry = official.score_from_metrics(scorecard['chemistry_metrics'], resources)
    old_cost = scorecard['candidate_costs']['dfthcsos']
    old_score = scorecard['local_combined_score']
    computed_old = math.prod(scorecard['reference_costs'][k] / v
                             for k, v in scorecard['candidate_costs'].items()) ** (1 / 3)
    assert abs(computed_old - old_score) < 1e-12
    cheaper = chemistry < old_cost
    result = dict(
        status='RESOURCE_GATE_PASSED' if cheaper else 'RESOURCE_GATE_REJECTED',
        baseline_score=old_score, baseline_chemistry_cost=old_cost,
        baseline_archive_sha256=accepted_hash,
        review_sha256=digest(args.review), factorization_sha256=factor_hash,
        resources=resources, predicted_chemistry_cost=chemistry,
        predicted_portfolio_score=old_score * (old_cost / chemistry) ** (1 / 3),
        cost_ratio=chemistry / old_cost, improves_baseline=cheaper,
        reaches28_by_resource_model=old_score * (old_cost / chemistry) ** (1 / 3) >= 28,
        comparison_scope='Identical decoded physics and unchanged other two task costs.',
        native_recovery=dict(required_addresses=1220, shots_per_address=1,
                             seed=2026111510, forward_and_reverse=True,
                             baseline_and_candidate_recovered=True,
                             decoded_vectors_bitwise_equal=True),
        full_official_verifier_run=False, competition_submission_performed=False,
        members=members,
        official_source_sha256={name: digest(args.verifiers / 'dfthcsos' / name)
                               for name in ['verify.py', 'scoreinfra/costs_prepare.py',
                                            'scoreinfra/circuits.py']},
    )
    if cheaper:
        # No explicit seed, salt or shot override: official defaults only.
        result['full_official_verifier_run'] = True
        try:
            receipt = official.verify(args.candidate)
            result['official_result'] = receipt
            result['status'] = 'OFFICIAL_PASS' if receipt['status'] == 'PASS' else 'OFFICIAL_FAIL'
        except Exception as error:
            result['status'] = 'OFFICIAL_FAIL'
            result['official_error'] = str(error)
    result['seconds'] = time.monotonic() - started
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items()
                      if k not in ['members', 'official_result']}, indent=2))


if __name__ == '__main__':
    main()
