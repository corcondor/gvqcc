"""Explicit interpolation multipliers and improved GF(2^12) inverse kernels.

The 12-bit multiplier uses degree-three polynomials over GF(8), evaluated
at six finite points and infinity. Seven GF(8) products need six ANDs each.
The 6-bit multiplier uses degree-two polynomials over GF(4): five products
with three ANDs each. All basis changes are linear and need no work bits.

This file is a standalone candidate; no competition DQI file is modified.
"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
import heapq
import json
from pathlib import Path
import time

import inverse_specialized as isp
import full_inverse_verify as fiv
import pebble_search as ps

POLYS = {1: 0b11, 2: 0b111, 3: 0b1011, 4: 0b10011, 6: 0b1000011, 12: 0x1053}


def polynomial_terms(left, right):
    """Unreduced Karatsuba tensor, independent of temporary module hooks."""
    n = len(left)
    if n == 1:
        return [(left[0], right[0], 1)]
    k = (n+1)//2
    low = polynomial_terms(left[:k], right[:k])
    high = polynomial_terms(left[k:], right[k:])
    mixed = polynomial_terms([left[i] ^ (left[k+i] if k+i < n else 0) for i in range(k)],
                             [right[i] ^ (right[k+i] if k+i < n else 0) for i in range(k)])
    return ([(u, v, w ^ (w << k)) for u, v, w in low]
            + [(u, v, (w << k) ^ (w << (2*k))) for u, v, w in high]
            + [(u, v, w << k) for u, v, w in mixed])


def mul(a, b, d):
    out = 0
    while b:
        if b & 1:
            out ^= a
        a <<= 1
        if a & (1 << d):
            a ^= POLYS[d]
        b >>= 1
    return out


def power(a, e, d):
    out = 1
    while e:
        if e & 1:
            out = mul(out, a, d)
        a = mul(a, a, d)
        e >>= 1
    return out


def evaluate(coeffs, x, d):
    out = 0
    for c in reversed(coeffs):
        out = mul(out, x, d) ^ c
    return out


def poly_bits_eval(poly, x, d):
    return evaluate([(poly >> i) & 1 for i in range(poly.bit_length())], x, d)


def xor_selected(values, mask):
    out = 0
    while mask:
        low = mask & -mask
        out ^= values[low.bit_length() - 1]
        mask ^= low
    return out


def binary_apply(rows, x):
    return sum(((row & x).bit_count() & 1) << i for i, row in enumerate(rows))


def inverse_matrix(a, d):
    n = len(a)
    w = [list(row) + [int(i == j) for j in range(n)] for i, row in enumerate(a)]
    for col in range(n):
        pivot = next(i for i in range(col, n) if w[i][col])
        w[col], w[pivot] = w[pivot], w[col]
        scale = power(w[col][col], (1 << d) - 2, d)
        w[col] = [mul(x, scale, d) for x in w[col]]
        for i in range(n):
            if i != col and w[i][col]:
                scale = w[i][col]
                w[i] = [x ^ mul(scale, y, d) for x, y in zip(w[i], w[col])]
    assert [row[:n] for row in w] == [[int(i == j) for j in range(n)] for i in range(n)]
    return [row[n:] for row in w]


@lru_cache(None)
def gf8_tensor():
    # A product of two degree-two binary polynomials has degree <= 4.
    # Values at 0, 1, omega in GF(4), plus the coefficient at infinity,
    # supply five independent binary coordinates for interpolation.
    columns = []
    for k in range(5):
        columns.append(int(k == 0) | (1 << 1) | (power(2, k, 2) << 2) | (int(k == 4) << 4))
    rows = [sum(((c >> j) & 1) << i for i, c in enumerate(columns)) for j in range(5)]
    inv = isp.invert_rows(rows)
    evaluation_terms = [(1, 1, 1), (7, 7, 2),
                        (5, 5, 3 << 2), (6, 6, 1 << 2), (3, 3, 2 << 2),
                        (4, 4, 1 << 4)]
    terms = []
    for u, v, value in evaluation_terms:
        polynomial = binary_apply(inv, value)
        while polynomial.bit_length() > 3:
            polynomial ^= POLYS[3] << (polynomial.bit_length() - 4)
        assert polynomial
        terms.append((u, v, polynomial))
    return tuple(terms)


@lru_cache(None)
def tensor(d):
    if d == 1:
        return ((1, 1, 1),)
    if d == 2:
        return ((1, 1, 3), (2, 2, 1), (3, 3, 2))
    if d == 3:
        return gf8_tensor()
    if d == 4:
        terms = polynomial_terms([1 << i for i in range(d)], [1 << i for i in range(d)])
        reduced = []
        for u, v, w in terms:
            while w.bit_length() > d:
                w ^= POLYS[d] << (w.bit_length() - d - 1)
            if w:
                reduced.append((u, v, w))
        return tuple(reduced)
    if d not in (6, 12):
        raise ValueError(d)
    g = 2 if d == 6 else 3
    n = d // g
    gamma = next(x for x in range(2, 1 << d) if poly_bits_eval(POLYS[g], x, d) == 0)
    base_columns = [power(gamma, j, d) for j in range(g)]

    def embed(x):
        return xor_selected(base_columns, x)

    # theta=2 is the ambient polynomial generator; its degree over the
    # subfield is n, hence this tower change of basis is invertible.
    columns = [mul(power(2, i, d), base_columns[j], d) for i in range(n) for j in range(g)]
    rows = [sum(((c >> j) & 1) << i for i, c in enumerate(columns)) for j in range(d)]
    to_tower = isp.invert_rows(rows)
    finite_points = list(range(2 * n - 2))
    assert len(finite_points) <= (1 << g)
    count = 2 * n - 1
    matrix = [[power(p, k, g) for k in range(count)] for p in finite_points]
    matrix.append([int(k == count - 1) for k in range(count)])
    interpolation = inverse_matrix(matrix, g)
    terms = []
    for point_index in range(count):
        # Product value at this point contributes L_j(theta) times itself.
        lagrange = evaluate([embed(interpolation[k][point_index]) for k in range(count)], 2, d)
        evaluation_columns = []
        for bit in range(d):
            coords = binary_apply(to_tower, 1 << bit)
            coeffs = [(coords >> (g * k)) & ((1 << g) - 1) for k in range(n)]
            evaluated = (evaluate(coeffs, finite_points[point_index], g)
                         if point_index < len(finite_points) else coeffs[-1])
            evaluation_columns.append(evaluated)
        evaluation_rows = [sum(((col >> k) & 1) << i for i, col in enumerate(evaluation_columns))
                           for k in range(g)]
        for u, v, w in tensor(g):
            out = mul(embed(w), lagrange, d)
            assert out
            terms.append((xor_selected(evaluation_rows, u), xor_selected(evaluation_rows, v), out))
    return tuple(terms)


def verify_tensors():
    reports = []
    for d in (2, 3, 4, 6, 12):
        terms = tensor(d)
        # The identity is bilinear. Equality on every pair of basis vectors
        # proves the complete truth table without enumerating 2^(2d) cases.
        for i in range(d):
            for j in range(d):
                actual = 0
                for u, v, w in terms:
                    if (u >> i) & 1 and (v >> j) & 1:
                        actual ^= w
                assert actual == mul(1 << i, 1 << j, d), (d, i, j, actual)
        reports.append({"field_degree": d, "ccx_count": len(terms), "basis_pairs_checked": d*d,
                        "all_pairs_proven_by_bilinearity": True, "status": "PASS"})
    return reports


def field_terms(left, right):
    d = len(left)
    assert d == len(right)
    return [(xor_selected(left, u), xor_selected(right, v), w) for u, v, w in tensor(d)]


@lru_cache(None)
def power_map(a):
    # Existing constructor expects output polynomials evaluated at a root
    # of POLYS[d]. Reducing them modulo that polynomial preserves its map.
    old = isp.polynomial_mul_terms
    try:
        isp.polynomial_mul_terms = field_terms
        return isp.make_power_map(a)
    finally:
        isp.polynomial_mul_terms = old


def compute_product(left, right, target, exponent_b):
    shift = fiv.frobenius_gates(left, exponent_b)
    gates = shift[:]
    for u, v, out in tensor(12):
        gu = sum(1 << left[i] for i in range(12) if (u >> i) & 1)
        gv = sum(1 << right[i] for i in range(12) if (v >> i) & 1)
        gates += fiv.vector_product(gu, gv, out, target)
    gates += list(reversed(shift))
    assert sum(g[0] == "CCX" for g in gates) == 42
    return gates


def search(cap, objective, costs):
    phase_goal = objective == "phase_then_clear"
    goal = ps.PHASE_BIT if phase_goal else ps.OUTPUT_BIT
    distances = {0: (0, 0, 0)}
    previous = {}
    heap = [(0, 0, 0, 0)]
    while heap:
        cost, multiplies, steps, state = heapq.heappop(heap)
        if distances[state] != (cost, multiplies, steps):
            continue
        if state == goal:
            break
        mask, phase = state & ps.VALUE_MASK, state & ps.PHASE_BIT
        count = mask.bit_count()
        moves = []
        if phase_goal and not phase and mask & ps.OUTPUT_BIT:
            moves.append((state | ps.PHASE_BIT, 0, 0,
                          {"action": "phase", "target": 11, "registers_during": count}))
        for k, decompositions in ps.FACTORS.items():
            bit = 1 << (k-2)
            erasing = bool(mask & bit)
            for a, b in decompositions:
                if not (ps.present(mask, a) and ps.present(mask, b)):
                    continue
                peak = count + (not erasing)
                if peak > cap:
                    continue
                step_cost = 0 if erasing else costs[a] if a == b else 42
                moves.append(((mask ^ bit) | phase, step_cost, int(not erasing),
                              {"action": "erase" if erasing else "compute", "target": k,
                               "a": a, "b": b, "forward_cost": step_cost, "registers_during": peak}))
        for next_state, step_cost, new_multiplies, move in moves:
            dist = cost + step_cost, multiplies + new_multiplies, steps + 1
            if dist >= distances.get(next_state, (10**9,)*3):
                continue
            move.update(live_before=ps.live_values(mask), live_after=ps.live_values(next_state & ps.VALUE_MASK))
            distances[next_state] = dist
            previous[next_state] = state, move
            heapq.heappush(heap, (*dist, next_state))
    if goal not in distances:
        return None
    path = []
    current = goal
    while current:
        current, move = previous[current]
        path.append(move)
    path.reverse()
    return {"model": "interpolation_weighted", "objective": objective, "max_registers": cap,
            "reachable": True, "forward_cost": distances[goal][0],
            "multiplications": distances[goal][1], "steps": path,
            "peak_registers": max(s["registers_during"] for s in path)}


def main():
    started = time.perf_counter()
    directory = Path(__file__).parent
    tensor_reports = verify_tensors()
    costs = {a: power_map(a)["ccx_count"] for a in range(1, 6)}
    print("Multiplier counts:", tensor_reports, flush=True)
    print("Specialized power counts:", costs, flush=True)
    # Full gate simulation below checks these constructors, including exact
    # cancellation of independent symbolic measurement phase coefficients.
    fiv.make_power_map = power_map
    fiv.compute_product = compute_product
    expected = {k: fiv.table_for_values([fiv.gf_power(x, (1 << k)-1) for x in range(4096)])
                for k in range(1, 12)}
    expected["inverse"] = fiv.table_for_values([fiv.gf_power(x, 4094) for x in range(4096)])
    assert all(isp.gf_mul(x, fiv.gf_power(x, 4094)) == 1 for x in range(1, 4096))
    reports = []
    schedules = []
    old_results = json.loads(directory.joinpath("full_inverse_verify_results.json").read_text())["results"]
    old_counts = {(r["objective"], r["extra_words"]): r["toffoli_count"] for r in old_results}
    for objective in ("retained_output", "phase_then_clear"):
        for cap in (3, 4, 5):
            schedule = search(cap, objective, costs)
            if schedule is None:
                continue
            schedules.append(schedule)
            compiled = fiv.compile_schedule(schedule)
            result = fiv.verify(compiled, objective, expected)
            counts = dict(Counter(g[0] for g in compiled["gates"]))
            result.update(objective=objective, extra_words=compiled["extra_words"],
                          qubits=compiled["qubits"], gates=len(compiled["gates"]),
                          gate_counts=counts, toffoli_count=counts["CCX"],
                          previous_toffoli_count=old_counts[(objective, cap)])
            result["toffoli_reduction"] = result["previous_toffoli_count"] - counts["CCX"]
            name = f"inverse_v2_{objective}_{cap}words.kmx"
            fiv.export_kmx(compiled, objective, directory/name)
            result["kmx_file"] = name
            reports.append(result)
            print(json.dumps(result), flush=True)
    payload = {"field_modulus": POLYS[12], "multiplier_proofs": tensor_reports,
               "specialized_power_counts": costs, "results": reports, "schedules": schedules,
               "elapsed_seconds": time.perf_counter()-started,
               "scope": "Standalone arithmetic kernels with exact input and HMR-phase verification; no DQI integration or official validator."}
    directory.joinpath("inverse_v2_results.json").write_text(json.dumps(payload, indent=2)+"\n")


if __name__ == "__main__":
    main()
