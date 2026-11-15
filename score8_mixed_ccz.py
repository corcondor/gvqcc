#!/usr/bin/env python3
"""Search a field-multiplication phase using arbitrary mixed-register CCZs.

Unlike bilinear multiplication synthesis, the three parity factors of each
CCZ may use every wire in all three registers. Linear/quadratic phases are
free Z/CZ corrections. UNKNOWN/timeouts are explicitly not lower bounds.
Every SAT witness is checked on all 2^(3n) basis states with integer ANF.
"""
from __future__ import annotations

import argparse
from functools import reduce
import hashlib
from itertools import combinations, permutations
import json
from pathlib import Path
import time


def multiply(a, b, n, polynomial):
    c = 0
    while b:
        if b & 1:
            c ^= a
        b >>= 1
        a <<= 1
        if a >> n:
            a ^= polynomial
    return c


def target_value(x, n, polynomial):
    m = (1 << n) - 1
    return (multiply(x & m, (x >> n) & m, n, polynomial) & (x >> (2 * n))).bit_count() & 1


def anf(values, dimensions):
    result = list(values)
    for j in range(dimensions):
        for x in range(1 << dimensions):
            if x & (1 << j):
                result[x] ^= result[x ^ (1 << j)]
    return [x for x, b in enumerate(result) if b]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--degree", type=int, default=3)
    p.add_argument("--polynomial", type=lambda x: int(x, 0), default=0b1011)
    p.add_argument("--terms", type=int, default=5)
    p.add_argument("--timeout-ms", type=int, default=90000)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    import z3

    start = time.monotonic()
    n, d, r = a.degree, 3 * a.degree, a.terms
    truth = [target_value(x, n, a.polynomial) for x in range(1 << d)]
    target = set(anf(truth, d))
    assert all(x.bit_count() == 3 for x in target)
    s = z3.Solver()
    s.set(timeout=a.timeout_ms)
    rows = [[z3.BitVec(f"p_{t}_{j}", d) for j in range(3)] for t in range(r)]
    # RREF is canonical under GL(3,2); changing parity basis only adds a
    # quadratic phase, which is handled by the exact witness check below.
    for u, v, w in rows:
        pu, pv, pw = [x & -x for x in (u, v, w)]
        s.add(u != 0, v != 0, w != 0, z3.ULT(pu, pv), z3.ULT(pv, pw))
        s.add(u & pv == 0, u & pw == 0, v & pw == 0)
    keys = [z3.Concat(*row) for row in rows]
    for x, y in zip(keys, keys[1:]):
        s.add(z3.ULT(x, y))
    bits = [[[z3.Extract(j, j, row[k]) == 1 for j in range(d)] for k in range(3)] for row in rows]
    for inds in combinations(range(d), 3):
        products = [z3.And(bits[t][0][i], bits[t][1][j], bits[t][2][k])
                    for t in range(r) for i, j, k in permutations(inds)]
        parity = reduce(z3.Xor, products, z3.BoolVal(False))
        s.add(parity == z3.BoolVal(sum(1 << j for j in inds) in target))
    encoded = time.monotonic()
    status = s.check()
    result = {"field_degree": n, "polynomial": a.polynomial, "num_qubits": d,
              "requested_ccz_count": r, "solver": "z3", "solver_version": z3.get_version_string(),
              "timeout_ms": a.timeout_ms, "status": str(status),
              "encoding_seconds": encoded - start, "solve_seconds": time.monotonic() - encoded,
              "scope": "arbitrary mixed-register linear parities, CCZ phase plus free Z/CZ corrections",
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "actual_submission_modified": False, "claimed_gate_savings": 0}
    if status == z3.sat:
        m = s.model()
        parities = [[m.eval(p).as_long() for p in row] for row in rows]
        candidate = [sum(all((x & p).bit_count() & 1 for p in row) for row in parities) & 1 for x in range(1 << d)]
        residual = [u ^ v for u, v in zip(truth, candidate)]
        corrections = anf(residual, d)
        assert all(q.bit_count() <= 2 for q in corrections)
        reconstructed = [candidate[x] ^ (sum((x & q) == q for q in corrections) & 1) for x in range(1 << d)]
        assert reconstructed == truth
        result.update(parity_masks=parities, free_correction_monomials=corrections,
                      exact_basis_states_checked=len(truth), exact_phase_errors=0,
                      witness_note="Candidate identity only; no claim of a matching live block or score reduction.")
    elif status == z3.unknown:
        result["reason_unknown"] = s.reason_unknown()
        result["not_a_lower_bound"] = True
    else:
        result["independently_checked_unsat_certificate"] = False
    a.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
