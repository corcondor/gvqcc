#!/usr/bin/env python3
"""Reproduce GVQCC Nov-23 angle-gauge LOCAL checks from an exact ZIP.

This is NOT KickMix verification, submission grading, or an optimized circuit.
It validates source hashes, executes 15-bank I and J trajectories, and records
value/phase/scratch checks for a collaborator without relying on /mnt/data paths.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import zipfile


def sha256_file(path: Path) -> str:
    dig = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            dig.update(chunk)
    return dig.hexdigest()


def check_manifest(archive: Path) -> dict:
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        for name in names:
            p = PurePosixPath(name)
            if not name or p.is_absolute() or '..' in p.parts or '\\' in name:
                raise ValueError(f'Unsafe archive member: {name!r}')
        manifest = json.loads(z.read('SHA256_MANIFEST.json'))
        items = manifest['items']
        for name, rec in items.items():
            if name not in names:
                raise ValueError(f'Missing {name!r}')
            h = hashlib.sha256()
            n = 0
            with z.open(name) as inp:
                for chunk in iter(lambda: inp.read(1 << 20), b''):
                    h.update(chunk)
                    n += len(chunk)
            if h.hexdigest() != rec['sha256'] or n != rec['size']:
                raise ValueError(f'Checksum mismatch for {name!r}')
        return {'entries': len(names), 'hashes_checked': len(items),
                'archive_sha256': sha256_file(archive), 'manifest_complete': True}


def run_family(root: Path, family: str, output: Path) -> dict:
    out = output / f'{family}_recheck.json'
    src = root / 'candidates' / family
    command = [sys.executable, 'src/verify_affine_zero_t.py', '--source',
               str(src.relative_to(root) / 'submission.npz'), '--circuit_dir',
               str(src.relative_to(root) / 'circuits'), '--out', str(out), '--seeds', '-1']
    env = os.environ.copy()
    env.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1',
               PYTHONPATH='src')
    run = subprocess.run(command, cwd=root, env=env, capture_output=True,
                         text=True, timeout=300, check=False)
    if run.returncode != 0 or not out.is_file():
        raise RuntimeError(f'{family}: exit={run.returncode}\n{run.stdout}\n{run.stderr}')
    result = json.loads(out.read_text())
    entries = result['seeds'][0]['results']
    verdict = {
        'family': family,
        'command': command,
        'python_exit_code': run.returncode,
        'recheck_sha256': sha256_file(out),
        'address_count': result['Naddresses'],
        'banks': len(entries),
        'toffoli_one_way': result['seeds'][0]['total_toFFoli_per_pass'],
        'max_qubits': max(x['Q'] for x in entries),
        'value_error_bits': sum(x['value_error_bits'] for x in entries),
        'phase_error_coefficients': sum(x['phase_error_coefficients'] for x in entries),
        'clean_scratch': all(x['clean_scratch'] for x in entries),
        'stdout': run.stdout.strip(),
        'official_verification': False,
    }
    if verdict['banks'] != 15 or verdict['value_error_bits'] or verdict['phase_error_coefficients'] or not verdict['clean_scratch']:
        raise AssertionError(f'Local check FAILED: {verdict}')
    return verdict


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('archive', type=Path, help='Original 136-file global-angle research ZIP')
    ap.add_argument('--workdir', type=Path, default=Path('gvqcc_claude_recheck'))
    args = ap.parse_args()
    archive = args.archive.expanduser().resolve()
    wd = args.workdir.expanduser().resolve()
    wd.mkdir(parents=True, exist_ok=True)
    manifest = check_manifest(archive)
    print('ARCHIVE OK:', manifest, flush=True)
    root = wd / 'unpacked'
    root.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        z.extractall(root)
    families = [run_family(root, fam, wd) for fam in ('I_affine_3357', 'J_C45_joint')]
    summary = {'manifest': manifest, 'families': families,
               'official_kickmix_executed': False,
               'warning': 'Valid only for local 15-bank sequential-clean phase/value/scratch tests. No global KickMix score.'}
    path = wd / 'local_recheck_report.json'
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print('REPORT', path, sha256_file(path), flush=True)
    for x in families:
        print(x['family'], 'addresses', x['address_count'], 'T',
              x['toffoli_one_way'], 'Q', x['max_qubits'],
              'value_errors', x['value_error_bits'], 'phase_errors',
              x['phase_error_coefficients'], flush=True)


if __name__ == '__main__':
    main()