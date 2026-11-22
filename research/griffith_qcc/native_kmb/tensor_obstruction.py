"""Exact GF(2) polar-tensor lower bound on real 38-CCX restart KMB cuts.

Explicit restricted architecture: retain the first nonlinear gate P0 as an
independent cached symbol, and synthesize the rest from 128 live cut wires
and P0 using affine XOR/AND. Under this independence hypothesis, the 37
subsequent products implement a multioutput quadratic function on 129 inputs.
A single AND increases the rank of the first-axis polar tensor flattening by
at most two. Therefore ceil(rank/2) is a lower bound on paid later gates.

This does not prove the full real 38-gate window minimal if the first product
is recomputed jointly with the rest or its algebraic relation P0=a*b is used.
It does not use or produce a modified native KMB or competition score.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from .real_kmb import KMB


def gf2_rank(vectors):
    pivots = {}
    for value in vectors:
        x = int(value)
        while x:
            bit = x.bit_length()-1
            if bit in pivots:
                x ^= pivots[bit]
            else:
                pivots[bit] = x
                break
    return len(pivots)


def prove_restart(kmb: KMB, phase: int) -> dict:
    if kmb.nq != 128 or phase < 1:
        raise ValueError("Expected public 128Q ANGLE KMB and positive phase")
    measurements = [i for i, op in enumerate(kmb.ops) if op.code == 0x50]
    if phase >= len(measurements):
        raise ValueError("HMR phase index out of range")
    start = measurements[phase-1]+1
    stop = measurements[phase]
    n = kmb.nq
    const = 1 << n
    linear = [1 << i for i in range(n)]
    factors = []
    for pos in range(start, stop):
        op = kmb.ops[pos]
        if op.code == 0x21:
            a, t = op.wires
            linear[t] ^= linear[a]
        elif op.code == 0x11:
            t, = op.wires
            linear[t] ^= const
        elif op.code == 0x31:
            a, b, t = op.wires
            factors.append((linear[a], linear[b]))
            linear[t] ^= 1 << (n+len(factors))
        elif op.code not in (0x10, 0x20, 0x90, 0xa0):
            raise ValueError(f"Unsupported gate in phase {phase}: 0x{op.code:x}")
    if len(factors) != 38:
        raise ValueError(f"Expected 38 nonlinear gates, found {len(factors)}")

    # Assumption to be CERTIFIED by this checker: no later gate uses any
    # nonlinear product except the first one. Treat the first product P0
    # as one more independent input; constants are affine, not quadratic.
    var_count = n+1
    mask = (1 << n)-1
    controls = []
    for i, (left, right) in enumerate(factors):
        if i > 0 and (left | right) >> (n+2):
            raise ValueError("A later AND depends on a non-first product")
        u = (left & mask) | (((left >> (n+1)) & 1) << n)
        v = (right & mask) | (((right >> (n+1)) & 1) << n)
        controls.append((u, v))

    directions = []
    for g in range(38):
        bit = n+1+g
        directions.append(
            sum(((linear[q] >> bit) & 1) << q for q in range(n))
        )
    if not all(directions):
        raise ValueError("Unexpected zero physical output direction")

    affected = [
        q for q in range(n)
        if any((d >> q) & 1 for d in directions[1:])
    ]
    polar_rows = []
    for input_index in range(var_count):
        slice_value = 0
        for g, (u, v) in enumerate(controls[1:], start=1):
            # Boolean polarization of (u dot x)*(v dot x):
            # matrix rows are u_i*v XOR v_i*u (GF2).
            row = (v if (u >> input_index) & 1 else 0) ^ (
                u if (v >> input_index) & 1 else 0
            )
            if not row:
                continue
            effect = directions[g]
            for output_index, physical_wire in enumerate(affected):
                if (effect >> physical_wire) & 1:
                    slice_value ^= row << (var_count*output_index)
        polar_rows.append(slice_value)

    flattened_rank = gf2_rank(polar_rows)
    min_products = (flattened_rank+1)//2
    return {
        "native_kmb_sha256": hashlib.sha256(kmb.render()).hexdigest(),
        "start_instruction": start, "stop_instruction_exclusive": stop,
        "initial_ccx_count": 38, "retained_P0_controls": [
            hex(factors[0][0]), hex(factors[0][1]),
        ],
        "later_products": 37,
        "affected_physical_wires": len(affected),
        "later_output_direction_rank": gf2_rank(directions[1:]),
        "flattening_rank": flattened_rank,
        "minimum_later_AND_with_independent_P0": min_products,
        "fixed_P0_architecture_saturates_bound": min_products == 37,
        "scope": "All 128 physical input wires + independent cached P0; quadratic functions only",
        "important_limitation": (
            "Not a global lower bound: P0 is actually the product of its "
            "two original controls; coordinated replacement, reachability, "
            "and HMR schedule changes are not excluded."
        ),
        "native_paid_CCX_saved": 0,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-angles", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--banks", type=int, nargs="+", default=[0,1,5,7,11])
    args = parser.parse_args()
    results = []
    for bank in args.banks:
        c = KMB.read(args.original_angles / f"angle_k_{bank}.kmb")
        row = prove_restart(c, 66 if bank == 0 else 63)
        row["bank"] = bank
        results.append(row)
    report = {
        "status": "RIGOROUS_CONDITIONAL_GF2_LOWER_BOUND_NO_PAID_SAVING",
        "family": "public Goodpjw2008 V8 128Q ANGLE",
        "underlying_assumption": "The first gate P0 remains a distinct independent cached source",
        "rank_bound": "Each AND contributes flattening rank <=2; k >= ceil(rank/2)",
        "results": results,
        "official_score_change": None,
        "real_paid_gate_saving": 0,
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    for row in results:
        print(
            f"bank {row['bank']}: tensor rank {row['flattening_rank']}, "
            f"AND lower bound {row['minimum_later_AND_with_independent_P0']}"
        )


if __name__ == "__main__":
    main()
