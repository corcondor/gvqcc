#!/usr/bin/env python3
"""Bind only the owned continuation-study files and lossless report archives."""
from __future__ import annotations

import ast
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PREFIXES = (
    'score_ancilla_', 'score_chemistry_', 'score_invsqrt_',
    'score_dfthcsos_', 'score_dqi_constant_', 'score_independent_',
    'score_continuation_',
)
ARCHIVED = (
    'score_ancilla_consuming_sites.json',
    'score_invsqrt_retire.json',
    'score_invsqrt_short_retire.json',
)
OUTPUT = ROOT / 'score_continuation_manifest.json'


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    archives = []
    for name in ARCHIVED:
        archive = ROOT / (name + '.gz')
        original = gzip.decompress(archive.read_bytes())
        if (ROOT / name).exists():
            assert original == (ROOT / name).read_bytes(), name
        json.loads(original)
        archives.append({
            'archive': archive.name,
            'restored_path': name,
            'restored_bytes': len(original),
            'restored_sha256': sha(original),
            'restore_command': f'gzip -dk {archive.name}',
        })

    files = []
    checks = {'python_syntax': [], 'json_readability': [], 'gzip_round_trip': archives}
    for path in sorted(ROOT.iterdir()):
        if not path.is_file() or not path.name.startswith(PREFIXES):
            continue
        if path == OUTPUT or path.name in ARCHIVED:
            continue
        content = path.read_bytes()
        if path.suffix == '.py':
            ast.parse(content, filename=path.name)
            checks['python_syntax'].append(path.name)
        elif path.suffix == '.json':
            json.loads(content)
            checks['json_readability'].append(path.name)
        files.append({'path': path.name, 'bytes': len(content), 'sha256': sha(content)})

    report = {
        'status': 'NO_ACCEPTED_SCORE_IMPROVEMENT',
        'scope': 'Additional finite searches, numerical refits, and independent reviews; no new submitted portfolio',
        'repository': 'corcondor/gvqcc',
        'branch': 'research/score-continuation-2026-11-14',
        'base_commit': '6e5a43933b00b44b919e860c16f2187131aec5cb',
        'base_pull_request': 5,
        'concurrent_public_result_source_commit': '5b3f06b88b9d6c4a33e65ae93bd166caf6e18ff0',
        'public_score_from_concurrent_record': 27.27654,
        'prior_best_public_score_from_concurrent_record': 27.30683,
        'public_score_observed_directly_by_this_work': False,
        'external_task1051_final_npz_available': False,
        'latest_user_reported_external_candidate': {
            'task': 1046, 'lambda_eff': 44.16992,
            'error1_mHa': 19.997, 'error2_mHa': 20.105,
            'changed_words': 0, 'official_rounded_word_acceptance_verified_here': False,
            'followup_task': 1051,
        },
        'new_full_official_circuit_verification': False,
        'kaggle_submission_performed': False,
        'baseline_inputs': {
            'dqi_development_kmb_sha256': 'e986d41663fa78ea2ed4ab0a47ebc4d99441ad1660b80e02872e7508cbce92a7',
            'previous_cnot_compacted_kmb_sha256': '3dfa80eb777a55659dcc143466d22427ccf278e198b720f24009cc921747bbcc',
            'invsqrt_kmb_sha256': 'e46d90c36d1beb3ce7731a3e0b5c3659b3cda7f5f290b73c6c34513d96c005b6',
            'chemistry_npz_sha256': '809063291b8af401b4075db850afb216b6cfca398468ed2e47e4c0623eb3fae5',
        },
        'main_report': 'score_continuation_report.md',
        'experiment_manifests': ['score_ancilla_manifest.json', 'score_chemistry_manifest.json', 'score_invsqrt_manifest.json'],
        'historical_run_hashes_preserved': True,
        'current_source_hashes_are_not_claimed_as_historical_run_hashes': True,
        'rejected_npz_or_emitted_candidate_included': False,
        'excluded_concurrent_work': ['README.md', 'score_loss_*', 'dqi_rare_*', 'chemistry_polish_v2_*'],
        'checks': checks,
        'files': files,
        'file_count_excluding_this_manifest': len(files),
        'stored_bytes_excluding_this_manifest': sum(x['bytes'] for x in files),
    }
    OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'status': report['status'], 'files': len(files), 'bytes': report['stored_bytes_excluding_this_manifest']}))


if __name__ == '__main__':
    main()
