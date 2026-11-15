"""234T/12-helper GF24 division when a target belongs to a fixed GF12 line."""
from dataclasses import dataclass

import kickmix as km

import gf24_nested_norm as arithmetic
from nested_norm_inverse import inverse_twelve_deferred
from quantum_reciprocal import xor_linear
from tower_inverse import apply_inplace_linear, kernel, norm_columns, phase_product, xor_product


@dataclass
class LineDebt:
    old_scalar: object
    norm_mask: object
    scaled_input: object
    line: int


def _public_scale(builder, wires, value, delta):
    col = [arithmetic.mul24(value, 1<<i, delta) for i in range(24)]
    rows = [sum((v>>i&1)<<j for j,v in enumerate(col)) for i in range(24)]
    apply_inplace_linear(builder,wires,rows)


def divide_line(builder, source, target, *, line=1, delta=2048):
    """Consume target/denominator with target initially in line*GF(4096)."""
    assert line and len(source)==len(target)==24 and not set(source).intersection(target)
    if line != 1:
        _public_scale(builder,target,arithmetic.inverse24(line,delta),delta)
    a,b = source[:12],source[12:]
    x,norm = target[:12],target[12:]
    u,v=norm_columns(12,delta)
    xor_product(builder,a,b,norm)
    xor_linear(builder,a,norm,u)
    xor_linear(builder,b,norm,v)
    norm_debts=inverse_twelve_deferred(builder,norm)
    arithmetic._repay_norm_source_masks(builder,source,norm_debts,delta)
    temporary=builder.alloc_qubits(12)
    xor_product(builder,x,norm,temporary)

    norm_mask=builder.alloc_bits(12)
    old_scalar=builder.alloc_bits(12)
    builder.hmr(norm,norm_mask)
    builder.hmr(x,old_scalar)
    xor_product(builder,b,temporary,norm)
    builder.cx(b,a)
    xor_product(builder,a,temporary,x)
    builder.cx(b,a)
    p_mask=builder.alloc_bits(12)
    builder.hmr(temporary,p_mask)
    builder.free(temporary)
    if line != 1:
        _public_scale(builder,target,line,delta)
    return LineDebt(old_scalar,norm_mask,p_mask,line)


def repay_line(builder, original_target, inverse_norm, debt, delta=2048):
    """Repay all three masks once target and the existing inverse norm are live."""
    if debt.line != 1:
        _public_scale(builder,original_target,arithmetic.inverse24(debt.line,delta),delta)
    x = original_target[:12]
    builder.cz(debt.old_scalar,x)
    builder.cz(debt.norm_mask,inverse_norm)
    phase_product(builder,x,inverse_norm,debt.scaled_input,kernel(12))
    if debt.line != 1:
        _public_scale(builder,original_target,debt.line,delta)
    for mask in (debt.old_scalar,debt.norm_mask,debt.scaled_input):
        builder.free(mask)
