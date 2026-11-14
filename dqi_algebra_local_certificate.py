"""Exact limited lower certificate for an eleven-point symmetric dictionary.

This is not a lower bound for the 17-point or unrestricted GF24 problem.
"""
import itertools
import json
from pathlib import Path
import time

from dqi_algebra_interpolation import dictionary, extension_source, outer


def span(rows):
    pivots = {}
    for value in rows:
        while value:
            bit = value.bit_length() - 1
            if bit not in pivots:
                pivots[bit] = value
                break
            value ^= pivots[bit]
    return pivots


def contains(pivots, value):
    while value:
        bit = value.bit_length() - 1
        if bit not in pivots:
            return False
        value ^= pivots[bit]
    return True


def main():
    start = time.monotonic()
    ext = extension_source()
    matrices = [sum(mask << (4*i) for i in range(4) if mask >> i & 1)
                for mask in range(1, 16)]
    target = [sum(((ext.small_mul(1 << i, 1 << j) >> k) & 1) << (4*i+j)
                  for i in range(4) for j in range(4)) for k in range(4)]
    examined, solutions = 0, 0
    for chosen in itertools.combinations(range(15), 8):
        basis = span(matrices[i] for i in chosen)
        solutions += all(contains(basis, value) for value in target)
        examined += 1
    assert examined == 6435 and solutions == 0
    forms, _, _, _, _ = dictionary(ext)
    ranks = {points: len(span(outer(a) for a in forms[:15*points]))
             for points in range(1, 18)}
    assert ranks[11] == 110
    report = dict(status='EXACT_LIMITED_DICTIONARY_CERTIFICATE',
                  local_GF16_dictionary_size=15, subsets_of_size8_checked=examined,
                  GF16_rank8_symmetric_subsets=solutions,
                  local_GF16_symmetric_dictionary_minimum=9,
                  cumulative_symmetric_dictionary_ranks=ranks,
                  eleven_point_subspaces_form_direct_sum=True,
                  eleven_point_cost_minimum=99,
                  explanation='Each of the first eleven points contributes a disjoint 10-dimensional symmetric-form space. The target component at each point is an injective linear embedding of full GF16 multiplication. Every 8-of-15 choice was ruled out, so each point needs at least nine products in this restricted dictionary.',
                  limitations=['Only the first eleven fixed points are certified as a direct sum here.',
                               'No lower bound for 12-17 active points, nonsymmetric products, cross-point products, nonlinear circuits, or unrestricted GF24 multiplication.'],
                  elapsed_seconds=time.monotonic()-start)
    Path(__file__).with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
