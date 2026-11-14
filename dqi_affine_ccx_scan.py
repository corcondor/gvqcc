#!/usr/bin/env python3
"""Bounded read-only affine-basis CCX sharing and quadratic-rank scan.

Unlike a physical-wire peephole, this follows CNOT/SWAP basis changes on
both controls and the output fanout. Explicit conditions, measurements,
reset, phases, classical operations and stack changes are boundaries.
No candidate or verification result is fabricated by this analysis.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import resource
import struct
import time
import dqi_ccx_peephole as shared

RUN = re.compile(rb"[\x11\x21\x22\x31]+")


def bits(x):
    while x:
        b = x & -x
        yield b.bit_length() - 1
        x ^= b


def product_anf(a, b, constant):
    result = set()
    for i in bits(a):
        u = 0 if i == constant else 1 << i
        for j in bits(b):
            v = 0 if j == constant else 1 << j
            m = u | v
            if m in result:
                result.remove(m)
            else:
                result.add(m)
    return result


def rank(rows):
    pivots = {}
    for row in rows:
        while row:
            p = row.bit_length() - 1
            if p in pivots:
                row ^= pivots[p]
            else:
                pivots[p] = row
                break
    return len(pivots)


def quadratic_rank(poly, n):
    rows = [0] * n
    for m in poly:
        if m.bit_count() == 2:
            a, b = bits(m)
            rows[a] ^= 1 << b
            rows[b] ^= 1 << a
    return rank(rows)


def inspect_piece(ops):
    """All CCX controls must be affine in the arbitrary input variables.

    Each CCX result is first tracked as a distinct formal token. This is
    conservative: a control with nonzero token coefficients is rejected
    even if an extra nonlinear polynomial cancellation could make it affine.
    """
    wires = sorted({q for op in ops for q in op.qubits})
    ix = {q: i for i, q in enumerate(wires)}
    n = len(wires)
    linear = [1 << i for i in range(n)]
    nonlinear = [0] * n
    products = []
    for j, op in enumerate(ops):
        q = [ix[x] for x in op.qubits]
        if op.opcode == 0x11:
            linear[q[0]] ^= 1 << n
        elif op.opcode == 0x21:
            linear[q[1]] ^= linear[q[0]]
            nonlinear[q[1]] ^= nonlinear[q[0]]
        elif op.opcode == 0x22:
            linear[q[0]], linear[q[1]] = linear[q[1]], linear[q[0]]
            nonlinear[q[0]], nonlinear[q[1]] = nonlinear[q[1]], nonlinear[q[0]]
        elif op.opcode == 0x31:
            a, b, t = q
            if nonlinear[a] or nonlinear[b]:
                return {"split_before": j}
            products.append((linear[a], linear[b], j))
            nonlinear[t] ^= 1 << (len(products) - 1)
        else:
            raise ValueError("non-affine-block gate")
    by_direction = defaultdict(list)
    directions = [0] * len(products)
    for output, mask in enumerate(nonlinear):
        for p in bits(mask):
            directions[p] ^= 1 << output
    polys = [product_anf(a, b, n) for a, b, _ in products]
    by_quadratic = defaultdict(list)
    for i, (v, p) in enumerate(zip(directions, polys)):
        by_direction[v].append(i)
        by_quadratic[frozenset(m for m in p if m.bit_count() == 2)].append(i)
    output_groups, input_groups = [], []
    for v, ids in by_direction.items():
        if len(ids) < 2:
            continue
        poly = set()
        for i in ids:
            poly ^= polys[i]
        r = quadratic_rank(poly, n)
        output_groups.append({"products": len(ids), "polar_rank": r,
                              "required_products": r // 2,
                              "algebraic_saving": len(ids) - r // 2,
                              "ids": ids})
    for p, ids in by_quadratic.items():
        if len(ids) < 2 and p:
            continue
        # Same quadratic product under different affine control expressions.
        direction = 0
        for i in ids:
            direction ^= directions[i]
        required = int(bool(p) and bool(direction))
        if len(ids) > required:
            input_groups.append({"products": len(ids), "required_products": required,
                                 "algebraic_saving": len(ids) - required, "ids": ids})
    candidates = [dict(kind="same_output_direction", **g) for g in output_groups if g["algebraic_saving"] > 0]
    candidates += [dict(kind="same_quadratic_product", **g) for g in input_groups]
    return {"ccx": len(products), "input_variables": n,
            "output_groups": output_groups, "input_groups": input_groups,
            "candidates": candidates}


def normalized_key(ops):
    wires = sorted({q for op in ops for q in op.qubits})
    ix = {q: i for i, q in enumerate(wires)}
    data = bytearray()
    for op in ops:
        data.append(op.opcode)
        for q in op.qubits:
            data.extend(struct.pack('<H', ix[q]))
    return hashlib.sha256(data).hexdigest()


def self_check():
    O = shared.Operation
    # a*b + a*(b+c) = a*c even though the physical CCX controls are identical
    # at two different points and b's basis has changed in between.
    ops = [O(0x31, (0, 1, 3)), O(0x21, (2, 1)), O(0x31, (0, 1, 3)), O(0x21, (2, 1))]
    result = inspect_piece(ops)
    assert result['candidates'][0]['algebraic_saving'] == 1
    # Hidden equality (a+b)*b = a*b+b; the linear remainder must be retained.
    ops2 = [O(0x31, (0, 1, 3)), O(0x21, (1, 0)), O(0x31, (0, 1, 4)), O(0x21, (1, 0))]
    result2 = inspect_piece(ops2)
    assert any(c['kind'] == 'same_quadratic_product' and c['algebraic_saving'] == 1 for c in result2['candidates'])
    # A two-output multiplier with independent products has no reduction here.
    assert not inspect_piece([O(0x31, (0, 1, 4)), O(0x31, (0, 2, 5))])['candidates']
    # Nonlinear controls must force a cut rather than pretending to be affine.
    assert inspect_piece([O(0x31, (0, 1, 4)), O(0x31, (4, 2, 5))]) == {'split_before': 1}
    return {'status': 'PASS', 'constructed_cases': 4,
            'scope': 'scanner algebra/barriers, not a generated circuit equivalence proof'}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('input', type=Path)
    ap.add_argument('--report', type=Path, required=True)
    ap.add_argument('--seconds', type=float, default=330)
    ap.add_argument('--max-ops', type=int, default=20000)
    args = ap.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (2 << 30, 2 << 30))
    started = time.monotonic()
    check = self_check()
    profile = shared.kp.profile(args.input, max_register_summaries=0)
    circuit = shared.BinaryCircuit(args.input, profile)
    counts = Counter()
    cache, hits = {}, []
    complete = True
    try:
        for match in RUN.finditer(circuit.opcodes):
            start, end = match.span()
            if circuit.opcodes[start:end].count(0x31) == 0:
                continue
            if time.monotonic() - started > args.seconds:
                complete = False
                break
            counts['pure_runs_with_ccx'] += 1
            for left in range(start, end, args.max_ops):
                right = min(left + args.max_ops, end)
                ops = list(circuit.operations(left, right))
                while ops:
                    key = normalized_key(ops)
                    if key in cache:
                        result = cache[key]
                        counts['cache_hits'] += 1
                    else:
                        result = inspect_piece(ops)
                        cache[key] = result
                        counts['distinct_piece_shapes'] += 1
                    if 'split_before' in result:
                        split = result['split_before']
                        assert split > 0
                        first = ops[:split]
                        # The prefix necessarily has affine CCX controls.
                        result = inspect_piece(first)
                        assert 'split_before' not in result
                        current, ops = first, ops[split:]
                        counts['nonlinear_control_cuts'] += 1
                    else:
                        current, ops = ops, []
                    counts['pieces'] += 1
                    counts['ccx_covered'] += result['ccx']
                    counts['same_direction_groups'] += len(result['output_groups'])
                    for c in result['candidates']:
                        counts['algebraic_candidate_groups'] += 1
                        hits.append({'start_op': current[0].source_index,
                                     'end_op_exclusive': current[-1].source_index + 1,
                                     'piece_ccx': result['ccx'], 'input_variables': result['input_variables'],
                                     **c})
    finally:
        circuit.close()
    report = {'status': 'COMPLETE' if complete else 'TIME_BOUNDED_PARTIAL',
              'input': str(args.input), 'input_sha256': profile['raw_kmb_sha256'],
              'scope': 'Read-only affine-basis sharing and same-output quadratic rank; no candidate written.',
              'self_check': check, 'counts': dict(counts), 'candidates': hits,
              'max_piece_operations': args.max_ops, 'elapsed_seconds': time.monotonic()-started,
              'max_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'memory_limit_bytes': 2 << 30}
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'candidates'}, indent=2))
    print('candidates', len(hits))


if __name__ == '__main__':
    main()
