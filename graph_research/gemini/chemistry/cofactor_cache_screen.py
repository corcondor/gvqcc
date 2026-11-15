#!/usr/bin/env python3
"""Care-based exact pivot replacement for two missing physical feature lanes."""
import argparse
from functools import lru_cache
import json
from pathlib import Path
import sys

import kickmix as km

from repair_tag_oracle import ONES


def bits(n):
    while n:
        one = n & -n
        yield one.bit_length()-1
        n ^= one


def emit_basis(values, pool, care):
    basis = {}
    for i in pool:
        row = values[i] & care
        directions = 1 << i
        while row:
            pivot = row.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = row, directions
                break
            other, mask = basis[pivot]
            row ^= other
            directions ^= mask
    return basis


def coordinates(row, basis):
    directions = 0
    while row:
        p = row.bit_length() - 1
        if p not in basis:
            return None
        other, mask = basis[p]
        row ^= other
        directions ^= mask
    return directions


def evaluate(mask, values):
    result = 0
    for i in bits(mask):
        result ^= values[i]
    return result


def reduce_outside(row, basis):
    quotient = 0
    while row:
        pivot = row.bit_length()-1
        if pivot in basis:
            row ^= basis[pivot][0]
        else:
            bit = 1 << pivot
            quotient ^= bit
            row ^= bit
    return quotient


def kernel_support(values):
    basis = {}
    support = []
    for i,vector in enumerate(values):
        row = vector
        comb = 1 << i
        while row:
            pivot = row.bit_length()-1
            if pivot not in basis:
                basis[pivot] = row, comb
                break
            oth, subset = basis[pivot]
            row ^= oth
            comb ^= subset
        if not row:
            support.append(list(bits(comb)))
    return support


def factor_axes(value):
    """Mixed tensor axes on the complete 76x16 rectangle of valid addresses."""
    offset = value & 1
    high = sum((((value >> (h*16)) & 1) ^ offset) << h for h in range(76))
    low = (value & 0xffff) ^ (0xffff if offset else 0)
    reconstructed = sum(((value & 0xffff) ^
                         (0xffff if high >> h & 1 else 0)) << (16*h)
                        for h in range(76))
    assert reconstructed == value & ((1<<1216)-1), "control is not separable"
    return high, low


def tensor_bounds(terms, vals, truth, available_bits, unavailable):
    high, low = zip(*(factor_axes(truth[i]) for i in available_bits))
    hspace = emit_basis(high, range(len(high)), (1<<76)-1)
    lspace = emit_basis(low, range(len(low)), 0xffff)
    axis_cache = {}

    def axes(f):
        if f not in axis_cache:
            axis_cache[f] = factor_axes(vals(f))
        return axis_cache[f]
    blocks = 0
    outside = []
    outside_term_ids = []
    for term_id,(u,v,direction) in enumerate(terms):
        if not (u | v) & unavailable:
            continue
        h,l = axes(u)
        k,m = axes(v)
        high_quot = sum(reduce_outside((k if l>>j&1 else 0) ^
                                      (h if m>>j&1 else 0),hspace) << (76*j)
                        for j in range(16))
        low_quot = sum(reduce_outside((m if h>>j&1 else 0) ^
                                     (l if k>>j&1 else 0),lspace) << (16*j)
                       for j in range(76))
        if high_quot or low_quot:
            blocks += 1
        projected = high_quot ^ (low_quot << 1216)
        outside.append(sum(projected << (2432*i) for i in bits(direction)))
        outside_term_ids.append(term_id)
    groups = [[outside_term_ids[i] for i in support] for support in kernel_support(outside)]
    return blocks, groups


