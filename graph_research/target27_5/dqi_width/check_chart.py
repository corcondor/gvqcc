"""Verify the complete width-877 third-pivot chart against the independent scalar oracle."""
import json
import sys

import numpy as np
import kickmix as km

import outcome_dqi_chart_check_norm as oracle
import outcome_dqi_chart_third_norm as chart
import borrow_inverse


def build():
    builder = km.CircuitBuilder()
    data = builder.create_quantum_register(840, "data")
    bank = builder.create_quantum_register(24, "bank")
    probe = builder.create_classical_register(24, "probe")
    flag = builder.alloc_qubits(1)
    heads, current = (data[:24], data[24:48]), data[48:72]
    original = chart.Norm
    chart.Norm = borrow_inverse
    try:
        record = chart.emit_prefix(builder, heads, current, bank, flag[0])
        prefix = builder.finish_circuit()
        builder.cz(probe, current)
        builder.ccz(current[0], current[7], current[18])
        builder.free(flag)
        chart.emit_closing(builder, heads, current, bank, record)
        return prefix, builder.finish_circuit()
    finally:
        chart.Norm = original


def main():
    rng = np.random.default_rng(20261115017)
    fixtures = []
    for _ in range(512):
        a, b = map(int, rng.integers(1, 1 << 24, 2))
        for y in (int(rng.integers(0, 1 << 24)), 0, oracle.inv(oracle.view(a))):
            expected, is_infinite = oracle.oracle(oracle.view(a), oracle.view(b), y)
            if not is_infinite:
                fixtures.append((a,b,y,expected))
    count = len(fixtures)
    inputs = np.array(fixtures, dtype=np.uint32)
    words = rng.integers(0, 2, (840, count), dtype=np.uint8).astype(bool)
    for offset, values in zip((0, 24, 48), inputs.T[:3]):
        words[offset:offset+24] = oracle.bits(values)
    wanted_prefix = words.copy()
    wanted_prefix[48:72] = oracle.bits(inputs[:, 3])
    mask = rng.integers(0, 1 << 24, count, dtype=np.uint32)
    phase = np.array([(int(m & e).bit_count() & 1) ^
                      ((int(e) >> 0 & 1) & (int(e) >> 7 & 1) & (int(e) >> 18 & 1))
                      for m, e in zip(mask, inputs[:, 3])], dtype=bool)
    prefix, pair = build()
    records = []
    for seed in (147, 1147):
        for label, circuit, expected in (("prefix", prefix, wanted_prefix), ("pair", pair, words)):
            sim = km.Simulator(batch_size=count, seed=seed, counting_operations=True)
            sim.use_same_registers_as(circuit)
            sim.write_across_shots(circuit.register_data["data"], words)
            sim.write_across_shots(circuit.register_data["probe"], oracle.bits(mask))
            sim.do(circuit)
            assert np.array_equal(sim.read_across_shots(circuit.register_data["data"]), expected)
            assert not sim.read_across_shots([km.q(i) for i in range(840, circuit.num_qubits)]).any()
            if label == "pair":
                assert np.array_equal(sim.read_phase_flipped_across_shots(), phase)
            records.append(dict(label=label, seed=seed, shots=count, Q=circuit.num_qubits,
                                value_errors=0, phase_errors=0 if label == "pair" else None,
                                mean_T=sim.operation_statistics().num_toffoli_like/count))
    json.dump(records, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
