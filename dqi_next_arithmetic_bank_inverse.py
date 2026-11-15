#!/usr/bin/env python3
"""Matched K24 inverse pair using 12 extra helpers and a clean owned bank24.

The supplied 24-extra-helper matched pair costs 386 static T. This independent
component changes the lifetime of its two child norms, borrowing the resulting
clean bank12 for consuming products. Prefix keeps a 12-bit original-norm mask;
return repays that mask from its reciprocal norm and locally repays its own
mask in 27 T. The resulting pair costs 409 T and 12 extra helpers.

This is a width/T tradeoff component, not a complete DQI candidate. All original
sources are imported read-only. No source manifests or production pipeline are
modified and no submission KMB is emitted.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True

import kickmix as km
import numpy as np


@dataclass
class NormRecord:
    builder_id: int
    source: tuple
    delta: int
    original_norm_mask: object
    closed: bool = False


class CleanBankLender:
    """Lend owned zero qubits without freeing them in the caller's allocator."""
    def __init__(self, builder, bank):
        self.builder = builder
        self.bank = tuple(bank)
        self.available = list(bank)
        self.borrowed = set()
        self.peak_borrowed = 0
        self.outer_allocated = builder.num_allocated_qubits

    def __getattr__(self, name):
        return getattr(self.builder, name)

    def alloc_qubits(self, count):
        if count > len(self.available):
            raise RuntimeError('phase helper allocation exceeded the clean bank')
        wires = self.available[:count]
        del self.available[:count]
        self.borrowed.update(wires)
        self.peak_borrowed = max(self.peak_borrowed, len(self.borrowed))
        assert self.builder.num_allocated_qubits == self.outer_allocated
        return km.array(wires)

    def free(self, value):
        wires = [value] if isinstance(value, (km.q, km.b)) else list(value)
        other = []
        for wire in wires:
            if isinstance(wire, km.q):
                if wire not in self.borrowed:
                    raise RuntimeError('attempt to free a quantum wire not lent here')
                self.borrowed.remove(wire)
                self.available.append(wire)
            else:
                other.append(wire)
        if other:
            self.builder.free(km.array(other))

    def finish(self):
        assert not self.borrowed
        assert set(self.available) == set(self.bank)
        assert self.builder.num_allocated_qubits == self.outer_allocated
        assert self.peak_borrowed <= 12


def inverse_with_bank(builder, source, clean_bank, modules, *, prefix_record=None):
    """Prefix if no record; matched return if the actual prefix record is given."""
    Base, A, Cubic, Phase12 = modules
    from tower_inverse import (quadratic_basis, apply_inplace_linear, xor_product,
                               phase_product, erase_norm, kernel)

    assert len(source) == len(clean_bank) == 24
    assert len(set([*source, *clean_bank])) == 48
    before = builder.num_allocated_qubits
    delta = A.DEFAULT_DELTA
    if prefix_record is not None:
        assert not prefix_record.closed
        assert prefix_record.builder_id == id(builder)
        assert prefix_record.source == tuple(source)
        assert prefix_record.delta == delta

    norm, child, child_inverse = clean_bank[:12], clean_bank[12:18], clean_bank[18:]
    Base._xor_norm(builder, source[:12], source[12:], norm, delta)
    info = quadratic_basis(12)
    apply_inplace_linear(builder, norm, info['to_tower'])
    left, right = norm[:6], norm[6:]
    Base._xor_norm(builder, left, right, child, info['delta'])
    returned = Cubic.inverse_six_cubic(builder, child, target=child_inverse)
    assert tuple(returned) == tuple(child_inverse)
    assert builder.num_allocated_qubits == before

    reciprocal = builder.alloc_qubits(12)
    builder.cx(right, left)
    xor_product(builder, left, child_inverse, reciprocal[:6])
    builder.cx(right, left)
    xor_product(builder, right, child_inverse, reciprocal[6:])
    # reciprocal is already in its L/F tower basis here.
    # Norm(inv0(norm)) = inv0(Norm(norm)) = child_inverse, including zero.
    erase_norm(builder, left, right, child, info['delta'])
    erase_norm(builder, reciprocal[:6], reciprocal[6:], child_inverse, info['delta'])
    apply_inplace_linear(builder, reciprocal, info['from_tower'])
    apply_inplace_linear(builder, norm, info['from_tower'])

    if prefix_record is not None:
        # Return's reciprocal norm equals prefix's original norm.
        builder.cz(prefix_record.original_norm_mask, reciprocal)
        builder.free(prefix_record.original_norm_mask)

    temporary = clean_bank[12:]
    for half in (source[:12], source[12:]):
        xor_product(builder, half, reciprocal, temporary)
        builder.swap(half, temporary)
        mask = builder.alloc_bits(12)
        builder.hmr(temporary, mask)
        # old_half = new_half * norm; this is a Clifford phase product.
        phase_product(builder, half, norm, mask, kernel(12))
        builder.free(mask)

    norm_mask = builder.alloc_bits(12)
    # Polynomial basis is the explicit new deferred-mask ABI.
    builder.hmr(norm, norm_mask)
    peak_borrowed = 0
    if prefix_record is not None:
        lender = CleanBankLender(builder, clean_bank)
        Phase12.phase_inverse_twelve_polynomial(lender, reciprocal, norm_mask)
        lender.finish()
        peak_borrowed = lender.peak_borrowed
        builder.free(norm_mask)

    builder.cx(source[12:], source[:12])
    erase_norm(builder, source[:12], source[12:], reciprocal, delta)
    builder.free(reciprocal)
    assert builder.num_allocated_qubits == before
    if prefix_record is None:
        return NormRecord(id(builder), tuple(source), delta, norm_mask)
    prefix_record.closed = True
    return dict(phase_peak_borrowed_from_owned_bank=peak_borrowed)


