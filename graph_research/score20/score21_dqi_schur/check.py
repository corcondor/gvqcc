"""Check the width-14 GF24 divisor on arbitrary unit pivots and zero-target zero."""
import argparse
import hashlib
import json
from pathlib import Path

import kickmix as km
import numpy as np

import outcome_dqi_chart_check_norm as reference
import schur


def matrix(values, n):
    bits = ((values[None, :] >> np.arange(n)[:, None]) & 1).astype(bool)
    return bits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20261115)
    a = np.arange(4096, dtype=np.int64)
    b = rng.integers(0, 4096, len(a))
    values = np.concatenate((a | (b << 12), np.arange(4096) << 12))
    data = rng.integers(0, 1 << 24, len(values), dtype=np.int64)
    data[values == 0] = 0
    result = {}
    for label in ("divide", "multiply", "adjoint"):
        if label == "divide":
            factors = [reference.inv(int(x)) for x in values]
        elif label == "adjoint":
            factors = [int(x) ^ (int(x) >> 12) for x in values]
        else:
            factors = list(map(int, values))
        expected = np.array([reference.mul(int(t), f) for t, f in zip(data, factors)])
        builder = km.CircuitBuilder()
        source = builder.create_quantum_register(24, "source")
        target = builder.create_quantum_register(24, "target")
        if label == "divide":
            schur.divide(builder, source, target)
        else:
            schur.multiply(builder, source, target, conjugate=label == "adjoint")
        tape = builder.finish_circuit()
        path = args.out / f"{label}.kmb"
        tape.to_file(path, format="kmb")
        assert tape.num_qubits == 62
        rows = []
        for seed in (631, 1631):
            simulator = km.Simulator(batch_size=len(values), counting_operations=True, seed=seed)
            simulator.use_same_registers_as(tape)
            simulator.write_across_shots(source, matrix(values,24))
            simulator.write_across_shots(target, matrix(data,24))
            simulator.do(tape)
            assert np.array_equal(simulator.read_across_shots(source), matrix(values,24))
            assert np.array_equal(simulator.read_across_shots(target), matrix(expected,24))
            assert not simulator.read_across_shots([km.q(i) for i in range(48,tape.num_qubits)]).any()
            assert not simulator.read_phase_flipped_across_shots().any()
            rows.append(dict(shots=len(values), seed=seed, errors=0,
                             mean_Toffoli=simulator.operation_statistics().num_toffoli_like/len(values)))
        result[label] = dict(width=tape.num_qubits, helper_width=tape.num_qubits-48,
                      static_Toffoli=tape.operation_statistics().num_toffoli_like,
                      sha256=hashlib.sha256(path.read_bytes()).hexdigest(), trials=rows,
                      a_zero_nonzero_b_fixtures=4095, zero_source_zero_target=True)
    (args.out / "all_products.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
