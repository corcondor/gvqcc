#!/usr/bin/env python3
"""Rebuild the independently verified exact-mode DQI and package all 18 tasks.

Kaggle inputs: official competition, 480CCX gauge128 v1 output, and
821-score2-verified v1 output. CPU only; no network, credentials, or submission.
The full DQI qualification is pinned to the exact rebuilt circuit bytes.
"""
from pathlib import Path, PurePosixPath
import base64
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile
import time
import zipfile

BUILD = __BUILD__
PAYLOAD_B64 = __PAYLOAD__


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()


def log(event, **fields):
    print(json.dumps({'event': event, **fields}), flush=True)


def copy_stream(src, dst):
    h = hashlib.sha256()
    size = 0
    for b in iter(lambda: src.read(8 << 20), b''):
        dst.write(b)
        h.update(b)
        size += len(b)
    return {'sha256': h.hexdigest(), 'bytes': size}


def check_members(z):
    expected = set(BUILD['portfolio_members'])
    infos = z.infolist()
    require(len(infos) == 18 and set(z.namelist()) == expected, 'Expected exact 18-member submission')
    for item in infos:
        p = PurePosixPath(item.filename)
        require(not p.is_absolute() and '..' not in p.parts and '\\' not in item.filename,
                'Unsafe archive member')
        require(not item.is_dir() and not (item.flag_bits & 1), 'Invalid archive member')
    return infos


def unpack(destination):
    raw = base64.b64decode(PAYLOAD_B64, validate=True)
    require(hashlib.sha256(raw).hexdigest() == BUILD['payload_sha256'], 'Embedded source checksum failed')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        require(set(z.namelist()) == set(BUILD['payload_files']), 'Unexpected embedded source files')
        for name, meta in BUILD['payload_files'].items():
            p = PurePosixPath(name)
            require(not p.is_absolute() and '..' not in p.parts, 'Unsafe source path')
            data = z.read(name)
            require(hashlib.sha256(data).hexdigest() == meta['sha256'], 'Source checksum: ' + name)
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)


def official_engine(root):
    for p in sorted(root.rglob('kickmix.so')):
        if digest(p) == BUILD['kaggle_engine_sha256']:
            return p.parent
    raise RuntimeError('Attach the pinned official competition data')


def sources(root, scratch):
    full = None
    old = None
    for path in sorted(root.rglob('submission.zip')):
        if digest(path) == BUILD['score2_zip_sha256']:
            full = path
        # Only examine the source notebook requested for the DQI donor.
        if 'gvqcc-verified-480ccx-gauge128' in path.parts:
            with zipfile.ZipFile(path) as z:
                check_members(z)
                target = scratch / 'e986_dqi.kmb'
                with z.open('dqi.kmb') as src, target.open('xb') as dst:
                    record = copy_stream(src, dst)
                require(record['sha256'] == BUILD['baseline_dqi_sha256'], 'Wrong donor DQI')
                old = target
    require(full is not None, 'Attach gvqcc-821-score2-verified version 1 output')
    require(old is not None, 'Attach gvqcc-verified-480ccx-gauge128 version 1 output')
    with zipfile.ZipFile(full) as z:
        check_members(z)
    return full, old


def package(source, candidate, destination):
    records = []
    with zipfile.ZipFile(source) as old, zipfile.ZipFile(destination, 'x', allowZip64=True) as new:
        for info in check_members(old):
            stream = candidate.open('rb') if info.filename == 'dqi.kmb' else old.open(info)
            with stream as src, new.open(info, 'w', force_zip64=True) as dst:
                record = copy_stream(src, dst)
            expected = (BUILD['candidate_dqi_sha256'] if info.filename == 'dqi.kmb'
                        else BUILD['portfolio_members'][info.filename])
            require(record['sha256'] == expected, 'Packaged member mismatch: ' + info.filename)
            records.append({'member': info.filename, **record})
    with zipfile.ZipFile(destination) as z:
        check_members(z)
        require(z.testzip() is None, 'Written ZIP failed CRC validation')
    return records


