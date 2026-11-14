#!/usr/bin/env python3
"""Build/check the score2 checkpoint; large JSON receipts are lossless gzip.

Run --restore-compressed after checkout if tools need the original JSON names.
The manifest binds both stored and uncompressed bytes. No external task inputs
or previously frozen score_ files are modified.
"""
from __future__ import annotations
import argparse
import ast
import gzip
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / 'score2_artifact_manifest.json'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify(restore=False):
    data = json.loads(MANIFEST.read_text())
    for row in data['files']:
        stored = (ROOT / row['stored_path']).read_bytes()
        assert len(stored) == row['stored_bytes'] and sha(stored) == row['stored_sha256']
        raw = gzip.decompress(stored) if row['encoding'] == 'gzip' else stored
        assert len(raw) == row['bytes'] and sha(raw) == row['sha256']
        if row['path'].endswith('.json'):
            json.loads(raw)
        if row['path'].endswith('.py'):
            ast.parse(raw, filename=row['path'])
        if restore and row['encoding'] == 'gzip':
            dest = ROOT / row['path']
            if dest.exists() and sha(dest.read_bytes()) != row['sha256']:
                raise ValueError(f'Refusing to overwrite changed file: {dest}')
            dest.write_bytes(raw)
    return {'status': 'PASS', 'files': len(data['files']),
            'stored_bytes': sum(row['stored_bytes'] for row in data['files']),
            'uncompressed_bytes': sum(row['bytes'] for row in data['files'])}


def build():
    inv = json.loads((ROOT / 'score2_invsqrt_manifest.json').read_text())
    inv_allowed = {Path(row['path']).name for row in inv['published_artifacts']}
    inv_allowed.add('score2_invsqrt_manifest.json')
    paths = []
    omitted = []
    for path in sorted(ROOT.glob('score2_*')):
        if not path.is_file() or path == MANIFEST or path.suffix not in {'.py','.cpp','.md','.json','.txt'}:
            continue
        if path.name.startswith('score2_invsqrt_') and path.name not in inv_allowed:
            omitted.append({'path': path.name, 'reason': 'Regenerable or interrupted input; see invsqrt manifest',
                            'bytes': path.stat().st_size, 'sha256': sha(path.read_bytes())})
            continue
        if not path.stat().st_size:
            raise ValueError(f'Empty published artifact: {path.name}')
        paths.append(path)
    rows = []
    for path in paths:
        raw = path.read_bytes()
        if path.suffix == '.json':
            json.loads(raw)
        if path.suffix == '.py':
            ast.parse(raw, filename=path.name)
        compress = path.suffix == '.json' and len(raw) > 60000
        stored = gzip.compress(raw, compresslevel=9, mtime=0) if compress else raw
        dest = path.with_suffix(path.suffix+'.gz') if compress else path
        if compress:
            dest.write_bytes(stored)
        rows.append({'path': path.name, 'bytes': len(raw), 'sha256': sha(raw),
                     'stored_path': dest.name, 'stored_bytes': len(stored),
                     'stored_sha256': sha(stored), 'encoding': 'gzip' if compress else 'plain'})
    report = {'status': 'FROZEN_VERIFIED_CHECKPOINT',
              'scope': 'Actual PyZX gate reductions, zero-added-Toffoli angle modifications, full official cost gain, bounded inverse-root searches',
              'self_hash_excluded': True, 'files': rows, 'regenerable_omitted': omitted,
              'candidate_zip_sha256': '091f7523ea8cea8be431954bb152df622b426987be2c0514f65d26e48d0dcd68',
              'candidate_npz_sha256': '5f8dd37ac194b09b5ba870c4150a487b6665775375d9abc864d38b32a2cb7357',
              'official_family_sha256': '142af563255af76b2d2097fb5e8cbc61340c583ea70dadeddf7858de501faf84',
              'public_submission_performed': False,
              'restore_command': 'python score2_artifact_manifest.py --restore-compressed',
              'check_command': 'python score2_artifact_manifest.py --check'}
    MANIFEST.write_text(json.dumps(report, indent=2) + '\n')
    return verify()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check', action='store_true')
    p.add_argument('--restore-compressed', action='store_true')
    args = p.parse_args()
    print(json.dumps(verify(args.restore_compressed) if args.check or args.restore_compressed else build()))


if __name__ == '__main__':
    main()
