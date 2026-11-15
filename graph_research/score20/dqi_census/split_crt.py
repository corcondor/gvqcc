"""Delay the 24-wire consuming residue product until after scalar CRT points."""

from argparse import ArgumentParser
from functools import cache
from hashlib import file_digest
import json
from pathlib import Path
import sys

import numpy as np


def forward_n_rows(source, r, i):
    field = source.F
    _, kappa = source.node(i)
    matrix = [[field.mul(field.mul(beta, beta) ^ beta ^ kappa, field.pow(beta, j))
               for j in range(r)] for beta in range(r)]
    return source.field_rows(matrix)


def inverse_crt_rows(source, r, i, invert_field_matrix):
    field = source.F
    n = r + 2
    rows = [[field.pow(beta, j) for j in range(n)] for beta in range(r)]
    residue = source.residue_powers(i, n)
    rows += [[p[0] for p in residue], [p[1] for p in residue]]
    return source.field_rows(invert_field_matrix(rows, field))


def emit_prefix(builder, N, D, P, i, source, *, guarded=False, mark=lambda *_: None):
    from field_tensor import invert_field_matrix

    r = len(N)
    assert len(D) == r + 1 and len(P) == 2 and 1 <= r <= 34
    base = builder.num_allocated_qubits
    source.apply_inplace_linear(builder, source.flat(N), forward_n_rows(source, r, i))
    mark("begin_scalar_updates", builder)
    for beta, target in enumerate(N):
        source.evaluation_view(builder, D, beta)
        source.evaluation_view(builder, P, beta)
        source.accumulate_product(builder, D[0], P[0], target)
        source.evaluation_view(builder, P, beta)
        source.evaluation_view(builder, D, beta)
    assert builder.num_allocated_qubits == base
    mark("end_scalar_updates", builder)
    source.apply_inplace_linear(builder, source.flat(D), source.residue_view_rows(r, i))
    t, _ = source.node(i)
    source.add_scaled(builder, P[1], P[0], t)
    mark("begin_residue", builder)
    # The old P mask has exactly the original common-K coordinates.
    pair = source.Arithmetic.emit_prefix(builder, source.flat(D[:2]), source.flat(P),
                                         delta=source.DELTA, guarded=guarded)
    mark("end_residue", builder)
    source.apply_inplace_linear(builder, source.flat(D), source.residue_view_rows(r, i, True))
    source.apply_inplace_linear(builder, source.flat(N + P),
                                inverse_crt_rows(source, r, i, invert_field_matrix))
    assert builder.num_allocated_qubits == base
    return source.Record(id(builder), r, i, pair)


def build(km, source, r, i, variant, closed):
    builder = km.CircuitBuilder()
    N = builder.create_quantum_register(r * 12, "N")
    D = builder.create_quantum_register((r + 1) * 12, "D")
    P = builder.create_quantum_register(24, "P")
    base = builder.num_allocated_qubits
    probe = builder.create_classical_register((r + 2) * 12, "probe")
    word_lists = [[word[j:j + 12] for j in range(0, len(word), 12)] for word in (N, D, P)]
    marks = {}

    def mark(name, builder):
        marks[name] = dict(operation=len(builder.finish_circuit()),
                           live_extra=builder.num_allocated_qubits - base)

    call = emit_prefix if variant else source.emit_prefix
    additional = dict(source=source, mark=mark) if variant else {}
    rec = call(builder, *word_lists, i, **additional)
    prefix_length = len(builder.finish_circuit())
    if closed:
        builder.cz(probe, km.array([*N, *P]))
        source.emit_closing(builder, *word_lists, rec)
    circuit = builder.finish_circuit()
    return circuit, prefix_length, marks, circuit.num_qubits - base


def words(bits):
    return np.sum(bits.reshape(-1, 12, bits.shape[1]).astype(np.uint32) *
                  (1 << np.arange(12, dtype=np.uint32))[None, :, None], axis=1)


