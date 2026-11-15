#!/usr/bin/env python3
"""Exact phase-block extraction and parity resynthesis, with official costing.

The algorithm is deliberately limited to explicitly closed, measured phase
blocks. It checks every local computational basis column and every HMR outcome
before replacing the nonlinear block by a rational Walsh phase polynomial.
It does not assume that a small Clifford+T drawing earns the same competition
cost, and does not mutate the accepted invsqrt file.
"""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import re
import sys
import time

from score2_invsqrt_phase_relocation import PANEL

BASE = Path(__file__).parent
SOURCE = BASE / 'score3_invsqrt_cache.kmx'
PIN = 'd431f212c7da02418429c2883dcdf4e3a90c9124ab2409c999efe0a5c7c037a8'
VERIFIER = Path('/workspace/scratch/7f542e06b7cf/official_sources/Inzainos/verifiers/invsqrt/verify_submission_invsqrt.py')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def wires(line):
    return tuple(map(int, re.findall(r'\bq(\d+)\b', line)))


def decimal(angle):
    angle %= 2
    n, d = angle.numerator, angle.denominator
    assert d & (d - 1) == 0
    k = d.bit_length() - 1
    if not k:
        return str(n)
    digits = str(n * 5**k).rjust(k + 1, '0')
    return (digits[:-k] + '.' + digits[-k:]).rstrip('0').rstrip('.')


def classify(angle):
    if angle % Fraction(1, 2) == 0:
        return 'clifford'
    if angle % Fraction(1, 4) == 0:
        return 't'
    return 'rotation'


def exact_run(lines, initial, outcomes):
    q = list(initial)
    b, stack, used, phase = {}, [], 0, Fraction(0)
    for line in lines:
        op = line.split()[0]
        if op == 'PUSH_CONDITION':
            bit = int(re.findall(r'\bb(\d+)\b', line)[0])
            stack.append(b[bit] and all(stack))
            continue
        if op == 'POP_CONDITION':
            stack.pop()
            continue
        if not all(stack):
            continue
        if ' if ' in line:
            bit = int(re.findall(r'\bb(\d+)\b', line)[-1])
            if not b[bit]:
                continue
        w = wires(line)
        if op == 'X':
            q[w[0]] ^= 1
        elif op == 'CX':
            q[w[1]] ^= q[w[0]]
        elif op == 'CCX':
            q[w[2]] ^= q[w[0]] & q[w[1]]
        elif op == 'SWAP':
            q[w[0]], q[w[1]] = q[w[1]], q[w[0]]
        elif op == 'CSWAP':
            if q[w[0]]:
                q[w[1]], q[w[2]] = q[w[2]], q[w[1]]
        elif op == 'Z_POW':
            phase += Fraction(line.split()[2]) * q[w[0]]
        elif op in ('Z', 'CZ', 'CCZ'):
            phase += math.prod(q[v] for v in w)
        elif op == 'NEG':
            phase += 1
        elif op == 'HMR':
            bit = int(re.findall(r'\bb(\d+)\b', line)[0])
            m = outcomes[used]
            used += 1
            b[bit] = m
            phase += m * q[w[0]]
            q[w[0]] = 0
        elif op in ('APPEND_TO_REGISTER', 'REGISTER'):
            pass
        else:
            raise ValueError(('unsupported local operation', line))
    assert not stack and used == len(outcomes)
    return q, phase % 2


def extract(lines, scratch):
    involved = sorted({q for line in lines for q in wires(line)})
    data = sorted(set(involved) - set(scratch))
    assert len(data) <= 12
    measurements = sum(line.startswith('HMR ') for line in lines)
    table, checked = [], 0
    for x in range(1 << len(data)):
        initial = [0] * (max(involved) + 1)
        for j, q in enumerate(data):
            initial[q] = x >> j & 1
        phase = None
        for outcomes in itertools.product((0, 1), repeat=measurements):
            final, value = exact_run(lines, initial, outcomes)
            assert final == initial, ('not closed', x, outcomes, initial, final)
            if phase is None:
                phase = value
            assert phase == value, ('outcome-dependent phase', x, outcomes)
            checked += 1
        table.append(phase)
    return data, table, checked, measurements


def walsh(table):
    """Return f(0) and exact parity coefficients of this chosen rational lift."""
    h = list(table)
    step = 1
    while step < len(h):
        for k in range(0, len(h), 2 * step):
            for j in range(step):
                a, b = h[k + j], h[k + j + step]
                h[k + j], h[k + j + step] = a + b, a - b
        step *= 2
    coefficients = [(s, (-2 * v / len(table)) % 2)
                    for s, v in enumerate(h) if s and v % len(table)]
    coefficients = [(s, a) for s, a in coefficients if a]
    for x, expected in enumerate(table):
        actual = table[0] + sum(a * ((s & x).bit_count() & 1) for s, a in coefficients)
        assert actual % 2 == expected
    return table[0], coefficients


