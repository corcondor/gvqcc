"""Validate fixed-low GF24 division on all high coefficients and dirty targets."""
import argparse
import hashlib
import json
from pathlib import Path

import kickmix as km
import numpy as np

import outcome_dqi_chart_check_norm as reference
import normalized


def bits(values):
    return ((values[None,:] >> np.arange(24)[:,None]) & 1).astype(bool)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out",type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rng = np.random.default_rng(202611152239)
    target_data = rng.integers(0,1 << 24,4096)
    result = {}
    for low in (1,13,4095):
        source_data = low | (np.arange(4096) << 12)
        expected = np.array([reference.mul(int(v),reference.inv(int(c)))
                             for c,v in zip(source_data,target_data)])
        builder = km.CircuitBuilder()
        source = builder.create_quantum_register(24,"source")
        target = builder.create_quantum_register(24,"target")
        normalized.divide_fixed_low(builder,source,target,low)
        tape = builder.finish_circuit()
        path = args.out/f"fixed_low_{low}.kmb"
        tape.to_file(path,format="kmb")
        assert tape.num_qubits == 60
        trials = []
        for seed in (8621,18621):
            sim = km.Simulator(batch_size=4096,seed=seed,counting_operations=True)
            sim.use_same_registers_as(tape)
            sim.write_across_shots(source,bits(source_data))
            sim.write_across_shots(target,bits(target_data))
            sim.do(tape)
            assert np.array_equal(sim.read_across_shots(source),bits(source_data))
            assert np.array_equal(sim.read_across_shots(target),bits(expected))
            assert not sim.read_phase_flipped_across_shots().any()
            assert not sim.read_across_shots([km.q(i) for i in range(48,60)]).any()
            trials.append(dict(shots=4096, seed=seed, errors=0,
                               mean_T=sim.operation_statistics().num_toffoli_like/4096))
        result[str(low)] = dict(helpers=12,T=tape.operation_statistics().num_toffoli_like,
                                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                                trials=trials)
    (args.out/"normalized.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
