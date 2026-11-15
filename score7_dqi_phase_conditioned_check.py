#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""All-basis exact checks for constant nonlinear derivatives under ab=1."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import kickmix as km

from dqi_ccx_peephole import Operation
import kmb_splice
from score7_dqi_phase_commute_check import run_exact
from score7_dqi_phase_conditioned import inspect


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--workspace', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    args.workspace.mkdir(parents=True, exist_ok=False)
    tests = [
        ('shared_a', 'CCX q0 q1 q2\nCCX q0 q2 q3\nCCX q0 q1 q2\n', True),
        ('shared_b', 'CCX q0 q1 q2\nCCX q1 q2 q3\nCCX q0 q1 q2\n', True),
        ('shared_phase', 'CCX q0 q1 q2\nCCX q0 q2 q3\nZ q3\nCCX q0 q1 q2\n', True),
        ('shared_outputs', 'CCX q0 q1 q2\nCCX q0 q2 q3\nCCX q1 q2 q4\nCCX q0 q1 q2\n', True),
        ('fredkin_shared_control', 'CCX q0 q1 q2\nCSWAP q0 q2 q3\nCCX q0 q1 q2\n', True),
        ('linear_phase_return', 'CCX q0 q1 q2\nCX q2 q3\nZ q3\nCX q2 q3\nCCX q0 q1 q2\n', True),
        ('nonshared_control', 'CCX q0 q1 q2\nCCX q2 q3 q4\nCCX q0 q1 q2\n', False),
        ('nonshared_fredkin', 'CCX q0 q1 q2\nCSWAP q2 q3 q4\nCCX q0 q1 q2\n', False),
    ]
    rows = []
    basis = 0
    for name, text, wanted in tests:
        path = args.workspace / f'{name}.kmb'
        km.Circuit(text).to_file(path, format='kmb')
        c = kmb_splice.open_circuit(path)
        try:
            ops = list(c.operations(0, len(c.opcodes)))
            interval = {'first': 0, 'second': len(ops)-1, 'qubits': [0,1,2]}
            result = inspect(c, interval)
            assert (result['status'] == 'EXACT_REWRITE_CANDIDATE') == wanted, (name, result)
            checked = 0
            if wanted:
                replacement = ops[1:-1]
                residual = result['residual_outputs']
                if residual:
                    target = residual[0]
                    fanout = [Operation(0x21, (target, q)) for q in residual[1:]]
                    replacement += fanout + [Operation(0x31, (0,1,target))] + fanout
                if result['phase_correction'] == 'CZ(a,b)':
                    replacement += [Operation(0x20, (0,1))]
                nq = c.profile['header']['num_qubits']
                for q in itertools.product((0,1), repeat=nq):
                    assert run_exact(ops, q, []) == run_exact(replacement, q, []), (name,q)
                    checked += 1
                basis += checked
            rows.append({'name': name, 'expected_rewrite': wanted, 'observed': result,
                         'independent_basis_phase_columns': checked,
                         'kmb_sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        finally:
            c.close()
    report = {'status': 'PASS', 'fixtures': rows, 'fixture_count': len(rows),
              'independent_basis_phase_columns': basis,
              'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'optimizer_sha256': hashlib.sha256(Path(__file__).with_name('score7_dqi_phase_conditioned.py').read_bytes()).hexdigest(),
              'benchmark_rewrite_or_score_gain': None}
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k:v for k,v in report.items() if k!='fixtures'}, indent=2))


if __name__ == '__main__':
    main()
