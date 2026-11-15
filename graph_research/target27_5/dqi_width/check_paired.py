"""Verify the changed paired division's exact prefix and inherited closing contracts."""
import argparse
import json
from pathlib import Path
import sys

import kickmix as km
import numpy as np

import outcome_dqi_chart_third_norm as preceding

sys.path.insert(0, str(preceding.WORK / "after_c5/converter_width"))
import gauge_park_paired as original
from gauge_park_lender import GaugeLender
import paired_divide as new
from tower_inverse import quadratic_basis


def matrix(values, n=12):
    return (((values[None, :] >> np.arange(n)[:, None]) & 1).astype(bool))


def read_word(sim, wires):
    return (sim.read_across_shots(wires).T * (1 << np.arange(12))).sum(axis=1)


def build(emitter, prefix_only):
    builder = km.CircuitBuilder()
    factor = builder.create_quantum_register(12, "factor")
    words = [builder.create_quantum_register(12, f"word{i}") for i in range(2)]
    flag = builder.create_quantum_register(1, "untouched")
    probe = builder.create_classical_register(12, "probe")
    debt = builder.create_classical_register(12, "debt")
    lender = GaugeLender(builder, flag[0])
    mask = emitter.divide_prefix(lender, words, factor)
    if prefix_only:
        builder.cx(mask, debt)
        builder.free(mask)
    else:
        builder.cz(probe, words[0])
        builder.ccz(words[0][2], words[1][6], factor[9])
        emitter.multiply_closing(lender, words, factor, mask)
    return builder.finish_circuit()


def verify(tape, prefix_only, values, first, second, probes, seed):
    field = km.GF2Field(12)
    inverses = np.array([field.invert(int(x)) for x in values], dtype=np.int64)
    scaled1 = np.array([field.mul(int(x), int(y)) for x, y in zip(first, inverses)])
    scaled2 = np.array([field.mul(int(x), int(y)) for x, y in zip(second, inverses)])
    flags = np.arange(len(values)) & 1
    sim = km.Simulator(batch_size=len(values), seed=seed, counting_operations=True)
    sim.use_same_registers_as(tape)
    data = tape.register_data
    for name, value in zip(("factor", "word0", "word1", "probe", "untouched"),
                           (values, first, second, probes, flags)):
        sim.write_across_shots(data[name], matrix(value, 1 if name == "untouched" else 12))
    sim.do(tape)
    assert np.array_equal(read_word(sim, data["factor"]), values)
    assert np.array_equal(read_word(sim, data["word0"]), scaled1 if prefix_only else first)
    assert np.array_equal(read_word(sim, data["word1"]), scaled2 if prefix_only else second)
    assert np.array_equal(sim.read_across_shots(data["untouched"])[0], flags)
    assert not sim.read_across_shots([km.q(i) for i in range(37, tape.num_qubits)]).any()
    if prefix_only:
        masks = read_word(sim, data["debt"])
        rows = quadratic_basis(12)["to_tower"]
        tower_values = [sum((((row & int(x)).bit_count() & 1) << i)
                            for i, row in enumerate(rows)) for x in inverses]
        expected = [(int(x) & int(m)).bit_count() & 1 for x, m in zip(tower_values, masks)]
    else:
        expected = [((int(x) & int(m)).bit_count() & 1) ^
                    ((x >> 2 & 1) & (y >> 6 & 1) & (f >> 9 & 1))
                    for x, y, f, m in zip(scaled1, scaled2, values, probes)]
    assert np.array_equal(sim.read_phase_flipped_across_shots(), expected)
    return dict(shots=len(values), seed=seed, errors=0,
                mean_T=sim.operation_statistics().num_toffoli_like / len(values))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    values = np.arange(1, 4097) % 4095 + 1
    rng = np.random.default_rng(20261115)
    words = rng.integers(0, 4096, (3, len(values)), dtype=np.int64)
    receipts = {}
    for emitter in (original, new):
        for prefix_only in (True, False):
            key = f"{emitter.__name__}-{'prefix' if prefix_only else 'paired'}"
            tape = build(emitter, prefix_only)
            name = args.out.parent / (key + ".kmb")
            tape.to_file(name, format="kmb")
            receipts[key] = dict(Q=tape.num_qubits, T=tape.operation_statistics().num_toffoli_like,
                                 length=len(tape),
                                 trials=[verify(tape, prefix_only, values, *words, seed)
                                         for seed in (871, 874)])
    args.out.write_text(json.dumps(receipts, indent=2) + "\n")
    print(json.dumps(receipts, indent=2))


if __name__ == "__main__":
    main()
