#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Exact local XOR/AND proof under f=ab=1, with an unconditioned endpoint proof.

A symbolic expression is an integer bitset over canonical AND atoms, not a
random fingerprint. Constants and repeated XOR/AND expressions are exact.
This deliberately incomplete normal form never proves an unproved identity.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
from pathlib import Path
import time

import kmb_splice


class Exact:
    def __init__(self):
        self.atoms = 1
        self.products = {}

    def fresh(self):
        answer = 1 << self.atoms
        self.atoms += 1
        return answer

    def mul(self, a, b):
        if not a or not b:
            return 0
        if a == 1:
            return b
        if b == 1 or a == b:
            return a
        if a == (b ^ 1):
            return 0
        ca, cb = a & 1, b & 1
        a ^= ca
        b ^= cb
        key = tuple(sorted((a, b)))
        if key not in self.products:
            self.products[key] = self.fresh()
        answer = self.products[key]
        if ca:
            answer ^= b
        if cb:
            answer ^= a
        if ca and cb:
            answer ^= 1
        return answer

    def product(self, values):
        result = 1
        for value in values:
            result = self.mul(result, value)
        return result


def inspect(circuit, interval):
    a, b, target = interval['qubits']
    begin, end = interval['first'], interval['second']
    nq = circuit.profile['header']['num_qubits']
    model = Exact()
    initial = [model.fresh() for _ in range(nq)]
    full = initial.copy()
    constrained = initial.copy()
    constrained[a] = constrained[b] = 1
    delta = [0] * nq
    delta[target] = 1
    full[target] ^= model.mul(full[a], full[b])
    constrained[target] ^= 1
    classical = {}
    phase_delta = 0
    nonlinear_passes = 0
    steps = 0

    def bit_expr(index):
        if index not in classical:
            classical[index] = model.fresh()
        return classical[index]

    def result(status, pos, **extra):
        return {'first': begin, 'second': end, 'qubits': [a,b,target],
                'status': status, 'witness_op': pos, 'steps': steps,
                'exact_and_atoms': model.atoms, 'nonlinear_passes': nonlinear_passes, **extra}

    for op in circuit.operations(begin + 1, end):
        steps += 1
        pos = op.source_index
        base = op.opcode & 0x7f
        qs = op.qubits
        guard = 1 if op.condition is None else bit_expr(op.condition)
        if op.opcode in (0x81, 0x01):
            return result('condition_boundary', pos)
        if base in (0x10, 0x20, 0x30):
            old = model.product(constrained[q] for q in qs)
            new = model.product(constrained[q] ^ delta[q] for q in qs)
            phase_delta ^= model.mul(guard, old ^ new)
        elif base == 0x11:
            full[qs[0]] ^= guard
            constrained[qs[0]] ^= guard
        elif base in (0x21, 0x31):
            controls, out = qs[:-1], qs[-1]
            old = model.product(constrained[q] for q in controls)
            new = model.product(constrained[q] ^ delta[q] for q in controls)
            change = model.mul(guard, old ^ new)
            if change not in (0, 1):
                return result('nonconstant_control_derivative', pos,
                              derivative_terms=change.bit_count(), operation_qubits=list(qs))
            if base == 0x31 and any(delta[q] for q in controls):
                nonlinear_passes += 1
            delta[out] ^= change
            constrained[out] ^= model.mul(guard, old)
            full[out] ^= model.mul(guard, model.product(full[q] for q in controls))
        elif base in (0x22, 0x32):
            left, right = qs[-2:]
            c = guard if base == 0x22 else model.mul(guard, constrained[qs[0]])
            c_new = guard if base == 0x22 else model.mul(guard, constrained[qs[0]] ^ delta[qs[0]])
            old_term = model.mul(c, constrained[left] ^ constrained[right])
            new_term = model.mul(c_new, constrained[left] ^ constrained[right] ^ delta[left] ^ delta[right])
            change = old_term ^ new_term
            if change not in (0, 1):
                return result('nonconstant_swap_derivative', pos,
                              derivative_terms=change.bit_count(), operation_qubits=list(qs))
            if any(delta[q] for q in qs):
                nonlinear_passes += base == 0x32
            delta[left] ^= change
            delta[right] ^= change
            constrained[left] ^= old_term
            constrained[right] ^= old_term
            full_term = model.mul(guard if base == 0x22 else model.mul(guard, full[qs[0]]),
                                  full[left] ^ full[right])
            full[left] ^= full_term
            full[right] ^= full_term
        elif base in (0x12, 0x50):
            if op.condition is not None:
                return result('conditional_reset_or_measurement', pos)
            if base == 0x12 and delta[qs[0]]:
                return result('reset_delta', pos)
            if base == 0x50:
                classical[op.bit] = model.fresh()
                if delta[qs[0]]:
                    phase_delta ^= classical[op.bit]
            constrained[qs[0]] = full[qs[0]] = 0
            delta[qs[0]] = 0
        elif base in (0x40, 0x41, 0x42):
            old = bit_expr(op.bit)
            if base == 0x42:
                classical[op.bit] = old ^ guard
            else:
                new = int(base == 0x41)
                classical[op.bit] = old ^ model.mul(guard, old ^ new)
        elif base == 0x00:
            pass
        else:
            return result('unsupported_operation', pos, opcode=op.opcode)
    if full[a] != initial[a] or full[b] != initial[b]:
        return result('endpoint_control_identity_unproved', end)
    if delta[a] or delta[b]:
        return result('endpoint_control_delta', end)
    # Deleting the SECOND CCX toggles the final discrepancy by f once more.
    delta[target] ^= 1
    residual = [q for q in range(nq) if delta[q]]
    # Every nonempty residual can be repaired with ONE multi-target fanout CCX
    # and free CNOTs, provided its controls a,b have zero discrepancy.
    data_cost = int(bool(residual))
    if phase_delta in (0,1):
        return result('EXACT_REWRITE_CANDIDATE', end, data_correction_toffoli=data_cost,
                      residual_outputs=residual, phase_correction='CZ(a,b)' if phase_delta else 'none',
                      delta_toffoli=data_cost - 2)
    return result('phase_correction_requires_resynthesis', end, residual_outputs=residual,
                  data_correction_toffoli=data_cost, phase_terms=phase_delta.bit_count())


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--profile', type=Path)
    p.add_argument('--pairs', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    t = time.monotonic()
    pairs = json.loads(args.pairs.read_text())['control_return_pairs']
    circuit = kmb_splice.open_circuit(args.baseline, args.profile)
    try:
        rows = [inspect(circuit, pair) for pair in pairs]
        baseline_sha = circuit.profile['raw_kmb_sha256']
    finally:
        circuit.close()
    report = {'schema': 'score7-phase-conditioned-v1', 'status': 'COMPLETE',
              'baseline_sha256': baseline_sha,
              'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'pair_file_sha256': hashlib.sha256(args.pairs.read_bytes()).hexdigest(),
              'interval_count': len(rows), 'counts': dict(collections.Counter(r['status'] for r in rows)),
              'nonlinear_passes': sum(r['nonlinear_passes'] for r in rows),
              'steps': sum(r['steps'] for r in rows),
              'elapsed_seconds': time.monotonic() - t, 'intervals': rows}
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'intervals'}, indent=2), flush=True)


if __name__ == '__main__':
    main()
