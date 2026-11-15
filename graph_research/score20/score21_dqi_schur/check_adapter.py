"""Test the narrow prefix with the original full return and additional next word."""
import argparse
import hashlib
import json
from pathlib import Path

import kickmix as km
import numpy as np

import outcome_dqi_chart_check_norm as reference
import score5_chem_width_classify as public
import adapter


def bitmatrix(values):
    return ((values[None,:] >> np.arange(24)[:,None]) & 1).astype(bool)


def build(prefix, with_next):
    builder = km.CircuitBuilder()
    source = builder.create_quantum_register(24, "source")
    target = builder.create_quantum_register(24, "target")
    bystander = builder.create_quantum_register(24, "next")
    probe = builder.create_classical_register(24, "probe")
    # The forward carry has previously scaled the next raw word.
    next_record = public.Direct.A.emit_prefix(builder, source, bystander) if with_next else None
    record = prefix(builder, source, target)
    builder.cz(probe, target)
    builder.ccz(target[0], target[9], target[13])
    public.Direct.restore_with_shared_norm(
        builder, source, target, record,
        next_word=bystander if with_next else None, next_input_record=next_record)
    return builder.finish_circuit()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(202611152137)
    source = rng.integers(1, 1 << 24, 2048)
    source[:128] = np.arange(1, 129) << 12
    target, third, probe = rng.integers(0, 1 << 24, (3, len(source)))
    quotient = [reference.mul(int(y), reference.inv(int(x))) for x, y in zip(source,target)]
    phase = np.array([((int(q) & int(m)).bit_count() & 1) ^
                      ((q >> 0 & 1) & (q >> 9 & 1) & (q >> 13 & 1))
                      for q,m in zip(quotient,probe)], dtype=bool)
    result = {}
    for label, prefix in (("original", public.Direct.divide_deferred),
                          ("schur", adapter.divide_deferred)):
        for next_word in (True, False):
            tape = build(prefix, next_word)
            trial = dict(T=tape.operation_statistics().num_toffoli_like,
                         Q=tape.num_qubits, trials=[])
            for seed in (237, 1237):
                sim = km.Simulator(batch_size=len(source), seed=seed, counting_operations=True)
                sim.use_same_registers_as(tape)
                for key, value in zip(("source","target","next","probe"),(source,target,third,probe)):
                    sim.write_across_shots(tape.register_data[key], bitmatrix(value))
                sim.do(tape)
                for key, value in zip(("source","target","next"),(source,target,third)):
                    assert np.array_equal(sim.read_across_shots(tape.register_data[key]),
                                          bitmatrix(value))
                assert not sim.read_across_shots([km.q(i) for i in range(72,tape.num_qubits)]).any()
                assert np.array_equal(sim.read_phase_flipped_across_shots(), phase)
                trial["trials"].append(dict(seed=seed, shots=len(source), errors=0))
            result[f"{label}_{next_word:d}"] = trial
    (args.out/"closing.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
