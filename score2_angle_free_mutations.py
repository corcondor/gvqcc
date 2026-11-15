#!/usr/bin/env python3
"""Enumerate zero-added-AND angle mutations supported on one 16-row block.

At the original output-accumulation stage, every existing affine feature and
product can be fanned out to an additional output direction without another
CCX. We compute the exact valid-address function span, then its intersection
with functions supported on a specified high-address block. Adjacent loaders
must both implement a change to an interior angle batch; the last batch needs
only its own loader. Enumeration is over at most sixteen remaining bits.

This script produces a synthesis search space, not an accepted submission.
The changed physical words, both-direction phase proof, and official numerical
constraints must still be checked by the builder and refitter.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

import kickmix as km

from score2_angle_feature_patch import feature_context, solve, vector_basis


COUNT = 1220
ONES = (1 << COUNT) - 1


def function_space(circuit):
    context = feature_context(circuit)
    features = context['functions']
    pool = context['pool']

    def evaluate(mask):
        answer = ONES if mask & 1 else 0
        for i, qubit in enumerate(pool):
            if mask >> (qubit + 1) & 1:
                answer ^= features[i]
        return answer

    products = [evaluate(left) & evaluate(right)
                for left, right, _ in context['extraction']['terms']]
    vectors = features + products
    return vectors, {'feature_vectors': len(features),
                     'product_vectors': len(products),
                     'full_span_rank': len(vector_basis(vectors))}


def supported_subspace(vectors, lo, size):
    """Kernel of restriction to every address outside [lo, lo+size)."""
    local_mask = ((1 << size) - 1) << lo
    outside = ONES ^ local_mask
    projected_basis = {}
    local_generators = []
    for original in vectors:
        full = int(original)
        projected = full & outside
        while projected:
            pivot = projected.bit_length() - 1
            if pivot not in projected_basis:
                projected_basis[pivot] = projected, full
                break
            reduced, old_full = projected_basis[pivot]
            projected ^= reduced
            full ^= old_full
        if not projected:
            assert not full & outside
            local_generators.append(full >> lo)
    local_basis = vector_basis(local_generators)
    return [v for v, _ in local_basis.values()]


def enumerate_space(basis):
    values = [0]
    for value in basis:
        values += [old ^ value for old in values]
    assert len(set(values)) == len(values)
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--loaders', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    started = time.monotonic()
    spaces = {}
    summary = []
    for k in range(1, 15):
        source = args.loaders / f'angle_k_{k}.kmb'
        vectors, row = function_space(km.Circuit.from_file(source))
        local_spaces = []
        for high in range(77):
            size = min(16, COUNT - 16 * high)
            basis = supported_subspace(vectors, 16 * high, size)
            local_spaces.append(basis)
        spaces[k] = local_spaces
        row.update(k=k, source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                   block_dimensions=[len(b) for b in local_spaces])
        summary.append(row)
        print(json.dumps(row), flush=True)
    entries = []
    for k in range(1, 15):
        for high in range(77):
            basis = spaces[k][high]
            values = enumerate_space(basis)
            if k != 14:
                other = vector_basis(spaces[k + 1][high])
                values = [v for v in values if solve(other, v) is not None]
            nonzero = sorted((v for v in values if v), key=lambda v: (v.bit_count(), v))
            intersection = vector_basis(nonzero)
            if nonzero:
                entries.append({'batch': k, 'high_address': high,
                                'first_address': 16 * high,
                                'valid_rows': min(16, COUNT - 16 * high),
                                'dimension': len(intersection),
                                'basis': [v for v, _ in intersection.values()],
                                'patterns': nonzero,
                                'minimum_changed_words_per_column': nonzero[0].bit_count(),
                                'additional_ccx': 0})
    report = {'status': 'EXACT_FUNCTION_SPACES_ENUMERATED',
              'scope': 'tag-preserving output XORs on 1220 valid addresses; original4033 sources',
              'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'source_directory': str(args.loaders), 'loaders': summary,
              'entries': entries,
              'total_batch_block_patterns': sum(len(e['patterns']) for e in entries),
              'minimum_support': min(e['minimum_changed_words_per_column'] for e in entries),
              'full_circuit_verified': False, 'score_gain_claimed': False,
              'seconds': time.monotonic() - started}
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('loaders','entries')}), flush=True)


if __name__ == '__main__':
    main()
