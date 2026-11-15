"""Coherent in-place GF24 multiply/divide via an adaptive two-by-two PLU."""

from argparse import ArgumentParser
from functools import cache
from hashlib import file_digest
import json
from pathlib import Path
import sys

import numpy as np


def join(words):
    import kickmix as km
    return km.array([q for word in words for q in word])


def classical_zero(builder, count):
    mask = builder.alloc_bits(count)
    builder.bit_store(mask, False)
    return mask


def consume_scalar(builder, target, multiplier):
    from tower_inverse import xor_product

    temporary = builder.alloc_qubits(12)
    xor_product(builder, target, multiplier, temporary)
    builder.swap(target, temporary)
    mask = builder.alloc_bits(12)
    builder.hmr(temporary, mask)
    builder.free(temporary)
    return mask


def repay_scalar(builder, result, reciprocal, mask):
    from tower_inverse import kernel, phase_product

    phase_product(builder, result, reciprocal, mask, kernel(12))
    builder.free(mask)


def visit_inverse(builder, source, action):
    """Visit inv0(source), run action, and restore source with exact phase."""
    from nested_norm_inverse import inverse_twelve_deferred
    from phase_inverse12 import phase_inverse_twelve_polynomial
    from quantum_reciprocal import xor_linear
    from tower_inverse import apply_inplace_linear, quadratic_basis

    before = inverse_twelve_deferred(builder, source)
    intermediate = action()
    on_return = inverse_twelve_deferred(builder, source)
    basis = quadratic_basis(12)
    apply_inplace_linear(builder, source, basis["to_tower"])
    builder.cz(join(before), source)
    apply_inplace_linear(builder, source, basis["from_tower"])
    for mask in before:
        builder.free(mask)
    standard = classical_zero(builder, 12)
    xor_linear(builder, join(on_return), standard, basis["to_tower"])
    for mask in on_return:
        builder.free(mask)
    phase_inverse_twelve_polynomial(builder, source, standard)
    builder.free(standard)
    return intermediate


@cache
def determinant_encoding(delta):
    """Extend r -> r + delta*r^2 to an invertible 13-wire map."""
    import kickmix as km
    from field_tensor import invert_binary_columns
    from tower_inverse import rows_from_columns

    field = km.GF2Field(12)
    kernel = field.invert(delta)
    selector = (kernel & -kernel).bit_length() - 1
    partial = []
    for index in range(12):
        basis = 1 << index
        image = basis ^ field.mul(delta, field.mul(basis, basis))
        partial.append(image | ((1 << 12) if index == selector else 0))
    for bit in range(12):
        columns = [*partial, 1 << bit]
        try:
            undo = invert_binary_columns(columns)
        except ValueError:
            continue
        assert any(column >> 12 for column in columns)
        return rows_from_columns(columns), undo
    raise ValueError("Could not extend the rank-eleven determinant form")


def visit_determinant(builder, normalized, delta, action):
    from tower_inverse import apply_inplace_linear

    sentinel = builder.alloc_qubits(1)
    view = join([normalized, sentinel])
    direction, undo = determinant_encoding(delta)
    apply_inplace_linear(builder, view, direction)
    builder.x(normalized[0])
    result = action()
    builder.x(normalized[0])
    apply_inplace_linear(builder, view, undo)
    builder.free(sentinel)
    return result


@cache
def multiplication_terms(delta):
    import kickmix as km
    from tower_inverse import kernel

    field = km.GF2Field(12)
    return [(x, y, field.mul(delta, w)) for x, y, w in kernel(12)]


def transvections(columns):
    """Write a constant GL(n,2) matrix as rank(A-I) transvections."""
    n = len(columns)
    cols = list(columns)
    swaps = []
    while cols != [1 << i for i in range(n)]:
        fixed = [x for x in range(1 << n)
                 if apply_columns(cols, x) == x]
        x = next(i for i in range(1, 1 << n) if apply_columns(cols, i) != i)
        v = apply_columns(cols, x) ^ x
        parity = next(mask for mask in range(1, 1 << n)
                      if parity_of(v, mask) == 0 and parity_of(x, mask) == 1
                      and all(parity_of(old, mask) == 0 for old in fixed))
        cols = [word ^ (v if parity_of(word, parity) else 0) for word in cols]
        swaps.append((v, parity))
    return tuple(reversed(swaps))


