#!/usr/bin/env python3
"""Remove quantum workspace from nonzero classical field multiplication.

This is an independent component experiment.  It imports the supplied source
read-only and does not patch it.  The Gaussian-elimination matrix is entirely
classical; the quantum operations are conditional CX and SWAP gates only.

If R(a^-1) is the binary matrix of multiplication by a^-1, elimination yields
E R(a^-1) = I.  Applying the same row operations to x therefore produces
E x = R(a) x = a*x.  No quantum scratch is required.  The caller must guarantee
a != 0 and supply its correct inverse.  These are already the conditions of
the supplied scalar inverse-phase circuit's classical scaling operation.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True

import kickmix as km
import numpy as np


def classical_scale_inplace(builder, source, multiplier, inverse_multiplier):
    """Set source <- multiplier*source, preserving all classical arguments.

    ``multiplier`` is retained as part of the original interface; its inverse
    determines the emitted elementary operations.  The degree is len(source).
    All scratch is classical and is released before returning.
    """
    width = len(source)
    assert width == len(multiplier) == len(inverse_multiplier)
    field = km.GF2Field(width)
    rows = [builder.alloc_bits(width) for _ in range(width)]
    for row in rows:
        builder.bit_store(row, False)
    # Column c of R(a^-1) is a^-1 * x^c, a linear function of its input bits.
    for c in range(width):
        for k, inverse_bit in enumerate(inverse_multiplier):
            column = field.mul(1 << k, 1 << c)
            for r in range(width):
                if column >> r & 1:
                    builder.cx(inverse_bit, rows[r][c])
    pivot_missing = builder.alloc_bits(1)
    chosen = builder.alloc_bits(1)
    for c in range(width):
        for r in range(c + 1, width):
            # Copy each decision to a stable bit.  Thus this implementation
            # does not depend on whether a condition stack snapshots its bit.
            builder.bit_store(pivot_missing, True)
            builder.cx(rows[c][c], pivot_missing[0])
            builder.bit_store(chosen, False)
            builder.push_condition(pivot_missing[0])
            builder.cx(rows[r][c], chosen[0])
            builder.pop_condition()
            builder.push_condition(chosen[0])
            builder.swap(rows[c], rows[r])
            builder.swap(source[c], source[r])
            builder.pop_condition()
        for r in range(width):
            if r == c:
                continue
            builder.bit_store(chosen, False)
            builder.cx(rows[r][c], chosen[0])
            builder.push_condition(chosen[0])
            builder.cx(rows[c], rows[r])
            builder.cx(source[c], source[r])
            builder.pop_condition()
    builder.free(chosen)
    builder.free(pivot_missing)
    for row in rows:
        builder.free(row)


def phase_inverse_six_inplace(builder, source, mask, scalar, root=True):
    """Supplied phase circuit with only its two classical scales replaced."""
    from quantum_reciprocal import xor_linear

    mu = scalar.classical_word(builder)
    xor_linear(builder, mask, mu, scalar.trace_dual_columns())
    reciprocal, owned = scalar.classical_inverse(builder, mu)
    active = builder.alloc_bits(1)
    builder.bit_store(active, False)
    builder.bit_store(active[0], True, control=mu)
    builder.push_condition(active[0])
    classical_scale_inplace(builder, source, reciprocal, mu)
    scalar.fixed_trace_phase(builder, source, root)
    classical_scale_inplace(builder, source, mu, reciprocal)
    builder.pop_condition()
    for word in owned:
        builder.free(word)
    builder.free(active)
    builder.free(mu)


def serialize(circuit):
    output = io.BytesIO()
    circuit.to_file(output, format='kmb')
    return output.getvalue()


def verify_scale(scalar):
    from quantum_reciprocal import bit_matrix

    builder = km.CircuitBuilder()
    source = builder.create_quantum_register(6, 'source')
    dirty = builder.create_quantum_register(9, 'preserved_dirty')
    multiplier = builder.create_classical_register(6, 'multiplier')
    inverse = builder.create_classical_register(6, 'inverse_multiplier')
    classical_scale_inplace(builder, source, multiplier, inverse)
    circuit = builder.finish_circuit()
    # All 64 quantum values and all 63 supported nonzero classical scalars.
    values = np.tile(np.arange(64, dtype=np.int64), 63)
    multipliers = np.repeat(np.arange(1, 64, dtype=np.int64), 64)
    inverses = np.array([scalar.FIELD.invert(int(a)) for a in multipliers])
    expected = np.array([scalar.FIELD.mul(int(x), int(a))
                         for x, a in zip(values, multipliers)])
    dirt = np.random.default_rng(928013).integers(0, 512, len(values))
    sim = km.Simulator(batch_size=len(values), seed=117, counting_operations=True)
    sim.use_same_registers_as(circuit)
    for register, val, width in ((source, values, 6), (dirty, dirt, 9),
                                 (multiplier, multipliers, 6), (inverse, inverses, 6)):
        sim.write_across_shots(register, bit_matrix(val, width))
    sim.do(circuit)
    assert np.array_equal(sim.read_across_shots(source), bit_matrix(expected, 6))
    assert np.array_equal(sim.read_across_shots(dirty), bit_matrix(dirt, 9))
    assert np.array_equal(sim.read_across_shots(multiplier), bit_matrix(multipliers, 6))
    assert np.array_equal(sim.read_across_shots(inverse), bit_matrix(inverses, 6))
    assert not sim.read_phase_flipped_across_shots().any()
    assert circuit.num_qubits == 15
    assert circuit.operation_statistics().num_toffoli_like == 0
    return dict(status='PASS', exhaustive_nonzero_scalar_source_pairs=len(values),
                Q_input=15, Q_helpers=0, T_static=0, dirty_qubits_preserved=9,
                input_classical_registers_preserved=True, phase_preserved=True)


def build_phase(scalar, *, inplace, quantum_root):
    builder = km.CircuitBuilder()
    source = builder.create_quantum_register(6, 'source')
    root = builder.create_quantum_register(1, 'root') if quantum_root else None
    mask = builder.create_classical_register(6, 'tower_mask')
    root_arg = root[0] if quantum_root else True
    if inplace:
        phase_inverse_six_inplace(builder, source, mask, scalar, root=root_arg)
    else:
        scalar.phase_inverse_six(builder, source, mask, root=root_arg)
    return builder.finish_circuit(), source, root, mask


def verify_phase(scalar, *, quantum_root):
    from quantum_reciprocal import bit_matrix
    from tower_inverse import quadratic_basis

    circuit, source, root, mask = build_phase(scalar, inplace=True,
                                             quantum_root=quantum_root)
    baseline = build_phase(scalar, inplace=False, quantum_root=quantum_root)[0]
    repeated = build_phase(scalar, inplace=True, quantum_root=quantum_root)[0]
    payload = serialize(circuit)
    assert payload == serialize(repeated)
    shots = 8192 if quantum_root else 4096
    index = np.arange(shots, dtype=np.int64)
    values = index % 64
    masks = (index // 64) % 64
    roots = index // 4096 if quantum_root else np.ones(shots, dtype=np.int64)
    rows = quadratic_basis(6)['to_tower']
    expected_phase = []
    for value, measured, outer in zip(values, masks, roots):
        inverse = scalar.FIELD.invert(int(value)) if value else 0
        tower = sum(((row & inverse).bit_count() % 2) << j
                    for j, row in enumerate(rows))
        expected_phase.append(bool(outer and (tower & int(measured)).bit_count() % 2))
    means = []
    live_input_qubits = 7 if quantum_root else 6
    for seed in range(4):
        sim = km.Simulator(batch_size=shots, seed=seed, counting_operations=True)
        sim.use_same_registers_as(circuit)
        sim.write_across_shots(source, bit_matrix(values, 6))
        if quantum_root:
            sim.write_across_shots(root, bit_matrix(roots, 1))
        sim.write_across_shots(mask, bit_matrix(masks, 6))
        sim.do(circuit)
        assert np.array_equal(sim.read_across_shots(source), bit_matrix(values, 6)), (seed, 'source')
        if quantum_root:
            assert np.array_equal(sim.read_across_shots(root), bit_matrix(roots, 1)), (seed, 'root')
        assert np.array_equal(sim.read_across_shots(mask), bit_matrix(masks, 6)), (seed, 'mask')
        assert not sim.read_across_shots([km.q(i) for i in
                                        range(live_input_qubits, circuit.num_qubits)]).any(), (seed, 'scratch')
        assert np.array_equal(sim.read_phase_flipped_across_shots(),
                              np.array(expected_phase, dtype=bool)), (seed, 'phase')
        means.append(sim.operation_statistics().num_toffoli_like / shots)
    static_t = 6 if quantum_root else 4
    expected_helpers = 6 if quantum_root else 4
    assert circuit.num_qubits == live_input_qubits + expected_helpers
    assert circuit.operation_statistics().num_toffoli_like == static_t
    assert baseline.operation_statistics().num_toffoli_like == static_t
    assert means == [static_t * 63 / 64] * 4
    return dict(status='PASS', quantum_root=quantum_root,
                Q_before=baseline.num_qubits, Q_after=circuit.num_qubits,
                helper_before=baseline.num_qubits-live_input_qubits,
                helper_after=expected_helpers, T_static=static_t,
                exact_uniform_mask_expected_T=static_t*63/64,
                native_mean_T_per_seed=means, exhaustive_cases_per_seed=shots,
                measurement_seeds=4, byte_identical_builds=True,
                circuit_sha256=hashlib.sha256(payload).hexdigest()), payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.source))
    import scalar_inverse_phase as scalar

    scale = verify_scale(scalar)
    fixed, fixed_payload = verify_phase(scalar, quantum_root=False)
    controlled, controlled_payload = verify_phase(scalar, quantum_root=True)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/'dqi_next_arithmetic_fixed_phase.kmb').write_bytes(fixed_payload)
    (args.output/'dqi_next_arithmetic_controlled_phase.kmb').write_bytes(controlled_payload)
    result = dict(status='PASS_LOCAL_COMPONENT_ONLY', scale=scale,
                  fixed_inverse_phase=fixed, controlled_inverse_phase=controlled,
                  proof='For each nonzero classical a, Gaussian elimination forms E with E*R(a^-1)=I; its identical quantum row operations apply E=R(a).',
                  domain='All GF64 quantum inputs including zero; nonzero classical multiplication factors; all classical inverse-phase masks including zero.',
                  whole_decoder_status='No whole-decoder integration or score improvement claimed. Other simultaneous live registers may still determine the 889-qubit peak.',
                  source_read_only=True,
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (args.output/'dqi_next_arithmetic_report.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
