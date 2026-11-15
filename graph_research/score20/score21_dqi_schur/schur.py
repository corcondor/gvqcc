"""Source-preserving, phase-clean K24 division through a rank-11 Schur map."""
from functools import cache

import kickmix as km
from coherent_border import toggle_zero
from nested_norm_inverse import inverse_twelve_deferred
from paired_divide import _inverse_closed, _joined
from tower_inverse import apply_inplace_linear, kernel, phase_product, quadratic_basis, xor_product
from field_tensor import invert_binary_columns

FIELD = km.GF2Field(12)
DELTA = 2048


def rows(columns):
    return tuple(sum(((x >> i) & 1) << j for j,x in enumerate(columns))
                 for i in range(len(columns)))


@cache
def schur_move():
    # New register holds (r + δr², extra distinguishing bit).
    # This rank-11 linear map vanishes exactly on {0, 1/δ}.
    # Move the otherwise lost bit into one reusable clean lane.
    columns = tuple((1 << i) ^ FIELD.mul(DELTA, FIELD.mul(1 << i, 1 << i))
                    for i in range(12))
    output_rows = list(rows(columns))
    pivots = {}
    dependent = None
    for index, raw in enumerate(output_rows):
        mask, combination = raw, 1 << index
        while mask:
            j = mask.bit_length() - 1
            if j not in pivots:
                pivots[j] = mask, combination
                break
            value, seen = pivots[j]
            mask ^= value
            combination ^= seen
        if not mask:
            assert dependent is None
            dependent = index, combination
    assert len(pivots) == 11
    missing, relation = dependent
    lost = FIELD.invert(DELTA)
    distinguishing_row = lost & -lost
    assert relation >> missing & 1
    output_rows[missing] ^= 1 << 12
    output_rows.append(distinguishing_row)
    # As the 12th input bit starts zero, the old missing row's dependency
    # is reconstructed exactly by this invertible extension.
    inverse = invert_binary_columns(rows(output_rows))
    return tuple(output_rows), inverse


@cache
def theta_orbit(inverse):
    inverse_delta = FIELD.invert(DELTA)

    def step(word):
        left, right = word & 4095, word >> 12
        if inverse:
            scaled = FIELD.mul(inverse_delta, left)
            return (scaled ^ right) | (scaled << 12)
        return FIELD.mul(DELTA, right) | ((left ^ right) << 12)

    # A constant field product has a cyclic companion form. Coordinate
    # changes use unconditional Clifford gates; only a shift and feedback
    # depend on the quantum flag.
    orbit = [1]
    for i in range(23):
        orbit.append(step(orbit[i]))
    to_orbit = invert_binary_columns(orbit)
    final = step(orbit[-1])
    feedback = sum(((row & final).bit_count() & 1) << i for i,row in enumerate(to_orbit))
    assert feedback & 1
    return to_orbit, rows(orbit), feedback


def qconstant_mul_theta(builder, flag, word, *, inverse=False):
    """Guard a field multiplication by using its companion coordinates."""
    to_orbit, from_orbit, feedback = theta_orbit(inverse)
    apply_inplace_linear(builder, word, to_orbit)
    for i in range(1,24):
        builder.cswap(flag, word[0], word[i])
    for i in range(1,24):
        if feedback >> i & 1:
            builder.ccx(flag, word[0], word[i])
    apply_inplace_linear(builder, word, from_orbit)


def _repay_old_factor(builder, factor, masks):
    if not masks:
        return
    basis = quadratic_basis(12)
    apply_inplace_linear(builder, factor, basis["to_tower"])
    builder.cz(_joined(masks), factor)
    apply_inplace_linear(builder, factor, basis["from_tower"])
    for mask in masks:
        builder.free(mask)


def _invert_and_pay(builder, factor, debt, *, closed=False):
    if closed:
        _inverse_closed(builder, factor)
        next_debt = ()
    else:
        next_debt = inverse_twelve_deferred(builder, factor)
    _repay_old_factor(builder, factor, debt)
    return next_debt


