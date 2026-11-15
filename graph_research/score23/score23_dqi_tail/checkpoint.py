"""Narrow zero tests and phase repayment for the DQI rolling tail."""

from argparse import ArgumentParser
from hashlib import file_digest
import json
from pathlib import Path
import sys

import numpy as np


def compute_chain(builder, controls, work):
    builder.init_and(controls[0], controls[1], work[0])
    for j in range(1, len(work)):
        builder.init_and(work[j - 1], controls[j + 1], work[j])


def clean_chain(builder, controls, work):
    for j in reversed(range(1, len(work))):
        builder.del_and(work[j - 1], controls[j + 1], work[j])
    if len(work):
        builder.del_and(controls[0], controls[1], work[0])


def all_one_phase(builder, controls, phase_mask):
    builder.push_condition(phase_mask)
    work = builder.alloc_qubits(len(controls) - 2)
    compute_chain(builder, controls, work)
    builder.cz(work[-1], controls[-1])
    clean_chain(builder, controls, work)
    builder.free(work)
    builder.pop_condition()


def checkpoint(builder, word, target, *, phase, split):
    import kickmix as km

    assert len(word) == 24 and 3 <= split <= 21
    if phase:
        builder.push_condition(target)
    builder.x(word)
    early, late = word[:split], word[split:]
    work = builder.alloc_qubits(len(early) - 1)
    compute_chain(builder, early, work)
    root = work[-1]
    clean_chain(builder, early, work[:-1])
    builder.free(work[:-1])
    controls = km.array([root, *late])
    consume = builder.alloc_qubits(len(controls) - 2)
    compute_chain(builder, controls, consume)
    if phase:
        builder.cz(consume[-1], controls[-1])
    else:
        builder.ccx(consume[-1], controls[-1], target)
    clean_chain(builder, controls, consume)
    builder.free(consume)
    debt = builder.alloc_bits(1)
    builder.hmr(root, debt[0])
    builder.free(root)
    all_one_phase(builder, early, debt[0])
    builder.free(debt)
    builder.x(word)
    if phase:
        builder.pop_condition()


def build(km, raw, controlled, phase, variant, split):
    builder = km.CircuitBuilder()
    word = builder.create_quantum_register(24, "word")
    if phase:
        target = builder.create_classical_register(1, "external")[0]
    else:
        target = builder.create_quantum_register(1, "external")[0]
    if variant:
        checkpoint(builder, word, target, phase=phase, split=split)
    elif phase:
        controlled.zero_phase(builder, word, target)
    else:
        raw.zero_xor(builder, word, target)
    return builder.finish_circuit()


def test(km, case, phase, rng, shots, trials):
    inputs = rng.integers(0, 2, (24, shots), dtype=np.uint8).astype(bool)
    inputs[:, ::3] = 0
    inputs[:, 1::3] = 0
    inputs[rng.integers(0, 24, len(inputs[0, 1::3])), np.arange(1, shots, 3)] = True
    external = rng.integers(0, 2, (1, shots), dtype=np.uint8).astype(bool)
    flag = ~inputs.any(axis=0)
    counts = []
    for seed in trials:
        sim = km.Simulator(batch_size=shots, seed=seed, counting_operations=True)
        sim.use_same_registers_as(case)
        sim.write_across_shots(case.register_data["word"], inputs)
        sim.write_across_shots(case.register_data["external"], external)
        sim.do(case)
        assert np.array_equal(sim.read_across_shots(case.register_data["word"]), inputs)
        expected = external if phase else external ^ flag
        assert np.array_equal(sim.read_across_shots(case.register_data["external"]), expected)
        assert np.array_equal(sim.read_phase_flipped_across_shots(),
                              (external[0] & flag) if phase else np.zeros(shots, dtype=bool))
        abi = 24 if phase else 25
        scratch = km.array([km.q(i) for i in range(abi, case.num_qubits)])
        assert not np.asarray(sim.read_across_shots(scratch)).any()
        counts.append(sim.operation_statistics().num_toffoli_like / shots)
    return counts


def main():
    cli = ArgumentParser(description=__doc__)
    cli.add_argument("--source", type=Path, required=True)
    cli.add_argument("--out", type=Path, required=True)
    cli.add_argument("--shots", type=int, default=8192)
    cli.add_argument("--split", type=int, default=10)
    args = cli.parse_args()
    for rel in ("after_c5/extractor_width", "night_c27/arithmetic", "night_c27/controller"):
        sys.path.insert(0, str(args.source / rel))
    import ew_paths  # noqa: F401
    import kickmix as km
    import rolling_tail
    import rolling_tail_conditional

    args.out.mkdir(parents=True, exist_ok=True)
    rows = {}
    for phase in (False, True):
        for variant in (False, True):
            case = ("phase" if phase else "xor") + ("_narrow" if variant else "_original")
            circuit = build(km, rolling_tail, rolling_tail_conditional, phase, variant, args.split)
            path = args.out / (case + ".kmb")
            circuit.to_file(path, format="kmb")
            circuit = km.Circuit.from_file(path)
            native = test(km, circuit, phase, np.random.default_rng(983211), args.shots, (31, 4042))
            with path.open("rb") as stream:
                sha = file_digest(stream, "sha256").hexdigest()
            rows[case] = dict(helpers=circuit.num_qubits - (24 if phase else 25),
                              static_T=circuit.operation_statistics().num_toffoli_like,
                              mean_T=native, ops=len(circuit), sha256=sha,
                              checked_shots=2 * args.shots)
            print(case, rows[case], flush=True)
    (args.out / "result.json").write_text(json.dumps(dict(split=args.split, cases=rows),
                                                      indent=2) + "\n")


if __name__ == "__main__":
    main()