def build(modules, *, candidate, retained=865):
    Base, A, Cubic, Phase12 = modules
    builder = km.CircuitBuilder()
    builder.set_max_qubits(retained + (12 if candidate else 24))
    source = builder.create_quantum_register(24, 'source')
    bank = builder.create_quantum_register(24, 'clean_bank')
    builder.create_quantum_register(retained-48, 'dirty')
    probe = builder.create_classical_register(24, 'phase_probe')
    if candidate:
        record = inverse_with_bank(builder, source, bank, modules)
    else:
        record = Base.inverse_prefix_with_bank(builder, source, bank)
    prefix = builder.finish_circuit()
    # Nontrivial phase between prefix and return detects an incorrect inverse
    # that would be invisible to an unprobed round trip.
    builder.cz(probe, source)
    builder.cz(source[2], source[13])
    if candidate:
        detail = inverse_with_bank(builder, source, bank, modules, prefix_record=record)
    else:
        detail = Base.inverse_return_with_bank(builder, source, bank, record)
    assert record.closed
    assert builder.num_allocated_qubits == retained
    circuit = builder.finish_circuit()
    assert prefix.operation_statistics().num_toffoli_like == 191
    assert circuit.operation_statistics().num_toffoli_like == (409 if candidate else 386)
    assert circuit.num_qubits == retained + (12 if candidate else 24)
    return circuit, prefix, detail


