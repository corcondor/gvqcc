#!/usr/bin/env python3
"""Borrow the whole chart-zero coefficient word without materializing a mask word."""
from argparse import ArgumentParser
import json
from pathlib import Path
import sys


def lend_word(builder, C, low, q0, q1, g):
    from monic_forney import F, flat, add_scaled
    from tower_inverse import apply_inplace_linear, xor_product
    from virtual_lender8 import evaluation_basis, mul_rows

    m = len(C)
    assert m >= 5 and len(low) == m
    points, forward, inverse = evaluation_basis(m)
    apply_inplace_linear(builder,flat(C),forward)
    witness = C[-1]
    # For g=0 it stays arbitrary and is never read without its guard.
    # For g=1 the raw last coefficient is zero and now stores the mask.
    builder.ccx(g,q0,witness)
    masked1 = builder.alloc_qubits(12)
    builder.init_and(g,q1,masked1)

    def move(q1_factor, masked0_factor, masked1_factor):
        add_scaled(builder,q1,q0,q1_factor)
        add_scaled(builder,masked1,q0,masked1_factor)
        if masked0_factor:
            apply_inplace_linear(builder,q0,mul_rows(F.invert(masked0_factor)))
            builder.ccx(g,witness,q0)
            apply_inplace_linear(builder,q0,mul_rows(masked0_factor))

    previous = (0,0,0)
    for i,point in enumerate(points):
        factors = (point,point^1,F.mul(point,point^1))
        move(*(a^b for a,b in zip(factors,previous)))
        xor_product(builder,C[i],q0,low[point])
        previous=factors
    move(*previous)

    builder.del_and(g,q1,masked1)
    builder.free(masked1)
    builder.ccx(g,q0,witness)
    apply_inplace_linear(builder,flat(C),inverse)

    # The two masked head expressions both vanish at p=1.
    for word in C[1:]:
        builder.cx(word,C[0])
    builder.cx(q1,q0)
    xor_product(builder,C[0],q0,low[1])
    builder.cx(q1,q0)
    for word in C[1:]:
        builder.cx(word,C[0])


def main(args):
    sys.path.insert(0,str(args.prior))
    for path in (args.source/"after_c5/extractor_width",
                 args.source/"after_c5/converter_width",
                 args.source/"night_c27/arithmetic"):
        sys.path.insert(0,str(path))
    import ew_paths # noqa: F401
    import kickmix as km
    import gauge_park_virtual as virtual
    from virtual_lender import verify

    args.out.mkdir(parents=True,exist_ok=True)
    report=[]
    for m in args.points:
        rec=verify(km,virtual,args,m,implementation=lend_word,parked_helpers=12)
        assert rec["records"][1]["static_paid"]-rec["records"][0]["static_paid"]==12*m+12
        report.append(rec)
        print(json.dumps(rec),flush=True)
    (args.out/"result.json").write_text(json.dumps(report,indent=2)+"\n")


if __name__=="__main__":
    p=ArgumentParser(description=__doc__)
    for key in ("source","prior","out"):
        p.add_argument("--"+key,type=Path,required=True)
    p.add_argument("--points",nargs="+",type=int,default=list(range(5,17)))
    p.add_argument("--shots",type=int,default=1024)
    main(p.parse_args())