def screen(terms, pool, missing, values, augmented):
    unavailable = sum(1 << (q+1) for q in missing)
    available_bits = [0, *(q+1 for q in pool if q not in missing)]
    truth = [ONES, *values]
    @lru_cache(maxsize=512)
    def vals(n):
        return evaluate(n, truth)
    @lru_cache(maxsize=512)
    def partial(care):
        return emit_basis(truth, available_bits, care)

    static = 0
    skipped = 0
    could_replace = []
    with_affine = []
    index_offset = len(truth)

    @lru_cache(maxsize=512)
    def augmented_basis(care):
        expanded = truth + [value & care for value in truth]
        columns = [*available_bits, *(i+index_offset for i in available_bits)]
        return emit_basis(expanded, columns, ONES)

    for i, (u,v,direction) in enumerate(terms):
        if not (u | v) & unavailable:
            static += 1
            continue
        if u & unavailable and v & unavailable:
            skipped += 1
            continue
        if v & unavailable:
            u,v = v,u
        care = vals(v)
        exact = vals(u) & care
        expr = coordinates(exact, partial(care))
        if expr is not None:
            assert not expr & unavailable
            assert vals(expr) & care == exact
            could_replace.append([i, u, v, expr, direction])
        elif augmented:
            span = augmented_basis(care)
            choice = coordinates(exact, span)
            if choice is not None:
                linear = choice & ((1<<index_offset)-1)
                operand = choice >> index_offset
                assert not (linear | operand) & unavailable
                assert (vals(linear) ^ (vals(operand) & care)) == exact
                with_affine.append([i,u,v,operand,linear,direction])
    lower_bound, joint_groups = tensor_bounds(terms, vals, truth, available_bits, unavailable)
    return {
        "mixed_quotient_obstructions": lower_bound,
        "joint_kernel_dimension": len(joint_groups),
        "first_joint_groups": joint_groups[:10],
        "missing": list(missing),
        "terms": len(terms),
        "direct_static": static,
        "both_factors_blocked": skipped,
        "one_factor_projected_exact": len(could_replace),
        "additional_projected_plus_affine": len(with_affine),
        "first_witness": could_replace[0] if could_replace else None,
        "first_affine_witness": with_affine[0] if with_affine else None,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--scheduler", type=Path, required=True)
    p.add_argument("--planner", type=Path, required=True)
    p.add_argument("--cache", type=Path, required=True)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--augment-affine", action="store_true")
    args = p.parse_args()
    sys.path[:0] = [str(args.repo), str(args.scheduler), str(args.planner)]
    import schedule_angle as S
    from chemistry_affine_span_resynthesis import parse_line
    from chemistry_joint_product_resynthesis import DATA, TAGS
    from feature_cache import exact_work_functions
    from repair_tag_oracle import TAGS as CONTROL_PAIRS
    plan = json.loads(args.cache.read_text())
    results = []
    for row in plan:
        k = row["batch"]
        circuit = km.Circuit.from_file(args.source / f"angle_k_{k}.kmb")
        lines = str(circuit).splitlines()
        ops = [parse_line(line) for line in lines]
        start = 1 + max(i for i, (g, q, _) in enumerate(ops) if g == "CCX" and q[-1] >= 51)
        stop = next(i for i, (g, _, _) in enumerate(ops) if g == "HMR")
        tags = sorted(TAGS)
        encoding_end = 5 + lines.index(f"CX q{tags[0]-1} q{tags[0]}")
        values = exact_work_functions(ops[encoding_end:start], circuit.num_qubits, tags,
                                      [CONTROL_PAIRS[tag] for tag in tags])
        frame, terms = S.get_frame(ops[start:stop], DATA, circuit.num_qubits)
        pool = tuple(q for q in range(circuit.num_qubits) if q not in DATA)
        result = screen(terms, pool, row["missing_start"], values, args.augment_affine)
        results.append({"batch":k, **result})
    totals = {k:sum(r[k] for r in results)
              for k in ("terms", "direct_static", "both_factors_blocked", "one_factor_projected_exact",
                        "additional_projected_plus_affine","mixed_quotient_obstructions",
                        "joint_kernel_dimension")}
    args.out.write_text(json.dumps({"totals":totals, "results":results}, indent=2) + "\n")
    print(totals)


if __name__ == "__main__":
    main()
