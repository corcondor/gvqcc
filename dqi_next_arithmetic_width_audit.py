#!/usr/bin/env python3
"""Native allocation audit of DQI arithmetic; no complete KMB is emitted."""
from __future__ import annotations

import argparse
from collections import Counter
import gzip
import hashlib
import inspect
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True

import kickmix as km
from dqi_next_arithmetic_classical_scale import classical_scale_inplace


class TraceBuilder:
    def __init__(self, retained):
        self.native = km.CircuitBuilder()
        self.data = self.native.create_quantum_register(retained, 'retained')
        self.retained = retained
        self.allocations = []
        self.live = {}
        self.peak = retained

    def __getattr__(self, name):
        return getattr(self.native, name)

    def alloc_qubits(self, count):
        result = self.native.alloc_qubits(count)
        stack = inspect.stack(context=0)
        origin = next(f for f in stack[1:] if f.filename != __file__)
        chain = [f'{Path(f.filename).name}:{f.function}:{f.lineno}'
                 for f in stack[1:] if f.filename != __file__][:6]
        key = f'{Path(origin.filename).name}:{origin.function}:{origin.lineno}'
        for q in result:
            self.live[q.id] = key
        current = self.native.num_allocated_qubits
        assert current == self.retained + len(self.live)
        self.peak = max(self.peak, current)
        self.allocations.append(dict(allocated=count, live_total=current,
                                     live_helpers=len(self.live), call_chain=chain,
                                     live_helper_owners=dict(Counter(self.live.values()))))
        return result

    def free(self, value):
        if isinstance(value, km.q):
            self.live.pop(value.id)
        elif isinstance(value, km.b):
            pass
        else:
            for wire in value:
                if isinstance(wire, km.q):
                    self.live.pop(wire.id)
        self.native.free(value)
        assert self.native.num_allocated_qubits == self.retained + len(self.live)


def component_case(name, modules, *, inplace):
    A, Original, Last, Scalar, Phase12, Nested = modules
    old_scale = Scalar.classical_scale
    Scalar.classical_scale = classical_scale_inplace if inplace else old_scale
    retained = 865
    b = TraceBuilder(retained)
    source, value, next_word = b.data[:24], b.data[24:48], b.data[48:72]
    try:
        if name == 'gf24_consuming_product':
            record = A.emit_prefix(b, source, value)
            A.free_product_mask(b, record)
        elif name == 'gf24_consuming_pair':
            record = A.emit_prefix(b, source, value)
            A.emit_closing(b, source, value, record)
        elif name == 'gf24_deferred_inverse':
            record = A.inverse_deferred(b, source)
            A.free_source_masks(b, record)
        elif name == 'direct_division_and_next_return':
            next_record = A.emit_prefix(b, source, next_word)
            record = Original.divide_deferred(b, source, value)
            Original.restore_with_shared_norm(b, source, value, record,
                next_word=next_word, next_input_record=next_record)
        elif name == 'direct_division_and_retained_last_return':
            record = Original.divide_deferred(b, source, value)
            Last.restore_with_shared_norm(b, source, value, record)
        elif name == 'gf24_affine_quotient_phase':
            mask = b.create_classical_register(24, 'mask')
            A.phase_affine_quotient(b, source, targets=[(value, mask)])
        elif name == 'outer_norm_plus_gf12_inverse':
            from tower_inverse import init_norm
            norm = init_norm(b, source[:12], source[12:], A.DEFAULT_DELTA)
            masks = Nested.inverse_twelve_deferred(b, norm)
            for mask in masks:
                b.free(mask)
            # This case measures the open component's allocation, not cleanup.
            b.free(norm)
        elif name == 'outer_norm_plus_gf12_phase':
            from tower_inverse import init_norm
            norm = init_norm(b, source[:12], source[12:], A.DEFAULT_DELTA)
            mask = b.create_classical_register(12, 'mask')
            Phase12.phase_inverse_twelve_polynomial(b, norm, mask)
            b.free(norm)
        elif name == 'outer_norm_child_plus_gf6_phase':
            from tower_inverse import init_norm, quadratic_basis, apply_inplace_linear
            norm = init_norm(b, source[:12], source[12:], A.DEFAULT_DELTA)
            info = quadratic_basis(12)
            apply_inplace_linear(b, norm, info['to_tower'])
            child = init_norm(b, norm[:6], norm[6:], info['delta'])
            mask = b.create_classical_register(6, 'mask')
            Scalar.phase_inverse_six(b, child, mask)
            b.free(child)
            b.free(norm)
        else:
            raise ValueError(name)
        circuit = b.finish_circuit()
        assert b.num_allocated_qubits == retained
        assert circuit.num_qubits == b.peak
        peaks = [row for row in b.allocations if row['live_total'] == b.peak]
        seen = set()
        examples = []
        for row in peaks:
            key = json.dumps(row['live_helper_owners'], sort_keys=True)
            if key not in seen:
                seen.add(key)
                examples.append(row)
        return dict(case=name, inplace_classical_scale=inplace,
                    retained=retained, native_peak_Q=b.peak,
                    helpers=b.peak-retained,
                    static_T=circuit.operation_statistics().num_toffoli_like,
                    peak_allocation_events=len(peaks),
                    unique_peak_allocation_compositions=examples,
                    scope='Native construction and live-allocation measurement only; not a full-decoder equivalence test.')
    finally:
        Scalar.classical_scale = old_scale


