#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Package one verified chemistry change into the exact score5 portfolio.

Python standard library only. This does not run the verifier or submit
anything. It requires completed, hash-bound receipts, preserves the other17
payloads, and checks every output member's SHA256 and ZIP CRC while reading.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import io
import json
import math
from pathlib import Path
import time
import zipfile


ROOT = Path(__file__).resolve().parent
SOURCE_ZIP_SHA = '7b59403add6ec475513b9f1f634781cfc563cd5acdc50970db03c91ad3d03978'
OLD_NPZ_SHA = '5f8dd37ac194b09b5ba870c4150a487b6665775375d9abc864d38b32a2cb7357'
NEW_NPZ_SHA = '16ee9ad3716309385aa9ce48c1f714e59484b79126ac6fe60591d3ba8bd7ebcf'
NPZ_MEMBER = 'dfthcsos/submission.npz'
DQI_SHA = 'e4e110436080b8538f50511dc7064185e1708c2bd386ea0e36322d7791311355'
INV_SHA = '684106f101730ca193627229920a0501bef9ea10ccfb34aa453fcf63edadb50a'


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def joint_score(reference, costs):
    return math.prod(reference[k] / costs[k] for k in reference) ** (1 / 3)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--chemistry', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--chemistry-receipt', type=Path, default=ROOT/'score6_chem_transfer_full_verification.json')
    p.add_argument('--baseline-scorecard', type=Path, default=ROOT/'score5_final_scorecard.json')
    p.add_argument('--dqi-receipt', type=Path, default=ROOT/'score5_dqi_final_full_verification.json')
    p.add_argument('--invsqrt-receipt', type=Path, default=ROOT/'score3_invsqrt_full_verification.json')
    p.add_argument('--backoff-receipt', type=Path, default=ROOT/'score6_chem_backoff_full_verification.json')
    p.add_argument('--receipt', type=Path, default=ROOT/'score6_package_receipt.json')
    p.add_argument('--scorecard', type=Path, default=ROOT/'score6_scorecard.json')
    a = p.parse_args()
    start = time.monotonic()
    assert not a.output.exists(), 'Refusing to overwrite an existing portfolio'
    assert sha(a.source) == SOURCE_ZIP_SHA
    assert sha(a.chemistry) == NEW_NPZ_SHA
    baseline = read_json(a.baseline_scorecard)
    chemistry = read_json(a.chemistry_receipt)
    dqi, inv = read_json(a.dqi_receipt), read_json(a.invsqrt_receipt)
    assert baseline['candidate']['zip_sha256'] == SOURCE_ZIP_SHA
    assert chemistry['factorization']['sha256'] == NEW_NPZ_SHA
    assert chemistry['baseline_source_sha256'] == OLD_NPZ_SHA
    new = chemistry['official_result']
    assert new['status'] == 'PASS' and new['verified_shots'] == 78080
    assert new['score'] < baseline['candidate_costs']['dfthcsos']
    assert (new['num_qubits'], new['toffoli_count'], new['resources']['angles_toffoli_per_pass']) == (427, 14728, 4033)
    assert dqi['status'] == inv['status'] == 'PASS'
    assert dqi['circuit_sha256'] == DQI_SHA and inv['circuit_sha256'] == INV_SHA
    assert dqi['verified_shots'] == 102400 and dqi['value_errors'] == dqi['phase_errors'] == 0
    assert inv['verified_shots'] == 200540928
    assert dqi['score'] == baseline['candidate_costs']['dqi']
    assert inv['score'] == baseline['candidate_costs']['invsqrt']
    expected = {'dqi.kmb': DQI_SHA, 'invsqrt.kmb': INV_SHA, NPZ_MEMBER: NEW_NPZ_SHA}
    expected.update({'dfthcsos/'+v['name']: v['sha256'] for v in chemistry['loaders']})
    assert len(expected) == 18
    new_npz = a.chemistry.read_bytes()
    members = []
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(a.source) as old:
        infos = old.infolist()
        assert len(infos) == len({v.filename for v in infos}) == 18
        assert set(old.namelist()) == set(expected)
        old_npz = old.read(NPZ_MEMBER)
        assert hashlib.sha256(old_npz).hexdigest() == OLD_NPZ_SHA
        with zipfile.ZipFile(io.BytesIO(old_npz)) as x, zipfile.ZipFile(io.BytesIO(new_npz)) as y:
            assert set(x.namelist()) == set(y.namelist())
            changed_arrays = [n for n in x.namelist() if x.read(n) != y.read(n)]
            assert set(changed_arrays) == {'W.npy', 'H2_I.npy'}
        with zipfile.ZipFile(a.output, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as out:
            for info in infos:
                target_info = copy.copy(info)
                digest = hashlib.sha256()
                count = 0
                if info.filename == NPZ_MEMBER:
                    stream = io.BytesIO(new_npz)
                    target_info.file_size = len(new_npz)
                else:
                    stream = old.open(info)
                with stream, out.open(target_info, 'w') as sink:
                    while data := stream.read(1 << 20):
                        digest.update(data)
                        count += len(data)
                        sink.write(data)
                assert digest.hexdigest() == expected[info.filename], info.filename
                members.append({'name': info.filename, 'bytes': count, 'sha256': digest.hexdigest(),
                                'unchanged_payload': info.filename != NPZ_MEMBER})
    # Reading each member to EOF independently checks its ZIP CRC too.
    with zipfile.ZipFile(a.output) as z:
        assert set(z.namelist()) == set(expected)
        for entry in members:
            with z.open(entry['name']) as f:
                digest = hashlib.file_digest(f, 'sha256').hexdigest()
            assert digest == entry['sha256'], entry['name']
    candidate_costs = {'dqi': dqi['score'], 'invsqrt': inv['score'], 'dfthcsos': new['score']}
    references = baseline['reference_costs']
    old_score = joint_score(references, baseline['candidate_costs'])
    score = joint_score(references, candidate_costs)
    assert abs(old_score - baseline['local_combined_score']) < 1e-12
    backoff = read_json(a.backoff_receipt)
    assert backoff['official_result']['status'] == 'PASS'
    backoff_costs = dict(candidate_costs, dfthcsos=backoff['official_result']['score'])
    counterfactuals = []
    for name, benchmark, factor in (
        ('DQI_Q889_to_888', 'dqi', (888/889)**2),
        ('DQI_one_unconditional_CCX', 'dqi', (dqi['toffoli_count']-1)/dqi['toffoli_count']),
        ('ANGLE_one_CCX_each_pass', 'dfthcsos', (14728-2)/14728),
        ('invsqrt_one_unconditional_CCX', 'invsqrt', (inv['score']-inv['num_qubits'])/inv['score']),
    ):
        proposed = dict(candidate_costs)
        proposed[benchmark] *= factor
        hypothetical = joint_score(references, proposed)
        counterfactuals.append({'change': name, 'combined_score': hypothetical, 'increase': hypothetical-score})
    scorecard = {
        'status': 'HASH_BOUND_LOCAL_PORTFOLIO_SCORE', 'reference_costs': references,
        'reference_source': baseline['reference_source'], 'formula': baseline['formula'],
        'candidate_costs': candidate_costs, 'previous_score5_local_score': old_score,
        'local_combined_score': score, 'local_combined_increase': score-old_score,
        'local_combined_score_5dp': f'{score:.5f}', 'previous_score5_5dp': f'{old_score:.5f}',
        'new_toffoli_reduction': 0, 'public_score': None, 'submission_performed': False,
        'chemistry_metrics': new['metrics'], 'chemistry_resources': new['resources'],
        'chemistry_npz_sha256': NEW_NPZ_SHA,
        'margin_preserving_alternative': {
            'npz_sha256': backoff['factorization']['sha256'],
            'chemistry_cost': backoff_costs['dfthcsos'],
            'local_combined_score': joint_score(references, backoff_costs),
            'metrics': backoff['official_result']['metrics'], 'full_official_shots': 78080,
        },
        'counterfactual_resource_sensitivities': counterfactuals,
        'sensitivity_scope': 'Hypothetical only: fixed other costs, repetition factor and execution frequency; not achieved circuit changes or server-score predictions.',
        'dqi_extra_CCX_break_even_for_Q888': dqi['toffoli_count']*((889/888)**2-1),
        'retained_dqi_limits': baseline['limits'][:2],
        'receipts': {str(p.name): sha(p) for p in (a.chemistry_receipt, a.dqi_receipt, a.invsqrt_receipt, a.backoff_receipt, a.baseline_scorecard)},
    }
    a.scorecard.write_text(json.dumps(scorecard, indent=2)+'\n')
    receipt = {
        'status': 'PASS_ALL_18_MEMBERS_SHA_AND_CRC',
        'source_zip_sha256': SOURCE_ZIP_SHA, 'source_zip': str(a.source.resolve()),
        'zip': str(a.output.resolve()), 'zip_sha256': sha(a.output), 'zip_bytes': a.output.stat().st_size,
        'members': members, 'unchanged_members': 17, 'changed_member': NPZ_MEMBER,
        'changed_arrays': changed_arrays, 'new_toffoli_reduction': 0,
        'scorecard_sha256': sha(a.scorecard), 'builder_sha256': sha(__file__),
        'local_combined_score': score, 'new_submission_performed': False,
        'seconds': time.monotonic()-start,
    }
    a.receipt.write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k!='members'}), flush=True)


if __name__ == '__main__':
    main()
