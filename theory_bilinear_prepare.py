#!/usr/bin/env python3
"""Prepare exact existing DQI multiplication tensors for Polytof research.

The multiplication algorithms themselves are imported from the original
Apache-2.0 Syed source; no arithmetic circuit is replaced by this script.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def rank(values):
    basis = {}
    for value in values:
        while value:
            p = value.bit_length() - 1
            if p in basis:
                value ^= basis[p]
            else:
                basis[p] = value
                break
    return len(basis)


def outer(a, b, width):
    return sum(b << (i * width) for i in range(width) if a >> i & 1)


def evaluate(terms, a, b):
    out = 0
    for u, v, w in terms:
        if (u & a).bit_count() % 2 and (v & b).bit_count() % 2:
            out ^= w
    return out


def gf_mul(a, b, degree=12, modulus=0x1053):
    result = 0
    while b:
        if b & 1:
            result ^= a
        b >>= 1
        a <<= 1
        if a >> degree:
            a ^= modulus
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source-root', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    args = p.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    field_path = args.source_root / 'controller_work/work/round2/milestone152/source'
    ext_path = args.source_root / 'controller_work/night_root'
    sys.path[:0] = [str(field_path), str(ext_path)]
    import field_tensor
    import extension24_tensor
    import kickmix as km
    assert km.GF2Field(12).modulus == 0x1053
    records = []
    for n, module in ((12, field_tensor), (24, extension24_tensor)):
        terms = tuple(tuple(int(x) for x in t) for t in module.multiplication_tensor())
        def oracle(a, b):
            if n == 12:
                return gf_mul(a, b)
            a0, a1, b0, b1 = a & 4095, a >> 12, b & 4095, b >> 12
            low = gf_mul(a0, b0) ^ gf_mul(extension24_tensor.DELTA, gf_mul(a1, b1))
            high = gf_mul(a0, b1) ^ gf_mul(a1, b0) ^ gf_mul(a1, b1)
            return low | (high << 12)
        table = [[oracle(1 << i, 1 << j) for j in range(n)] for i in range(n)]
        for i in range(n):
            for j in range(n):
                assert evaluate(terms, 1 << i, 1 << j) == table[i][j]
        paired_ranks = {
            f'{i}{j}': rank(outer(t[i], t[j], n) for t in terms)
            for i, j in ((0, 1), (0, 2), (1, 2))
        }
        path = args.output_dir / f'gf{n}_input.txt'
        path.write_text(f'{n} {len(terms)}\n' + ''.join(' '.join(map(str, t)) + '\n' for t in terms))
        record = dict(degree=n, rank=len(terms), basis_pair_checks=n*n,
                      exact_bilinear_identity=True,
                      distinct_factors=[len({t[i] for t in terms}) for i in range(3)],
                      paired_factor_ranks=paired_ranks,
                      fixed_two_factors_deletion_obstructed=all(v == len(terms) for v in paired_ranks.values()),
                      source_path=str(Path(module.__file__).resolve()),
                      source_sha256=hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
                      input_path=str(path), input_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                      terms=terms)
        records.append(record)
    out = dict(status='PASS_EXACT_BILINEAR_CERTIFICATES', records=records,
               caveat='Fixed paired-factor independence is a restricted obstruction, not tensor-rank optimality.')
    output = args.output_dir / 'input_certificate.json'
    output.write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps({k:v for k,v in out.items() if k != 'records'}))
    print(json.dumps([{k:v for k,v in x.items() if k != 'terms'} for x in records], indent=2))


if __name__ == '__main__':
    main()
