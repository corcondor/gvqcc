"""Low-width GF12 quotient trace phase with quantum numerator."""
import kickmix as km

from cubic_inverse130 import _phase_trace_triple
from nested_norm_inverse import inverse_six_deferred, repay_norm_entry
from scalar_inverse_phase import phase_inverse_six
from tower_inverse import apply_inplace_linear, erase_norm, init_norm, quadratic_basis


def phase_trace_quotient(builder, denominator, numerator):
    """Apply Tr(numerator/denominator) using twelve work qubits."""
    assert len(numerator) == len(denominator) == 12 and not set(numerator).intersection(denominator)
    basis = quadratic_basis(12)
    apply_inplace_linear(builder, denominator, basis["to_tower"])
    apply_inplace_linear(builder, numerator, basis["to_tower"])
    left,right = denominator[:6],denominator[6:]
    low,high = numerator[:6],numerator[6:]
    norm = init_norm(builder,left,right,basis["delta"])
    old_norm = inverse_six_deferred(builder,norm)
    repay_norm_entry(builder,left,right,basis["delta"],old_norm)
    _phase_trace_triple(builder,right,norm,low)
    _phase_trace_triple(builder,left,norm,high)
    apply_inplace_linear(builder,norm,quadratic_basis(6)["to_tower"])
    inv_mask = builder.alloc_bits(6)
    builder.hmr(norm,inv_mask)
    builder.free(norm)
    norm = init_norm(builder,left,right,basis["delta"])
    phase_inverse_six(builder,norm,inv_mask)
    builder.free(inv_mask)
    erase_norm(builder,left,right,norm,basis["delta"])
    builder.free(norm)
    apply_inplace_linear(builder,numerator,basis["from_tower"])
    apply_inplace_linear(builder,denominator,basis["from_tower"])


def phase_linear_numerator(builder, denominator, numerator,
                           factor_mask, tower_offset):
    """Apply dot(factor_mask,numerator/denominator)+dot(tower_offset,tower(1/denominator))."""
    import gauge_park_paired as public
    from quantum_reciprocal import xor_linear
    import gf24_nested_norm as arithmetic

    polynomial_duals,tower_duals = public.trace_columns()
    scale = public.classical_word(builder)
    offset = public.classical_word(builder)
    xor_linear(builder,factor_mask,scale,polynomial_duals)
    xor_linear(builder,tower_offset,offset,tower_duals)
    active = public.classical_word(builder,1)
    builder.bit_store(active[0],True,control=scale)
    builder.push_condition(active[0])
    reciprocal, owned = public.classical_inverse(builder,scale)
    public.classical_scale(builder,numerator,scale,reciprocal)
    builder.cx(offset,numerator)
    phase_trace_quotient(builder,denominator,numerator)
    builder.cx(offset,numerator)
    public.classical_scale(builder,numerator,reciprocal,scale)
    for word in owned:
        builder.free(word)
    builder.pop_condition()
    builder.x(active)
    builder.push_condition(active[0])
    poly_mask = public.classical_word(builder)
    xor_linear(builder,tower_offset,poly_mask,quadratic_basis(12)["to_tower"])
    arithmetic.Phase12.phase_inverse_twelve_polynomial(builder,denominator,poly_mask)
    builder.free(poly_mask)
    builder.pop_condition()
    for word in (scale,offset,active):
        builder.free(word)
