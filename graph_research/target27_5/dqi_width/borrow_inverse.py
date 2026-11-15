# Copyright 2026 Syed Asad Ali. SPDX-License-Identifier: Apache-2.0.
# Credits: Opus and Astra.
"""Matched GF24 inverse with a measured and reconstructed norm lifetime."""
from __future__ import annotations

from dataclasses import dataclass
import kickmix as km
import gf24_nested_norm as Arithmetic
import cubic_inverse130 as Cubic
from retained_scale import borrow_norm_for_scale, repay_child_mask
from quantum_reciprocal import xor_linear
from tower_inverse import (quadratic_basis, apply_inplace_linear, norm_columns,
                           xor_product, phase_product, erase_norm, kernel)


@dataclass
class PrefixRecord:
    builder_id: int
    source: tuple
    delta: int
    child_mask: object
    prefix_static_T: int = 221
    child_mask_bits: int = 6
    closed: bool = False


def _xor_norm(builder, left, right, target, delta):
    squares_left, squares_right = norm_columns(len(left), delta)
    xor_product(builder, left, right, target)
    xor_linear(builder, left, target, squares_left)
    xor_linear(builder, right, target, squares_right)


def _inverse_with_bank(builder, source, clean_bank, delta,
                       *, defer_child=False, prefix_record=None, zero_flag=None):
    """Exact inverse map; only the declared child-mask debt may remain open."""
    if len(source) != 24 or len(clean_bank) != 24:
        raise ValueError('one K24 source and twenty-four clean owned bits are required')
    quantum = [*source, *clean_bank]
    if not all(isinstance(wire, km.q) for wire in quantum):
        raise TypeError('source and clean storage bank must be quantum')
    if len(set(quantum)) != len(quantum):
        raise ValueError('source and clean storage bank must be disjoint')
    if delta != Arithmetic.DEFAULT_DELTA:
        raise ValueError('this provider is bound to the production extension')
    if prefix_record is not None:
        if defer_child or not isinstance(prefix_record, PrefixRecord):
            raise TypeError('the matched return requires a prefix record')
        if (prefix_record.closed or prefix_record.builder_id != id(builder)
                or prefix_record.source != tuple(source) or prefix_record.delta != delta
                or len(prefix_record.child_mask) != 6):
            raise ValueError('prefix record does not own this exact open inverse debt')
    if zero_flag is not None:
        if not isinstance(zero_flag, km.q) or zero_flag in quantum:
            raise ValueError('The infinity flag must be a distinct owned quantum bit')
    before = builder.num_allocated_qubits
    original_norm, child_norm, child_inverse = clean_bank[:12], clean_bank[12:18], clean_bank[18:]
    _xor_norm(builder, source[:12], source[12:], original_norm, delta)
    info = quadratic_basis(12)
    apply_inplace_linear(builder, original_norm, info['to_tower'])
    left, right = original_norm[:6], original_norm[6:]
    _xor_norm(builder, left, right, child_norm, info['delta'])
    returned = Cubic.inverse_six_cubic(builder, child_norm, target=child_inverse, zero_flag=zero_flag)
    assert tuple(returned) == tuple(child_inverse)
    assert builder.num_allocated_qubits == before

    # The return input is the inverse of the exact prefix entry. Its child
    # reciprocal is therefore the prefix entry's original child norm.
    # The saved mask belongs to that value's quadratic6 tower coordinates.
    if prefix_record is not None:
        child_info = quadratic_basis(6)
        apply_inplace_linear(builder, child_inverse, child_info['to_tower'])
        builder.cz(prefix_record.child_mask, child_inverse)
        apply_inplace_linear(builder, child_inverse, child_info['from_tower'])
        builder.free(prefix_record.child_mask)

    inverse_norm = builder.alloc_qubits(12)
    builder.cx(right, left)
    xor_product(builder, left, child_inverse, inverse_norm[:6])
    builder.cx(right, left)
    xor_product(builder, right, child_inverse, inverse_norm[6:])
    apply_inplace_linear(builder, inverse_norm, info['from_tower'])
    apply_inplace_linear(builder, original_norm, info['from_tower'])
    borrow_norm_for_scale(builder, source, original_norm, inverse_norm, child_norm, info)

    # HMR the original norm in the exact tower coordinates used by its
    # retained-child reconstruction. If inverse_norm=(X,Y), the original
    # norm is((X+Y)*child_norm, Y*child_norm), also when both are zero.
    apply_inplace_linear(builder, original_norm, info['to_tower'])
    norm_mask = builder.alloc_bits(12)
    builder.hmr(original_norm, norm_mask)
    apply_inplace_linear(builder, inverse_norm, info['to_tower'])
    inverse_left, inverse_right = inverse_norm[:6], inverse_norm[6:]
    builder.cx(inverse_right, inverse_left)
    phase_product(builder, inverse_left, child_norm, norm_mask[:6], kernel(6))
    builder.cx(inverse_right, inverse_left)
    phase_product(builder, inverse_right, child_norm, norm_mask[6:], kernel(6))
    builder.free(norm_mask)

    # This mask belongs to tower(child_norm), not its polynomial encoding.
    # The accepted scalar phase explicitly expects this tower-mask ABI.
    child_info = quadratic_basis(6)
    apply_inplace_linear(builder, child_norm, child_info['to_tower'])
    child_mask = builder.alloc_bits(6)
    builder.hmr(child_norm, child_mask)
    if not defer_child:
        repay_child_mask(builder, child_inverse, child_mask, original_norm[:6])
        builder.free(child_mask)
    erase_norm(builder, inverse_left, inverse_right, child_inverse, info['delta'])
    apply_inplace_linear(builder, inverse_norm, info['from_tower'])
    builder.cx(source[12:], source[:12])
    erase_norm(builder, source[:12], source[12:], inverse_norm, delta)
    builder.free(inverse_norm)
    assert builder.num_allocated_qubits == before
    if defer_child:
        return PrefixRecord(id(builder), tuple(source), delta, child_mask,
                            prefix_static_T=221 + int(zero_flag is not None))
    if prefix_record is not None:
        prefix_record.closed = True
    return dict(inverse_static_T=225 + int(zero_flag is not None), retained_storage_bits=24,
                original_norm_bits=12, child_norm_bits=6, child_inverse_bits=6,
                scalar_inverse_phase_static_T=4, maximum_additional_helpers=12,
                all_owned_storage_bits_reset=True,
                deferred_prefix_mask_paid=prefix_record is not None)


def inverse_prefix_with_bank(builder, source, clean_bank,
                             delta=Arithmetic.DEFAULT_DELTA, *, zero_flag=None):
    """Map S to inv0(S), reset the bank, return its exact six-bit phase debt."""
    return _inverse_with_bank(builder, source, clean_bank, delta, defer_child=True, zero_flag=zero_flag)


def inverse_return_with_bank(builder, source, clean_bank, record,
                             delta=Arithmetic.DEFAULT_DELTA, *, zero_flag=None):
    """Restore the prefix entry and pay its stored mask before witness reuse.

The same physical source must contain inv0(the prefix entry), as ensured by
the matched compute/uncompute caller. This is a quantum value contract,
not a value inspected or certified by Python.
"""
    if not isinstance(record, PrefixRecord):
        raise TypeError('the matched return requires its actual prefix record')
    return _inverse_with_bank(builder, source, clean_bank, delta,
                              prefix_record=record, zero_flag=zero_flag)

