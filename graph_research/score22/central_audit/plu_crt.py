"""Compose the narrow PLU residue with the forward and return CRT sweeps."""

from argparse import ArgumentParser
from hashlib import file_digest
import json
from pathlib import Path
import sys

import numpy as np

from plu_residue import consume
from split_crt import check_case, emit_prefix, formula


def emit_closing(builder, N, D, P, record, source):
    r, i = record.r, record.node_index
    assert id(builder) == record.builder_id
    assert len(N) == r and len(D) == r + 1 and len(P) == 2
    source.apply_inplace_linear(builder, source.flat(N + P), source.crt_rows(r, i))
    source.apply_inplace_linear(builder, source.flat(D), source.residue_view_rows(r, i))
    consume(builder, source.flat(D[:2]), source.flat(P), inverse=True, delta=source.DELTA)
    source.Arithmetic.repay_product_input(builder, source.flat(P), record.pair_record)
    source.apply_inplace_linear(builder, source.flat(D), source.residue_view_rows(r, i, True))
    t, _ = source.node(i)
    source.add_scaled(builder, P[1], P[0], t)
    for beta, target in enumerate(N):
        source.evaluation_view(builder, D, beta)
        source.evaluation_view(builder, P, beta)
        source.accumulate_product(builder, D[0], P[0], target)
        source.evaluation_view(builder, P, beta)
        source.evaluation_view(builder, D, beta)
    source.apply_inplace_linear(builder, source.flat(N), source.recover_n_rows(r, i))


def build(km, source, r, i, narrow):
    builder = km.CircuitBuilder()
    N = builder.create_quantum_register(r * 12, "N")
    D = builder.create_quantum_register((r + 1) * 12, "D")
    P = builder.create_quantum_register(24, "P")
    data_qubits = builder.num_allocated_qubits
    probe = builder.create_classical_register((r + 2) * 12, "probe")
    N_words, D_words, P_words = ([word[j:j + 12] for j in range(0, len(word), 12)]
                                  for word in (N, D, P))

    def prefix_residue(builder, D_value, P_value, delta, guarded):
        mask = consume(builder, D_value, P_value, delta=delta)
        return source.Arithmetic.make_record(builder, mask, delta=delta, guarded=guarded)

    points = {}

    def mark(name, builder):
        points[name] = len(builder.finish_circuit())

    if narrow:
        record = emit_prefix(builder, N_words, D_words, P_words, i, source, mark=mark,
                             consume_residue=prefix_residue)
    else:
        record = source.emit_prefix(builder, N_words, D_words, P_words, i)
    prefix = builder.finish_circuit()
    prefix_mask = [int(str(b)[1:]) for b in record.pair_record.old_target_mask]
    builder.cz(probe, km.array([*N, *P]))
    points["begin_return"] = len(builder.finish_circuit())
    if narrow:
        emit_closing(builder, N_words, D_words, P_words, record, source)
    else:
        source.emit_closing(builder, N_words, D_words, P_words, record)
    assert builder.num_allocated_qubits == data_qubits
    return prefix, builder.finish_circuit(), points, data_qubits, prefix_mask


def main():
    cli = ArgumentParser(description=__doc__)
    cli.add_argument("--source", type=Path, required=True)
    cli.add_argument("--out", type=Path, required=True)
    cli.add_argument("--degree", type=int, default=34)
    cli.add_argument("--node", type=int, default=0)
    cli.add_argument("--shots", type=int, default=1024)
    args = cli.parse_args()
    for rel in ("night_c27/synthesis", "night_c27/arithmetic",
                "after_c5/extractor_width", "after_c5/arithmetic_t"):
        sys.path.insert(0, str(args.source / rel))
    import ew_paths  # noqa: F401
    import fused_crt_synthesis as source
    import gf24_nested_norm as arithmetic
    import kickmix as km

    source.Arithmetic = arithmetic
    r, i = args.degree, args.node
    rng = np.random.default_rng(7213)
    regs = {name: rng.integers(0, 2, (12 * length, args.shots), dtype=np.uint8).astype(bool)
            for name, length in (("N", r), ("D", r + 1), ("P", 2), ("probe", r + 2))}
    expected = formula(source, regs, r, i)
    args.out.mkdir(parents=True, exist_ok=True)
    report = dict(degree=r, node=i, rows=[])
    for narrow in (False, True):
        prefix, closed, points, data, prefix_mask = build(km, source, r, i, narrow)
        for component, circuit in (("prefix", prefix), ("closed", closed)):
            label = ("plu_" if narrow else "original_") + component
            path = args.out / (label + ".kmb")
            circuit.to_file(path, format="kmb")
            read = km.Circuit.from_file(path)
            check_case(km, source, regs, r, i, read, expected, (10981, 461782),
                       component == "closed")
            with path.open("rb") as stream:
                sha = file_digest(stream, "sha256").hexdigest()
            row = dict(case=label, helper_peak=read.num_qubits - data, operations=len(read),
                       prefix_ops=len(prefix), marks=points, old_target_mask_ids=prefix_mask,
                       static_T=read.operation_statistics().num_toffoli_like,
                       native_shots=args.shots * 2, sha256=sha)
            report["rows"].append(row)
            print({key: value for key, value in row.items() if key != "old_target_mask_ids"},
                  flush=True)
    (args.out / "result.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
