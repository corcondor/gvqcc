"""Narrow K24 quotient prefix exposing a norm-only phase debt to the return."""
from dataclasses import dataclass

import kickmix as km

from coherent_border import toggle_zero
from quantum_reciprocal import xor_linear
from tower_inverse import apply_inplace_linear, kernel, phase_product, quadratic_basis, xor_product

import quotient_phase
import schur


@dataclass
class PrefixDebt:
    old_target_mask: object
    cofactor_mask: object


def divide_deferred(builder, source, target):
    """Source restored, exact quotient in target and two classical phase masks."""
    assert len(source) == len(target) == 24 and not set(source).intersection(target)
    a,b = source[:12],source[12:]
    x,y = target[:12],target[12:]
    pivot = builder.alloc_qubits(1)
    toggle_zero(builder,a,pivot[0])
    builder.cswap(pivot[0],a,b)
    # Keep the scalar reciprocal live throughout the Schur elimination.
    # The masks on x,y already refer to the original full K24 target.
    scalar_debt = schur._invert_and_pay(builder,a,())
    old_b, old_x, old_y = schur._scale_words(builder,a,(b,x,y))
    xor_product(builder,b,x,y)
    saved = builder.alloc_qubits(1)
    r_view = km.array([*b,*saved])
    forward,backward = schur.schur_move()
    apply_inplace_linear(builder,r_view,forward)
    builder.x(b[0])
    denom_debt = schur._invert_and_pay(builder,b,())
    prior_y = schur._scale_words(builder,b,(y,))
    inverse_debt = schur._invert_and_pay(builder,b,denom_debt)
    schur._repay_scales(builder,b,(y,),prior_y)

    inverse_mask = builder.alloc_bits(12)
    builder.bit_store(inverse_mask,False)
    xor_linear(builder,schur._joined(inverse_debt),inverse_mask,quadratic_basis(12)["to_tower"])
    for word in inverse_debt:
        builder.free(word)
    # When pivot=1 the selected chart has b=0, thus D(r)=1.
    # On the other chart the owed inverse is original a²/N(source).
    builder.cz(inverse_mask[0],pivot[0])
    builder.x(b[0])
    apply_inplace_linear(builder,r_view,backward)
    builder.free(saved)
    schur._upper_shear(builder,b,x,y)

    scalar_inverse_debt = schur._invert_and_pay(builder,a,scalar_debt)
    old_ratio = schur._scale_words(builder,a,(b,))[0]
    builder.cz(old_b,b)
    builder.free(old_b)
    quotient_phase.phase_linear_numerator(
        builder,a,b,old_ratio,schur._joined(scalar_inverse_debt))
    builder.free(old_ratio)
    for word in scalar_inverse_debt:
        builder.free(word)
    builder.cswap(pivot[0],a,b)
    schur.qconstant_mul_theta(builder,pivot[0],target,inverse=True)
    toggle_zero(builder,a,pivot[0])
    builder.free(pivot)
    return PrefixDebt(schur._joined((old_x,old_y)), inverse_mask)


def phase_cofactor(builder, source, inverse_norm, mask):
    """Pay dot(mask,a²/N(source)) at the existing inverse-norm seam."""
    a = source[:12]
    square = tuple(schur.FIELD.mul(1 << i,1 << i) for i in range(12))
    apply_inplace_linear(builder,a,schur.rows(square))
    phase_product(builder,a,inverse_norm,mask,kernel(12))
    apply_inplace_linear(builder,a,schur.invert_binary_columns(square))
    builder.free(mask)


def restore_with_existing_norm(builder, source, target, record, *,
                               next_word=None, next_input_record=None):
    """Use the existing direct-carry return with its rank-99 products intact."""
    import direct_carry_arithmetic as original

    assert (next_word is None) == (next_input_record is None)
    delta = schur.DELTA
    arithmetic = original.A
    head_return = arithmetic.emit_prefix(builder, source, target, delta)
    next_mask = None
    if next_word is not None:
        next_mask = original._adjoint_consume(builder, source, next_word, delta)
    inverse_norm = original._inverse_norm(builder, source, delta)
    phase_cofactor(builder, source, inverse_norm, record.cofactor_mask)
    record.cofactor_mask = None
    next_adjoint = None
    if next_word is not None:
        next_adjoint = original._consume_halves(builder, inverse_norm, next_word)

    builder.cz(record.old_target_mask, target)
    builder.free(record.old_target_mask)
    record.old_target_mask = None
    original._quotient_phase_with_norm(
        builder,source,inverse_norm,target,head_return.old_target_mask,delta)
    arithmetic.free_product_mask(builder,head_return)
    if next_word is not None:
        phase_product(builder,source,next_word,next_mask,arithmetic.tensor24(delta))
        builder.free(next_mask)
        arithmetic.repay_product_input(builder,next_word,next_input_record)

    from tower_inverse import erase_norm, init_norm
    inverse_mask = builder.alloc_bits(12)
    builder.hmr(inverse_norm,inverse_mask)
    builder.free(inverse_norm)
    norm = init_norm(builder,source[:12],source[12:],delta)
    original.Phase12.phase_inverse_twelve_polynomial(builder,norm,inverse_mask)
    builder.free(inverse_mask)
    if next_word is not None:
        for half,mask in zip((next_word[:12],next_word[12:]),next_adjoint):
            phase_product(builder,norm,half,mask,kernel(12))
            builder.free(mask)
    erase_norm(builder,source[:12],source[12:],norm,delta)
    builder.free(norm)