def parity_of(word, mask):
    return (word & mask).bit_count() & 1


def apply_columns(cols, x):
    value = 0
    while x:
        low = x & -x
        value ^= cols[low.bit_length() - 1]
        x ^= low
    return value


@cache
def constant_scale(scalar):
    import kickmix as km

    field = km.GF2Field(12)
    return transvections(tuple(field.mul(scalar, 1 << i) for i in range(12)))


def controlled_scale(builder, flag, word, scalar):
    from field_tensor import parity_pivot

    for direction, parity in constant_scale(scalar):
        low = direction & -direction
        pivot = low.bit_length() - 1
        fanout = [q for i, q in enumerate(word) if i != pivot and direction >> i & 1]
        for q in fanout:
            builder.cx(word[pivot], q)
        control_parity = parity & ~low
        control = parity_pivot(builder, word, control_parity)
        builder.ccx(flag, control, word[pivot])
        parity_pivot(builder, word, control_parity)
        for q in reversed(fanout):
            builder.cx(word[pivot], q)


def controlled_theta(builder, flag, x, y, delta, inverse=False):
    import kickmix as km

    if inverse:
        controlled_scale(builder, flag, x, km.GF2Field(12).invert(delta))
        builder.ccx(flag, x, y)
        builder.cswap(flag, x, y)
    else:
        builder.cswap(flag, x, y)
        builder.ccx(flag, x, y)
        controlled_scale(builder, flag, x, delta)


def consume(builder, source, target, delta=2048, *, inverse=False):
    """Multiply or divide the target. Source unit, or source=target=0.

    Forward returns (0, m_y), representing exactly the original target
    phase. The inverse mode pays all its internal phases and returns None.
    """
    from coherent_border import toggle_zero
    from field_tensor import accumulate_product
    from tower_inverse import xor_product

    assert len(source) == len(target) == 24 and not set(source) & set(target)
    old_allocation = builder.num_allocated_qubits
    a, b = source[:12], source[12:]
    x, y = target[:12], target[12:]
    flag = builder.alloc_qubits(1)
    toggle_zero(builder, a, flag[0])
    builder.cswap(flag[0], a, b)
    if inverse:
        controlled_theta(builder, flag[0], x, y, delta, inverse=True)

    def begin():
        original_b = consume_scalar(builder, b, a)
        scales = [consume_scalar(builder, word, a) for word in (x, y)] if inverse else []
        return original_b, scales

    old_b, inverse_scale = visit_inverse(builder, a, begin)
    if inverse:
        for word, mask in zip((x, y), inverse_scale):
            repay_scalar(builder, word, a, mask)
        xor_product(builder, b, x, y)
        visit_determinant(
            builder, b, delta,
            lambda: repay_scalar(builder, y, b, visit_inverse(
                builder, b, lambda: consume_scalar(builder, y, b))),
        )
        accumulate_product(builder, b, y, x, multiplication_terms(delta))
        old_target_y = None
        scaled = []
    else:
        accumulate_product(builder, b, y, x, multiplication_terms(delta))
        old_target_y = visit_determinant(
            builder, b, delta, lambda: consume_scalar(builder, y, b),
        )
        xor_product(builder, b, x, y)
        scaled = [consume_scalar(builder, word, a) for word in (x, y)]
    normalized_b = consume_scalar(builder, b, a)

    def restore_phase():
        repay_scalar(builder, b, a, normalized_b)
        for word, mask in zip((x, y), scaled):
            repay_scalar(builder, word, a, mask)

    visit_inverse(builder, a, restore_phase)
    builder.cz(old_b, b)
    builder.free(old_b)
    if not inverse:
        controlled_theta(builder, flag[0], x, y, delta)
    builder.cswap(flag[0], a, b)
    toggle_zero(builder, a, flag[0])
    builder.free(flag)
    assert builder.num_allocated_qubits == old_allocation
    if inverse:
        return None
    old_target = classical_zero(builder, 24)
    builder.cx(old_target_y, old_target[12:])
    builder.free(old_target_y)
    return old_target