def generic_lower_bound(num_data, coefficients):
    """A modular-lift obstruction to making a parity angle Clifford or T.

    Two exact phase tables (half-turn units) differ by 2*z[x]. Their nonzero
    parity coefficients differ by (4/2**n)*integer. If a coefficient does not
    lie in the lattice generated by this modulus and 1/4, no integer lift of
    the phase table can make that parity a Clifford/T angle. This gives a
    lower bound, not a claim that all admissible coefficient changes can be
    realized independently.
    """
    modulus = Fraction(4, 1 << num_data)
    lattice = Fraction(1, 1 << max(num_data - 2, 2))
    forced = [mask for mask, angle in coefficients if angle % lattice]
    return dict(lift_modulus_half_turns=str(modulus),
                clifford_t_membership_lattice_half_turns=str(lattice),
                forced_generic_parities=forced,
                minimum_generic_rotation_count=len(forced))


def emit(data, constant, coefficients):
    assert constant == 0, 'This emitter does not add a nonzero constant phase.'
    lines = []
    for mask, angle in coefficients:
        active = [q for j, q in enumerate(data) if mask >> j & 1]
        pivot = active[0]
        network = [f'CX q{q} q{pivot}' for q in active[1:]]
        lines.extend(network)
        lines.append(f'Z_POW q{pivot} {decimal(angle)}')
        lines.extend(reversed(network))
    return lines


def tariff(lines):
    counts = Counter(line.split()[0] for line in lines)
    rotations = Counter(classify(Fraction(line.split()[2]))
                        for line in lines if line.startswith('Z_POW '))
    return dict(toffoli=sum(counts[g] for g in ('CCX', 'CCZ', 'CSWAP')),
                t=rotations['t'], generic=rotations['rotation'],
                clifford_phases=rotations['clifford'], cx=counts['CX'])


def clean_entry_evidence(lines, start, scratch):
    last = {}
    depth = 0
    for i, line in enumerate(lines[:start]):
        op = line.split()[0]
        if op == 'PUSH_CONDITION':
            depth += 1
        elif op == 'POP_CONDITION':
            depth -= 1
        qs = wires(line)
        written = (qs[-1:] if op in ('X', 'CX', 'CCX', 'HMR', 'R') else
                   qs if op == 'SWAP' else qs[1:] if op == 'CSWAP' else ())
        for q in set(written) & set(scratch):
            last[q] = dict(line=i + 1, instruction=line, depth=depth)
    for q in scratch:
        assert q in last and last[q]['instruction'].startswith('HMR ')
        assert last[q]['depth'] == 0 and ' if ' not in last[q]['instruction']
    return {str(q):last[q] for q in scratch}


def full_cost(counts, old_counts, receipt):
    """Keep phase and worst-case residual identical; recompute epsilon split."""
    new_n = receipt['rotation_count'] - old_counts['generic'] + counts['generic']
    new_t = receipt['t_count'] - old_counts['t'] + counts['t']
    new_mean = receipt['toffoli_count'] - old_counts['toffoli'] + counts['toffoli']
    # The residual error budget is unchanged by the exact phase substitution.
    eps = receipt['rotation_eps'] * receipt['rotation_count'] / new_n if new_n else None
    rotation_cost = new_n * (0.56 * math.log2(1 / eps) + 5.3) if new_n else 0
    return receipt['num_qubits'] * (new_mean + (new_t + rotation_cost) / 4)


