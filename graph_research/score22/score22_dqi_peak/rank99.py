"""Verify streaming of the pinned GF24 tensor and the operand-alias obstacle."""

import argparse
from collections import Counter
from itertools import batched
import json
from pathlib import Path
import sys

import kickmix as km
import numpy as np


def parity(value):
    return value.bit_count() & 1


def set_bits(value):
    while value:
        bit = value & -value
        yield bit.bit_length() - 1
        value ^= bit


def evaluate(terms, a, b):
    value = 0
    for u, v, p in terms:
        if parity(u & a) and parity(v & b):
            value ^= p
    return value


def alias_evidence(terms, multiply):
    # A write by term i modifies a still-needed factor of term j.
    dependencies = [(i, j) for i, (_, _, output) in enumerate(terms)
                    for j, (_, right, _) in enumerate(terms)
                    if parity(output & right)]
    info = Counter("self" if i == j else "other" for i, j in dependencies)
    mutual = set(dependencies)
    mutual_pairs = sum(i < j and (j, i) in mutual for i, j in dependencies)
    term_id = next(i for i, j in dependencies if i == j)
    left, right, output = terms[term_id]
    source = left & -left
    assert parity(left & source) and parity(output & right)
    # If implemented as a local in-place XOR, this rank-one term would send
    # both 0 and output to 0 for this fixed nonzero source.
    assert multiply(source, output) != multiply(source, 0)

    alias_counterexample = None
    for a_index in range(24):
        a = 1 << a_index
        for b_index in range(24):
            b = 1 << b_index
            wanted = multiply(a, b)
            assert evaluate(terms, a, b) == wanted
            had = b
            for u, v, p in terms:
                if parity(u & a) and parity(v & had):
                    had ^= p
            if alias_counterexample is None and had != wanted:
                alias_counterexample = dict(a=a, b=b, expected=wanted, obtained=had)
    assert alias_counterexample is not None
    # Attempt to keep a public baseline M(a0)b on the same output lanes
    # and stream (a+a0)*b into it. The retained controls see
    # b=M(a0^-1)output until an update. For every update to be a reversible
    # rank-one in-place step its self-overlap must vanish. These are binary
    # linear constraints on z=a0^-1.
    pivots = {}
    for _, right, output in terms:
        row = sum(parity(right & multiply(1 << j, output)) << j for j in range(24))
        while row:
            pivot = row.bit_length() - 1
            if pivot not in pivots:
                pivots[pivot] = row
                break
            row ^= pivots[pivot]
    return dict(original_basis_pair_checks=24**2, terms=len(terms),
                directed_read_after_write_edges=info["other"],
                self_alias_terms=info["self"], mutual_term_pairs=mutual_pairs,
                constant_field_scale_self_overlap_constraint_rank=len(pivots),
                nonzero_constant_field_scales_passing_all_self_overlap_tests=(
                    (1 << (24-len(pivots))) - 1),
                singular_local_update=dict(term=term_id, nonzero_left_input=source,
                                           colliding_right_inputs=[0, output]),
                naive_alias_sequential_counterexample=alias_counterexample)


def batched_product(builder, left, right, out, terms, size, field_tensor):
    work = builder.alloc_qubits(size)
    for group in batched(terms, size):
        pending = []
        for (u, v, output), q in zip(group, work):
            a = field_tensor.parity_pivot(builder, left, u)
            b = field_tensor.parity_pivot(builder, right, v)
            builder.init_and(a, b, q)
            field_tensor.parity_pivot(builder, right, v)
            field_tensor.parity_pivot(builder, left, u)
            pending.append((q, u, v, output))
        for q, _, _, output in pending:
            for receiver in set_bits(output):
                builder.cx(q, out[receiver])
        for q, u, v, _ in reversed(pending):
            a = field_tensor.parity_pivot(builder, left, u)
            b = field_tensor.parity_pivot(builder, right, v)
            builder.del_and(a, b, q)
            field_tensor.parity_pivot(builder, right, v)
            field_tensor.parity_pivot(builder, left, u)
    builder.free(work)


def build(terms, batch_size, field_tensor):
    builder = km.CircuitBuilder()
    left = builder.create_quantum_register(24, "a")
    right = builder.create_quantum_register(24, "b")
    out = builder.create_quantum_register(24, "out")
    if batch_size:
        batched_product(builder, left, right, out, terms, batch_size, field_tensor)
    else:
        # A CNOT conjugation implements every output column on its own
        # pivot without storing the product on any separate temporary.
        field_tensor.accumulate_product(builder, left, right, out, terms)
    return builder.finish_circuit()


def bits(words):
    return (((words[None, :] >> np.arange(24, dtype=np.uint32)[:, None]) & 1)
            .astype(bool))


def verify(circuit, inputs, output, batch_size):
    length = inputs.shape[1]
    receipts = []
    for seed in (912, 1912):
        sim = km.Simulator(batch_size=length, counting_operations=True, seed=seed)
        sim.use_same_registers_as(circuit)
        for name, word in zip(("a", "b", "out"), inputs):
            sim.write_across_shots(circuit.register_data[name], bits(word))
        sim.do(circuit)
        for name, word in zip(("a", "b", "out"), (*inputs[:2], output)):
            assert np.array_equal(sim.read_across_shots(circuit.register_data[name]), bits(word))
        if batch_size:
            assert not sim.read_across_shots(
                km.array([km.q(q) for q in range(72, circuit.num_qubits)])
            ).any()
        assert not sim.read_phase_flipped_across_shots().any()
        assert sim.operation_statistics().num_toffoli_like == 99 * length
        receipts.append(dict(shots=length, seed=seed, errors=0))
    return dict(batch_size=batch_size, extra_work_wires=circuit.num_qubits-72,
                static_paid=circuit.operation_statistics().num_toffoli_like,
                operations=len(circuit), trials=receipts)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    sys.path[:0] = [str(a.source/"night_c27/arithmetic")]
    import gf24_arithmetic as arithmetic
    import field_tensor
    # The rank-one summands commute on disjoint outputs. Sort the same
    # summands so the reported alias witness has a stable term index.
    terms = tuple(sorted(arithmetic.tensor24()))
    result = alias_evidence(terms, arithmetic.mul24)
    rng = np.random.default_rng(2026111522)
    inputs = rng.integers(0, 1 << 24, size=(3,8192), dtype=np.uint32)
    products = np.fromiter((arithmetic.mul24(int(a),int(b)) for a,b in zip(*inputs[:2])),
                           dtype=np.uint32, count=inputs.shape[1])
    output = inputs[2] ^ products
    result["disjoint_accumulation"] = [
        verify(build(terms, size, field_tensor), inputs, output, size) for size in (0,16,24)]
    a.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