def _scale_words(builder, coefficient, words):
    temporary = builder.alloc_qubits(12)
    masks = []
    for word in words:
        xor_product(builder, word, coefficient, temporary)
        builder.swap(word, temporary)
        mask = builder.alloc_bits(12)
        builder.hmr(temporary, mask)
        masks.append(mask)
    builder.free(temporary)
    return masks


def _repay_scales(builder, inverse_coefficient, words, masks):
    for word, mask in zip(words, masks):
        phase_product(builder, word, inverse_coefficient, mask, kernel(12))
        builder.free(mask)


def _transform(builder, source, target, *, inverse):
    """Preserve nonzero K24 source and apply its scalar action."""
    assert len(source) == len(target) == 24 and not set(source) & set(target)
    a,b = source[:12],source[12:]
    x,y = target[:12],target[12:]
    polar = builder.alloc_qubits(1)
    toggle_zero(builder, a, polar[0])
    builder.cswap(polar[0], a, b)

    # Normalize source position b to r=b/a, and scale both target words
    # by a^-1 while that coefficient is already live.
    debt = _invert_and_pay(builder, a, ())
    initial_words = (b,x,y) if inverse else (b,)
    masks = _scale_words(builder, a, initial_words)
    debt = _invert_and_pay(builder, a, debt)
    _repay_scales(builder, a, initial_words, masks)

    if inverse:
        xor_product(builder, b, x, y)
    else:
        _upper_shear(builder, b, x, y)
    # The Schur denominator is d=1+r+δr². Hold the single missing kernel
    # bit while reusing the entire r register for d and its reciprocal.
    saved = builder.alloc_qubits(1)
    r_view = km.array([*b, *saved])
    forward, backward = schur_move()
    apply_inplace_linear(builder, r_view, forward)
    builder.x(b[0])
    if inverse:
        remainder = _invert_and_pay(builder, b, ())
        old_y = _scale_words(builder, b, (y,))
        _invert_and_pay(builder, b, remainder, closed=True)
        _repay_scales(builder, b, (y,), old_y)
    else:
        old_y = _scale_words(builder, b, (y,))
        remainder = _invert_and_pay(builder, b, ())
        _repay_scales(builder, b, (y,), old_y)
        _invert_and_pay(builder, b, remainder, closed=True)
    builder.x(b[0])
    apply_inplace_linear(builder, r_view, backward)
    builder.free(saved)
    if inverse:
        _upper_shear(builder, b, x, y)
    else:
        xor_product(builder, b, x, y)

    # Refrain from duplicating the 12-bit scalar register. In forward
    # multiplication this final pass also applies the public chart scale.
    final_words = (b,) if inverse else (b,x,y)
    final_masks = _scale_words(builder, a, final_words)
    debt = _invert_and_pay(builder, a, debt)
    _repay_scales(builder, a, final_words, final_masks)
    _invert_and_pay(builder, a, debt, closed=True)
    builder.cswap(polar[0], a, b)
    qconstant_mul_theta(builder, polar[0], target, inverse=inverse)
    toggle_zero(builder, a, polar[0])
    builder.free(polar)


def _upper_shear(builder, factor, x, y):
    delta_columns = tuple(FIELD.mul(DELTA, 1 << i) for i in range(12))
    delta_rows = rows(delta_columns)
    delta_inverse = invert_binary_columns(delta_columns)
    apply_inplace_linear(builder, factor, delta_rows)
    xor_product(builder, factor, y, x)
    apply_inplace_linear(builder, factor, delta_inverse)


def divide(builder, source, target):
    """Preserve a unit source and consume target into target/source."""
    _transform(builder, source, target, inverse=True)


def multiply(builder, source, target, *, conjugate=False):
    """Preserve a unit source and multiply the target by it or its conjugate."""
    if conjugate:
        builder.cx(source[12:], source[:12])
    _transform(builder, source, target, inverse=False)
    if conjugate:
        builder.cx(source[12:], source[:12])
