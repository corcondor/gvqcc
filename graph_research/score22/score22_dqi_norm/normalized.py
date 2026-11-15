"""Norm-reduced consuming GF24 quotient with a fixed, nonzero low source word."""
import kickmix as km

import gf24_nested_norm as arithmetic
from modular_quadratic_direct import repay_twelve_source
from nested_norm_inverse import inverse_twelve_deferred
from field_tensor import accumulate_product, invert_binary_columns
from tower_inverse import apply_inplace_linear, kernel, phase_product, xor_product
from quantum_reciprocal import xor_linear


def columns(function):
    return tuple(function(1 << i) for i in range(12))


def rows(col):
    return tuple(sum((value >> i & 1) << j for j,value in enumerate(col))
                 for i in range(12))


def fixed_scale(builder, word, coefficient):
    field = arithmetic.FIELD
    apply_inplace_linear(builder, word, rows(columns(lambda x: field.mul(coefficient,x))))


def norm_add(builder, r, out, delta):
    field = arithmetic.FIELD
    builder.x(out[0])
    xor_linear(builder, r, out, columns(lambda x: x ^ field.mul(delta,field.mul(x,x))))


def divide_fixed_low(builder, source, target, low_word=1, delta=2048):
    """On source low=public nonzero value, restore source and consume target."""
    field = arithmetic.FIELD
    assert 0 < low_word < 4096
    assert len(source) == len(target) == 24 and not set(source).intersection(target)
    norm, r = source[:12],source[12:]
    x,y = target[:12],target[12:]
    if low_word != 1:
        inverse = field.invert(low_word)
        for word in (r,x,y):
            fixed_scale(builder, word, inverse)
    xor_product(builder,r,x,y)
    for i in range(12):
        if low_word >> i & 1:
            builder.x(norm[i])
    norm_add(builder,r,norm,delta)
    original_norm_debts = inverse_twelve_deferred(builder,norm)
    temporary = builder.alloc_qubits(12)
    norm_add(builder,r,temporary,delta)
    repay_twelve_source(builder,temporary,original_norm_debts)
    norm_add(builder,r,temporary,delta)
    xor_product(builder,norm,y,temporary)
    builder.swap(y,temporary)
    old_y = builder.alloc_bits(12)
    builder.hmr(temporary,old_y)
    builder.free(temporary)
    inverse_mask = builder.alloc_bits(12)
    builder.hmr(norm,inverse_mask)
    norm_add(builder,r,norm,delta)
    arithmetic.Phase12.phase_inverse_twelve_polynomial(builder,norm,inverse_mask)
    builder.free(inverse_mask)
    phase_product(builder,norm,y,old_y,kernel(12))
    builder.free(old_y)
    norm_add(builder,r,norm,delta)
    for i in range(12):
        if low_word >> i & 1:
            builder.x(norm[i])
    accumulate_product(builder,r,y,x,[(a,b,field.mul(delta,c)) for a,b,c in kernel(12)])
    if low_word != 1:
        fixed_scale(builder, r, low_word)
