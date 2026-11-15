#!/usr/bin/env python3
"""Independent polynomial oracle and native component checks for the new chart."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import time

import numpy as np
import kickmix as km
import outcome_dqi_chart_third_norm as Candidate

ROOT = Path(__file__).resolve().parent
SOURCE = Candidate.WORK / 'night_c27/census/reference.py'
spec = importlib.util.spec_from_file_location('outcome_chart_reference', SOURCE)
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)
DELTA = 2048


def unpack(x):
    return x & 4095, x >> 12


def pack(x):
    return x[0] | (x[1] << 12)


def mul(a, b):
    return pack(R.quadratic_mul(unpack(a), unpack(b), DELTA))


def inv(x):
    return pack(R.quadratic_div((1, 0), unpack(x), DELTA)) if x else 0


def view(coefficient, index=2):
    a, b = unpack(coefficient)
    return (a ^ R.mul(2 * index, b)) | (b << 12)


def oracle(A, B, Y):
    numerator = mul(18, 1 ^ mul(A, Y))
    denominator = mul(20, Y) ^ mul(B, 1 ^ mul(A, Y))
    assert numerator or denominator
    return (mul(numerator, inv(denominator)), 0) if denominator else (0, 1)


def projective(A, B, Y):
    a, f = Y, 0
    for kind, parameter in [('inv', 0), ('add', A), ('inv', 0),
                            ('scale', 20), ('add', B),
                            ('scale', R.INV[18]), ('inv', 0)]:
        if kind == 'inv':
            f ^= a == 0
            a = inv(a)
        elif kind == 'add':
            if not f:
                a ^= parameter
        else:
            a = mul(a, parameter)
        assert not f or a == 0
    return a, int(f)


def old_chart(A, B, Y):
    x = inv(Y)
    if Y:
        x ^= A
    x = mul(20, inv(x)) ^ B
    return inv(mul(R.INV[18], x))


def physical_records():
    cases = json.loads((ROOT / 'score_loss_v2_report.json').read_text())[
        'known_regression_classification']['records']
    output = []
    for case in cases:
        n, d = R.physical_pair(case['roots'], case['values'])
        raw = [R.quadratic_div(R.quadratic_remainder(n, c),
                              R.quadratic_remainder(d, c), c)
               for c in R.KAPPAS]
        trace, heads = [], []
        for i in range(len(case['roots'])):
            nr = R.quadratic_remainder(n, R.KAPPAS[i])
            dr = R.quadratic_remainder(d, R.KAPPAS[i])
            row = {'node': i, 'N': list(nr), 'D': list(dr),
                   'numerator_degree': len(n)-1, 'denominator_degree': len(d)-1}
            trace.append(row)
            if nr == (0, 0):
                row['stop'] = 'zero numerator: infinity head remains unsupported'
                break
            head = R.quadratic_div(dr, nr, R.KAPPAS[i])
            row['head'] = list(head)
            heads.append(head)
            nxt, remainder = R.divrem(R.add(d, R.product(head, n)), R.QUADRATICS[i])
            assert not remainder
            n, d = nxt, n
        A, B = view(pack(heads[0])), view(pack(heads[1]))
        Y = view(pack(raw[2]))
        expected = oracle(A, B, Y)
        assert expected == projective(A, B, Y)
        output.append({'case_sha256': case['case_sha256'], 'weight': len(case['roots']),
                       'trace': trace, 'third_input': {'head0_coefficient': pack(heads[0]),
                       'head1_coefficient': pack(heads[1]), 'rawY_common': Y,
                       'A_common': A, 'B_common': B}, 'third_expected': expected,
                       'old_third_result': old_chart(A, B, Y),
                       'allowing_zero_heads_reaches_terminal': not n and len(d)==1 and bool(d[0]),
                       'terminal': {'N': n, 'D': d}})
    return output


def bits(values, width=24):
    return ((np.asarray(values, dtype=np.uint32)[None, :] >>
             np.arange(width, dtype=np.uint32)[:, None]) & 1).astype(bool)


def build():
    b = km.CircuitBuilder()
    b.set_max_qubits(889)
    # Match the production quantum-wire roles. Native tests include all unused inputs.
    data = b.create_quantum_register(840, 'data')
    heads = (data[:24], data[24:48])
    current = data[48:72]
    bank = b.create_quantum_register(24, 'bank')
    flag = b.alloc_qubits(1)
    probe = b.create_classical_register(24, 'probe')
    rec = Candidate.emit_prefix(b, heads, current, bank, flag[0])
    prefix = b.finish_circuit()
    prefix.to_file(ROOT/'outcome_dqi_chart_norm_component_prefix.kmb', format='kmb')
    b.cz(probe, current)
    b.ccz(current[0], current[7], current[18])
    b.free(flag)
    Candidate.emit_closing(b, heads, current, bank, rec)
    pair = b.finish_circuit()
    pair.to_file(ROOT/'outcome_dqi_chart_norm_component_pair.kmb', format='kmb')
    return prefix, pair


def main():
    start = time.monotonic()
    physical = physical_records()
    rng = np.random.default_rng(20261115017)
    tuples = []
    # Public deterministic component corpus: independent generic triples and
    # algebraically constructed zero/pole cases, not leaderboard sample tuning.
    for _ in range(1024):
        ca, cb = map(int, rng.integers(1, 1 << 24, 2, dtype=np.uint32))
        A, B = view(ca), view(cb)
        for Y in (int(rng.integers(0, 1 << 24)), 0, inv(A)):
            tuples.append((ca, cb, Y))
        denominator = 20 ^ mul(A, B)
        if denominator:
            tuples.append((ca, cb, mul(B, inv(denominator))))
    for row in physical:
        x = row['third_input']
        tuples.append((x['head0_coefficient'], x['head1_coefficient'], x['rawY_common']))
    outcomes = [oracle(view(a), view(b), y) for a, b, y in tuples]
    assert all(projective(view(a), view(b), y) == out
               for (a, b, y), out in zip(tuples, outcomes))
    admitted = [(v, out[0]) for v, out in zip(tuples, outcomes) if out[1] == 0]
    prefix, pair = build()
    inputs = np.array([v for v, _ in admitted], dtype=np.uint32)
    expected = np.array([out for _, out in admitted], dtype=np.uint32)
    data_bits = np.zeros((840, len(admitted)), dtype=bool)
    for offset, values in zip((0, 24, 48), inputs.T):
        data_bits[offset:offset+24] = bits(values)
    mask = rng.integers(0, 1 << 24, len(admitted), dtype=np.uint32)
    phase = np.array([(int(m & e).bit_count() & 1) ^
                      ((int(e) >> 0 & 1) & (int(e) >> 7 & 1) & (int(e) >> 18 & 1))
                      for m, e in zip(mask, expected)], dtype=bool)
    records = []
    for seed in (147, 1147, 2147, 3147):
        for label, c in (('prefix', prefix), ('roundtrip_phase_probe', pair)):
            sim = km.Simulator(batch_size=len(admitted), seed=seed, counting_operations=True)
            sim.use_same_registers_as(c)
            sim.write_across_shots(c.register_data['data'], data_bits)
            sim.write_across_shots(c.register_data['probe'], bits(mask))
            sim.do(c)
            wanted = data_bits.copy()
            if label == 'prefix':
                wanted[48:72] = bits(expected)
            actual = sim.read_across_shots(c.register_data['data'])
            garbage = sim.read_across_shots([km.q(i) for i in range(840, c.num_qubits)])
            value_errors = (np.any(actual != wanted, axis=0) | np.any(garbage, axis=0))
            phase_errors = (sim.read_phase_flipped_across_shots() != phase) if label != 'prefix' else None
            records.append({'seed': seed, 'kind': label, 'shots': len(admitted),
                            'value_errors': int(value_errors.sum()),
                            'phase_errors': None if phase_errors is None else int(phase_errors.sum()),
                            'mean_T': sim.operation_statistics().num_toffoli_like/len(admitted)})
            assert not value_errors.any()
            if phase_errors is not None:
                assert not phase_errors.any()
    result = {'status': 'PASS_CLASSICAL_AND_NATIVE_COMPONENT_ONLY', 'physical_records': physical,
              'classical_cases': len(tuples), 'finite_output_native_cases': len(admitted),
              'infinity_output_cases_excluded_from_whole_decoder_contract': len(tuples)-len(admitted),
              'prefix_static_T': prefix.operation_statistics().num_toffoli_like,
              'pair_static_T_including_one_probe_CCZ': pair.operation_statistics().num_toffoli_like,
              'peak_Q': pair.num_qubits, 'tests': records, 'elapsed_seconds': time.monotonic()-start,
              'proof': 'Canonical P1 representation (a,0) for finitea and(0,1) for infinity. inv0(a) withf XOR[a=0] swaps0/infinity. Public nonzero scaling preservesf. Addition only onf=0 preservesinfinity. Their composition is the exact matrix-derived Mobius map. Finite-output promise makes the only released boundaryflag zero. Matched inverse masks are paid on exact inverse operands in reverse order.',
              'scope': 'Extends the thirdpivot tozero queriedD withN nonzero. Doesnot repair allzeroN cases or any other full-decoder failure. No completeKMB patch or officialverification implied.',
              'source_sha256': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                                for path in (Path(__file__), Path(Candidate.__file__), Path(Candidate.Norm.__file__), Path(Candidate.Norm.Cubic.__file__), Path(Candidate.Original.__file__), SOURCE)}}
    (ROOT/'outcome_dqi_chart_norm_component_report.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('physical_records','source_sha256')}, indent=2))


if __name__ == '__main__':
    main()
