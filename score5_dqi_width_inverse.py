# Copyright 2026 Syed Asad Ali. SPDX-License-Identifier: Apache-2.0.
# Credits: Opus and Astra.
"""Child-norm pebbling derivative of the exact matched GF24 inverse.

Adds 12 (one bit) or 30 (six bits) CCX per inverse to reduce its temporary
helper peak by one or six. Source and all measurement-phase contracts are
unchanged. Derived from outcome_dqi_chart_inverse_norm.py; retained credits.

Original documentation: optional coherent zero query at its existing GF4 norm.

Experimental derivative of the cited public module. The only algorithm change
is forwarding zero_flag to the already-supported cubic inverse API (one CCX).
The unmodified no-flag pair ledger below does not include that optional CCX.

Matched inverse pair with one deferred six-bit child-norm phase.

Both calls use twenty-four caller-owned zero bits and at most24 extra
helpers. Prefix191 returns the actual tower-child HMR mask. Return195
pays it against its existing child reciprocal before that witness changes.
Each call resets all owned bank bits; inv0 includes the zero source.
"""
from __future__ import annotations

from dataclasses import dataclass
# Establish the same frozen source search path as the production adapter.
from outcome_dqi_chart_third_norm import WORK
import kickmix as km
import gf24_nested_norm as Arithmetic
import cubic_inverse130 as Cubic
import scalar_inverse_phase as Scalar
from quantum_reciprocal import xor_linear
from tower_inverse import (quadratic_basis, apply_inplace_linear, norm_columns,
                           xor_product, phase_product, erase_norm, kernel)


@dataclass
class PrefixRecord:
    builder_id: int
    source: tuple
    delta: int
    child_mask: object
    prefix_static_T: int = 191
    child_mask_bits: int = 6
    closed: bool = False


def _xor_norm(builder, left, right, target, delta):
    squares_left, squares_right = norm_columns(len(left), delta)
    xor_product(builder, left, right, target)
    xor_linear(builder, left, target, squares_left)
    xor_linear(builder, right, target, squares_right)


def _surcharge(borrow_bits):
    return 12 if borrow_bits == 1 else 30


def _xor_norm_bit(builder, left, right, target, delta, bit=0):
    """XOR one GF64 norm coordinate using six independent product rows.

    N(L,R)=L^2+L*R+delta*R^2. For each input L_i, the selected
    product output bit is L_i times a parity of the R_j. Nonzero
    trace-pairing rows require exactly six CCX, and all pivots restore.
    """
    assert len(left) == len(right) == 6
    field = km.GF2Field(6)
    squares_left, squares_right = norm_columns(6, delta)
    for i in range(6):
        selected = [right[j] for j in range(6)
                    if (field.mul(1 << i, 1 << j) >> bit) & 1]
        assert selected
        pivot = selected[0]
        for wire in selected[1:]:
            builder.cx(wire, pivot)
        builder.ccx(left[i], pivot, target)
        for wire in reversed(selected[1:]):
            builder.cx(wire, pivot)
        if (squares_left[i] >> bit) & 1:
            builder.cx(left[i], target)
        if (squares_right[i] >> bit) & 1:
            builder.cx(right[i], target)


def _toggle_borrowed_child(builder, original_norm, child_norm, info, borrow_bits):
    apply_inplace_linear(builder, original_norm, info['to_tower'])
    if borrow_bits == 6:
        _xor_norm(builder, original_norm[:6], original_norm[6:], child_norm, info['delta'])
    else:
        _xor_norm_bit(builder, original_norm[:6], original_norm[6:], child_norm[0], info['delta'])
    apply_inplace_linear(builder, original_norm, info['from_tower'])


