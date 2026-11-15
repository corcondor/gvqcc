#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Independent finite checks of the shared-GF8 rank-11 SAT reduction.

This validates the necessary first-factor counts and the symmetries used to
normalize them. It does not assert rank 11 is achievable or impossible.
Only integer bit operations and exhaustive small finite sets are used.
"""
from __future__ import annotations
import hashlib
import itertools
import json
from pathlib import Path
import time


def parity(x):
    return x.bit_count() & 1


def evaluate(terms, a, b):
    y = 0
    for u, v, w in terms:
        if parity(u & a) and parity(v & b):
            y ^= w
    return y


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


def multiply(a, b):
    out = []
    for row in a:
        total = 0
        for k, value in enumerate(b):
            if row >> k & 1:
                total ^= value
        out.append(total)
    return tuple(out)


def column_apply(matrix, value):
    return sum(parity(row & value) << i for i, row in enumerate(matrix))


def compositions(total, size):
    if size == 1:
        yield (total,)
    else:
        for first in range(total + 1):
            for tail in compositions(total - first, size - 1):
                yield (first,) + tail


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    start = time.monotonic()
    root = Path(__file__).resolve().parent
    source = root / 'symmetry_dqi_20261115_gf8_joint12_input.txt'
    lines = source.read_text().splitlines()
    assert tuple(map(int, lines[0].split())) == (6, 12)
    terms = [tuple(map(int, line.split())) for line in lines[1:] if line.strip()]
    assert len(terms) == 12
    slices = [tuple(evaluate(terms, a, 1 << b) for b in range(6)) for a in range(8)]
    assert slices[1] == tuple(1 << i for i in range(6))
    assert all(rank(matrix) == 6 for matrix in slices[1:])
    small = [tuple(row & 7 for row in matrix[:3]) for matrix in slices]
    assert all(matrix == tuple(small[a]) + tuple(x << 3 for x in small[a])
               for a, matrix in enumerate(slices))
    reverse = {matrix: a for a, matrix in enumerate(small)}
    field = [[reverse[multiply(small[a], small[b])] for b in range(8)] for a in range(8)]
    assert all(field[a][b] == field[b][a] for a in range(8) for b in range(8))
    assert all((field[a ^ b][c] == (field[a][c] ^ field[b][c]))
               for a, b, c in itertools.product(range(8), repeat=3))
    inverses = [0] + [next(b for b in range(1, 8) if field[a][b] == 1) for a in range(1, 8)]
    # Check the common-operand change a -> a/a0 and output restoration y -> a0*y.
    scalar_checks = 0
    for a0 in range(1, 8):
        inverse = inverses[a0]
        for a in range(8):
            mapped = field[a][inverse]
            if a == a0:
                assert mapped == 1
            for b in range(64):
                y = evaluate(terms, mapped, b)
                restored = field[a0][y & 7] | (field[a0][y >> 3] << 3)
                assert restored == evaluate(terms, a, b)
                scalar_checks += 1
    # Sum of seven slice active counts is4r. Rank6 at every nonzero input
    # excludes r<=10. For r=11, enumerate all first-factor multiplicities.
    feasible = []
    enumerated = 0
    for counts in compositions(11, 7):
        enumerated += 1
        weights = [sum(counts[u - 1] for u in range(1, 8) if parity(u & a)) for a in range(1, 8)]
        if min(weights) < 6:
            continue
        distinguished = [a for a, w in enumerate(weights, 1) if w == 8]
        assert len(distinguished) == 1 and sorted(weights) == [6] * 6 + [8]
        a0 = distinguished[0]
        assert counts == tuple(1 + parity(u & a0) for u in range(1, 8))
        feasible.append({'a0': a0, 'counts': list(counts), 'weights': weights})
    assert len(feasible) == 7
    # GL(2,GF8) is represented by 2x2 blocks of the3x3 scalar matrices.
    # Verify that every invertible block matrix centralizes the three
    # independent slices, and its action on one nonzero factor reaches all63.
    group_size = 0
    first_factor_orbit = set()
    stabilizer_size = 0
    second_factor_orbit = set()
    for a, b, c, d in itertools.product(range(8), repeat=4):
        matrix = tuple(small[a][i] | (small[b][i] << 3) for i in range(3)) + tuple(
            small[c][i] | (small[d][i] << 3) for i in range(3))
        if rank(matrix) != 6:
            continue
        group_size += 1
        assert all(multiply(matrix, slices[t]) == multiply(slices[t], matrix) for t in (1, 2, 4))
        first_factor_orbit.add(column_apply(matrix, 1))
        if column_apply(matrix, 1) == 1:
            stabilizer_size += 1
            second_factor_orbit.add(column_apply(matrix, 8))
    assert group_size == (64 - 1) * (64 - 8) == 3528
    assert first_factor_orbit == set(range(1, 64))
    assert stabilizer_size == 56 and second_factor_orbit == set(range(8, 64))
    result = {
        'status': 'PASS_NECESSARY_COUNTS_AND_AUTOTOPIES_ONLY',
        'input_sha256': sha(source), 'source_sha256': sha(__file__),
        'tensor_dimensions': [3, 6, 6], 'input_rank': 12,
        'nonzero_slice_ranks': [rank(matrix) for matrix in slices[1:]],
        'field_identity_coordinate': 1, 'scalar_autotopy_checks': scalar_checks,
        'rank_below_11_excluded_by': '4*r >= 7*6',
        'rank11_count_vectors_enumerated': enumerated,
        'rank11_feasible_first_factor_count_vectors': sorted(feasible, key=lambda item: item['a0']),
        'centralizer_group_size': group_size, 'nonzero_factor_orbit_size': len(first_factor_orbit),
        'first_factor_stabilizer_size': stabilizer_size,
        'second_factor_stabilizer_orbit': sorted(second_factor_orbit),
        'fixed_v_normalization': 'Every nonzero factor can be mapped to1 by a centralizer conjugation; duplicate-u factors may be reordered.',
        'rank11_sat_or_unsat_claim': None,
        'seconds': time.monotonic() - start,
    }
    output = root / 'score6_dqi_shared11_independent.json'
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'rank11_feasible_first_factor_count_vectors'}))


if __name__ == '__main__':
    main()