def words(w, signals):
    return ((signals[None, :] >> np.arange(w, dtype=np.uint32)[:, None]) & 1).astype(bool)


def run(km, source_module, out, count):
    v = km.CircuitBuilder()
    u = v.create_quantum_register(24, "source")
    target = v.create_quantum_register(24, "target")
    probe = v.create_classical_register(24, "probe")
    retired = v.create_classical_register(24, "retired")
    debit = consume(v, u, target)
    v.cx(debit, retired)
    prefix = v.finish_circuit()
    v.cz(probe, target)
    consume(v, u, target, inverse=True)
    v.cz(debit, target)
    v.free(debit)
    assert v.num_allocated_qubits == 48
    pair = v.finish_circuit()

    rng = np.random.default_rng(549816)
    source = rng.integers(1, 1 << 24, count, dtype=np.uint32)
    source[::4] = rng.integers(1, 4096, len(source[::4]), dtype=np.uint32)
    source[1::4] = rng.integers(1, 4096, len(source[1::4]), dtype=np.uint32) << 12
    data = rng.integers(0, 1 << 24, count, dtype=np.uint32)
    source[0] = data[0] = 0
    check = rng.integers(0, 1 << 24, count, dtype=np.uint32)
    truth = np.asarray([source_module.mul24(int(x), int(y)) for x, y in zip(source, data)])
    table = dict(source=words(24, source), target=words(24, data),
                 probe=words(24, check))
    out.mkdir(parents=True, exist_ok=True)
    receipts = []
    for label, circuit, closed in (("prefix", prefix, False), ("closed", pair, True)):
        path = out / (label + ".kmb")
        circuit.to_file(path, format="kmb")
        item = km.Circuit.from_file(path)
        counts = []
        for seed in (1049782, 551962):
            sim = km.Simulator(batch_size=count, seed=seed, counting_operations=True)
            sim.use_same_registers_as(item)
            for name, values in table.items():
                sim.write_across_shots(item.register_data[name], values)
            sim.do(item)
            assert np.array_equal(sim.read_across_shots(item.register_data["source"]), table["source"])
            assert np.array_equal(sim.read_across_shots(item.register_data["target"]),
                                  table["target"] if closed else words(24, truth))
            debt = np.asarray(sim.read_across_shots(item.register_data["retired"]))
            assert not debt[:12].any()
            phase = np.count_nonzero(
                (table["probe"] & words(24, truth)) if closed else (debt & table["target"]),
                axis=0,
            ) % 2
            assert np.array_equal(sim.read_phase_flipped_across_shots(), phase)
            scratch = km.array([km.q(j) for j in range(48, item.num_qubits)])
            assert not np.asarray(sim.read_across_shots(scratch)).any()
            counts.append(sim.operation_statistics().num_toffoli_like / count)
        with path.open("rb") as stream:
            digest = file_digest(stream, "sha256").hexdigest()
        row = dict(circuit=label, peak_helpers=item.num_qubits - 48,
                   static_T=item.operation_statistics().num_toffoli_like,
                   measured_mean_T=counts, operations=len(item),
                   shots=2 * count, sha256=digest)
        receipts.append(row)
        print(row, flush=True)
    (out / "result.json").write_text(json.dumps(receipts, indent=2) + "\n")


def main():
    cli = ArgumentParser(description=__doc__)
    cli.add_argument("--source", type=Path, required=True)
    cli.add_argument("--out", type=Path, required=True)
    cli.add_argument("--shots", type=int, default=4096)
    args = cli.parse_args()
    for rel in ("after_c5/extractor_width", "night_c27/arithmetic", "after_c5/arithmetic_t"):
        sys.path.insert(0, str(args.source / rel))
    import ew_paths  # noqa: F401
    import gf24_nested_norm as source_module
    import kickmix as km

    run(km, source_module, args.out, args.shots)


if __name__ == "__main__":
    main()