def _inverse_with_bank(builder, source, clean_bank, delta,
                       *, defer_child=False, prefix_record=None, zero_flag=None, borrow_bits=1):
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
    if borrow_bits not in (1, 6):
        raise ValueError('this proved provider supports one or all six child-norm bits')
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
    # The child norm is a deterministic quadratic function of original_norm.
    # Erase it coherently while its original parents survive; borrow the clean
    # storage only through consuming products that reset all targets with HMR.
    _toggle_borrowed_child(builder, original_norm, child_norm, info, borrow_bits)
    owned_temporary = builder.alloc_qubits(12 - borrow_bits)
    temporary = km.array([*owned_temporary, *child_norm[:borrow_bits]])
    masks = []
    for half in (source[:12], source[12:]):
        xor_product(builder, half, inverse_norm, temporary)
        builder.swap(half, temporary)
        mask = builder.alloc_bits(12)
        builder.hmr(temporary, mask)
        masks.append(mask)
    builder.free(owned_temporary)
    for half, mask in zip((source[:12], source[12:]), masks):
        phase_product(builder, half, original_norm, mask, kernel(12))
        builder.free(mask)

    # Each borrowed bit is zero after the second target HMR. Restore the exact
    # polynomial child norm before the retained-child phase witness is used.
    _toggle_borrowed_child(builder, original_norm, child_norm, info, borrow_bits)

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
        Scalar.phase_inverse_six(builder, child_inverse, child_mask)
        builder.free(child_mask)
    erase_norm(builder, inverse_left, inverse_right, child_inverse, info['delta'])
    apply_inplace_linear(builder, inverse_norm, info['from_tower'])
    builder.cx(source[12:], source[:12])
    erase_norm(builder, source[:12], source[12:], inverse_norm, delta)
    builder.free(inverse_norm)
    assert builder.num_allocated_qubits == before
    if defer_child:
        return PrefixRecord(id(builder), tuple(source), delta, child_mask,
                            prefix_static_T=191 + int(zero_flag is not None) + _surcharge(borrow_bits))
    if prefix_record is not None:
        prefix_record.closed = True
    return dict(inverse_static_T=195 + int(zero_flag is not None) + _surcharge(borrow_bits), retained_storage_bits=24,
                original_norm_bits=12, child_norm_bits=6, child_inverse_bits=6,
                scalar_inverse_phase_static_T=4, maximum_additional_helpers=24 - borrow_bits,
                borrowed_child_norm_bits=borrow_bits, extra_static_T=_surcharge(borrow_bits),
                all_owned_storage_bits_reset=True,
                deferred_prefix_mask_paid=prefix_record is not None)


def inverse_prefix_with_bank(builder, source, clean_bank,
                             delta=Arithmetic.DEFAULT_DELTA, *, zero_flag=None, borrow_bits=1):
    """Map S to inv0(S), reset the bank, return its exact six-bit phase debt."""
    return _inverse_with_bank(builder, source, clean_bank, delta, defer_child=True, zero_flag=zero_flag, borrow_bits=borrow_bits)


def inverse_return_with_bank(builder, source, clean_bank, record,
                             delta=Arithmetic.DEFAULT_DELTA, *, zero_flag=None, borrow_bits=1):
    """Restore the prefix entry and pay its stored mask before witness reuse.

The same physical source must contain inv0(the prefix entry), as ensured by
the matched compute/uncompute caller. This is a quantum value contract,
not a value inspected or certified by Python.
"""
    if not isinstance(record, PrefixRecord):
        raise TypeError('the matched return requires its actual prefix record')
    return _inverse_with_bank(builder, source, clean_bank, delta,
                              prefix_record=record, zero_flag=zero_flag, borrow_bits=borrow_bits)


def source_ledger():
    return dict(status='PEBBLED_SOURCE_NATIVE_PENDING',
                baseline_prefix_static_T=191, baseline_return_static_T=195,
                one_bit_extra_T_per_call=12, six_bit_extra_T_per_call=30,
                one_bit_peak_additional_helpers=23, six_bit_peak_additional_helpers=18,
                all_owned_storage_bits_reset=True,
                scope='Same exact inv0/deferred child-mask contract; no global width claim')
