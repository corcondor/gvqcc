#!/usr/bin/env python3
"""Verify an actual NPZ and its complete loader family with the official code.

The candidate is copied byte-for-byte. Changed integer words are permitted;
the official simulator must recover them from the supplied circuits. The
comparison baseline is bound to a previously recorded full official PASS.
No Kaggle submission is performed.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import time

import numpy as np

from score2_clifford_affine_reduce import checked_angle_words


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--loaders', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--baseline-receipt', type=Path, required=True)
    parser.add_argument('--verifier', type=Path, required=True)
    parser.add_argument('--engine-dir', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    args.out.mkdir(parents=True)
    started = time.monotonic()
    report = {'created_utc': datetime.now(timezone.utc).isoformat(),
              'status': 'PREPARING', 'script_sha256': sha(__file__),
              'verifier': str(args.verifier), 'verifier_sha256': sha(args.verifier),
              'candidate_source': str(args.candidate), 'candidate_sha256': sha(args.candidate),
              'baseline_source': str(args.baseline), 'baseline_sha256': sha(args.baseline),
              'baseline_receipt': str(args.baseline_receipt),
              'baseline_receipt_sha256': sha(args.baseline_receipt),
              'kaggle_submission_performed': False, 'observed_public_score': None}
    try:
        previous = json.loads(args.baseline_receipt.read_text())
        baseline_result = previous['official_result']
        assert baseline_result['status'] == 'PASS'
        assert baseline_result['verified_shots'] == 78080
        assert previous['factorization']['sha256'] == report['baseline_sha256']
        assert previous['verifier_sha256'] == report['verifier_sha256']
        report['comparison_baseline_result'] = baseline_result
        report['comparison_provenance'] = 'SHA-bound complete official baseline PASS'
        with np.load(args.baseline, allow_pickle=False) as data:
            base = {key: np.array(data[key]) for key in data.files}
        with np.load(args.candidate, allow_pickle=False) as data:
            candidate = {key: np.array(data[key]) for key in data.files}
        for key in ('W', 'H2_I', 'angle_words', 'tree_edges'):
            assert candidate[key].shape == base[key].shape
            assert np.all(np.isfinite(candidate[key]))
        declared_words = checked_angle_words(args.candidate)
        report['changed_word_count'] = int(np.count_nonzero(candidate['angle_words'] != base['angle_words']))
        report['tree_edges_unchanged'] = bool(np.array_equal(candidate['tree_edges'], base['tree_edges']))
        report['W_unchanged'] = bool(np.array_equal(candidate['W'], base['W']))
        report['H2_I_unchanged'] = bool(np.array_equal(candidate['H2_I'], base['H2_I']))
        target = args.out / 'submission.npz'
        shutil.copyfile(args.candidate, target)
        assert sha(target) == report['candidate_sha256']
        report['factorization'] = {'path': str(target), 'sha256': sha(target),
                                   'candidate_copied_byte_for_byte': True}
        count = (candidate['angle_words'].shape[1] + 4) // 5
        circuits = [args.loaders / f'angle_k_{k}.kmb' for k in range(count)]
        report['loaders'] = [{'name': p.name, 'sha256': sha(p)} for p in circuits]
        sys.path.insert(0, str(args.engine_dir.resolve()))
        sys.path.insert(0, str(args.verifier.resolve().parents[1]))
        spec = importlib.util.spec_from_file_location('official_score2_candidate', args.verifier)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        # The official verifier scores recovered circuit words; it does not
        # assert equality to the optional angle_words metadata in the NPZ.
        # Bind that metadata explicitly without changing official verifier code.
        recovered_words, recovered_layout, recovered_toffoli = module.recover_words_from_circuits(
            module.load_circuits(circuits), num_vectors=declared_words.shape[0],
            num_angles=declared_words.shape[1], shots_per_address=2, seed=0)
        if not np.array_equal(recovered_words, declared_words):
            raise ValueError('Circuit-recovered integer words differ from the candidate NPZ')
        report['circuit_words_match_candidate_npz'] = True
        report['word_binding_check'] = {
            'all_declared_words': int(declared_words.size), 'all_addresses': int(declared_words.shape[0]),
            'shots_per_address': 2, 'seed': 0,
            'forward_reverse_workspace_and_phase_checked': True,
            'broT': int(recovered_layout.brot), 'roundtrip_toffoli': float(recovered_toffoli),
            'canonical_u64_words_sha256': hashlib.sha256(declared_words.astype('<u8').tobytes()).hexdigest()}
        result = module.verify(circuits, target, tree_edges=candidate['tree_edges'])
        assert result['status'] == 'PASS' and result['verified_shots'] == 78080
        report['official_result'] = result
        before, after = baseline_result['score'], result['score']
        tolerance = max(1e-9, 32 * abs(float(np.spacing(max(abs(before), abs(after))))))
        report['comparison_roundoff_tolerance'] = tolerance
        report['local_cost_reduction'] = before - after
        report['local_cost_reduction_percent'] = 100 * (1 - after / before)
        report['lower_than_matched_baseline'] = bool(after < before - tolerance)
        report['same_cost_within_roundoff'] = bool(abs(after - before) <= tolerance)
        report['lambda_below_user_log_46_905894137'] = bool(result['lambda_eff'] < 46.905894137)
        report['status'] = ('PASS_AND_LOWER_MATCHED_COST' if report['lower_than_matched_baseline']
                            else 'PASS_SAME_MATCHED_COST' if report['same_cost_within_roundoff']
                            else 'PASS_WITHOUT_MATCHED_GAIN')
    except Exception as error:
        report.update(status='REJECTED', error=f'{type(error).__name__}: {error}')
    report['seconds'] = time.monotonic() - started
    (args.out / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)
    if report['status'] == 'REJECTED':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
