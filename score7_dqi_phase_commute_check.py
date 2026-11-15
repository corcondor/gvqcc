#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Independent all-basis phase checks and binary controls for the three passes."""
from __future__ import annotations
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import kickmix as km

import kmb_splice


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run_exact(ops, inputs, bits, candidate=None):
    q = list(inputs)
    bits = list(bits)
    phase = 0
    skip = set()
    corrections = {}
    if candidate is not None:
        skip = {candidate['first'], candidate['second']}
        for correction in candidate['corrections']:
            corrections.setdefault(correction['before_source_op'], []).append(correction)
    for i, op in enumerate(ops):
        for correction in corrections.get(i, []):
            guard = correction['condition']
            if guard < 0 or bits[guard]:
                phase ^= int(all(q[x] for x in correction['qubits']))
        if i in skip:
            continue
        if op.condition is not None and not bits[op.condition]:
            continue
        base = op.opcode & 0x7f
        x = op.qubits
        if base in (0x10, 0x20, 0x30):
            phase ^= int(all(q[j] for j in x))
        elif base == 0x11:
            q[x[0]] ^= 1
        elif base == 0x21:
            q[x[1]] ^= q[x[0]]
        elif base == 0x31:
            q[x[2]] ^= q[x[0]] & q[x[1]]
        elif base == 0x22:
            q[x[0]], q[x[1]] = q[x[1]], q[x[0]]
        elif base == 0x32:
            if q[x[0]]:
                q[x[1]], q[x[2]] = q[x[2]], q[x[1]]
        elif base == 0x42:
            bits[op.bit] ^= 1
        elif base == 0x40:
            bits[op.bit] = 0
        elif base == 0x41:
            bits[op.bit] = 1
        else:
            raise ValueError(('unsupported independent operation', base))
    return tuple(q), tuple(bits), phase


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--direct-scanner', type=Path, required=True)
    p.add_argument('--return-scanner', type=Path, required=True)
    p.add_argument('--delta-scanner', type=Path, required=True)
    p.add_argument('--workspace', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    args.workspace.mkdir(parents=True, exist_ok=False)
    fixtures = [
        ('z_crossing', 'CCX q0 q1 q2\nZ q2\nCCX q0 q1 q2\n', 1, 1, 1),
        ('cz_crossing', 'CCX q0 q1 q2\nCZ q2 q3\nCCX q0 q1 q2\n', 1, 1, 1),
        ('ccz_overlap', 'CCX q0 q1 q2\nCCZ q2 q0 q3\nCCX q0 q1 q2\n', 1, 1, 1),
        ('quartic_correction', 'CCX q0 q1 q2\nCCZ q2 q3 q4\nCCX q0 q1 q2\n', 0, 1, 1),
        ('cancelled_corrections', 'CCX q0 q1 q2\nCZ q2 q3\nCZ q2 q3\nCCX q0 q1 q2\n', 1, 1, 1),
        ('restored_controls', 'CCX q0 q1 q2\nCX q3 q0\nCX q3 q0\nCZ q2 q3\nCCX q0 q1 q2\n', 0, 1, 1),
        ('linear_fanout_return', 'CCX q0 q1 q2\nCX q2 q3\nZ q3\nCX q2 q3\nCCX q0 q1 q2\n', 0, 1, 1),
        ('nonlinear_fanout', 'CCX q0 q1 q2\nCCX q2 q3 q4\nCCX q0 q1 q2\n', 0, 1, 0),
        ('fredkin_fanout', 'CCX q0 q1 q2\nCSWAP q2 q3 q4\nCCX q0 q1 q2\n', 0, 1, 0),
        ('control_changed', 'CCX q0 q1 q2\nCX q3 q0\nCCX q0 q1 q2\n', 0, 0, 0),
        ('phase_guard', 'CCX q0 q1 q2\nCZ q2 q3 if b0\nCCX q0 q1 q2\n', 1, 1, 1),
        ('guard_changed', 'CCX q0 q1 q2\nCZ q2 q3 if b0\nBIT_INVERT b0\nCZ q2 q3 if b0\nCCX q0 q1 q2\n', 0, 1, 1),
    ]
    rows = []
    basis_count = 0
    for name, text, want_direct, want_return, want_delta in fixtures:
        path = args.workspace / (name + '.kmb')
        km.Circuit(text).to_file(path, format='kmb')
        direct = args.workspace / (name + '_direct.json')
        ret = args.workspace / (name + '_return.json')
        subprocess.run([str(args.direct_scanner), str(path), str(direct)], check=True)
        subprocess.run([str(args.return_scanner), str(path), str(ret)], check=True)
        d = json.loads(direct.read_text())
        r = json.loads(ret.read_text())
        assert d['candidate_count'] == want_direct, (name, d)
        assert len(r['control_return_pairs']) == want_return, (name, r)
        pairs_path = args.workspace / (name + '_pairs.txt')
        pairs_path.write_text(''.join(' '.join(map(str, [c['first'], c['second'], *c['qubits']])) + '\n'
                                     for c in r['control_return_pairs']))
        delta_path = args.workspace / (name + '_delta.json')
        subprocess.run([str(args.delta_scanner), str(path), str(pairs_path), str(delta_path)], check=True)
        delta = json.loads(delta_path.read_text())
        assert delta['surviving_count'] == want_delta, (name, delta)
        c = kmb_splice.open_circuit(path)
        try:
            operations = list(c.operations(0, len(c.opcodes)))
            nq = c.profile['header']['num_qubits']
            nb = c.profile['header']['num_bits']
            checked = 0
            for candidate in d['candidates']:
                for q in itertools.product((0, 1), repeat=nq):
                    for bits in itertools.product((0, 1), repeat=nb):
                        assert run_exact(operations, q, bits) == run_exact(operations, q, bits, candidate), (name, q, bits)
                        checked += 1
            basis_count += checked
        finally:
            c.close()
        rows.append({'name': name, 'kmb_sha256': sha(path), 'direct_candidates': d['candidate_count'],
                     'control_return_pairs': len(r['control_return_pairs']), 'delta_survivors': delta['surviving_count'],
                     'independent_value_and_phase_columns': checked, 'direct': d, 'delta': delta})
    # Exact, independent algebra checks for the two newly admitted families.
    extra_columns = 0
    for a, b, t, c in itertools.product((0, 1), repeat=4):
        f = a & b
        # Copy t to c and back, with an intervening phase on c.
        assert ((c ^ t ^ f) ^ (c ^ t)) == f
        # Non-overlapping quartic correction really differs from cubic ones.
        assert ((t ^ f)*a*c) ^ (t*a*c) == a*b*c
        extra_columns += 2
    result = {'status': 'PASS', 'source_sha256': sha(__file__),
              'scanner_source_sha256': {name: sha(Path(__file__).with_name(name)) for name in
                 ('score7_dqi_phase_commute.cpp', 'score7_dqi_phase_return.cpp', 'score7_dqi_phase_delta.cpp')},
              'scanner_binary_sha256': {name: sha(path) for name, path in
                 [('direct', args.direct_scanner), ('control_return', args.return_scanner), ('delta', args.delta_scanner)]},
              'fixture_count': len(rows), 'independent_basis_phase_columns': basis_count,
              'independent_algebra_columns': extra_columns, 'fixtures': rows,
              'benchmark_rewrite_or_score_gain': None}
    args.report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'fixtures'}, indent=2))


if __name__ == '__main__':
    main()
