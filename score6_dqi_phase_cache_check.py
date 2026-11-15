#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Binary-parser positive controls and independent basis checks for discovery."""
from pathlib import Path
import argparse
import hashlib
import itertools
import json
import subprocess
import kickmix as km


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scanner', type=Path, required=True)
    ap.add_argument('--workspace', type=Path, required=True)
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    args.workspace.mkdir(parents=True, exist_ok=False)
    fixtures = [
        ('cached_product', 'R q2\nCCX q0 q1 q2\nCCZ q0 q1 q3\n', 1, 0),
        ('dirty_target', 'CCX q0 q1 q2\nCCZ q0 q1 q3\n', 0, 0),
        ('fredkin_roundtrip', 'R q4\nCCX q0 q1 q4\nCSWAP q2 q4 q5\nCSWAP q2 q4 q5\nCCZ q0 q1 q3\n', 1, 0),
        ('branch_roundtrip', 'R q4\nPUSH_CONDITION if b0\nCCX q0 q1 q4\nCSWAP q2 q4 q5\nCSWAP q2 q4 q5\nCCZ q0 q1 q3\nPOP_CONDITION\n', 1, 0),
        ('same_phase', 'CCZ q0 q1 q2\nCX q3 q4\nCCZ q0 q1 q2\n', 0, 1),
        ('different_guard_versions', 'CCZ q0 q1 q2 if b0\nBIT_INVERT b0\nCCZ q0 q1 q2 if b0\n', 0, 0),
    ]
    rows = []
    for name, text, want_cache, want_phase in fixtures:
        path = args.workspace / (name + '.kmb')
        km.Circuit(text).to_file(path, format='kmb')
        output = args.workspace / (name + '.json')
        command = [str(args.scanner), str(path), str(output), '--branches', '--fredkin']
        subprocess.run(command, check=True, capture_output=True, text=True)
        found = json.loads(output.read_text())
        assert found['candidate_count'] == want_cache, (name, found)
        assert found['phase_duplicate_count'] == want_phase, (name, found)
        rows.append({'name': name, 'kmb_sha256': sha(path), 'expected_cache_candidates': want_cache,
                     'expected_phase_pairs': want_phase, 'observed': found})
    # Independent Boolean/Kraus-free check: after a clean computation t=a*b,
    # CCZ(a,b,c) and CZ(t,c) have identical complete computational-basis phases.
    phase_checks = 0
    for a, b, c, reference in itertools.product((0, 1), repeat=4):
        t = a & b
        before = ((a, b, c, t, reference), (-1)**(a*b*c))
        after = ((a, b, c, t, reference), (-1)**(t*c))
        assert before == after
        phase_checks += 1
    dirty_counterexamples = sum((-1)**(a*b*c) != (-1)**((old ^ (a & b))*c)
                                for a, b, c, old in itertools.product((0, 1), repeat=4))
    assert dirty_counterexamples == 4
    result = {'status': 'PASS', 'source_sha256': sha(__file__),
              'scanner_source_sha256': sha(Path(__file__).with_name('score6_dqi_phase_cache_scan.cpp')),
              'scanner_binary_sha256': sha(args.scanner), 'fixtures': rows,
              'all_basis_phase_columns_checked': phase_checks,
              'dirty_target_counterexamples': dirty_counterexamples,
              'production_rewrite_or_score_claim': None}
    args.report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'fixtures'}))


if __name__ == '__main__':
    main()
