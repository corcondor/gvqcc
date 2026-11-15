#!/usr/bin/env python3
"""Construct and check the child-norm pebble, without changing source files."""
from pathlib import Path
from types import SimpleNamespace
import argparse
import functools
import hashlib
import json
import time

import numpy as np
import kickmix as km
import outcome_dqi_chart_third_norm as Chart
import outcome_dqi_chart_inverse_norm as Original
import score5_dqi_width_inverse as Pebble


def bits(values, width):
    return ((np.asarray(values, dtype=np.uint32)[None, :] >>
             np.arange(width, dtype=np.uint32)[:, None]) & 1).astype(bool)


def gf24_inverse(value):
    if value == 0:
        return 0
    field = km.GF2Field(12)
    left, right = value & 4095, value >> 12
    norm = field.mul(left, left) ^ field.mul(left, right) ^ field.mul(
        2048, field.mul(right, right))
    reciprocal = field.invert(norm)
    return field.mul(left ^ right, reciprocal) | (field.mul(right, reciprocal) << 12)


def adapter(borrow):
    if not borrow:
        return Original
    return SimpleNamespace(
        inverse_prefix_with_bank=functools.partial(Pebble.inverse_prefix_with_bank, borrow_bits=borrow),
        inverse_return_with_bank=functools.partial(Pebble.inverse_return_with_bank, borrow_bits=borrow))


def single_pair(module, out, label):
    b = km.CircuitBuilder()
    b.set_max_qubits(73)
    source = b.create_quantum_register(24, 'source')
    bank = b.create_quantum_register(24, 'bank')
    flag = b.create_quantum_register(1, 'flag')
    probe = b.create_classical_register(24, 'probe')
    record = module.inverse_prefix_with_bank(b, source, bank, zero_flag=flag[0])
    prefix_len = len(b.finish_circuit())
    b.cz(probe, source)
    b.ccz(source[0], source[7], source[18])
    module.inverse_return_with_bank(b, source, bank, record, zero_flag=flag[0])
    circuit = b.finish_circuit()
    path = out / f'{label}_pair.kmb'
    circuit.to_file(path, format='kmb')
    return circuit, dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                         Q=circuit.num_qubits, T=circuit.operation_statistics().num_toffoli_like,
                         prefix_ops=prefix_len, operations=len(circuit),
                         prefix_T=record.prefix_static_T)


def chart_pair(module, out, label):
    b = km.CircuitBuilder()
    b.set_max_qubits(889)
    data = b.create_quantum_register(840, 'data')
    bank = b.create_quantum_register(24, 'bank')
    flag = b.alloc_qubits(1)
    old = Chart.Norm
    Chart.Norm = module
    try:
        record = Chart.emit_prefix(b, (data[:24], data[24:48]), data[48:72], bank, flag[0])
        prefix_ops = len(b.finish_circuit())
        masks = [[int(str(bit)[1:]) for bit in rec.child_mask] for rec in record.inverses]
        b.free(flag)
        Chart.emit_closing(b, (data[:24], data[24:48]), data[48:72], bank, record)
    finally:
        Chart.Norm = old
    circuit = b.finish_circuit()
    path = out / f'{label}_chart.kmb'
    circuit.to_file(path, format='kmb')
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                Q=circuit.num_qubits, T=circuit.operation_statistics().num_toffoli_like,
                prefix_ops=prefix_ops, operations=len(circuit), bits=circuit.num_bits,
                saved_child_masks=masks)


def scalar_proof():
    field = km.GF2Field(6)
    delta = Pebble.quadratic_basis(12)['delta']
    left_columns, right_columns = Pebble.norm_columns(6, delta)
    masks = [sum(((field.mul(1 << i, 1 << j) & 1) << j) for j in range(6))
             for i in range(6)]
    failures = 0
    for left in range(64):
        for right in range(64):
            value = sum((((left >> i) & 1) * ((right & masks[i]).bit_count() & 1))
                        for i in range(6)) & 1
            value ^= sum(((left >> i) & 1) * (left_columns[i] & 1) for i in range(6)) & 1
            value ^= sum(((right >> i) & 1) * (right_columns[i] & 1) for i in range(6)) & 1
            actual = (field.mul(left, left) ^ field.mul(left, right)
                      ^ field.mul(delta, field.mul(right, right))) & 1
            failures += value != actual
    assert not failures
    assert all(masks)
    return dict(status='PASS', input_pairs=4096, errors=failures,
                selected_polynomial_bit=0, product_row_masks=masks,
                added_CCX_per_toggle=6,
                identity='N(L,R) = L^2 + L*R + delta*R^2 in GF(64)')


