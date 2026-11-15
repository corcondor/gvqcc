#!/usr/bin/env python3
"""Exact integer Givens sign-gauge constraints, not a candidate circuit builder."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import sys
import time
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = Path('/workspace/scratch/3815fb5fae06/score2_best_family/submission.npz')


def solve(rows, n):
    pivots = {}
    for row in rows:
        while row & ((1 << n) - 1):
            p = (row & ((1 << n) - 1)).bit_length() - 1
            if p not in pivots:
                pivots[p] = row
                break
            row ^= pivots[p]
        else:
            if row >> n:
                return None, len(pivots)
    value = 0
    for p, row in sorted(pivots.items()):
        bit = ((row >> n) ^ ((row & value).bit_count() & 1)) & 1
        value |= bit << p
    assert all((((r & ((1 << n)-1)) & value).bit_count() & 1) == (r >> n) for r in rows)
    return value, len(pivots)


def gauge_row(words, edges, target_tags):
    # Variable j is angle reflection s_j; variable 75 is global sign.
    n = len(words) + 1
    rhs = 1 << n
    signs = [0] * n
    active = [False] * n
    active[0] = True
    delta = (((words >> 6) ^ (words >> 7)) & 1) ^ target_tags[np.arange(len(words)) % 5]
    for j, (p, c) in enumerate(edges):
        # For w -> -w, bit6 XOR bit7 changes iff w == 64 or 192.
        axis = int(words[j] % 128 == 64)
        k = (int(delta[j]) * rhs) ^ ((1 << j) if axis else 0)
        signs[p] ^= k
        signs[c] = signs[p] ^ (1 << j)
        was = active[p]
        active[p] = was and words[j] % 128 != 64
        active[c] = was and words[j] % 128 != 0
    constraints = [signs[i] ^ (1 << (n-1)) for i in range(n) if active[i]]
    solution, rank = solve(constraints, n)
    if solution is None:
        return None, rank, sum(active)
    reflections = np.array([(solution >> j) & 1 for j in range(n-1)], dtype=np.int64)
    shifts = delta ^ ((words % 128 == 64) & reflections)
    changed = (((1 - 2 * reflections) * words) + 128 * shifts) % 256
    assert np.array_equal((((changed >> 6) ^ (changed >> 7)) & 1), target_tags[np.arange(n-1) % 5])
    return (changed, int(solution >> (n-1)), reflections, shifts), rank, sum(active)


def binary_rank(table):
    rows = []
    for row in np.asarray(table, dtype=np.uint8):
        rows.append(int.from_bytes(row.tobytes(), 'little'))
    pivots = {}
    for row in rows:
        while row:
            p = row.bit_length() - 1
            if p in pivots: row ^= pivots[p]
            else:
                pivots[p] = row
                break
    return len(pivots)


def main():
    start = time.monotonic()
    source = dict(np.load(SOURCE, allow_pickle=False))
    words = source['angle_words'].astype(np.int64)
    edges = source['tree_edges'].astype(int)
    sys.path.insert(0, str(ROOT/'official_sources/Inzainos/verifiers'))
    from dfthcsos.scoreinfra.dfthc_math import reconstruct_u_vectors
    original = reconstruct_u_vectors(words / 128, edges)
    tags = (((words >> 6) ^ (words >> 7)) & 1)
    assert np.array_equal(tags, np.tile(tags[:, :5], (1, 15)))
    addresses = np.arange(len(words))
    pairs = [(0,1),(0,2),(1,2),(0,3),(1,3)]
    canonical = np.stack([((addresses >> a)&1)*((addresses >> b)&1) for a,b in pairs], axis=1)
    assert np.array_equal(canonical, tags[:, :5])
    studies = []
    choices = [('zero', np.zeros((len(words),5), dtype=np.int64))]
    choices += [(f'constant_{1<<j}', np.tile(np.eye(5,dtype=np.int64)[j], (len(words),1))) for j in range(5)]
    for name, desired in choices:
        changed = words.copy()
        global_signs = []
        ranks, supports = Counter(), Counter()
        reflections_count = shifts_count = 0
        for a in range(len(words)):
            solved, rank, active = gauge_row(words[a], edges, desired[a])
            assert solved is not None, (name,a)
            changed[a], g, reflections, shifts = solved
            global_signs.append(1-2*g)
            ranks[rank] += 1
            supports[int(active)] += 1
            reflections_count += int(reflections.sum())
            shifts_count += int(shifts.sum())
        transformed = reconstruct_u_vectors(changed/128, edges)
        residual = np.max(np.abs(transformed - np.asarray(global_signs)[:,None] * original))
        assert residual < 2e-14
        # The first address->40-bit load has five output-linear constraints in
        # a constant-tag gauge. Transitions already have these in the baseline.
        first_rank = binary_rank(changed[:,:5].astype(np.uint8))
        transition_ranks = [binary_rank((changed[:,5*k:5*k+5] ^ changed[:,5*(k-1):5*k]).astype(np.uint8)) for k in range(1,15)]
        studies.append(dict(name=name, rows=len(words), changed_words=int(np.count_nonzero(changed!=words)),
                            reflection_choices=reflections_count, pi_shift_choices=shifts_count,
                            sign_constraint_rank_distribution=dict(sorted(ranks.items())),
                            final_exact_nonzero_coordinate_count=dict(sorted(supports.items())),
                            max_signed_vector_residual=float(residual),
                            first_load_binary_rank=first_rank,
                            first_load_affine_rank=binary_rank((changed[:,:5] ^ changed[0,:5]).astype(np.uint8)),
                            transition_binary_ranks=transition_ranks,
                            table_sha256=hashlib.sha256(changed.tobytes()).hexdigest()))
    result = dict(source=str(SOURCE), source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                  theorem='wprime=(-1)^s*w+128*k mod256; tag change is k XOR s*[w mod128=64]; propagated final signs equal on nonzero coordinates.',
                  canonical_tags_confirmed=True, baseline_first_load_binary_rank=binary_rank(words[:,:5].astype(np.uint8)),
                  baseline_first_load_affine_rank=binary_rank((words[:,:5] ^ words[0,:5]).astype(np.uint8)),
                  baseline_transition_binary_ranks=[binary_rank((words[:,5*k:5*k+5] ^ words[:,5*(k-1):5*k]).astype(np.uint8)) for k in range(1,15)],
                  studies=studies, seconds=time.monotonic()-start,
                  scope='Exact gauge constraints and all-row vector equality. No matching loader emitted, no Toffoli reduction, no full circuit or official numeric verification newly claimed.',
                  interpretation='Initial-load output rank may fall by five, but every later delta already has five conserved-tag relations. Existing tags also cache useful address ANDs. Generic zero-tag normalization therefore does not certify gate savings.')
    path = HERE/'symmetry_chemistry_20261115_tags.json'
    path.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__ == '__main__': main()
