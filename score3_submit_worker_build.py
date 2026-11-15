#!/usr/bin/env python3
"""Build the pinned, self-contained score3 Kaggle worker from known source files."""
from pathlib import Path
import base64
import hashlib
import io
import json
import zipfile

REPO = Path(__file__).resolve().parent
WORKSPACE = REPO.parent
SYED = WORKSPACE / 'official_sources/Syed_v12/source/dqi_source/src'
DEPENDENCIES = REPO / 'score3_submit_source_dependencies.json'
QUALIFICATION = REPO / 'score3_full_20261115_verification.json'
EXPECTED_QUALIFICATION = 'e98986fc57fcc920b6275f26fdd9b9db4f9f72604a24802b5a21cf85e05df714'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    qualification = QUALIFICATION.read_bytes()
    assert sha(qualification) == EXPECTED_QUALIFICATION
    q = json.loads(qualification)
    assert q['status'] == 'PASS' and q['verified_shots'] == 102400
    assert q['value_errors'] == q['phase_errors'] == 0
    payload = {}
    for rel in json.loads(DEPENDENCIES.read_text()):
        payload['syed/src/' + rel] = (SYED / rel).read_bytes()
    own = ['score3_gauge_sort.py', 'dqi_gauge_expand.py', 'kmb_splice.py',
           'kmb_profile.py', 'dqi_ccx_peephole.py']
    for name in own:
        payload['own/' + name] = (REPO / name).read_bytes()
    payload['reference/gauge_pieces.json'] = (WORKSPACE / 'dqi_inputs/gauge128/gauge_pieces.json').read_bytes()
    payload['qualification/score3_full_20261115_verification.json'] = qualification
    payload['reference/score3_gauge_sort_proof.md'] = (REPO / 'score3_gauge_sort_proof.md').read_bytes()
    payload['reference/score3_gauge_sort_native.json'] = (REPO / 'score3_gauge_sort_native.json').read_bytes()
    payload['reference/score3_gauge_sort_build.json'] = (REPO / 'score3_gauge_sort_build.json').read_bytes()
    payload['NOTICE.md'] = (REPO / 'NOTICE.md').read_bytes()
    for name in ('Qualtran_Apache_2.0.txt', 'Syed_DQI_Apache_2.0.txt'):
        payload['third_party/' + name] = (REPO / 'third_party' / name).read_bytes()
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in sorted(payload.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 15, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    raw = archive.getvalue()
    portfolio = json.loads((REPO / 'submission_v5_bestbase_local_receipt.json').read_text())
    build = {
        'candidate_dqi_sha256': '9a82f54226707185fa8a7f59a293e6af8ab7d59bff04a4d92919e4178d7d82f1',
        'baseline_dqi_sha256': 'e986d41663fa78ea2ed4ab0a47ebc4d99441ad1660b80e02872e7508cbce92a7',
        'score2_zip_sha256': 'dfacbef6f0e0c6856cca66a8497740eb1ac88d46dfb08884d02ce6637d91565f',
        'source_notebooks': [
            'https://www.kaggle.com/code/geocpuresearch/gvqcc-verified-480ccx-gauge128?scriptVersionId=369627280',
            'https://www.kaggle.com/code/geocpuresearch/gvqcc-821-score2-verified?scriptVersionId=369715705'],
        'kaggle_engine_sha256': 'c66b3216c4029e0cdfd09054306aa0feadf53ab2f50c1164e37f752874e5005e',
        'official_dqi_verifier_sha256': q['verifier_sha256'],
        'qualification_sha256': EXPECTED_QUALIFICATION,
        'payload_sha256': sha(raw),
        'payload_files': {k: {'sha256': sha(v), 'bytes': len(v)} for k, v in sorted(payload.items())},
        'portfolio_members': {r['member']: r['sha256'] for r in portfolio['members']},
    }
    template = (REPO / 'score3_submit_worker_template.py').read_text()
    source = template.replace('__BUILD__', repr(build)).replace('__PAYLOAD__', repr(base64.b64encode(raw).decode()))
    compile(source, 'score3_submit_worker.py', 'exec')
    worker = REPO / 'score3_submit_worker.py'
    worker.write_text(source)
    (REPO / 'score3_submit_worker_build.json').write_text(json.dumps({
        'status': 'BUILT_PINNED_WORKER_NOT_EXECUTED_ON_KAGGLE',
        'worker': worker.name, 'worker_sha256': sha(worker.read_bytes()), 'worker_bytes': worker.stat().st_size,
        'payload_bytes': len(raw), 'payload_files': len(payload), 'build': build,
    }, indent=2)+'\n')
    print(json.dumps({'worker': str(worker), 'bytes': worker.stat().st_size,
                      'sha256': sha(worker.read_bytes()), 'payload_bytes': len(raw),
                      'files': len(payload), 'qualification_sha256': EXPECTED_QUALIFICATION}, indent=2))


if __name__ == '__main__':
    main()