def actual_public_witnesses(repo, old_repo, source, profile):
    sys.path.insert(0, str(old_repo))
    import dqi_ccx_peephole as shared
    from theory_bilinear_verify import parse
    from theory_bilinear_patch import source_ordered_gf12, wire_match
    audit = json.load(gzip.open(repo/'symmetry_dqi_20261115_scan.json.gz', 'rt'))
    with source.open('rb') as stream:
        actual_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
    assert actual_hash == audit['source_sha256']
    assert actual_hash == '821bf8d157c03c3e868a0099b0ab1438cfba664ab1bc6fec3210654099b672a3'
    certificate = json.loads((old_repo/'inverse_v2_actual_eea_product_certificate.json').read_text())
    inputs = json.loads((old_repo/'theory_bilinear_input_certificate.json').read_text())['records']
    old24 = parse(old_repo/'inverse_v2_actual_eea_product.kmx')
    templates = {
        'gf12': (source_ordered_gf12(inputs[0]['terms']), list(range(12)), list(range(12,24)), list(range(24,36))),
        'gf24': (old24[12:-12], certificate['input_left'], certificate['input_right'], certificate['output_qubits_in_field_order'])}
    circuit = shared.BinaryCircuit(source, json.loads(profile.read_text()))
    result = []
    try:
        for kernel in ('gf12', 'gf24'):
            blocks = [b for b in audit['blocks'] if b['kernel'] == kernel]
            high = [b for b in blocks if max(b['target']) == 888]
            witness = high[0]
            before, left, right, target = templates[kernel]
            actual = list(circuit.operations(witness['start'], witness['end']))
            mapping = wire_match(before, actual)
            assert mapping is not None
            assert [mapping[q] for q in left] == witness['left']
            assert [mapping[q] for q in right] == witness['right']
            assert [mapping[q] for q in target] == witness['target']
            result.append(dict(kernel=kernel, all_exact_kernel_occurrences=len(blocks),
                               target_q888_occurrences=len(high),
                               target_q888_count_scope='Prior saved complete exact-template audit of the same freshly rehashed file.',
                               newly_revalidated_witness=witness,
                               output_qubit_max_histogram=dict(Counter(max(b['target']) for b in blocks))))
    finally:
        circuit.close()
    return dict(public_baseline_sha256=actual_hash,
                public_baseline_native_Q=889,
                not_private_norm_candidate=True,
                exact_template_witnesses=result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True, type=Path)
    parser.add_argument('--old-repo', required=True, type=Path)
    parser.add_argument('--source-kmb', required=True, type=Path)
    parser.add_argument('--profile', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    repo = Path(__file__).parent
    for relative in ('after_c5/arithmetic_t', 'after_c5/extractor_width',
                     'after_v3/k24', 'night_c27/arithmetic'):
        sys.path.insert(0, str(args.work/relative))
    import k24_paths  # noqa: F401
    import gf24_nested_norm as A
    import nested_norm_inverse as Nested
    import direct_carry_arithmetic as Original
    import last_return_retained_norm as Last
    import scalar_inverse_phase as Scalar
    import phase_inverse12 as Phase12
    # Component-only provider choices, matching the documented production
    # bindings. No full pipeline, pinned manifest, or old file is modified.
    Original.A, Original.Prior = A, Nested
    assert Last.A is A and Last.Nested is Nested and Last.Original is Original
    modules = (A, Original, Last, Scalar, Phase12, Nested)
    names = ('gf24_consuming_product', 'gf24_consuming_pair', 'gf24_deferred_inverse',
             'direct_division_and_next_return', 'direct_division_and_retained_last_return',
             'gf24_affine_quotient_phase', 'outer_norm_plus_gf12_inverse',
             'outer_norm_plus_gf12_phase', 'outer_norm_child_plus_gf6_phase')
    measured = []
    for name in names:
        measured.append(dict(before=component_case(name, modules, inplace=False),
                             after=component_case(name, modules, inplace=True)))
    actual = actual_public_witnesses(repo, args.old_repo, args.source_kmb, args.profile)
    source_files = (A, Nested, Original, Last, Scalar, Phase12)
    result = dict(status='PASS_WIDTH_OBSTRUCTION_CONFIRMED',
                  actual_public=actual, components=measured,
                  source_sha256={str(Path(m.__file__).relative_to(args.work)):
                                 hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()
                                 for m in source_files},
                  no_whole_decoder_kmb_emitted=True,
                  limitations=['Component builder models 865 retained qubits; actual public kernel witnesses independently bind unchanged 24-wide arithmetic to DQI821.',
                               'No claim that the complete supplied source regenerates DQI821 byte for byte.',
                               'No global peak-width reduction or Public Score gain is established.',
                               'Private chart-norm candidate and public DQI821 remain separate.'])
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],
        components=[dict(name=r['before']['case'], Q_before=r['before']['native_peak_Q'],
                         Q_after=r['after']['native_peak_Q'],
                         T_before=r['before']['static_T'], T_after=r['after']['static_T'])
                    for r in measured],
        public_witnesses=[dict(kernel=r['kernel'], target_q888_occurrences=r['target_q888_occurrences'],
                              newly_revalidated_interval=[r['newly_revalidated_witness']['start'],r['newly_revalidated_witness']['end']])
                          for r in actual['exact_template_witnesses']]), indent=2))


if __name__ == '__main__':
    main()
