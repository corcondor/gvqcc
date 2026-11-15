#!/usr/bin/env python3
"""Find dense rank-two quadratic realizations of short invsqrt phase gadgets."""
import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys
import time

import kickmix as km
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'graph_inv'))
from temporal_phase_graph import MAX_X, SOURCE_SHA, advance, columns, gate

@dataclass(frozen=True)
class Feature:
    base: int
    start: int
    phase: int
    stop: int

FEATURES = (Feature(8192, 8193, 8199, 8207), Feature(8260, 8261, 8263, 8269),
            Feature(8296, 8297, 8305, 8317), Feature(8317, 8318, 8321, 8329))

def trace(ops, xs, cuts):
    working = columns(xs)
    mask = (1 << len(xs)) - 1
    states = {}
    stack = []
    for i, (op, qs) in enumerate(ops):
        if i in cuts:
            states[i] = working[:]
        if op == 'PUSH_CONDITION':
            stack.append(working[:])
        elif op == 'POP_CONDITION':
            assert working == stack.pop(), i
        else:
            advance(op, qs, working, mask)
    assert not stack
    return states, mask

def independent(values, mask):
    pivots = {mask.bit_length() - 1: mask}
    wires = []
    for j, value in enumerate(values):
        reduced = value
        while reduced:
            pivot = reduced.bit_length() - 1
            if pivot not in pivots:
                pivots[pivot] = reduced
                wires.append(j)
                break
            reduced ^= pivots[pivot]
    return wires

def insert(pivots, value, expression=0):
    while value:
        pivot = value.bit_length() - 1
        entry = pivots.get(pivot)
        if entry is None:
            pivots[pivot] = value, expression
            return None
        base, terms = entry
        value ^= base
        expression ^= terms
    return expression

def coefficients(data, mask, targets):
    wires = independent(data, mask)
    pivots = {}
    for v in [mask, *[data[q] for q in wires]]:
        assert insert(pivots, v) is None
    kernel = []
    edges = []
    for j, q in enumerate(wires):
        for i, p in enumerate(wires[:j]):
            value = data[p] & data[q]
            expression = insert(pivots, value, 1 << len(edges))
            if expression is not None:
                kernel.append(expression)
            edges.append((i, j))
    particular = []
    for t in targets:
        answer = insert(pivots.copy(), t)
        particular.append(answer)
    return wires, edges, kernel, particular

def star_space(edges, n):
    stars = [0] * n
    index = {}
    for position, (i, j) in enumerate(edges):
        stars[i] |= 1 << position
        stars[j] |= 1 << position
        index[i, j] = index[j, i] = position
    return stars, index

def star_basis(kernel, star):
    projected = {}
    for k in kernel:
        insert(projected, star & k)
    return [b for b, _ in projected.values()]

def component(x, edges, index, n, pivot):
    i, j = edges[pivot]
    a = [d for d in range(n) if d != j and x >> index[d, j] & 1]
    b = [d for d in range(n) if d != i and x >> index[d, i] & 1]
    return a, b

def insert_kernel(basis, v):
    while v:
        k = v.bit_length() - 1
        if k not in basis:
            return False
        v ^= basis[k]
    return True

def solve_coset(particular, kernel, edges, n, limit):
    if particular == 0:
        return (0, 0), True, 0
    stars, index = star_space(edges, n)
    flexible = 0
    for x in kernel:
        flexible |= x
    rigid = particular & ~flexible
    if rigid:
        # A fixed nonzero entry is a pivot for every possible rank-two form.
        choices = [p for p in range(len(edges)) if rigid >> p & 1]
    else:
        # Build the dual certificate. At least one edge participating in this
        # nonzero linear equation must be nonzero in every realization.
        dual = {}
        for k in kernel:
            for p in sorted(dual, reverse=True):
                if k >> p & 1:
                    k ^= dual[p][0]
            assert k
            p = k.bit_length() - 1
            dual[p] = k, 1 << p
        labels = 0
        for p in sorted(dual, reverse=True):
            if particular >> p & 1:
                k, _ = dual[p]
                particular ^= k
        assert particular
        q = particular.bit_length() - 1
        functional = 1 << q
        for p in sorted(dual):
            if (functional & dual[p][0]).bit_count() & 1:
                functional ^= 1 << p
        assert (functional & particular).bit_count() & 1
        assert all(not ((functional & k).bit_count() & 1) for k in kernel)
        choices = [p for p in range(len(edges)) if functional >> p & 1]

    projected = []
    for pivot in choices:
        i, j = edges[pivot]
        star = stars[i] | stars[j]
        deltas = star_basis(kernel, star)
        projected.append((len(deltas), pivot, star, deltas))
    projected.sort()
    if rigid:
        projected = projected[:1]
    values = {}
    for k in kernel:
        insert(values, k)
    basis = {p:k for p,(k,_) in values.items()}
    excluded = True
    peak = 0
    for rank, pivot, star, deltas in projected:
        peak = max(peak, rank)
        if rank > limit:
            excluded = False
            continue
        t = particular & star
        for k in range(1 << rank):
            if k:
                t ^= deltas[(k & -k).bit_length()-1]
            if not t >> pivot & 1:
                continue
            a,b = component(t, edges, index, n, pivot)
            matrix = 0
            for i in a:
                for j in b:
                    if i != j:
                        matrix ^= 1 << index[i, j]
            if insert_kernel(basis, particular ^ matrix):
                return (sum(1 << i for i in a), sum(1 << i for i in b)), True, peak
    return None, excluded, peak

