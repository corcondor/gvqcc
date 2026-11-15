#!/usr/bin/env python3
"""Use eight dirty chart lanes as an in-place masked field word."""
from argparse import ArgumentParser
from functools import cache
import json
from pathlib import Path
import sys

from virtual_lender import partial_rows, verify


@cache
def mul_rows(factor):
    from monic_forney import constant_columns
    from tower_inverse import rows_from_columns
    return rows_from_columns(constant_columns(factor))


@cache
def evaluation_basis(m):
    points = (0,*range(2,m))
    return points, *partial_rows(m,points)


def lend_eight(builder, C, low, q0, q1, g):
    import kickmix as km
    from monic_forney import F, flat, add_scaled
    from tower_inverse import apply_inplace_linear, xor_product

    m = len(C)
    assert m >= 5 and len(low) == m
    points, forward, inverse = evaluation_basis(m)
    apply_inplace_linear(builder,flat(C),forward)
    witness = C[-1][:8]
    masked0 = builder.alloc_qubits(12)
    builder.init_and(g,q0,masked0)
    builder.cswap(g,masked0[:8],witness)
    builder.reset(masked0[:8])
    builder.free(masked0[:8])
    live_mask = masked0[8:]
    masked1 = builder.alloc_qubits(12)
    builder.init_and(g,q1,masked1)

    def move(q1_factor, masked0_factor, masked1_factor):
        add_scaled(builder,q1,q0,q1_factor)
        add_scaled(builder,masked1,q0,masked1_factor)
        if masked0_factor:
            # Each nonzero multiplication by a public field element is
            # an invertible linear basis. Conjugating the eight CCX applies
            # the entire rank-eight linear update for exactly eight T gates.
            apply_inplace_linear(builder,q0,mul_rows(F.invert(masked0_factor)))
            builder.ccx(g,witness,q0[:8])
            builder.cx(live_mask,q0[8:])
            apply_inplace_linear(builder,q0,mul_rows(masked0_factor))

    previous = (0,0,0)
    for i, point in enumerate(points):
        factors = (point,point^1,F.mul(point,point^1))
        move(*(a^b for a,b in zip(factors,previous)))
        xor_product(builder,C[i],q0,low[point])
        previous = factors
    move(*previous)

    builder.del_and(g,q1,masked1)
    builder.free(masked1)
    restore = builder.alloc_qubits(8)
    builder.cswap(g,restore,witness)
    both = km.array([*restore,*live_mask])
    builder.del_and(g,q0,both)
    builder.free(both)
    apply_inplace_linear(builder,flat(C),inverse)

    # At p=1 both masked forms vanish. The final scalar step fits with
    # no work bank. C[0] is evaluation at 1 while the other C words stay.
    for j in range(1,m):
        builder.cx(C[j],C[0])
    builder.cx(q1,q0)
    xor_product(builder,C[0],q0,low[1])
    builder.cx(q1,q0)
    for j in range(1,m):
        builder.cx(C[j],C[0])


def main(args):
    for path in (args.source/"after_c5/extractor_width",
                 args.source/"after_c5/converter_width",
                 args.source/"night_c27/arithmetic"):
        sys.path.insert(0,str(path))
    import ew_paths # noqa: F401
    import kickmix as km
    import gauge_park_virtual as virtual

    args.out.mkdir(parents=True,exist_ok=True)
    report=[]
    for m in args.points:
        rec=verify(km,virtual,args,m,implementation=lend_eight,parked_helpers=16)
        assert rec["records"][1]["static_paid"]-rec["records"][0]["static_paid"]==8*m+16
        report.append(rec)
        print(json.dumps(rec),flush=True)
    (args.out/"result.json").write_text(json.dumps(report,indent=2)+"\n")


if __name__=="__main__":
    p=ArgumentParser(description=__doc__)
    for key in ("source","out"):
        p.add_argument("--"+key,type=Path,required=True)
    p.add_argument("--points",nargs="+",type=int,default=list(range(5,17)))
    p.add_argument("--shots",type=int,default=1024)
    main(p.parse_args())