def check_case(km, source, regs, r, i, circuit, expected, seeds, closed):
    size = regs["N"].shape[1]
    for seed in seeds:
        sim = km.Simulator(batch_size=size, seed=seed, counting_operations=True)
        sim.use_same_registers_as(circuit)
        for name, value in regs.items():
            sim.write_across_shots(circuit.register_data[name], value)
        sim.do(circuit)
        register = circuit.register_data
        out = {k: np.asarray(sim.read_across_shots(register[k])) for k in ("N", "D", "P")}
        assert np.array_equal(regs["D"], out["D"])
        abi = {q for reg in register.values() for q in reg if isinstance(q, km.q)}
        scratch = km.array([km.q(q) for q in range(circuit.num_qubits) if km.q(q) not in abi])
        assert not np.asarray(sim.read_across_shots(scratch)).any()
        if closed:
            assert np.array_equal(regs["N"], out["N"]) and np.array_equal(regs["P"], out["P"])
            prod_bits = ((expected[:, None, :] >> np.arange(12)[None, :, None]) & 1).reshape(-1, size)
            phase = np.count_nonzero(regs["probe"] & prod_bits, axis=0) % 2
            assert np.array_equal(phase, sim.read_phase_flipped_across_shots())
        else:
            assert np.array_equal(words(np.vstack((out["N"], out["P"]))), expected)


def formula(source, regs, r, i):
    field = source.F
    _, kappa = source.node(i)
    n, d, p = (words(regs[name]) for name in ("N", "D", "P"))
    output = np.zeros((r + 2, n.shape[1]), dtype=np.uint32)
    mult = np.vectorize(field.mul, otypes=[np.uint32])
    for j, a in enumerate(n):
        output[j] ^= mult(kappa, a)
        output[j + 1] ^= a
        output[j + 2] ^= a
    for j, a in enumerate(d):
        output[j] ^= mult(a, p[0])
        output[j + 1] ^= mult(a, p[1])
    powers = source.residue_powers(i, r + 1)
    lo = np.zeros(n.shape[1], dtype=np.uint32)
    hi = lo.copy()
    for (a, b), coefficient in zip(powers, d):
        lo ^= mult(a, coefficient)
        hi ^= mult(b, coefficient)
    assert np.all(lo | hi), "Nonunit denominator in the guarded=False fixture"
    return output


def main():
    cli = ArgumentParser(description=__doc__)
    cli.add_argument("--source", type=Path, required=True)
    cli.add_argument("--out", type=Path, required=True)
    cli.add_argument("--degree", type=int, default=5)
    cli.add_argument("--node", type=int, default=29)
    cli.add_argument("--shots", type=int, default=1024)
    args = cli.parse_args()
    r, i = args.degree, args.node
    for rel in ("night_c27/synthesis", "night_c27/arithmetic", "after_c5/extractor_width"):
        sys.path.insert(0, str(args.source / rel))
    import ew_paths  # noqa: F401
    import kickmix as km
    import fused_crt_synthesis as source

    rng = np.random.default_rng(501634)
    regs = {name: rng.integers(0, 2, (12 * length, args.shots), dtype=np.uint8).astype(bool)
            for name, length in (("N", r), ("D", r + 1), ("P", 2), ("probe", r + 2))}
    expected = formula(source, regs, r, i)
    args.out.mkdir(parents=True, exist_ok=True)
    report = dict(degree=r, node=i, expected_t_increase_per_prefix=15, rows=[])
    for early in (False, True):
        for closed in (False, True):
            circuit, prefix, marks, helpers = build(km, source, r, i, early, closed)
            name = f"{'split' if early else 'original'}_{'closed' if closed else 'prefix'}"
            path = args.out / (name + ".kmb")
            circuit.to_file(path, format="kmb")
            read = km.Circuit.from_file(path)
            check_case(km, source, regs, r, i, read, expected, (3719, 11845), closed)
            with path.open("rb") as stream:
                sha = file_digest(stream, "sha256").hexdigest()
            row = dict(case=name, helper_peak=helpers, instructions=len(read),
                       prefix_operations=prefix, native_shots=args.shots * 2,
                       static_t=read.operation_statistics().num_toffoli_like, marks=marks,
                       sha256=sha)
            report["rows"].append(row)
            print(row, flush=True)
    (args.out / "result.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
