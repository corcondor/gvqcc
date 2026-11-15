# Portions derived from Syed Asad Ali, 2026. SPDX-License-Identifier: Apache-2.0.
"""Borrow retired norm storage from the existing GF24 inverse bank."""
import kickmix as km

import scalar_inverse_phase as scalar
from tower_inverse import apply_inplace_linear, kernel, phase_product, xor_product
from quantum_reciprocal import xor_linear


def visit_inverse_witness(builder, reciprocal_norm, child_norm, target, measured):
    """XOR or phase-pair the original GF12 norm using a GF64 witness."""
    left, right = reciprocal_norm[:6], reciprocal_norm[6:]
    builder.cx(right, left)
    if measured:
        phase_product(builder, left, child_norm, target[:6], kernel(6))
        builder.cx(right, left)
        phase_product(builder, right, child_norm, target[6:], kernel(6))
    else:
        xor_product(builder, left, child_norm, target[:6])
        builder.cx(right, left)
        xor_product(builder, right, child_norm, target[6:])


def borrow_norm_for_scale(builder, source, original_norm, reciprocal_norm, child_norm, basis):
    """Measure the old norm, scale both halves using its lanes, and rebuild it."""
    apply_inplace_linear(builder, original_norm, basis["to_tower"])
    apply_inplace_linear(builder, reciprocal_norm, basis["to_tower"])
    norm_mask = builder.alloc_bits(12)
    builder.hmr(original_norm, norm_mask)
    visit_inverse_witness(builder, reciprocal_norm, child_norm, norm_mask, measured=True)
    builder.free(norm_mask)
    apply_inplace_linear(builder, reciprocal_norm, basis["from_tower"])
    old_source_masks = []
    for half in (source[:12], source[12:]):
        xor_product(builder, half, reciprocal_norm, original_norm)
        builder.swap(half, original_norm)
        mask = builder.alloc_bits(12)
        builder.hmr(original_norm, mask)
        old_source_masks.append(mask)
    apply_inplace_linear(builder, reciprocal_norm, basis["to_tower"])
    visit_inverse_witness(builder, reciprocal_norm, child_norm, original_norm, measured=False)
    apply_inplace_linear(builder, reciprocal_norm, basis["from_tower"])
    apply_inplace_linear(builder, original_norm, basis["from_tower"])
    for half, mask in zip((source[:12], source[12:]), old_source_masks):
        phase_product(builder, half, original_norm, mask, kernel(12))
        builder.free(mask)


def _scale_from_classical(builder, source, multiplier, inverse_multiplier, temporary):
    xor_product(builder, source, multiplier, temporary)
    builder.swap(source, temporary)
    xor_product(builder, source, inverse_multiplier, temporary)


def _fixed_trace(builder, source, temporary):
    assert scalar.certificate()
    signals = list(source)
    records = []
    for (left, right), target in zip(scalar.GATES[:4], temporary[:4]):
        rows, undo = scalar.operand_basis(len(signals), left, right)
        view = km.array(signals)
        apply_inplace_linear(builder, view, rows)
        builder.init_and(view[0], view[1], target)
        apply_inplace_linear(builder, view, undo)
        records.append((view, target, rows, undo))
        signals.append(target)
    for left, right in scalar.GATES[4:]:
        rows, undo = scalar.operand_basis(len(signals), left, right)
        view = km.array(signals)
        apply_inplace_linear(builder, view, rows)
        builder.cz(view[0], view[1])
        apply_inplace_linear(builder, view, undo)
    for j, wire in enumerate(signals):
        if scalar.OUTPUT >> j & 1:
            builder.z(wire)
    for view, target, rows, undo in reversed(records):
        apply_inplace_linear(builder, view, rows)
        builder.del_and(view[0], view[1], target)
        apply_inplace_linear(builder, view, undo)


def repay_child_mask(builder, source, mask, temporary):
    """The public fixed trace provider using six caller-owned clean lanes."""
    assert len(source) == len(mask) == len(temporary) == 6
    multiplier = scalar.classical_word(builder)
    xor_linear(builder, mask, multiplier, scalar.trace_dual_columns())
    reciprocal, owned = scalar.classical_inverse(builder, multiplier)
    active = builder.alloc_bits(1)
    builder.bit_store(active, False)
    builder.bit_store(active[0], True, control=multiplier)
    builder.push_condition(active[0])
    _scale_from_classical(builder, source, reciprocal, multiplier, temporary)
    _fixed_trace(builder, source, temporary)
    _scale_from_classical(builder, source, multiplier, reciprocal, temporary)
    builder.pop_condition()
    for word in owned:
        builder.free(word)
    builder.free(active)
    builder.free(multiplier)
