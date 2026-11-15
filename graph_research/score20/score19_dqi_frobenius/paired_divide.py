"""Low-peak paired GF(4096) division by visiting the factor's reciprocal in place."""
import kickmix as km

from nested_norm_inverse import inverse_twelve_deferred
from tower_inverse import apply_inplace_linear, quadratic_basis, kernel, phase_product, xor_product


def _joined(words):
    return km.array([entry for word in words for entry in word])


def divide_prefix(builder, words, factor):
    """Consume words into words/factor, return the existing tower reciprocal debt."""
    assert len(factor) == 12 and all(len(word) == 12 for word in words)
    assert len(set(factor).union(*map(set, words))) == 12 * (1 + len(words))
    factor_debt = inverse_twelve_deferred(builder, factor)
    old_word_masks = []
    temporary = builder.alloc_qubits(12)
    for word in words:
        xor_product(builder, word, factor, temporary)
        builder.swap(word, temporary)
        mask = builder.alloc_bits(12)
        builder.hmr(temporary, mask)
        old_word_masks.append(mask)
    builder.free(temporary)
    reciprocal_debt = inverse_twelve_deferred(builder, factor)
    basis = quadratic_basis(12)
    apply_inplace_linear(builder, factor, basis["to_tower"])
    builder.cz(_joined(factor_debt), factor)
    apply_inplace_linear(builder, factor, basis["from_tower"])
    for mask in factor_debt:
        builder.free(mask)
    for word, mask in zip(words, old_word_masks):
        phase_product(builder, word, factor, mask, kernel(12))
        builder.free(mask)

    # Consumers free a single owned array. Transfer the two measured words.
    packed = builder.alloc_bits(12)
    builder.bit_store(packed, False)
    builder.cx(_joined(reciprocal_debt), packed)
    for mask in reciprocal_debt:
        builder.free(mask)
    return packed


def _inverse_closed(builder, source):
    """In-place inverse of the factor with both measurement debts discharged."""
    from nested_norm_inverse import inverse_six_deferred, repay_norm_entry
    from scalar_inverse_phase import phase_inverse_six
    from tower_inverse import erase_norm, init_norm

    basis = quadratic_basis(12)
    apply_inplace_linear(builder, source, basis["to_tower"])
    left, right = source[:6], source[6:]
    norm = init_norm(builder, left, right, basis["delta"])
    original_norm_mask = inverse_six_deferred(builder, norm)
    repay_norm_entry(builder, left, right, basis["delta"], original_norm_mask)
    temporary = builder.alloc_qubits(6)
    masks = []
    for half in (left, right):
        xor_product(builder, half, norm, temporary)
        builder.swap(half, temporary)
        mask = builder.alloc_bits(6)
        builder.hmr(temporary, mask)
        masks.append(mask)
    builder.free(temporary)

    # The new half pair has norm 1/Norm(old). Retire that measurement's
    # phase after visiting the old norm to repay the two saved-half masks.
    new_norm_mask = inverse_six_deferred(builder, norm)
    repay_norm_entry(builder, left, right, basis["delta"], new_norm_mask)
    for half, mask in zip((left, right), masks):
        phase_product(builder, half, norm, mask, kernel(6))
        builder.free(mask)

    apply_inplace_linear(builder, norm, quadratic_basis(6)["to_tower"])
    old_mask = builder.alloc_bits(6)
    builder.hmr(norm, old_mask)
    builder.free(norm)
    norm = init_norm(builder, left, right, basis["delta"])
    phase_inverse_six(builder, norm, old_mask)
    builder.free(old_mask)
    erase_norm(builder, left, right, norm, basis["delta"])
    builder.free(norm)
    builder.cx(right, left)
    apply_inplace_linear(builder, source, basis["from_tower"])


def quotient_phases(builder, factor, targets, inverse_mask):
    """Pay the paired quotient phases with at most 12 local work qubits."""
    source_debt = inverse_twelve_deferred(builder, factor)
    for word, mask in targets:
        phase_product(builder, word, factor, mask, kernel(12))
    basis = quadratic_basis(12)
    apply_inplace_linear(builder, factor, basis["to_tower"])
    builder.cz(inverse_mask, factor)
    apply_inplace_linear(builder, factor, basis["from_tower"])
    _inverse_closed(builder, factor)
    apply_inplace_linear(builder, factor, basis["to_tower"])
    builder.cz(_joined(source_debt), factor)
    apply_inplace_linear(builder, factor, basis["from_tower"])
    for mask in source_debt:
        builder.free(mask)


def multiply_closing(builder, words, factor, inverse_mask):
    from low_cached_arithmetic import scale_words

    masks = scale_words(builder, words, factor, defer=True)
    quotient_phases(builder, factor, list(zip(words, masks)), inverse_mask)
    for mask in masks:
        builder.free(mask)
    builder.free(inverse_mask)
