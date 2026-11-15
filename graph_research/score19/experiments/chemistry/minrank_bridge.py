#!/usr/bin/env python3
"""Search rank-two bridge terms beyond a pair-sum closure of ANGLE matrices."""
from __future__ import annotations

import argparse
from collections import defaultdict
from functools import reduce
import hashlib
import json
from pathlib import Path
import struct
import sys
import time

import z3


def rank(vectors):
    basis = {}
    for value in vectors:
        while value:
            pivot = value.bit_length()
            if pivot not in basis:
                basis[pivot] = value
                break
            value ^= basis[pivot]
    return len(basis)


def rank2_sum(a, b):
    basis = {}
    for u, v in zip(a, b):
        value = u ^ v
        while value:
            pivot = value.bit_length()
            if pivot not in basis:
                basis[pivot] = value
                break
            value ^= basis[pivot]
        if len(basis) > 2:
            return None
    return tuple(u ^ v for u, v in zip(a, b))


def closure_components(original):
    assert rank([sum(row << (15 * h) for h, row in enumerate(m)) for m in original]) == len(original)
    mats = list(original)
    support = [1 << i for i in range(len(mats))]
    seen = set(mats)
    groups = support.copy()
    for i, a in enumerate(mats):
        for j in range(i):
            s = rank2_sum(a, mats[j])
            if s is None:
                continue
            joined = support[i] | support[j]
            merged = joined
            unaffected = []
            for group in groups:
                if group & joined:
                    merged |= group
                else:
                    unaffected.append(group)
            groups = unaffected + [merged]
            if s in seen:
                continue
            assert s != (0,) * 76
            seen.add(s)
            mats.append(s)
            support.append(support[i] ^ support[j])
    assert sum(g.bit_count() for g in groups) == len(original)
    return len(mats), groups


def load_segments(path, metadata):
    data = path.read_bytes()
    records = json.loads(metadata.read_text())
    offset = 0
    for row in records:
        size, = struct.unpack_from('<I', data, offset)
        offset += 4
        matrices = [struct.unpack_from('<76H', data, offset + i * 152) for i in range(size)]
        offset += size * 152
        assert len(matrices) == len(row['directions'])
        yield matrices, row
    assert offset == len(data)


def xor_sum(bits):
    return reduce(z3.Xor, bits, z3.BoolVal(False))


def check(matrices, metadata, time_limit):
    start = time.monotonic()
    n = len(matrices)
    closure_size, groups = closure_components(matrices)
    # Solve for every nonzero combination touching at least two old graph
    # components. Low plane coordinates and its two row coefficients are
    # unconstrained, so rank zero, one, or two are all admitted.
    solver = z3.Solver()
    solver.set(timeout=int(time_limit * 1000))
    select = [z3.Bool(f'e{i}') for i in range(n)]
    basis_a = [z3.Bool(f'a{j}') for j in range(15)]
    basis_b = [z3.Bool(f'b{j}') for j in range(15)]
    active = [z3.Or(*[select[i] for i in range(n) if g >> i & 1]) for g in groups]
    solver.add(z3.PbGe([(a, 1) for a in active], 2))
    for h in range(76):
        coeff_a, coeff_b = z3.Bools(f'ca{h} cb{h}')
        for l in range(15):
            given = xor_sum(select[i] for i in range(n) if matrices[i][h] >> l & 1)
            unknown = z3.Xor(z3.And(coeff_a, basis_a[l]), z3.And(coeff_b, basis_b[l]))
            solver.add(given == unknown)
    setup_seconds = time.monotonic() - start
    result = solver.check()
    row = dict(batch=metadata['batch'], first=metadata['start'], products=n,
               closure_size=closure_size, original_components=len(groups), status=str(result),
               setup_seconds=setup_seconds, seconds=time.monotonic() - start,
               source_sha256=metadata['source_sha256'])
    if result == z3.unknown:
        row['reason'] = solver.reason_unknown()
    elif result == z3.sat:
        model = solver.model()
        chosen = [i for i, e in enumerate(select) if z3.is_true(model.eval(e, model_completion=True))]
        support = sum(1 << i for i in chosen)
        merged = [g for g in groups if support & g]
        assert len(merged) >= 2
        combined = [reduce(int.__xor__, (matrices[i][h] for i in chosen), 0) for h in range(76)]
        new_rank = rank(combined)
        assert 0 < new_rank <= 2
        original_vertices = [i for i in range(n) if any(g >> i & 1 for g in merged)]
        output_rank = rank([metadata['directions'][i] for i in original_vertices])
        row.update(support=chosen, matrix=combined, verified_rank=new_rank,
                   merged_vertices=original_vertices, merged_output_rank=output_rank,
                   merged_output_dependent=output_rank < len(original_vertices))
    return row


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--segments', type=Path, required=True)
    p.add_argument('--metadata', type=Path, required=True)
    p.add_argument('--loaders', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--batch', type=int, required=True)
    p.add_argument('--seconds', type=float, default=10)
    a = p.parse_args()
    rows = []
    for matrices, record in load_segments(a.segments, a.metadata):
        if record['batch'] != a.batch:
            continue
        source = a.loaders / f"angle_k_{record['batch']}.kmb"
        assert hashlib.sha256(source.read_bytes()).hexdigest() == record['source_sha256']
        row = check(matrices, record, a.seconds)
        print(json.dumps(row), flush=True)
        rows.append(row)
    assert rows
    a.output.write_text(json.dumps(rows, indent=2) + '\n')


if __name__ == '__main__':
    main()
