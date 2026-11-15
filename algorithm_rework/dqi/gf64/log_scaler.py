"""GF(8) unit scaling with no clean product register, plus an inverse fixture."""

from collections import deque
from functools import cache
import argparse
import hashlib
import json
from pathlib import Path
import sys

import kickmix as km
import numpy as np

GF8 = km.GF2Field(3)
IDENTITY = (1, 2, 4)


def transform(columns, value):
    return _xor(c for bit, c in enumerate(columns) if value >> bit & 1)


def _xor(values):
    out = 0
    for value in values:
        out ^= value
    return out


@cache
def linear_paths():
    """Shortest left-transvection factorization of all GL(3,2) matrices."""
    gates = [(v, w) for v in range(1, 8) for w in range(1, 8)
             if (v & w).bit_count() % 2 == 0]
    paths = {IDENTITY: ()}
    frontier = deque([IDENTITY])
    while frontier:
        matrix = frontier.popleft()
        for v, w in gates:
            dest = tuple(x ^ (v if (x & w).bit_count() % 2 else 0)
                         for x in matrix)
            if dest not in paths:
                paths[dest] = paths[matrix] + ((v, w),)
                frontier.append(dest)
    assert len(paths) == 168
    return paths


def cycle_swaps(perm):
    handled = set()
    pairs = []
    for root in range(8):
        if root in handled:
            continue
        p = root
        handled.add(p)
        while (p := perm[p]) != root:
            pairs.append((root, p))
            handled.add(p)
    return tuple(pairs)


@cache
def affine_permutation(perm):
    """Represent a permutation by transpositions and a final affine map."""
    best = None
    for columns in linear_paths():
        for offset in range(8):
            affine = [transform(columns, x) ^ offset for x in range(8)]
            residual = [affine.index(x) for x in perm]
            swaps = cycle_swaps(residual)
            candidate = len(swaps), columns, offset, swaps
            if best is None or candidate < best:
                best = candidate
    return best


@cache
def unit_layout():
    """Encode a nonzero norm directly as the exponent of its reciprocal."""
    choices = []
    for generator in range(2, 8):
        powers = [GF8.pow(generator, k) for k in range(7)]
        assert len(set(powers)) == 7
        encode = [7] + [(-powers.index(x)) % 7 for x in range(1, 8)]
        reciprocal_decode = [*powers, 0]
        forward = affine_permutation(tuple(encode))
        backward = affine_permutation(tuple(reciprocal_decode))
        scales = [linear_paths()[tuple(GF8.mul(powers[1 << k], e)
                                      for e in IDENTITY)] for k in range(3)]
        cost = forward[0] + backward[0] + 2 * sum(map(len, scales))
        choices.append((cost, generator, forward, backward, scales))
    return min(choices)


def emit_rank_one(builder, scalar_bit, word, direction, form):
    from field_tensor import invert_binary_columns
    from tower_inverse import apply_inplace_linear, rows_from_columns

    control = next(x for x in range(1, 8) if (x & form).bit_count() % 2)
    other = next(x for x in range(1, 8)
                 if (x & form).bit_count() % 2 == 0 and x != direction)
    basis = (direction, control, other)
    apply_inplace_linear(builder, word, invert_binary_columns(basis))
    builder.ccx(scalar_bit, word[1], word[0])
    apply_inplace_linear(builder, word, rows_from_columns(basis))


def emit_swap_states(builder, word, a, b):
    from field_tensor import invert_binary_columns
    from tower_inverse import apply_inplace_linear, rows_from_columns

    basis = [a ^ b]
    for v in IDENTITY:
        if v not in {transform(basis, t) for t in range(1 << len(basis))}:
            basis.append(v)
    assert len(basis) == 3
    offset = [word[k] for k in range(3) if a >> k & 1]
    builder.x(offset)
    apply_inplace_linear(builder, word, invert_binary_columns(basis))
    builder.x(word[1:])
    builder.ccx(word[1], word[2], word[0])
    builder.x(word[1:])
    apply_inplace_linear(builder, word, rows_from_columns(basis))
    builder.x(offset)


def emit_perm(builder, word, representation):
    from tower_inverse import apply_inplace_linear, rows_from_columns

    _, columns, offset, swaps = representation
    for a, b in swaps:
        emit_swap_states(builder, word, a, b)
    apply_inplace_linear(builder, word, rows_from_columns(columns))
    builder.x([word[k] for k in range(3) if offset >> k & 1])


