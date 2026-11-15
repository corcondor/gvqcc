#!/usr/bin/env python3
"""Phase-checked GF(2^24) consuming product on the chart source bit 0 = 1."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

import kickmix as km
import numpy as np


FIELD_BITS = 24


def rank_one_row(tensor, output_bit):
    """Collect source parities for individual basis bits of the right input."""
    row = [0] * FIELD_BITS
    for left, right, output in tensor:
        if output >> output_bit & 1:
            for j in range(FIELD_BITS):
                if right >> j & 1:
                    row[j] ^= left
    return row


def factor_binary_matrix(columns):
    """Factor a bipartite bilinear form into exactly rank(matrix) terms."""
    basis = {}
    right_by_generator = []
    generators = []
    for j, column in enumerate(columns):
        left = column
        while left:
            pivot = left.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = len(generators)
                generators.append(left)
                right_by_generator.append(0)
            i = basis[pivot]
            left ^= generators[i]
            right_by_generator[i] ^= 1 << j
    return list(zip(generators, right_by_generator))


def split_product(tensor):
    early, late = [], []
    residual = [0] * (FIELD_BITS - 1)
    for a, b, c in tensor:
        if b & 1:
            if c >> 1:
                early.append((a, b, c >> 1))
            if c & 1:
                for j in range(FIELD_BITS - 1):
                    if (b >> (j + 1)) & 1:
                        residual[j] ^= a
        else:
            late.append((a, b >> 1, c))
    # Since source[0]=1, its contribution is a linear right parity.
    linear = sum((col & 1) << j for j, col in enumerate(residual))
    nonlinear = factor_binary_matrix([col >> 1 for col in residual])
    return early, late, linear, nonlinear


def product_prefix(builder, source, target, tensor):
    """Keep target bit 0 in place and record debt for the other old bits."""
    from field_tensor import accumulate_product

    if rank_one_row(tensor, 0)[0] != 1:
        raise ValueError("This compiler requires the unit to occupy field bit 0")
    early, late, linear, nonlinear = split_product(tensor)
    temporary = builder.alloc_qubits(FIELD_BITS - 1)
    accumulate_product(builder, source, target, temporary, early)

    # All outstanding updates depend on target[1:], so the pivot becomes an
    # output and the late tensor terms can fan out into it without more T.
    combined = km.array([target[0], *temporary])
    accumulate_product(builder, source, target[1:], combined, late)
    accumulate_product(builder, source[1:], target[1:], target[:1],
                       [(a, b, 1) for a, b in nonlinear])
    for j, bit in enumerate(target[1:]):
        if linear >> j & 1:
            builder.cx(bit, target[0])
    builder.swap(target[1:], temporary)

    mask = builder.alloc_bits(FIELD_BITS)
    builder.bit_store(mask[0], False)
    builder.hmr(temporary, mask[1:])
    builder.free(temporary)
    return mask


def build(field, *, pivot, closed):
    builder = km.CircuitBuilder()
    source = builder.create_quantum_register(FIELD_BITS, "source")
    target = builder.create_quantum_register(FIELD_BITS, "target")
    probe = builder.create_classical_register(FIELD_BITS, "probe")
    if pivot:
        mask = product_prefix(builder, source, target, field.tensor24())
        record = field.make_record(builder, mask)
    else:
        record = field.emit_prefix(builder, source, target)
        mask = record.old_target_mask
    if closed:
        builder.cz(probe, target)
        builder.cz(target[1], target[17])
        field.emit_closing(builder, source, target, record)
    else:
        exposed = builder.create_classical_register(FIELD_BITS, "saved_mask")
        builder.cx(mask, exposed)
        field.free_product_mask(builder, record)
    assert builder.num_allocated_qubits == 2 * FIELD_BITS
    return builder.finish_circuit()


def read_words(simulator, bits):
    matrix = np.asarray(simulator.read_across_shots(bits), dtype=np.uint32)
    powers = 1 << np.arange(FIELD_BITS, dtype=np.uint32)
    return np.sum(matrix * powers[:, None], axis=0, dtype=np.uint32)


def verify(circuit, source, target, probe, products, *, pivot, closed, seed):
    from quantum_reciprocal import bit_matrix

    simulator = km.Simulator(batch_size=len(source), seed=seed, counting_operations=True)
    simulator.use_same_registers_as(circuit)
    registers = circuit.register_data
    for name, data in (("source", source), ("target", target), ("probe", probe)):
        simulator.write_across_shots(registers[name], bit_matrix(data, FIELD_BITS))
    simulator.do(circuit)
    assert np.array_equal(read_words(simulator, registers["source"]), source)
    assert np.array_equal(read_words(simulator, registers["target"]), target if closed else products)
    assert np.array_equal(read_words(simulator, registers["probe"]), probe)
    if closed:
        phase = [((int(z) & int(p)).bit_count() + ((int(z) >> 1) & (int(z) >> 17) & 1)) % 2
                 for z, p in zip(products, probe)]
    else:
        masks = read_words(simulator, registers["saved_mask"])
        if pivot:
            assert not np.any(masks & 1)
        phase = [(int(m) & int(x)).bit_count() % 2 for m, x in zip(masks, target)]
    assert np.array_equal(simulator.read_phase_flipped_across_shots(), phase)
    scratch = km.array([km.q(i) for i in range(2 * FIELD_BITS, circuit.num_qubits)])
    assert not np.asarray(simulator.read_across_shots(scratch)).any()
    return simulator.operation_statistics().num_toffoli_like / len(source)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    for rel in ("after_c5/arithmetic_t", "after_v3/k24", "night_c27/arithmetic"):
        sys.path.insert(0, str(args.work / rel))
    import gf24_nested_norm as field
    from field_tensor import tensor_value

    tensor = field.tensor24()
    assert all(tensor_value(tensor, 1 << i, 1 << j) == field.mul24(1 << i, 1 << j)
               for i in range(FIELD_BITS) for j in range(FIELD_BITS))
    rng = np.random.default_rng(318842)
    count = 2048
    source = rng.integers(0, 1 << FIELD_BITS, size=count, dtype=np.uint32) | 1
    target = rng.integers(0, 1 << FIELD_BITS, size=count, dtype=np.uint32)
    probe = rng.integers(0, 1 << FIELD_BITS, size=count, dtype=np.uint32)
    source[:4] = (1, 3, 0xffffff, 0x800001)
    target[:4] = (0, 1, 0xffffff, 0x800000)
    products = np.asarray([field.mul24(int(a), int(b)) for a, b in zip(source, target)], dtype=np.uint32)
    args.out.mkdir(parents=True, exist_ok=True)
    rows = []
    for pivot in (False, True):
        for closed in (False, True):
            circuit = build(field, pivot=pivot, closed=closed)
            label = f"{'pivot' if pivot else 'reference'}_{'pair' if closed else 'prefix'}"
            path = args.out / (label + ".kmb")
            circuit.to_file(path, format="kmb")
            circuit = km.Circuit.from_file(path)
            seeds = (310488, 381006)
            observed = [verify(circuit, source, target, probe, products, pivot=pivot, closed=closed, seed=seed)
                        for seed in seeds]
            row = dict(
                component=label,
                helpers=circuit.num_qubits - 2 * FIELD_BITS,
                static_toffoli=circuit.operation_statistics().num_toffoli_like,
                operations=len(circuit),
                source_target_probe_scratch_and_phase_pass=True,
                shots=len(source) * len(seeds),
                mean_toffoli=observed,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            )
            print(json.dumps(row), flush=True)
            rows.append(row)
    (args.out / "one_pivot_result.json").write_text(json.dumps(dict(
        status="NATIVE_COMPONENT_PASS_NOT_PRODUCTION",
        chart="bit 0 of GF24 source equals 1",
        multiplication_tensor_basis_pairs_pass=FIELD_BITS ** 2,
        split_terms={"early": len(split_product(tensor)[0]), "late": len(split_product(tensor)[1]),
                     "nonlinear_residual_rank": len(split_product(tensor)[3])},
        rows=rows,
    ), indent=2) + "\n")


if __name__ == "__main__":
    main()