def simulate_pair(circuit, values, flags, probes, seed):
    sim = km.Simulator(batch_size=len(values), seed=seed, counting_operations=True)
    sim.use_same_registers_as(circuit)
    sim.write_across_shots(circuit.register_data['source'], bits(values, 24))
    sim.write_across_shots(circuit.register_data['flag'], bits(flags, 1))
    sim.write_across_shots(circuit.register_data['probe'], bits(probes, 24))
    sim.do(circuit)
    inverses = [gf24_inverse(int(x)) for x in values]
    phase = np.asarray([((int(x) & int(m)).bit_count() & 1) ^
                        ((int(x) >> 0 & 1) & (int(x) >> 7 & 1) & (int(x) >> 18 & 1))
                        for x, m in zip(inverses, probes)], dtype=bool)
    source_errors = int(np.any(sim.read_across_shots(circuit.register_data['source'])
                               != bits(values, 24), axis=0).sum())
    flag_errors = int(np.any(sim.read_across_shots(circuit.register_data['flag'])
                             != bits(flags, 1), axis=0).sum())
    garbage_ids = [km.q(q) for q in [*range(24, 48), *range(49, circuit.num_qubits)]]
    garbage_errors = int(np.any(sim.read_across_shots(garbage_ids), axis=0).sum())
    phase_errors = int((sim.read_phase_flipped_across_shots() != phase).sum())
    assert source_errors == flag_errors == garbage_errors == phase_errors == 0
    return dict(seed=seed, shots=len(values), source_errors=source_errors,
                flag_errors=flag_errors, garbage_errors=garbage_errors, phase_errors=phase_errors,
                mean_T=sim.operation_statistics().num_toffoli_like / len(values))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    # Fixed public fixture; never selected from whole-decoder failure inputs.
    rng = np.random.default_rng(20261115051)
    values = np.asarray([0, 1, 4095, 4096, (1 << 24)-1,
                         *rng.integers(0, 1 << 24, 507)], dtype=np.uint32)
    flags = np.arange(len(values), dtype=np.uint32) & 1
    probes = rng.integers(0, 1 << 24, len(values), dtype=np.uint32)
    result = dict(status='IN_PROGRESS', scalar_identity=scalar_proof(), variants=[])
    for borrow in (0, 1, 6):
        module = adapter(borrow)
        label = f'borrow{borrow}'
        circuit, row = single_pair(module, args.out, label)
        row['borrow_bits'] = borrow
        row['native_tests'] = [simulate_pair(circuit, values, flags, probes, seed)
                               for seed in (251, 1251)]
        row['chart_template'] = chart_pair(module, args.out, label)
        result['variants'].append(row)
        print(json.dumps(row), flush=True)
    base, one, six = result['variants']
    assert [row['Q'] for row in result['variants']] == [73, 72, 67]
    assert one['T'] - base['T'] == 24
    assert six['T'] - base['T'] == 60
    assert [row['chart_template']['Q'] for row in result['variants']] == [889, 888, 883]
    assert one['chart_template']['T'] - base['chart_template']['T'] == 72
    assert six['chart_template']['T'] - base['chart_template']['T'] == 180
    result.update(status='PASS_SOURCE_COMPONENT_ONLY', elapsed_seconds=time.monotonic()-started,
                  proof_scope='Exact coherent child-norm erase/restore identity plus source-local native checks; not yet a whole DQI width claim.',
                  source_sha256={str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in (Path(__file__), Path(Pebble.__file__),
                                              Path(Original.__file__), Path(Chart.__file__))})
    path = args.out / 'component.json'
    path.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(status=result['status'], report=str(path), seconds=result['elapsed_seconds'])))


if __name__ == '__main__':
    main()