def relative_scale(builder, norm, targets):
    """Map target -> target/norm for nonzero norm; replace norm by inv0(norm).

    At norm=0 every target must be 0. The circuit remains reversible, but an
    arbitrary nonzero target there is outside the stated inverse contract.
    """
    _, _, encode, decode, plans = unit_layout()
    emit_perm(builder, norm, encode)
    for target in targets:
        for bit, plan in enumerate(plans):
            for direction, form in plan:
                emit_rank_one(builder, norm[bit], target, direction, form)
    emit_perm(builder, norm, decode)


def inverse_six_deferred(builder, source):
    """Exact inverse with a zero-valued compatible deferred-mask ABI."""
    from tower_inverse import apply_inplace_linear, erase_norm, init_norm, quadratic_basis

    info = quadratic_basis(6)
    apply_inplace_linear(builder, source, info['to_tower'])
    left, right = source[:3], source[3:]
    norm = init_norm(builder, left, right, info['delta'])
    relative_scale(builder, norm, (left, right))
    builder.cx(right, left)
    erase_norm(builder, left, right, norm, info['delta'])
    builder.free(norm)
    apply_inplace_linear(builder, source, info['from_tower'])
    masks = tuple(builder.alloc_bits(3) for _ in range(2))
    for mask in masks:
        builder.bit_store(mask, False)
    return masks


def check(work, out):
    sys.path.insert(0, str(work / 'after_c5/arithmetic_t'))
    sys.path.insert(0, str(work / 'night_c27/arithmetic'))
    import c27_paths  # noqa: F401
    import nested_norm_inverse as original
    from quantum_reciprocal import bit_matrix

    records = []
    for variant in ('scale', 'inverse_baseline', 'inverse_log'):
        builder = km.CircuitBuilder()
        data = builder.create_quantum_register(6, 'data')
        probes = builder.create_classical_register(6, 'probe')
        values = np.arange(64, dtype=np.int64)
        if variant == 'scale':
            values = values[(values % 8 != 0) | (values == 0)]
            relative_scale(builder, data[:3], (data[3:],))
            expected = np.asarray([GF8.invert(int(x % 8)) ^
                                   (GF8.mul(int(x // 8), GF8.invert(int(x % 8))) << 3)
                                   if x else 0 for x in values])
        else:
            field = km.GF2Field(6)
            expected = np.asarray([field.invert(int(x)) if x else 0 for x in values])
            routine = (original.inverse_six_deferred if variant.endswith('baseline')
                       else inverse_six_deferred)
            mask = routine(builder, data)
            # Repay the existing deferred masks against a separately retained
            # entry copy. The copy costs no Toffoli and is common to both runs.
            source_copy = builder.create_quantum_register(6, 'entry_witness')
            from tower_inverse import apply_inplace_linear, quadratic_basis
            apply_inplace_linear(builder, source_copy, quadratic_basis(6)['to_tower'])
            builder.cz(mask[0], source_copy[:3])
            builder.cz(mask[1], source_copy[3:])
            apply_inplace_linear(builder, source_copy, quadratic_basis(6)['from_tower'])
            for part in mask:
                builder.free(part)
        builder.cz(probes, data)
        circuit = builder.finish_circuit()
        occupied = set(data)
        if variant != 'scale':
            occupied.update(source_copy)
        scratch = [km.q(k) for k in range(circuit.num_qubits) if km.q(k) not in occupied]
        rng = np.random.default_rng(501)
        for seed in range(8):
            sim = km.Simulator(batch_size=len(values), seed=seed)
            sim.use_same_registers_as(circuit)
            sim.write_across_shots(data, bit_matrix(values, 6))
            probe = rng.integers(0, 64, size=len(values))
            sim.write_across_shots(probes, bit_matrix(probe, 6))
            if variant != 'scale':
                sim.write_across_shots(source_copy, bit_matrix(values, 6))
            sim.do(circuit)
            assert np.array_equal(sim.read_across_shots(data), bit_matrix(expected, 6))
            if variant != 'scale':
                assert np.array_equal(sim.read_across_shots(source_copy), bit_matrix(values, 6))
            assert not scratch or not sim.read_across_shots(scratch).any()
            observed = sim.read_phase_flipped_across_shots()
            assert np.array_equal(observed, [(int(x)&int(y)).bit_count()%2
                                              for x, y in zip(expected, probe)])
        path = out / (variant + '.kmb')
        circuit.to_file(path, format='kmb')
        records.append({'variant': variant, 'width': circuit.num_qubits,
                        'toffoli': circuit.operation_statistics().num_toffoli_like,
                        'data_and_witness_width': len(occupied),
                        'extra_helpers': len(scratch), 'shots': 8 * len(values),
                        'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    return {'status': 'PASS_NATIVE_COMPONENT', 'records': records,
            'unit_exp_configuration': unit_layout()}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    result = check(args.work, args.out)
    (args.out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