def native_control(out):
    import numpy as np
    import kickmix as km
    spec = importlib.util.spec_from_file_location('score7_phase_verifier', VERIFIER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    old = ['CCX q0 q1 q22', 'Z_POW q22 0.5', 'HMR q22 b0', 'CZ q0 q1 if b0']
    data, table, cases, _ = extract(old, [22])
    constant, coefficients = walsh(table)
    new = emit(data, constant, coefficients)
    # Keep the same circuit width and a fresh random measurement output so
    # that this is a complete local quantum instrument, not postselection.
    new += ['HMR q22 b0']
    assert tariff(old)['toffoli'] == 1 and tariff(new)['t'] == 3
    new_cases = 0
    for x in range(4):
        initial = [0] * 23
        initial[0], initial[1] = x & 1, x >> 1
        for m in (0, 1):
            q, phase = exact_run(new, initial, (m,))
            assert q == initial and phase == table[x]
            new_cases += 1
    header = [f'APPEND_TO_REGISTER q{j} r0' for j in range(22)] + ['REGISTER r0 "x"']
    xs = np.arange(512, dtype=np.uint64)
    expected = np.array([module.half_turns_to_units(Fraction(1, 2) * (int(x) & 1) * (int(x) >> 1 & 1))
                         for x in xs], dtype=np.uint64)
    receipts, artifacts = [], []
    for name, body in (('source', old), ('candidate', new)):
        kmx = out / f'positive_{name}.kmx'
        kmx.write_text('\n'.join(header + body) + '\n')
        circuit = km.Circuit(kmx.read_text())
        kmb = out / f'positive_{name}.kmb'
        circuit.to_file(kmb, format='kmb')
        xr, scratch = module.validate_registers(circuit, module.ProblemSpecInvSqrt.for_n_p(10))
        for seed in (720261115, 720261116):
            sim = km.Simulator(batch_size=len(xs), counting_operations=True, seed=seed)
            sim.use_same_registers_as(circuit)
            sim.write_across_shots(xr, module.to_bits(xs, 22))
            sim.do(circuit)
            phase = np.array([module.half_turns_to_units(sim.read_shot_phase(i))
                              for i in range(len(xs))], dtype=np.uint64)
            row = dict(name=name, seed=seed, shots=len(xs),
                       phase_errors=int(np.count_nonzero(phase != expected)),
                       value_errors=int(np.count_nonzero(module.from_bits(sim.read_across_shots(xr)) != xs)),
                       scratch_errors=int(np.any(sim.read_across_shots(scratch), axis=0).sum()),
                       mean_toffoli=sim.operation_statistics().num_toffoli_like / len(xs))
            assert row['phase_errors'] == row['value_errors'] == row['scratch_errors'] == 0
            receipts.append(row)
        artifacts += [dict(path=str(p), bytes=p.stat().st_size, sha256=sha(p)) for p in (kmx, kmb)]
    return dict(synthetic_only=True, status='PASS', exact_source_branch_cases=cases,
                exact_candidate_branch_cases=new_cases, native_receipts=receipts,
                cost_before=1.0, cost_after=0.75, Q_before=23, Q_after=23,
                identity='(pi/2)*ab = (pi/4)*a + (pi/4)*b - (pi/4)*(a XOR b)',
                artifacts=artifacts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    began = time.monotonic()
    assert sha(SOURCE) == PIN
    lines = SOURCE.read_text().splitlines()
    receipt = json.loads((BASE / 'score3_invsqrt_full_verification.json').read_text())
    blocks, total_cases = [], 0
    for item in PANEL:
        lo, hi = item['start'] + 4, item['end'] + 4
        body = lines[lo:hi]
        scratch = sorted({wires(line)[0] for line in body if line.startswith('HMR ')})
        clean = clean_entry_evidence(lines, lo, scratch)
        data, table, cases, measurements = extract(body, scratch)
        constant, coefficients = walsh(table)
        candidate = emit(data, constant, coefficients)
        # Retain the same random classical output bits in the same order.
        # The extracted branch phase is independent of all outcomes, so moving
        # these HMRs onto reset scratch preserves the complete local instrument.
        candidate += [line for line in body if line.startswith('HMR ')]
        before, after = tariff(body), tariff(candidate)
        bound = generic_lower_bound(len(data), coefficients)
        optimistic = dict(toffoli=0, t=0, generic=bound['minimum_generic_rotation_count'])
        total_cases += cases
        for x in range(1 << len(data)):
            initial = [0] * (max(data + scratch) + 1)
            for j, q in enumerate(data):
                initial[q] = x >> j & 1
            for outcomes in itertools.product((0, 1), repeat=measurements):
                final, phase = exact_run(candidate, initial, outcomes)
                assert final == initial and phase == table[x]
        estimated = full_cost(after, before, receipt)
        row = dict(name=item['name'], lines_1_based=[lo + 1, hi],
                   data_wires=data, clean_scratch=scratch, measurements=measurements,
                   clean_entry_last_write_evidence=clean,
                   same_measurement_output_bits_and_order=True,
                   exact_all_branch_cases=cases,
                   original=before, parity_candidate=after,
                   parity_modular_lower_bound=bound,
                   modeled_Q46_full_cost=estimated,
                   modeled_cost_change=estimated - receipt['score'],
                   optimistic_modular_cost_lower_bound_Q46=full_cost(optimistic, before, receipt),
                   beneficial_under_fixed_Q_tariff=estimated < receipt['score'],
                   constant_half_turns=str(constant),
                   coefficients=[dict(parity_mask=m, half_turns=str(a)) for m, a in coefficients])
        blocks.append(row)
    control = native_control(args.out)
    report = dict(status='COMPLETE', algorithm='exact local phase extraction + rational Walsh parity resynthesis',
                  source_path=str(SOURCE), source_sha256=PIN,
                  baseline_kmb_sha256=receipt['circuit_sha256'],
                  official_verifier_sha256=sha(VERIFIER),
                  baseline_verified_cost=receipt['score'],
                  phase_blocks=len(blocks), total_exact_all_branch_cases=total_cases,
                  beneficial_blocks=sum(b['beneficial_under_fixed_Q_tariff'] for b in blocks),
                  blocks=blocks, positive_control=control,
                  candidate_emitted=False, new_benchmark_gain=0,
                  limitations=['candidate uses canonical rational Walsh lift; modular bound covers every integer lift on the same independent data wires',
                               'eight pre-existing closed phase blocks; arbitrary global resynthesis not exhausted',
                               'cost comparison holds Q46 fixed and unchanged residual error; no full verifier run'],
                  seconds=time.monotonic()-began, script_sha256=sha(__file__))
    (args.out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('blocks','positive_control')}, indent=2))
    for row in blocks:
        print(json.dumps({k:row[k] for k in ('name','original','parity_candidate','modeled_cost_change')}))


if __name__ == '__main__':
    main()
