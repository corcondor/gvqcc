#!/usr/bin/env python3
"""Exact local nonlinear-rank screening on both reachable ANGLE directions.

A window's entrance and exit wires are exact truth tables on 2440 inputs.
The number rank(span(1, entrance, exit))-rank(span(1, entrance)) is a lower
bound on new AND products needed by any XOR/AND implementation of that whole
wire mapping. Unlike the earlier fixed-prefix and single-CCX affine scans,
this includes all incoming angle-word bits and windows of several CCX gates.
The measurement/phase audit is separate: a value lower bound cannot by itself
certify an accepted candidate or claim global circuit optimality.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import resource
import time

import kickmix as km
import numpy as np

from chemistry_affine_span_resynthesis import parse_line
from chemistry_reachable_exact_proof import pack


def add(basis, value):
    while value:
        p = value.bit_length() - 1
        if p not in basis:
            basis[p] = value
            return True
        value ^= basis[p]
    return False


def rank_basis(values):
    basis = {}
    for value in values:
        add(basis, value)
    return basis


def audit(circuit, previous, current, sizes):
    count = len(previous)
    inputs = np.concatenate([previous, current], axis=0)
    addresses = np.tile(np.arange(count, dtype=np.uint64), 2)
    one = (1 << (2 * count)) - 1
    state = [0] * circuit.num_qubits
    state[:11] = [pack((addresses >> q) & 1) for q in range(11)]
    initial_selection = state[:11]
    for j in range(5):
        for bit in range(8):
            state[11 + 8 * j + bit] = pack((inputs[:, j] >> bit) & 1)
    entries, exits, positions, segments = [], [], [], []
    phase = {}
    gate_counts = Counter()
    first_diagonal = None
    last_ccx = None
    segment = 0
    for pos, line in enumerate(str(circuit).splitlines()):
        gate, qs, condition = parse_line(line)
        if gate in {'', 'REGISTER', 'APPEND_TO_REGISTER'}:
            continue
        gate_counts[gate] += 1
        if gate in {'X', 'CX', 'CCX', 'SWAP', 'HMR', 'R'}:
            assert condition is None
        if gate == 'X':
            state[qs[0]] ^= one
        elif gate == 'CX':
            state[qs[1]] ^= state[qs[0]]
        elif gate == 'SWAP':
            state[qs[0]], state[qs[1]] = state[qs[1]], state[qs[0]]
        elif gate == 'CCX':
            entries.append(tuple(state)); positions.append(pos); segments.append(segment)
            state[qs[2]] ^= state[qs[0]] & state[qs[1]]
            exits.append(tuple(state)); last_ccx = pos
        elif gate == 'R':
            assert state[qs[0]] == 0
        elif gate == 'HMR':
            bit = int(line.split()[-1][1:])
            assert not phase.get(bit, 0)
            phase[bit] = state[qs[0]]
            state[qs[0]] = 0
            segment += 1
        elif gate == 'CZ':
            if first_diagonal is None:
                first_diagonal = pos
            assert condition is not None and condition in phase
            phase[condition] ^= state[qs[0]] & state[qs[1]]
        else:
            raise ValueError((pos, gate))
    assert state[:11] == initial_selection
    assert not any(state[51:]) and not any(phase.values())
    expected = np.concatenate([current, previous], axis=0)
    for j in range(5):
        for bit in range(8):
            assert state[11 + 8 * j + bit] == pack((expected[:, j] >> bit) & 1)

    stats = {str(n): Counter() for n in sizes}
    deficient = []
    # The same entrance basis is reused for all selected window lengths.
    for i, entrance in enumerate(entries):
        base = rank_basis([one, *entrance])
        for size in sizes:
            j = i + size - 1
            if j >= len(exits):
                continue
            crosses_measurement = segments[i] != segments[j]
            if crosses_measurement:
                stats[str(size)]['crosses_measurement'] += 1
            basis = base.copy()
            extra = sum(add(basis, f) for f in exits[j])
            assert extra <= size
            stats[str(size)][f'extra_rank_{extra}'] += 1
            if extra < size:
                deficient.append(dict(ccx_first=i, ccx_last=j, line_first=positions[i],
                                      line_last=positions[j], size=size,
                                      entrance_rank=len(base), new_dimensions=extra,
                                      crosses_measurement=crosses_measurement))
    return dict(gates=dict(gate_counts), ccx=len(entries),
                first_diagonal_line=first_diagonal, last_ccx_line=last_ccx,
                all_phase_corrections_after_last_ccx=(first_diagonal is None or first_diagonal > last_ccx),
                exact_forward_reverse_values_and_formal_HMR_phase='PASS',
                statistics={k: dict(v) for k, v in stats.items()},
                deficient_windows=deficient)


def toy_checks():
    # Two independent ANDs require two products, even with arbitrary linear mixing.
    one = (1 << 16) - 1
    x = [sum(1 << a for a in range(16) if a >> b & 1) for b in range(4)]
    base = rank_basis([one, *x, 0, 0])
    b = base.copy()
    assert sum(add(b, v) for v in [*x, x[0] & x[1], x[2] & x[3]]) == 2
    # Common-target two-AND sum has only one new output dimension, so must survive.
    b = base.copy()
    assert sum(add(b, v) for v in [*x, (x[0] & x[1]) ^ (x[0] & x[2]), 0]) == 1
    # The surviving example is actually one AND x0*(x1 XOR x2).
    assert ((x[0] & x[1]) ^ (x[0] & x[2])) == (x[0] & (x[1] ^ x[2]))
    return dict(independent_two_product_lower_bound=2, common_factor_positive_bound=1,
                common_factor_positive_identity='PASS', exhaustive_basis_inputs=16)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--loaders', type=Path, required=True)
    ap.add_argument('--table', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--max-window', type=int, default=6)
    args = ap.parse_args()
    assert not args.output.exists()
    start = time.monotonic()
    data = np.load(args.table, allow_pickle=False)
    words = data['angle_words'].astype(np.uint64)
    assert words.shape == (1220, 75)
    sizes = list(range(2, args.max_window + 1))
    rows = []
    for k in range(15):
        path = args.loaders / f'angle_k_{k}.kmb'
        previous = words[:, 5*(k-1):5*k] if k else np.zeros((1220, 5), dtype=np.uint64)
        current = words[:, 5*k:5*(k+1)]
        row = audit(km.Circuit.from_file(path), previous, current, sizes)
        row.update(k=k, source_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        rows.append(row)
        print(json.dumps({k:v for k,v in row.items() if k not in {'deficient_windows','gates'}}), flush=True)
    result = dict(status='EXACT_LOCAL_NONLINEAR_RANK_SCREEN_COMPLETE',
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  table_sha256=hashlib.sha256(args.table.read_bytes()).hexdigest(),
                  truth_table_bits=2440, tested_window_sizes=sizes,
                  basis='constant plus every live quantum wire, including actual incoming angle-word data',
                  proof_scope='Same whole-wire mapping on both reachable batch directions, basis-preserving XOR/AND circuits; per-window entrance/exit only. No unrestricted-quantum or global-optimality claim.',
                  new_candidate_emitted=False, toffoli_reduction=0,
                  toy_checks=toy_checks(), loaders=rows,
                  seconds=time.monotonic()-start,
                  peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(status=result['status'], seconds=result['seconds'],
                         ccx=sum(r['ccx'] for r in rows),
                         deficient_windows=sum(len(r['deficient_windows']) for r in rows))), flush=True)


if __name__ == '__main__':
    main()