def main():
    started = time.monotonic()
    os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
    os.environ.setdefault('OMP_NUM_THREADS', '1')
    root, output = Path('/kaggle/input'), Path('/kaggle/working')
    require(root.is_dir() and output.is_dir(), 'Run in a fresh Kaggle notebook')
    require(not (output / 'submission.zip').exists(), 'submission.zip already exists')
    scratch = Path(tempfile.mkdtemp(prefix='gvqcc-score3-submit-', dir='/tmp'))
    source = scratch / 'sources'
    unpack(source)
    qualification_path = source / 'qualification/score3_full_20261115_verification.json'
    qualification = json.loads(qualification_path.read_text())
    require(digest(qualification_path) == BUILD['qualification_sha256'], 'Wrong full qualification receipt')
    require(qualification['status'] == 'PASS' and qualification['verified_shots'] == 102400,
            'Full DQI qualification is not complete')
    require(qualification['value_errors'] == 0 and qualification['phase_errors'] == 0,
            'DQI qualification contains errors')
    require(qualification['circuit_sha256'] == BUILD['candidate_dqi_sha256'] and
            qualification['verifier_sha256'] == BUILD['official_dqi_verifier_sha256'],
            'Qualification is not bound to the candidate and official verifier')
    require(qualification['seed'] is None and qualification['salt'] == '' and
            qualification['log2_delta'] == -128, 'Unexpected qualification settings')
    sys.path.insert(0, str(official_engine(root)))
    sys.path.insert(0, str(source / 'own'))
    portfolio, baseline = sources(root, scratch)
    log('inputs_verified', donor_dqi=BUILD['baseline_dqi_sha256'],
        qualification_sha256=BUILD['qualification_sha256'], portfolio_sha256=digest(portfolio))
    from dqi_gauge_expand import load_original, build_pieces
    from score3_gauge_sort import build_and_splice
    original = load_original(source / 'syed/src')
    pieces = scratch / 'gauge128'
    prior = build_pieces(original, pieces, labels=128, reserved=154157)
    expected = json.loads((source / 'reference/gauge_pieces.json').read_text())
    for key in ('baseline_prefix', 'baseline_pair', 'expanded_prefix', 'expanded_pair'):
        require(prior[key]['sha256'] == expected[key]['sha256'], 'Recreated gauge boundary mismatch: ' + key)
    require(prior['fixed_pivot'] == expected['fixed_pivot'], 'Fixed pivot changed')
    log('old_gauge_reproduced', seconds=time.monotonic()-started)
    build = build_and_splice(original, baseline, pieces, scratch / 'score3')
    candidate = Path(build['candidate_path'])
    require(build['candidate']['sha256'] == BUILD['candidate_dqi_sha256'] and
            digest(candidate) == BUILD['candidate_dqi_sha256'], 'Rebuilt candidate differs from qualified bytes')
    require(build['candidate']['bytes'] == 522345615, 'Wrong candidate size')
    log('qualified_candidate_reproduced', candidate_sha256=BUILD['candidate_dqi_sha256'],
        shots=qualification['verified_shots'], seconds=time.monotonic()-started)
    staged = scratch / 'submission.zip'
    members = package(portfolio, candidate, staged)
    receipt = {'status': 'EXACT_QUALIFIED_CANDIDATE_PACKAGED', 'submission_performed': False,
               'source_notebooks': BUILD['source_notebooks'],
               'source_portfolio_zip_sha256': digest(portfolio),
               'source_dqi_sha256': BUILD['baseline_dqi_sha256'],
               'candidate_dqi_sha256': digest(candidate), 'members': members,
               'other_members_preserved': 17,
               'qualification_sha256': BUILD['qualification_sha256'],
               'qualification': qualification, 'builder': build,
               'qualification_note': 'Independent official 102400-shot verification was performed before this run; this run exactly reproduces its SHA256-bound candidate. No full quantum verification is rerun here.',
               'payload_sha256': BUILD['payload_sha256'],
               'submission_zip_sha256': digest(staged), 'submission_zip_bytes': staged.stat().st_size,
               'seconds': time.monotonic()-started, 'observed_public_score': None}
    shutil.copyfile(staged, output / 'submission.zip')
    require(digest(output / 'submission.zip') == receipt['submission_zip_sha256'], 'Final ZIP copy differs')
    (output / 'score3_submit_receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    shutil.copyfile(qualification_path, output / 'score3_full_20261115_verification.json')
    shutil.copyfile(source / 'NOTICE.md', output / 'SOURCE_NOTICE.md')
    for p in (source / 'third_party').iterdir():
        shutil.copyfile(p, output / p.name)
    log('ready', submission_zip_sha256=receipt['submission_zip_sha256'],
        bytes=receipt['submission_zip_bytes'], seconds=receipt['seconds'])


if __name__ == '__main__':
    main()
