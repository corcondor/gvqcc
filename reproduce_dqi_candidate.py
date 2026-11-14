#!/usr/bin/env python3
"""Reproduce the pinned 96-CCX + gauge128 DQI candidate, then verify it.

Public downloads are checksum verified. An existing baseline ZIP can optionally
be repackaged without changing its invsqrt or chemistry members. No Kaggle
credentials, hash search, salt search, or competition submission is performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import urllib.request
import zipfile

BASELINE_SHA = '821bf8d157c03c3e868a0099b0ab1438cfba664ab1bc6fec3210654099b672a3'
SOURCE_SHA = '49e2b331d4008afb724985caf1038765b7a910f08838b590bf6e8fb692772763'
VERIFIER_SHA = 'f14274bc0943fb9769ddb01131be6063191a15009fe1caf1d4bdd9fd25194e65'
CANDIDATE_SHA = 'aafed8b0fa2bbfde21f47672a5e548a84a6d42d735e800557efbb2c04c310f09'
BASELINE_URL = 'https://www.kaggle.com/api/v1/datasets/download/manwithacat/vqcc-apache-public-circuits/circuits%2Fdqi%2F821bf8d157c0.kmb'
SOURCE_URL = 'https://www.kaggle.com/api/v1/datasets/download/syed3000/vqcc-own-circuit-portfolio/dqi_source_zip'
VERIFIER_URL = 'https://raw.githubusercontent.com/Inzainos/quantum-circuit-compilation/4277c767440df9efb8a90860ae2ce47028e46ba9/verifiers/dqi/verify_submission_dqi.py'
HERE = Path(__file__).resolve().parent


def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def check_pin(path, expected):
    actual = sha256(path)
    if actual != expected:
        raise ValueError(f'SHA-256 mismatch for {path}: expected {expected}, received {actual}')
    return Path(path).resolve()


def acquire(supplied, url, destination, expected):
    if supplied is not None:
        return check_pin(supplied, expected)
    print(json.dumps({'event': 'download', 'url': url}), flush=True)
    with urllib.request.urlopen(url, timeout=120) as source, destination.open('xb') as target:
        shutil.copyfileobj(source, target, 1 << 22)
    return check_pin(destination, expected)


def extract_source(archive, destination):
    destination.mkdir()
    with zipfile.ZipFile(archive) as source:
        if sum(member.file_size for member in source.infolist()) > 256 * 1024 * 1024:
            raise ValueError('Source archive exceeds expected expanded size')
        seen = set()
        for member in source.infolist():
            name = PurePosixPath(member.filename)
            if name.is_absolute() or '..' in name.parts or '\\' in member.filename:
                raise ValueError('Unsafe source archive path')
            if stat.S_ISLNK(member.external_attr >> 16) or member.filename in seen:
                raise ValueError('Source archive contains a link or duplicate member')
            seen.add(member.filename)
            path = destination.joinpath(*name.parts)
            if member.is_dir():
                path.mkdir(parents=True, exist_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                with source.open(member) as incoming, path.open('xb') as outgoing:
                    shutil.copyfileobj(incoming, outgoing)
    return destination / 'dqi_source' / 'src'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-dir', type=Path, required=True,
                        help='New output directory; existing directories are refused')
    parser.add_argument('--baseline', type=Path, help='Pinned uncompressed 821 KMB; otherwise downloaded')
    parser.add_argument('--source-archive', type=Path, help='Pinned Syed source ZIP; otherwise downloaded')
    parser.add_argument('--verifier', type=Path, help='Pinned official verifier; otherwise downloaded')
    parser.add_argument('--engine-dir', type=Path, help='Optional directory containing competition kickmix.so')
    parser.add_argument('--baseline-zip', type=Path, help='Existing submission ZIP to update after full verification')
    parser.add_argument('--build-only', action='store_true', help='Build without verification or submission ZIP')
    args = parser.parse_args()
    work = args.work_dir.resolve()
    work.mkdir(parents=True, exist_ok=False)
    baseline = acquire(args.baseline, BASELINE_URL, work / 'baseline_821.kmb', BASELINE_SHA)
    archive = acquire(args.source_archive, SOURCE_URL, work / 'syed_dqi_source.zip', SOURCE_SHA)
    verifier = acquire(args.verifier, VERIFIER_URL, work / 'verify_submission_dqi.py', VERIFIER_SHA)
    source_root = extract_source(archive, work / 'upstream')
    environment = dict(os.environ)
    if args.engine_dir:
        environment['PYTHONPATH'] = str(args.engine_dir.resolve()) + os.pathsep + environment.get('PYTHONPATH', '')

    def run(script, *arguments):
        command = [sys.executable, '-u', str(HERE / script), *map(str, arguments)]
        print(json.dumps({'event': 'run', 'command': command}), flush=True)
        subprocess.run(command, env=environment, check=True)

    peephole = work / '821_ccx_peephole.kmb'
    pieces = work / 'gauge128'
    candidate = work / 'dqi.kmb'
    run('dqi_ccx_peephole.py', baseline, peephole, '--progress')
    run('dqi_gauge_expand.py', '--source-root', source_root, '--out-dir', pieces, '--labels', 128)
    run('dqi_gauge_expand_verify.py', '--source-root', source_root, '--labels', 128,
        '--output', work / 'selector_verify.json')
    run('kmb_splice.py', '--baseline', peephole, '--pieces', pieces, '--out', candidate)
    check_pin(candidate, CANDIDATE_SHA)
    receipt = {'baseline_sha256': BASELINE_SHA, 'source_archive_sha256': SOURCE_SHA,
               'verifier_sha256': VERIFIER_SHA, 'candidate_sha256': CANDIDATE_SHA,
               'status': 'BUILT_NOT_VERIFIED', 'kaggle_submission_performed': False}
    if not args.build_only:
        result_path = work / 'dqi_full102400.json'
        run('verify_dqi_candidate.py', candidate, '--verifier', verifier, '--output', result_path)
        result = json.loads(result_path.read_text())
        if result.get('status') != 'PASS' or result.get('verified_shots') != 102400:
            raise RuntimeError('Full DQI verification did not pass; submission ZIP not created')
        if result.get('circuit_sha256') != CANDIDATE_SHA:
            raise RuntimeError('Verification report does not identify the candidate')
        receipt.update(status='LOCAL_FULL_VERIFIER_PASS', verification=result)
        if args.baseline_zip:
            run('replace_dqi_submission.py', '--baseline-zip', args.baseline_zip,
                '--dqi', candidate, '--verification', result_path, '--output', work / 'submission.zip')
    (work / 'reproduction_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2), flush=True)


if __name__ == '__main__':
    main()
