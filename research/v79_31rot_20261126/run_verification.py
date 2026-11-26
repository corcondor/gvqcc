#!/usr/bin/env python3
"""Verify final serialized KMBs; optional full legal-domain official runs.

Run from any directory. Requires Python 3.12+, g++, numpy, scipy, kickmix.
Does not submit to Kaggle. The official run uses one shot per legal input.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
FINAL = ('ccx_min36_care', 'balanced30_36_care', 'cost_min36_care')

def run(argv, cwd=ROOT):
    print('+', ' '.join(map(str, argv)), flush=True)
    subprocess.run(list(map(str, argv)), cwd=cwd, check=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--official', action='store_true')
    parser.add_argument('--workers', type=int, default=3)
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'MANIFEST.json').read_text())
    for item in manifest['files']:
        path = ROOT / item['path']
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == item['sha256'], f'Hash mismatch: {path}'
    print(f"Manifest: {len(manifest['files'])} files PASS", flush=True)
    donor = ROOT / 'recovered/V79'
    run(['g++', '-O3', '-std=c++17', donor / 'phasecheck.cpp', '-o', donor / 'phasecheck'])
    output = ROOT / 'reverification'
    output.mkdir(exist_ok=True)
    for name in FINAL:
        source = ROOT / 'theory/care' / name
        stem = output / name
        for suffix in ('.kmb', '.json'):
            shutil.copy2(source.with_suffix(suffix), stem.with_suffix(suffix))
        run([sys.executable, ROOT / 'theory/verify_domain.py', stem, 'recip.plan.json'], cwd=donor)
        # Loading the binary is only a packaging/parser check, separate from
        # the all-input results in the .official_all_inputs.json receipts.
        verifier = ROOT / 'official-qcc/verifiers/invsqrt/verify_submission_invsqrt.py'
        if args.official:
            cmd = [sys.executable, verifier, stem.with_suffix('.kmb'),
                   '--shots-per-x', '1', '--batch-size', '2044',
                   '--max-workers', str(args.workers)]
            out = subprocess.run(list(map(str, cmd)), cwd=ROOT, check=True,
                                 text=True, capture_output=True)
            result = json.loads(out.stdout)
            assert result['status'] == 'PASS' and result['verified_shots'] == 3133452
            assert result['circuit_sha256'] == hashlib.sha256(stem.with_suffix('.kmb').read_bytes()).hexdigest()
            (output / f'{name}.official_all_inputs.json').write_text(out.stdout)
            print(json.dumps(result), flush=True)
        else:
            import kickmix
            loaded = kickmix.Circuit.from_file(str(stem.with_suffix('.kmb')), format='kmb')
            assert loaded.num_qubits == 36
            print(f'{name}: KickMix loader PASS', flush=True)
    print('Completed. Partial arithmetic and 31R specification receipts have separate scopes.', flush=True)

if __name__ == '__main__':
    main()