def simulate(circuit, arrays, expected_phase, *, seed, prefix, A):
    from quantum_reciprocal import bit_matrix
    shots = len(arrays['values'])
    sim = km.Simulator(batch_size=shots, seed=seed, counting_operations=True)
    sim.use_same_registers_as(circuit)
    sim.write_across_shots(circuit.register_data['source'], bit_matrix(arrays['values'], 24))
    sim.write_across_shots(circuit.register_data['dirty'], arrays['dirty'])
    sim.write_across_shots(circuit.register_data['phase_probe'], bit_matrix(arrays['probe'], 24))
    sim.do(circuit)
    wanted = arrays['inverse'] if prefix else arrays['values']
    assert np.array_equal(sim.read_across_shots(circuit.register_data['source']), bit_matrix(wanted, 24)), (seed, 'source')
    assert np.array_equal(sim.read_across_shots(circuit.register_data['dirty']), arrays['dirty']), (seed, 'dirty')
    assert np.array_equal(sim.read_across_shots(circuit.register_data['phase_probe']), bit_matrix(arrays['probe'], 24)), (seed, 'probe')
    assert not sim.read_across_shots(circuit.register_data['clean_bank']).any(), (seed, 'bank')
    assert not sim.read_across_shots([km.q(i) for i in range(865, circuit.num_qubits)]).any(), (seed, 'extra_helpers')
    if not prefix:
        assert np.array_equal(sim.read_phase_flipped_across_shots(), expected_phase), (seed, 'phase')
    return dict(seed=seed, shots=shots, source_errors=0, bank_errors=0,
                dirty_errors=0, mask_errors=0, helper_errors=0,
                phase_errors=None if prefix else 0,
                measured_mean_T=sim.operation_statistics().num_toffoli_like/shots)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    for relative in ('after_c5/arithmetic_t', 'after_v3/k24',
                     'night_c27/arithmetic', 'after_v3/blocks/v5'):
        sys.path.insert(0, str(args.work/relative))
    import k24_paths  # noqa: F401
    import inverse_retained_norm_deferred as Base
    import gf24_nested_norm as A
    import cubic_inverse130 as Cubic
    import phase_inverse12 as Phase12
    modules = Base, A, Cubic, Phase12

    rng = np.random.default_rng(202611150912)
    values = np.concatenate((np.arange(4096, dtype=np.int64),
                             np.arange(4096, dtype=np.int64) << 12,
                             rng.integers(0, 1 << 24, 8192, dtype=np.int64)))
    inverses = np.array([A.inverse24(int(v)) for v in values], dtype=np.int64)
    probes = rng.integers(0, 1 << 24, len(values), dtype=np.int64)
    dirt = rng.integers(0, 2, (817, len(values)), dtype=np.int8).astype(bool)
    arrays = dict(values=values, inverse=inverses, probe=probes, dirty=dirt)
    expected_phase = np.array([bool((int(v)&int(p)).bit_count() % 2)
                               for v, p in zip(inverses, probes)])
    expected_phase ^= (((inverses >> 2)&1) & ((inverses >> 13)&1)).astype(bool)
    rows = []
    for candidate in (False, True):
        circuit, prefix, detail = build(modules, candidate=candidate)
        prefix_checks = [simulate(prefix, arrays, expected_phase, seed=2201,
                                  prefix=True, A=A)]
        checks = [simulate(circuit, arrays, expected_phase, seed=seed,
                           prefix=False, A=A) for seed in (2201, 2202, 2203, 2204)]
        rows.append(dict(candidate=candidate, Q=circuit.num_qubits,
                         retained_qubits=865, additional_helpers=circuit.num_qubits-865,
                         T_static=circuit.operation_statistics().num_toffoli_like,
                         prefix_T_static=prefix.operation_statistics().num_toffoli_like,
                         exact_uniform_HMR_mean_T=(409-27/4096) if candidate else (386-4/64),
                         native_prefix_checks=prefix_checks, native_pair_checks=checks,
                         details=detail))
    result = dict(status='PASS_LOCAL_WIDTH_T_TRADEOFF',
                  baseline_special_source='inverse_retained_norm_deferred.py matched special pair',
                  whole_decoder_public_baseline='821bf8d157c03c3e868a0099b0ab1438cfba664ab1bc6fec3210654099b672a3',
                  whole_decoder_integration=False, submission_kmb_emitted=False,
                  independent_algebra_review=True,
                  cases_per_seed=len(values), case_structure='All 4096 low-only and all 4096 high-only words, including zero; 8192 fixed random general K24 words.',
                  results=rows, static_T_delta=23,
                  exact_mean_T_delta=(409-27/4096)-(386-4/64),
                  helper_delta=-12,
                  new_deferred_mask_bits=12, previous_deferred_mask_bits=6,
                  proof=['C=Norm(N) and D=Norm(inv0(N)); erasing each child from its preserved parent is a zero-T phase repayment.',
                         'The now-clean owned bank12 consumes both source halves while N remains available to repay their masks.',
                         'Prefix mask is of polynomial N; matched return reciprocal norm equals that same N.',
                         'Return pays its own N mask with phase_inverse_twelve_polynomial(R, mask), since N=inv0(R).',
                         'Clean bank is explicitly lent to the phase helper allocator; all bank and extra helper values are zero at both boundaries.'],
                  limitations=['No general dirty-bank or arbitrary-carry claim.',
                               'This only addresses matched special inverse calls; actual DQI821 consuming product and generic norm peaks remain.',
                               'No full-circuit correctness, error rate or Public Score improvement is claimed.',
                               'Separate from the unpublished chart-norm repair candidate.'],
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(status=result['status'], cases_per_seed=len(values),
                         before_Q=rows[0]['Q'], after_Q=rows[1]['Q'],
                         before_T=rows[0]['T_static'], after_T=rows[1]['T_static'],
                         exact_mean_T_delta=result['exact_mean_T_delta'],
                         native_pair_tests=sum(len(r['native_pair_checks']) for r in rows),
                         prefix_tests=2, all_value_phase_and_restoration_errors=0,
                         no_whole_decoder_integration=True), indent=2))


if __name__ == '__main__':
    main()
