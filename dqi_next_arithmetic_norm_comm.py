#!/usr/bin/env python3
"""Exact quadratic GF24 norm synthesis with mixed control forms.

Unlike bilinear GF12 searches, both AND factors may mix the two GF12
halves. The output remains a separate quantum register, so no Hadamard
gates or coherent classical lookups are introduced. Boolean diagonal
terms are retained as explicit CNOT corrections. A successful lower
rank still requires full-decoder substitution and verification.

Uses Syed Asad Ali's Apache-2.0 GF12 tensor as the initial decomposition
and the unmodified Polytof COMM executable as a bounded optimizer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.dont_write_bytecode = True
import numpy as np
import kickmix as km


def bits(value):
    while value:
        low = value & -value
        yield low.bit_length() - 1
        value ^= low


def polynomial(terms):
    result = {}
    for a, b, out in terms:
        for i in bits(a):
            for j in bits(b):
                key = (1 << i) | (1 << j)
                result[key] = result.get(key, 0) ^ out
    return {key: value for key, value in result.items() if value}


def pool_read(path):
    rows = np.load(path, allow_pickle=False)
    assert rows.ndim == 2 and rows.shape[1] % 6 == 0
    schemes = []
    for row in rows:
        vectors = [int(row[i]) | (int(row[i+1]) << 64)
                   for i in range(0, len(row), 2)]
        scheme = [tuple(vectors[i:i+3]) for i in range(0, len(vectors), 3)]
        schemes.append([(a, b, w) for a, b, w in scheme if a and b and a != b and w])
    return schemes


def pool_write(path, schemes):
    rows = [[piece for term in terms for vector in term
             for piece in (vector & ((1 << 64)-1), vector >> 64)]
            for terms in schemes]
    np.save(path, np.array(rows, dtype=np.uint64))


def bits_matrix(values, width):
    return ((np.asarray(values, dtype=np.uint64)[None, :] >>
             np.arange(width, dtype=np.uint64)[:, None]) & 1).astype(bool)


def parity_pair(builder, source, a, b):
    """Reversibly expose two independent linear forms without ancillas."""
    assert a and b and a != b
    p = (a & -a).bit_length()-1
    reduced = b ^ a if (b >> p) & 1 else b
    assert reduced and not (reduced >> p) & 1
    q = (reduced & -reduced).bit_length()-1
    gates = [(i, p) for i in bits(a) if i != p]
    gates += [(i, q) for i in bits(reduced) if i != q]
    if (b >> p) & 1:
        gates.append((p, q))
    for control, target in gates:
        builder.cx(source[control], source[target])
    return source[p], source[q], gates


def emit_norm(builder, source, target, terms, linear_correction, square_columns):
    for a, b, out in terms:
        first, second, gates = parity_pair(builder, source, a, b)
        pivot = (out & -out).bit_length()-1
        others = [j for j in bits(out) if j != pivot]
        for j in others:
            builder.cx(target[pivot], target[j])
        builder.ccx(first, second, target[pivot])
        for j in reversed(others):
            builder.cx(target[pivot], target[j])
        for i, j in reversed(gates):
            builder.cx(source[i], source[j])
    for i, col in enumerate(square_columns):
        for j in bits(col ^ linear_correction.get(1 << i, 0)):
            builder.cx(source[i], target[j])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--optimizer', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--attempts', type=int, default=10000)
    parser.add_argument('--path-limit', type=int, default=500000)
    parser.add_argument('--seconds', type=int, default=60)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(args.source))
    from field_tensor import multiplication_tensor
    field = km.GF2Field(12)
    terms = [(a, b << 12, w) for a, b, w in multiplication_tensor()]
    original = polynomial(terms)
    triples = []
    for mask, out in original.items():
        if mask.bit_count() == 2:
            i, j = list(bits(mask))
            triples.extend((i, j, k) for k in bits(out))
    tid = 9712
    tensor_dir = args.output/'data/tensors'
    pool_dir = args.output/'data/cpd/comm'
    tensor_dir.mkdir(parents=True)
    pool_dir.mkdir(parents=True)
    np.save(tensor_dir/f'{tid:04d}.npy', np.array([(24, 24, 12)] + sorted(triples), dtype=np.int64))
    pool_write(pool_dir/f'{tid:04d}-00042.npy', [terms])
    command = [str(args.optimizer), str(tid), '--continue', '--fgs', '--plus',
               '--save', '--verify', '--log', '-f', str(args.path_limit),
               '-m', str(args.attempts), '-s', '64', '-t', '2', '-p', '5000']
    started = time.monotonic()
    with (args.output/'optimizer.log').open('w') as log:
        proc = subprocess.Popen(command, cwd=args.output, stdout=log, stderr=subprocess.STDOUT)
        timed_out = False
        try:
            returncode = proc.wait(timeout=args.seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            proc.terminate()
            try:
                returncode = proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                returncode = proc.wait()
    bestpath = min(pool_dir.glob('9712-*.npy'), key=lambda p: int(p.stem.split('-')[1]))
    best = pool_read(bestpath)[0]
    candidate = polynomial(best)
    delta = {m: original.get(m, 0) ^ candidate.get(m, 0)
             for m in set(original) | set(candidate)}
    delta = {m: w for m, w in delta.items() if w}
    assert all(m.bit_count() == 1 for m in delta), 'Quadratic mismatch'
    square_columns = [field.mul(1 << i, 1 << i) for i in range(12)]
    square_columns += [field.mul(2048, field.mul(1 << i, 1 << i)) for i in range(12)]
    # Every constant, singleton, and pair coefficient is checked, which
    # exhaustively proves a degree <= 2 Boolean polynomial identity.
    checked = [0] + [1 << i for i in range(24)]
    checked += [(1 << i) | (1 << j) for i in range(24) for j in range(i+1, 24)]
    for x in checked:
        got = 0
        for a, b, w in best:
            if ((a & x).bit_count() & (b & x).bit_count() & 1):
                got ^= w
        for mask, w in delta.items():
            if (mask & x).bit_count() & 1:
                got ^= w
        assert got == field.mul(x & 4095, x >> 12)
    builder = km.CircuitBuilder()
    source = builder.create_quantum_register(24, 'source')
    target = builder.create_quantum_register(12, 'target')
    emit_norm(builder, source, target, best, delta, square_columns)
    circuit = builder.finish_circuit()
    cpath = args.output/'norm.kmb'
    circuit.to_file(cpath, format='kmb')
    rng = np.random.default_rng(2026111509712)
    values = rng.integers(0, 1 << 24, 16384, dtype=np.uint64)
    values[:len(checked)] = checked
    targets = rng.integers(0, 4096, len(values), dtype=np.uint64)
    expected = []
    for v, y in zip(values, targets):
        a, b = int(v) & 4095, int(v) >> 12
        expected.append(int(y) ^ field.mul(a, a) ^ field.mul(a, b) ^ field.mul(2048, field.mul(b, b)))
    simulator = km.Simulator(batch_size=len(values), seed=9712, counting_operations=True)
    simulator.use_same_registers_as(circuit)
    simulator.write_across_shots(source, bits_matrix(values, 24))
    simulator.write_across_shots(target, bits_matrix(targets, 12))
    simulator.do(circuit)
    assert np.array_equal(simulator.read_across_shots(source), bits_matrix(values, 24))
    assert np.array_equal(simulator.read_across_shots(target), bits_matrix(expected, 12))
    assert not simulator.read_phase_flipped_across_shots().any()
    simulator.do(circuit)
    assert np.array_equal(simulator.read_across_shots(target), bits_matrix(targets, 12))
    assert not simulator.read_phase_flipped_across_shots().any()
    report = dict(status='QUADRATIC_IDENTITY_AND_NATIVE_PASS', initial_and=42,
                  final_and=len(best), and_saved=42-len(best), optimizer_command=command,
                  optimizer_timed_out=timed_out, optimizer_returncode=returncode,
                  seconds=time.monotonic()-started, source_qubits=24, output_qubits=12,
                  total_qubits=circuit.num_qubits, clean_scratch=0,
                  static_toffoli=circuit.operation_statistics().num_toffoli_like,
                  symbolic_coefficient_checks=len(checked), symbolic_scope='All 2^24 input values by degree <=2 coefficient identity; arbitrary XOR target',
                  native_cases=len(values), native_passes=2, value_errors=0, phase_errors=0,
                  terms=best, diagonal_correction=delta,
                  circuit_sha256=hashlib.sha256(cpath.read_bytes()).hexdigest(),
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  source_files_modified=False, whole_decoder_candidate=False)
    (args.output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('terms','diagonal_correction')}, indent=2))


if __name__ == '__main__':
    main()
