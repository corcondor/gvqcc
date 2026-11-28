#!/usr/bin/env python3
"""Connect infinity-CF words to error magnitudes using four continuants.

The classical checker covers the full 70-word diagnostic panel. The native
part is a single coherent continuant transition, not a complete decoder.
Neither part is a 316k repair or a competition submission.
"""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import time


def evaluate(ref, code, x):
    D = ref.D
    N, P, dN, dP = 0, 1, 0, 0
    blocks, end = ref.blocks(code)
    if any(code[end:]):
        raise ValueError('non-exhausted rational expansion')
    for p, q, d in reversed(blocks):
        quotient = list(reversed(code[p:q]))
        a = D.ev(quotient, x)
        da = D.ev([quotient[k] if k % 2 else 0
                   for k in range(1, len(quotient))], x)
        N, P, dN, dP = P, N ^ D.mul(a, P), dP, dN ^ D.mul(a, dP) ^ D.mul(da, P)
    return N, P, dN, dP


def classical_check(ref, source):
    import numpy as np
    D = ref.D
    started = time.perf_counter()
    z = np.load(source/'fixtures'/'hybrid_cases.npz')
    rows = [(list(map(int, s)), m, bool(h))
            for s, m, h in zip(z['S'], z['M'], z['expected'])]
    failures = json.loads((source/'fixtures'/'rotation_receipt.json').read_text())['failure_case_ids']['0']
    for idx in failures:
        syndrome = [D.mul(int(v), D.EXP[-j % 4095]) for j, v in enumerate(z['S'][idx], 1)]
        rows.append((syndrome, np.roll(z['M'][idx], -1), bool(z['expected'][idx])))
    rng = np.random.default_rng(20261128)
    for w in range(1, 36):
        for _ in range(2):
            xs = list(map(int, rng.choice(np.arange(1, 4096), w, replace=False)))
            errors = D.weights_for_n(xs, [1], False)
            rows.append((D.moments(errors), None, None))
    cases = root_checks = nonroot_checks = phase_checks = 0
    for syndrome, mask, expected in rows:
        # Independent Hankel solve obtains the sparse solution; this does not
        # read the quotient decoder's N/D or use an external branch selector.
        _, _, weight, _, errors = D.forward_checked(syndrome)
        code = ref.encode(syndrome)
        assert ref.decode(code) == syndrome
        recovered = {}
        for x, value in errors.items():
            N, P, dN, dP = evaluate(ref, code, x)
            assert P == 0 and dP != 0
            recovered[x] = D.div(N, D.mul(x, dP))
            assert recovered[x] == value
            root_checks += 1
        for x in rng.integers(1, 4096, 4):
            x = int(x)
            N, P, dN, dP = evaluate(ref, code, x)
            assert (P == 0) == (x in errors)
            nonroot_checks += 1
        assert len(recovered) == weight and D.moments(recovered) == syndrome
        if mask is not None:
            phase = bool(sum((int(mask[D.LOG[x]]) & value).bit_count()
                             for x, value in recovered.items()) & 1)
            assert phase == expected
            phase_checks += 1
        cases += 1
    return {'legal_cases': cases, 'root_magnitude_checks': root_checks,
            'additional_position_checks': nonroot_checks,
            'supplied_mask_phase_checks': phase_checks, 'errors': 0,
            'seconds': time.perf_counter()-started,
            'scope': '70-word classical continuants vs independent Hankel decoder; not native oracle'}


