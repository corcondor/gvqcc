#!/usr/bin/env python3
"""Independently verify numerical coefficients from Wang's Kaggle post759048.

The all-basis-pairs check is exhaustive for this bilinear map. This is not
an assertion that the current DQI circuit contains a compatible block.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

POLY = 0x1053
MASK = (1 << 12) - 1
GAMMA = 2048


def kmul(a, b):
    raw = 0
    for j in range(12):
        if (b >> j) & 1:
            raw ^= a << j
    for j in range(22, 11, -1):
        if (raw >> j) & 1:
            raw ^= POLY << (j - 12)
    return raw


def lmul(a, b):
    a0, a1 = a & MASK, a >> 12
    b0, b1 = b & MASK, b >> 12
    p11 = kmul(a1, b1)
    return (kmul(a0, b0) ^ kmul(GAMMA, p11)) | ((kmul(a0, b1) ^ kmul(a1, b0) ^ p11) << 12)


def target(h, d):
    return lmul(h, d) | (lmul(h >> 12, lmul(d, d)) << 24)


def basis_errors(terms):
    bad = []
    for i in range(24):
        for j in range(24):
            actual = 0
            for left, right, out in terms:
                if (left >> i) & (right >> j) & 1:
                    actual ^= out
            expected = target(1 << i, 1 << j)
            if actual != expected:
                bad.append([i, j, actual ^ expected])
    return bad


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--coefficients', type=Path, default=Path(__file__).with_name('outcome_rank173_coefficients.json'))
    parser.add_argument('--report', type=Path, default=Path(__file__).with_name('outcome_rank173_check.json'))
    args = parser.parse_args()
    started = time.monotonic()
    raw = args.coefficients.read_bytes()
    data = json.loads(raw)
    terms = data['terms']
    assert len(terms) == data['rank'] == 173
    assert data['K_poly'] == POLY
    assert all(len(t) == 3 and 0 < t[0] < 1 << 24 and 0 < t[1] < 1 << 24 and 0 <= t[2] < 1 << 48 for t in terms)
    # The chosen generator has multiplicative order4095, verifying the field.
    generator, seen = 1, set()
    for _ in range(4095):
        assert generator not in seen and generator != 0
        seen.add(generator)
        generator = kmul(generator, 2)
    assert generator == 1 and len(seen) == 4095
    trace, power = 0, GAMMA
    for _ in range(12):
        trace ^= power
        power = kmul(power, power)
    assert trace == 1
    errors = basis_errors(terms)
    assert not errors, errors[:5]
    mutated = [t.copy() for t in terms]
    mutated[0][2] ^= 1
    mutation_errors = basis_errors(mutated)
    assert mutation_errors
    result = {
        'status': 'PASS_BILINEAR_MAP_ONLY',
        'coefficient_source': data['provenance'],
        'coefficient_file_sha256': hashlib.sha256(raw).hexdigest(),
        'checker_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'rank': 173,
        'field_polynomial': POLY,
        'gamma': GAMMA,
        'basis_pairs_checked': 576,
        'output_bits_per_pair': 48,
        'mismatched_pairs': len(errors),
        'negative_control': {'flipped_output_mask_bit': 0, 'term_index': 0, 'detected_mismatched_pairs': len(mutation_errors)},
        'whole_circuit_candidate_generated': False,
        'scope': 'Complete identity check of the specified bilinear map, not a rank-optimality proof or a currentDQI substitution.',
        'applicability': 'Author states this improves older176-productpairedblocks to173. Current1376 independentGF24multipliers do not match that interface.',
        'seconds': time.monotonic() - started,
    }
    args.report.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