def compile_solution(data, mask, target, wires, fact):
    x, y = [[q for i, q in enumerate(wires) if f >> i & 1] for f in fact]
    def parity(qs):
        v = 0
        for q in qs:
            v ^= data[q]
        return v
    residual = target ^ (parity(x) & parity(y))
    express = {}
    for i, v in enumerate([mask, *[data[q] for q in wires]]):
        assert insert(express, v, 1 << i) is None
    a = insert(express, residual)
    assert a is not None
    return [x, y, [q for i, q in enumerate(wires, 1) if a >> i & 1], a & 1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--range', choices=['local', 'phase', 'whole'], default='local')
    parser.add_argument('--samples', type=int, default=11000)
    parser.add_argument('--nullity-limit', type=int, default=14)
    parser.add_argument('--sat-ms', type=int, default=0)
    parser.add_argument('--complements', action='store_true')
    args = parser.parse_args()
    assert hashlib.sha256(args.source.read_bytes()).hexdigest() == SOURCE_SHA
    lines = str(km.Circuit.from_file(args.source, format='kmb')).splitlines()
    ops = list(map(gate, lines))
    phase_pos = {f.phase for f in FEATURES}
    assert all(ops[p] == ('Z_POW', (21,)) for p in phase_pos)
    queries = {}
    depth = 0
    starts = {f.start: i for i, f in enumerate(FEATURES)}
    for i, (op, qs) in enumerate(ops):
        if op == 'POP_CONDITION':
            depth -= 1
        if i in starts:
            queries[i] = [starts[i]]
        elif (not depth and op in ('CCX', 'CSWAP', 'HMR', 'Z_POW') and
              (args.range == 'whole' or args.range == 'phase' and 7600 <= i <= 8400)):
            eligible = [j for j, f in enumerate(FEATURES) if not f.start <= i < f.stop]
            if eligible:
                queries[i] = eligible
        if op == 'PUSH_CONDITION':
            depth += 1
    rng = np.random.default_rng(74005)
    xs = np.unique(np.r_[np.arange(1, 900), rng.integers(1, MAX_X+1, args.samples-900), MAX_X]).astype(np.uint32)
    if args.complements:
        phase_pos |= {f.base for f in FEATURES}
    def predicate(states, f):
        v = states[f.phase][21]
        if args.complements:
            v ^= states[f.base][ops[f.base][1][0]]
        return v
    sample_count = len(xs)
    states, mask = trace(ops, xs, set(queries) | phase_pos)
    phase = [predicate(states, f) for f in FEATURES]
    result = []
    hits = []
    for cut, selection in queries.items():
        data = states[cut]
        if cut not in starts and 0 not in data:
            continue
        wires, edges, kernel, particular = coefficients(data, mask, [phase[j] for j in selection])
        for j, p in zip(selection, particular):
            row = dict(cut=cut, feature=j, affine_rank=len(wires)+1, nullity=len(kernel))
            if p is None:
                row['result'] = 'outside_quadratic_span'
            else:
                fact, exhausted, row['star_rank'] = solve_coset(p, kernel, edges, len(wires), args.nullity_limit)
                if fact is None and not exhausted and args.sat_ms:
                    from complete_tripartite import find_by_sat
                    fact, exhausted = find_by_sat(len(wires), edges, kernel, p, args.sat_ms)
                    row['sat'] = 'SAT' if fact is not None else ('UNSAT' if exhausted else 'UNKNOWN')
                row['result'] = 'rank_two_candidate'  if fact is not None else ('rank_two_excluded' if exhausted else 'nullity_above_limit')
                if fact is not None:
                    row['solution'] = compile_solution(data, mask, phase[j], wires, fact)
                    hits.append(row)
            result.append(row)
        if cut in starts or len(result) % 100 == 0:
            print(result[-len(selection):], flush=True)
    if hits:
        xs = np.arange(1, MAX_X+1, dtype=np.uint32)
        full, domain = trace(ops, xs, {r['cut'] for r in hits} | phase_pos)
        for hit in hits:
            cut = hit['cut']
            v = full[cut]
            x, y, z, const = hit['solution']
            def xor(qs):
                p = 0
                for q in qs:
                    p ^= v[q]
                return p
            function = (xor(x) & xor(y)) ^ xor(z) ^ (domain if const else 0)
            signature = predicate(full, FEATURES[hit['feature']])
            difference = function ^ signature
            hit['zero_wires'] = [j for j, value in enumerate(v) if value == 0]
            hit['full_domain'] = difference == 0 and bool(hit['zero_wires'])
            if difference:
                hit['first_counterexample'] = (difference & -difference).bit_length()
    out = dict(source_sha=SOURCE_SHA, complements=args.complements, sample_count=sample_count, queries=len(result), results=result)
    args.output.write_text(json.dumps(out, indent=2)+'\n')
    print('queries', len(result), 'hits', hits, flush=True)

if __name__ == '__main__':
    main()