def native_transition(ref, degree, x):
    import kickmix as km
    from transport42_lean import gate_tape
    D = ref.D
    b = km.CircuitBuilder()
    A = [b.create_quantum_register(12, f'a{k}') for k in range(degree+1)]
    S = [b.create_quantum_register(12, name) for name in ('N', 'P', 'dN', 'dP')]
    flag = b.create_quantum_register(1, 'active')[0]
    C, T = b.alloc_qubits(12), b.alloc_qubits(12)
    N, P, dN, dP = S
    for left, right in ((N, P), (dN, dP)):
        for a, z in zip(left, right):
            b.cswap(flag, a, z)

    def linear_eval(derivative):
        for k, word in enumerate(A):
            if derivative and k % 2 == 0:
                continue
            coefficient = D.EXP[(D.LOG[x] * (k-int(derivative))) % 4095]
            for j in range(12):
                v = D.mul(1 << j, coefficient)
                for bit in range(12):
                    if v >> bit & 1:
                        b.cx(word[j], C[bit])

    def masked_products(pairs, derivative=False):
        linear_eval(derivative)
        for i in range(12):
            b.ccx(flag, C[i], T[i])
        for left, target in pairs:
            gate_tape(b, T, left, target)
        for i in range(12):
            b.ccx(flag, C[i], T[i])
        linear_eval(derivative)

    masked_products(((N, P), (dN, dP)))
    masked_products(((N, dP),), derivative=True)
    b.free(T)
    b.free(C)
    return b.finish_circuit()


def native_check(ref, output, degree):
    import numpy as np
    import kickmix as km
    D = ref.D
    x = 1234
    circuit = native_transition(ref, degree, x)
    path = output/f'continuant_d{degree}.kmb'
    circuit.to_file(str(path), format='kmb')
    circuit = km.Circuit.from_file(str(path))
    rng = np.random.default_rng(20261128+degree)
    shots = 256
    rows = rng.integers(0, 4096, (shots, degree+5), dtype=np.int64)
    active = rng.integers(0, 2, shots).astype(bool)
    expected = rows.copy()
    for i, row in enumerate(rows):
        a = list(map(int, row[:degree+1]))
        av = D.ev(a, x)
        dav = D.ev([a[k] if k % 2 else 0 for k in range(1, len(a))], x)
        N, P, dN, dP = map(int, row[-4:])
        if active[i]:
            expected[i, -4:] = P, N ^ D.mul(av, P), dP, dN ^ D.mul(av, dP) ^ D.mul(dav, P)
    bits = lambda r: ((r[:, :, None] >> np.arange(12)) & 1).reshape(shots, -1).T.astype(bool)
    inp, tgt = bits(rows), bits(expected)
    data_count = 12*(degree+5)
    q = km.array([km.q(i) for i in range(data_count)])
    flag = km.array([km.q(data_count)])
    anc = km.array([km.q(i) for i in range(data_count+1, circuit.num_qubits)])
    errors = [0, 0, 0]
    for st in range(0, shots, 64):
        en = min(st+64, shots)
        sim = km.Simulator(batch_size=en-st, seed=1234+st, debug_print=False)
        sim.use_same_registers_as(circuit)
        sim.write_across_shots(q, inp[:, st:en])
        sim.write_across_shots(flag, active[None, st:en])
        sim.do(circuit)
        errors[0] += int(((sim.read_across_shots(q) ^ tgt[:, st:en]).any(0)
                         | (sim.read_across_shots(flag)[0] ^ active[st:en])).sum())
        errors[1] += int(sim.read_across_shots(anc).any(0).sum())
        errors[2] += int(sim.read_phase_flipped_across_shots().sum())
    if any(errors):
        raise AssertionError(errors)
    return {'degree': degree, 'native_shots': shots, 'value_dirty_phase_errors': errors,
            'qubits': circuit.num_qubits, 'ops': len(circuit),
            'paid': int(circuit.operation_statistics().num_toffoli_like),
            'sha256': hashlib.file_digest(path.open('rb'), 'sha256').hexdigest(),
            'scope': 'one controlled quotient transition on arbitrary states; not DQI oracle'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--kit', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    a = p.parse_args()
    os.environ['DQI_KIT'] = str(a.kit.resolve())
    sys.path.insert(0, str(a.source.resolve()))
    ref = importlib.import_module('infinity_cf')
    a.output_dir.mkdir(parents=True, exist_ok=True)
    results = {'classical': classical_check(ref, a.source),
               'native': [native_check(ref, a.output_dir, d) for d in (1, 7, 35)],
               'submission_performed': False, 'full_native_oracle': False}
    (a.output_dir/'continuant_receipt.json').write_text(json.dumps(results, indent=2)+'\n')
    print(json.dumps(results, indent=2), flush=True)


if __name__ == '__main__':
    main()
