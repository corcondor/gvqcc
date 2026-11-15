"""Third-pivot Mobius map with infinity toggles fused into existing GF4 norms.

New local experimental component. The finite-output domain is extended to
include a zero queried denominator; a zero queried numerator remains outside
the whole decoder contract. No input fixture, RNG seed, or input weight is
used to select a circuit. Dependencies are the unmodified public source.
"""
from dataclasses import dataclass
from pathlib import Path
import sys

WORK = Path(__file__).resolve().parents[1] / 'official_sources/Syed_v12/source/dqi_source/src/controller_work'
for relative in ('night_c27/arithmetic', 'night_c27/controller',
                 'after_c5/extractor_width', 'after_c5/arithmetic_t',
                 'after_v3/blocks/v5', 'after_v3/blocks/v6'):
    directory = str(WORK / relative)
    if directory not in sys.path:
        sys.path.insert(0, directory)

import kickmix as km
import third_pivot_chart as Original

Base = Original.Base
import outcome_dqi_chart_inverse_norm as Norm
Tail = Original.Tail


@dataclass
class Record:
    builder_id: int
    current: tuple
    heads: tuple
    inverses: tuple
    borrowed_flag: object
    closed: bool = False


def _reset_flag(builder, flag):
    """This flag is zero on the declared finite-output domain.

    HMR still physically resets out-of-domain inputs. No claim of coherent
    correctness is made for those inputs; the full approximate decoder must
    be checked separately. On the admitted domain the reset has phase zero.
    """
    mask = builder.alloc_bits(1)
    builder.hmr(km.array([flag]), mask)
    builder.free(mask)


def emit_prefix(builder, heads, current, clean_bank, flag):
    Original._contract(heads, current, clean_bank, flag)
    first, second = Original._constants()
    inverses = []
    # Canonical projective representation: (a,0) is finite a; (0,1) is infinity.
    # Inversion is inv0(a), followed by f ^= [a==0]. Scaling preserves f.
    # A translation acts only on finite values.
    inverses.append(Norm.inverse_prefix_with_bank(builder, current, clean_bank, zero_flag=flag))
    Original._add_head(builder, heads[0], current, flag)
    inverses.append(Norm.inverse_prefix_with_bank(builder, current, clean_bank, zero_flag=flag))
    Base.public_scale(builder, current, first)
    Original._add_head(builder, heads[1], current, flag)
    Base.public_scale(builder, current, Base.FIELD.invert(second))
    inverses.append(Norm.inverse_prefix_with_bank(builder, current, clean_bank, zero_flag=flag))
    _reset_flag(builder, flag)
    return Record(id(builder), tuple(current), tuple(tuple(h) for h in heads),
                  tuple(inverses), flag)


def emit_closing(builder, heads, current, clean_bank, record):
    Original._contract(heads, current, clean_bank)
    assert record.builder_id == id(builder) and not record.closed
    assert record.current == tuple(current)
    assert record.heads == tuple(tuple(h) for h in heads)
    first, second = Original._constants()
    flag = builder.alloc_qubits(1)
    inner, middle, outer = record.inverses
    receipts = [Norm.inverse_return_with_bank(builder, current, clean_bank, outer, zero_flag=flag[0])]
    Base.public_scale(builder, current, second)
    Original._add_head(builder, heads[1], current, flag[0])
    Base.public_scale(builder, current, Base.FIELD.invert(first))
    receipts.append(Norm.inverse_return_with_bank(builder, current, clean_bank, middle, zero_flag=flag[0]))
    Original._add_head(builder, heads[0], current, flag[0])
    receipts.append(Norm.inverse_return_with_bank(builder, current, clean_bank, inner, zero_flag=flag[0]))
    _reset_flag(builder, flag[0])
    builder.free(flag)
    assert all(r.closed for r in record.inverses)
    record.closed = True
    return {'inverse_receipts': receipts, 'closed_inverse_calls': 3,
            'finite_output_domain': True, 'queried_denominator_zero_supported': True}
