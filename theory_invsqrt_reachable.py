#!/usr/bin/env python3
"""Exact reachable-domain contraction of inverse-root reversible phase circuits.

This pass uses bit-packed truth tables for every permitted x, never sampled
inputs as proof. Small deterministic signatures are only candidate filters.
Conditioned subcircuits are explored on the complete entry domain; they may
be joined only when their data outputs equal their entry values exactly.
HMR is retained verbatim, so each measurement outcome and phase correction
retains the same quantum value at the measurement. General rotations and
all classical operations are retained. No approximation is introduced.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import re
import resource
import time

import numpy as np

MAX_X = 3_133_452
BASELINE_SHA = 'e46d90c36d1beb3ce7731a3e0b5c3659b3cda7f5f290b73c6c34513d96c005b6'


def run(source, report_path, output=None, max_terms=2):
    import kickmix as km
    started = time.monotonic()
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != BASELINE_SHA:
        raise ValueError('This initial pass is pinned to the inspected e46 circuit.')
    circuit = km.Circuit.from_file(str(source))
    original = str(circuit).splitlines()
    domain = ((1 << (MAX_X + 1)) - 1) ^ 1
    xs = np.arange(MAX_X + 1, dtype=np.uint32)
    values = [int.from_bytes(np.packbits(((xs >> k) & 1).astype(np.uint8), bitorder='little').tobytes(), 'little') & domain for k in range(22)]
    values += [0] * (circuit.num_qubits - 22)
    del xs
    rng = random.Random(20261115)
    sample = [1, 2, 3, MAX_X] + [rng.randrange(1, MAX_X + 1) for _ in range(252)]
    sigmask = (1 << len(sample)) - 1
    signatures = [sum(((x >> k) & 1) << j for j, x in enumerate(sample)) for k in range(22)]
    signatures += [0] * (circuit.num_qubits - 22)
    initial_values = values.copy()
    branches = []
    rewrites = []
    kept = []
    verified_joins = 0
    scanned = Counter()
    stop = None
    peak_nonzero = {'count': 0, 'line': 0, 'qubits': []}
    affine_decisions = {'queries': 0, 'counterexample_refinements': 0, 'max_refinements': 0,
                        'witness_inputs': []}

    def affine_match(value, signature, excluded):
        if not value:
            return (False, ())
        if value == domain:
            return (True, ())
        eligible = [q for q in range(len(values)) if q not in excluded]
        index = {}
        for q in eligible:
            index.setdefault(signatures[q], []).append(q)
        if max_terms > 2:
            affine_decisions['queries'] += 1
            generators = [(sigmask, domain, 1 << len(values))]
            generators += [(signatures[q], values[q], 1 << q) for q in eligible]
            target_signature, signature_width = signature, len(sample)
            # A rejected signature solution produces an exact counterexample
            # row. It increases the augmented constraint rank, so after at
            # most number_of_generators+1 refinements the linear system is
            # either inconsistent or a full-domain solution is certified.
            for refinements in range(len(generators) + 2):
                affine_decisions['max_refinements'] = max(affine_decisions['max_refinements'], refinements)
                basis = {}
                for s, _v, mask in generators:
                    while s:
                        pivot = s.bit_length() - 1
                        if pivot not in basis:
                            basis[pivot] = (s, mask)
                            break
                        bs, bm = basis[pivot]
                        s ^= bs
                        mask ^= bm
                s, coefficients = target_signature, 0
                while s:
                    pivot = s.bit_length() - 1
                    if pivot not in basis:
                        return None
                    bs, bm = basis[pivot]
                    s ^= bs
                    coefficients ^= bm
                constant = bool(coefficients >> len(values))
                controls = tuple(q for q in eligible if (coefficients >> q) & 1)
                rebuilt = domain if constant else 0
                for q in controls:
                    rebuilt ^= values[q]
                difference = rebuilt ^ value
                if difference == 0:
                    return constant, controls
                witness = (difference & -difference).bit_length() - 1
                assert 1 <= witness <= MAX_X
                generators = [(s | (((v >> witness) & 1) << signature_width), v, mask)
                              for s, v, mask in generators]
                target_signature |= ((value >> witness) & 1) << signature_width
                signature_width += 1
                affine_decisions['counterexample_refinements'] += 1
                affine_decisions['witness_inputs'].append({'source_line': lineno, 'x': witness})
            raise AssertionError('Affine refinement did not converge within its rank bound')
        for constant in (False, True):
            target_sig = signature ^ (sigmask if constant else 0)
            target = value ^ (domain if constant else 0)
            for q in index.get(target_sig, []):
                if values[q] == target:
                    return (constant, (q,))
            if max_terms >= 2:
                for q in eligible:
                    for r in index.get(target_sig ^ signatures[q], []):
                        if r > q and (values[q] ^ values[r]) == target:
                            return (constant, (q, r))
        return None

    for lineno, line in enumerate(original):
        parts = line.split()
        op = parts[0]
        qubits = list(map(int, re.findall(r'\bq(\d+)\b', line)))
        replacement = None
        scanned[op] += 1
        if op == 'PUSH_CONDITION':
            branches.append((lineno, values.copy(), signatures.copy()))
        elif op == 'POP_CONDITION':
            start_line, before, before_sig = branches.pop()
            changes = [q for q in range(len(values)) if values[q] != before[q]]
            if changes:
                stop = {'at_line': lineno, 'branch_start': start_line, 'changed_data_qubits': changes}
                kept.extend(original[lineno:])
                break
            verified_joins += 1
            values, signatures = before, before_sig
        elif op == 'X':
            q, = qubits
            values[q] ^= domain
            signatures[q] ^= sigmask
        elif op == 'CX':
            a, t = qubits
            values[t] ^= values[a]
            signatures[t] ^= signatures[a]
        elif op == 'CCX':
            a, b, t = qubits
            product = values[a] & values[b]
            product_sig = signatures[a] & signatures[b]
            match = affine_match(product, product_sig, {t})
            if match is not None:
                constant, controls = match
                replacement = ([f'X q{t}'] if constant else []) + [f'CX q{q} q{t}' for q in controls]
            values[t] ^= product
            signatures[t] ^= product_sig
        elif op == 'CSWAP':
            control, a, b = qubits
            delta = values[control] & (values[a] ^ values[b])
            delta_sig = signatures[control] & (signatures[a] ^ signatures[b])
            if delta == 0:
                replacement = []
            elif delta == (values[a] ^ values[b]):
                replacement = [f'SWAP q{a} q{b}']
            else:
                match = affine_match(delta, delta_sig, {a, b})
                if match is not None:
                    constant, controls = match
                    replacement = ([f'X q{a}', f'X q{b}'] if constant else [])
                    replacement += [l for q in controls for l in (f'CX q{q} q{a}', f'CX q{q} q{b}')]
            values[a] ^= delta
            values[b] ^= delta
            signatures[a] ^= delta_sig
            signatures[b] ^= delta_sig
        elif op == 'SWAP':
            a, b = qubits
            values[a], values[b] = values[b], values[a]
            signatures[a], signatures[b] = signatures[b], signatures[a]
        elif op == 'HMR':
            q, = qubits
            values[q] = signatures[q] = 0
        elif op in ('CCZ',):
            product = domain
            product_sig = sigmask
            for q in qubits:
                product &= values[q]
                product_sig &= signatures[q]
            match = affine_match(product, product_sig, set())
            if match is not None:
                constant, controls = match
                suffix = (' if ' + line.split(' if ', 1)[1]) if ' if ' in line else ''
                replacement = ([f'NEG{suffix}'] if constant else []) + [f'Z q{q}{suffix}' for q in controls]
        elif op in ('Z', 'CZ', 'Z_POW', 'NEG', 'BIT_INVERT', 'BIT_STORE0', 'REGISTER', 'APPEND_TO_REGISTER'):
            pass
        else:
            raise ValueError(f'Unmodeled opcode at {lineno}: {line}')
        if replacement is None:
            kept.append(line)
        else:
            kept.extend(replacement)
            rewrites.append({'source_line_zero_based': lineno, 'before': line, 'after': replacement,
                             'condition_depth': len(branches), 'proof': 'exact_truth_table_all_valid_inputs'})
        live = [q for q, v in enumerate(values) if v]
        if len(live) > peak_nonzero['count']:
            peak_nonzero = {'count': len(live), 'line': lineno, 'qubits': live}
        if lineno and lineno % 4000 == 0:
            print(json.dumps({'line': lineno, 'rewrites': len(rewrites), 'seconds': time.monotonic() - started}), flush=True)
    full_scan = stop is None
    result = {'status': 'COMPLETE' if full_scan else 'STOPPED_AT_NONIDENTITY_BRANCH',
              'source_sha256': digest, 'source': str(source), 'valid_input_count': MAX_X,
              'method': 'Exact reachable-state truth tables; arbitrary-affine membership uses counterexample-guided signature refinement to completeness.',
              'max_affine_terms': max_terms, 'verified_conditional_joins': verified_joins,
              'scanned_opcodes': dict(scanned), 'stop': stop, 'rewrites': rewrites,
              'static_toffoli_like_reduction': len(rewrites),
              'all_final_data_restored': values == initial_values if full_scan else None,
              'peak_simultaneously_nonzero_functions': peak_nonzero,
              'affine_membership_decisions': affine_decisions,
              'elapsed_seconds': time.monotonic() - started,
              'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'scope': 'Exact gatewise equivalence on reachable subspace, with original measurement/phase operations retained; official full verification is separate.'}
    if output is not None and rewrites:
        if output.exists() or source.resolve() == output.resolve():
            raise FileExistsError('Candidate must be new and separate.')
        candidate = km.Circuit('\n'.join(kept) + '\n')
        candidate.to_file(str(output), format='kmb')
        result.update(output=str(output), output_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                      output_num_qubits=candidate.num_qubits)
    report_path.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'rewrites'}, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--max-terms', type=int, choices=(1, 2, 46), default=46)
    args = parser.parse_args()
    run(args.source, args.report, args.output, args.max_terms)
