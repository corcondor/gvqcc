"""Source-level integration with the released direct-carry closing ABI."""
import direct_carry_arithmetic as direct
import schur


def divide_deferred(builder, source, target, delta=schur.DELTA):
    """Run a closed prefix yet expose the original compatible zero debts."""
    if delta != schur.DELTA:
        raise ValueError("This Schur chart uses the pinned K24 extension.")
    schur.divide(builder, source, target)

    def zero_mask(width):
        result = builder.alloc_bits(width)
        builder.bit_store(result, False)
        return result

    return direct.DivisionRecord(id(builder), tuple(source), tuple(target),
                                 zero_mask(24), (zero_mask(12), zero_mask(12)),
                                 zero_mask(12), delta)
