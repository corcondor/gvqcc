#!/usr/bin/env python3
"""Synthetic all-branch and native control of the joint phase rewrite.

This is deliberately not an invsqrt benchmark candidate or score claim.
"""
import argparse
from fractions import Fraction
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import re
import sys

import numpy as np
import kickmix as km


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run_exact(lines, x, outcomes):
    q = [(x >> j) & 1 for j in range(22)] + [0, 0]
    bits, used, phase = {}, 0, Fraction(0)
    for line in lines:
        op = line.split()[0]
        if ' if ' in line and not bits[int(line.rsplit('b', 1)[1])]:
            continue
        w = tuple(map(int, re.findall(r'\bq(\d+)\b', line)))
        if op == 'CX':
            a, t = w; q[t] ^= q[a]
        elif op == 'CCX':
            a, b, t = w; q[t] ^= q[a] & q[b]
        elif op == 'Z_POW':
            phase += Fraction(line.split()[2])*q[w[0]]/2
        elif op == 'Z':
            phase += Fraction(q[w[0]], 2)
        elif op == 'CZ':
            phase += Fraction(q[w[0]] & q[w[1]], 2)
        elif op == 'HMR':
            b = int(line.rsplit('b', 1)[1]); m = outcomes[used]; used += 1
            bits[b] = m; phase += Fraction(m*q[w[0]], 2); q[w[0]] = 0
    assert q[:22] == [(x >> j) & 1 for j in range(22)]
    assert not any(q[22:]) and used == len(outcomes)
    return phase % 1


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args(); args.out.mkdir(parents=True, exist_ok=True)
    header = [f'APPEND_TO_REGISTER q{j} r0' for j in range(22)] + ['REGISTER r0 "x"']
    old = header + [
        'Z_POW q0 0.09375',
        'CCX q0 q1 q22', 'Z_POW q22 0.3125', 'HMR q22 b0', 'CZ q0 q1 if b0',
        'CX q0 q23', 'CCX q0 q1 q23',
        'CCX q1 q2 q0', 'CCX q1 q2 q0',
        'HMR q23 b1', 'Z q0 if b1', 'CZ q0 q1 if b1']
    new = header + [
        'Z_POW q0 0.40625',
        'CX q0 q23', 'CCX q0 q1 q23',
        'CCX q1 q2 q0', 'Z_POW q23 1.6875', 'CCX q1 q2 q0',
        'HMR q23 b1', 'Z q0 if b1', 'CZ q0 q1 if b1']
    exact_cases = 0
    for lines, n in ((old, 2), (new, 1)):
        for x in range(8):
            expected = (Fraction(3, 64)*(x & 1) + Fraction(5, 32)*((x & 1) & (x >> 1 & 1))) % 1
            for outcomes in itertools.product((0, 1), repeat=n):
                assert run_exact(lines, x, outcomes) == expected
                exact_cases += 1
    verifier = Path('/workspace/scratch/7f542e06b7cf/official_sources/Inzainos/verifiers/invsqrt/verify_submission_invsqrt.py')
    spec = importlib.util.spec_from_file_location('score6_positive_verifier', verifier)
    module = importlib.util.module_from_spec(spec); sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    xs = np.arange(0, 512, dtype=np.uint64)
    expected = np.array([module.half_turns_to_units(Fraction(3, 32)*(int(x) & 1)
        + Fraction(5, 16)*((int(x) & 1) & (int(x) >> 1 & 1))) for x in xs], dtype=np.uint64)
    receipts, artifacts = [], []
    for name, lines in (('source', old), ('candidate', new)):
        path = args.out/f'{name}.kmx'; path.write_text('\n'.join(lines)+'\n')
        circuit = km.Circuit(path.read_text()); binary = args.out/f'{name}.kmb'
        circuit.to_file(binary, format='kmb')
        artifacts.append(dict(path=str(binary), sha256=sha(binary), Q=circuit.num_qubits,
                              static_toffoli=circuit.operation_statistics().num_toffoli_like))
        xr, scratch = module.validate_registers(circuit, module.ProblemSpecInvSqrt.for_n_p(10))
        for seed in (620261115, 620261116):
            sim = km.Simulator(batch_size=len(xs), counting_operations=True, seed=seed)
            sim.use_same_registers_as(circuit)
            sim.write_across_shots(xr, module.to_bits(xs, 22)); sim.do(circuit)
            phase = np.array([module.half_turns_to_units(sim.read_shot_phase(i)) for i in range(len(xs))], dtype=np.uint64)
            r = dict(name=name, seed=seed, shots=len(xs),
                     phase_failures=int(np.count_nonzero(phase != expected)),
                     input_restore_failures=int(np.count_nonzero(module.from_bits(sim.read_across_shots(xr)) != xs)),
                     dirty_scratch_failures=int(np.any(sim.read_across_shots(scratch), axis=0).sum()),
                     measured_mean_toffoli=sim.operation_statistics().num_toffoli_like/len(xs))
            assert r['phase_failures'] == r['input_restore_failures'] == r['dirty_scratch_failures'] == 0
            receipts.append(r)
    report = dict(status='PASS', synthetic_only=True, benchmark_improvement=False,
        identity='g<=f; alpha*f+beta*g=(alpha+beta)*f-beta*(f XOR g)',
        f='a', g='a*b', relocated_feature='a XOR (a*b)',
        exact_all_branch_cases=exact_cases, native_receipts=receipts, artifacts=artifacts,
        Q_before=24, Q_after=24, static_toffoli_before=4, static_toffoli_after=3,
        generic_rotations_before=2, generic_rotations_after=2,
        phase_preserved_including_global=True, script_sha256=sha(__file__),
        official_helpers_sha256=sha(verifier))
    (args.out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
