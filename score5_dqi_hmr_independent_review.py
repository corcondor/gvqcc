#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Independent Kraus proof and whole-binary binding for the two HMR hoists.

Uses shared binary readers only. Does not import the scanner, rewriter, its
encoder, or its native checker. Reads both complete artifacts without mutation.
"""
import argparse
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path
import time

import kmb_profile as K
from dqi_ccx_peephole import BinaryCircuit, Operation
from kmb_splice import compare_ranges, register_bytes

SOURCE_SHA = '6a998c4688dc22b33f52e41be46c5e51f7ea927fab40d9141bc5e99ebf6a2e02'


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def signature(op):
    return [op.opcode, list(op.qubits), op.bit, op.condition, op.angle.hex()]


def digest_ops(ops):
    raw = json.dumps([signature(op) for op in ops], separators=(',', ':')).encode()
    return hashlib.sha256(raw).hexdigest()


def independently_prove_kraus():
    checked = 0
    for a, b, t, reference, old_bit, outcome in itertools.product((0, 1), repeat=6):
        # Omit the common factor 1/sqrt(2); compare every nonzero Kraus
        # matrix entry, including both outcomes and an untouched reference.
        old = ((a, b, 0, reference, outcome), (-1)**(outcome*(t ^ (a & b))))
        new = ((a, b, 0, reference, outcome), (-1)**(outcome*t)*(-1)**(outcome*a*b))
        assert old == new
        # Explicit emitted BIT_STORE0; BIT_INVERT_IF is a copy, not NOT.
        published = 0 ^ outcome
        assert published == outcome
        checked += 1
    return checked


def check_binary_layout(c):
    values = K.HEADER.unpack_from(c.data, 0)
    assert values[0] == K.MAGIC
    assert dict(zip(K.HEADER_FIELDS, values[1:])) == c.profile['header']
    for kind, packet in c.packets.items():
        assert K.PACKET.unpack_from(c.data, packet['header_offset']) == (kind, packet['payload_bytes'])
    end = c.packets[11]['payload_offset'] + c.packets[11]['payload_bytes']
    assert end == len(c.data)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', type=Path, default=Path('/workspace/scratch/3815fb5fae06/score5_norm_fanout_fanin/dqi.kmb'))
    ap.add_argument('--build', type=Path, default=Path('/workspace/scratch/3815fb5fae06/score5_norm_final'))
    ap.add_argument('--expected-candidate-sha256', required=True)
    ap.add_argument('--output', type=Path, default=Path(__file__).with_suffix('.json'))
    args = ap.parse_args()
    begun = time.monotonic()
    cert_path = args.build/'rewrite_certificate.json'
    cert = json.loads(cert_path.read_text())
    old_profile = json.loads((args.source.parent/'profile.json').read_text())
    new_profile = json.loads((args.build/'profile.json').read_text())
    candidate = args.build/'dqi.kmb'
    assert sha(args.source) == old_profile['raw_kmb_sha256'] == cert['source_sha256'] == SOURCE_SHA
    assert sha(candidate) == new_profile['raw_kmb_sha256'] == cert['candidate_sha256'] == args.expected_candidate_sha256
    kraus_entries = independently_prove_kraus()
    old = BinaryCircuit(args.source, old_profile)
    new = BinaryCircuit(candidate, new_profile)
    groups, gaps = [], []
    old_cursor = new_cursor = offset = 0
    middle_families = Counter()
    try:
        check_binary_layout(old)
        check_binary_layout(new)
        assert register_bytes(old) == register_bytes(new)
        expected_deltas = {'num_bits': 2, 'num_ops': 4, 'num_ops_with_3_target_qubits': -2,
                           'num_ops_with_2_target_qubits': 2, 'num_ops_with_1_target_bit': 4,
                           'num_ops_with_1_condition_bit': 4}
        for name, value in old_profile['header'].items():
            assert new_profile['header'][name] == value + expected_deltas.get(name, 0)
        assert old_profile['header']['num_qubits'] == new_profile['header']['num_qubits'] == 889
        assert new_profile['header']['num_bits'] == 208169
        assert old_profile['max_classical_id'] < old_profile['header']['num_bits'] == 208167
        assert old_profile['header']['num_info_tags'] == new_profile['header']['num_info_tags'] == 0
        for c in (old, new):
            p = c.packets[11]
            assert c.data[p['payload_offset']:p['payload_offset']+p['payload_bytes']] == b'\0'*8
        assert len(cert['blocks']) == 2
        for number, block in enumerate(cert['blocks']):
            lo, hi = block['start'], block['end']
            assert old_cursor <= lo < hi
            assert old.opcodes[:lo].count(0x81) == old.opcodes[:lo].count(0x01)
            original = list(old.operations(lo, hi))
            first, last = original[0], original[-1]
            assert first.opcode == 0x31 and first.condition is None and len(set(first.qubits)) == 3
            target = first.qubits[-1]
            assert last.opcode == 0x50 and last.qubits == (target,) and last.condition is None
            fresh = old_profile['header']['num_bits'] + number
            assert (block['target'], block['controls'], block['fresh_bit'], block['original_bit']) == (
                target, list(first.qubits[:2]), fresh, last.bit)
            assert all(target not in op.qubits for op in original[1:-1])
            depth = 0
            for op in original:
                if op.opcode == 0x81:
                    depth += 1
                elif op.opcode == 0x01:
                    depth -= 1
                    assert depth >= 0
                assert fresh not in (op.bit, op.condition)
            assert depth == 0
            independent = [Operation(0x50, (target,), bit=fresh),
                           Operation(0xa0, first.qubits[:2], condition=fresh)] + original[1:-1] + [
                           Operation(0x40, (), bit=last.bit),
                           Operation(0xc2, (), bit=last.bit, condition=fresh)]
            new_lo, new_hi = lo+offset, hi+offset+2
            gap = compare_ranges(old, old_cursor, lo, new, new_cursor, new_lo)
            assert gap['equal']
            gaps.append({'source': [old_cursor, lo], 'candidate': [new_cursor, new_lo],
                         'all_ten_columns_byte_equal': True})
            actual = list(new.operations(new_lo, new_hi))
            assert [signature(op) for op in actual] == [signature(op) for op in independent]
            untouched_middle = compare_ranges(old, lo+1, hi-1, new, new_lo+2, new_hi-2)
            assert untouched_middle['equal']
            middle_families.update(K.OPCODES[op.opcode] for op in original[1:-1])
            old_reads = sum(op.condition == last.bit for op in original[1:-1])
            old_writes = sum(op.bit == last.bit for op in original[1:-1])
            assert old_reads == block['intermediate_original_bit_uses']
            assert old_writes == block['intermediate_original_bit_writes']
            groups.append({'source': [lo, hi], 'candidate': [new_lo, new_hi],
                'target': target, 'fresh_measurement_bit': fresh, 'original_measurement_bit': last.bit,
                'intermediate_target_references': 0, 'intermediate_original_bit_reads': old_reads,
                'intermediate_original_bit_writes': old_writes,
                'old_bit_publication_timing_preserved': True, 'middle_all_columns_byte_equal': True,
                'before_sha256': digest_ops(original), 'independent_after_sha256': digest_ops(independent),
                'actual_candidate_matches_independent_rewrite': True})
            old_cursor, new_cursor = hi, new_hi
            offset += 2
        assert offset == 4
        tail = compare_ranges(old, old_cursor, len(old.opcodes), new, new_cursor, len(new.opcodes))
        assert tail['equal']
        gaps.append({'source': [old_cursor, len(old.opcodes)], 'candidate': [new_cursor, len(new.opcodes)],
                     'all_ten_columns_byte_equal': True})
        deltas = {0x31: -2, 0xa0: 2, 0x40: 2, 0xc2: 2}
        # Exact reconstruction above already binds every other opcode. Check
        # the edited families and conserved HMR count without256 full scans.
        for opcode in (*deltas, 0x50):
            assert new.opcodes.count(opcode) - old.opcodes.count(opcode) == deltas.get(opcode, 0)
    finally:
        old.close()
        new.close()
    result = {'status': 'INDEPENDENT_KRAUS_AND_FULL_BINARY_BINDING_PASS',
        'source_sha256': SOURCE_SHA, 'candidate_sha256': args.expected_candidate_sha256,
        'unconditional_ccx_reduction': 2, 'added_conditioned_CZ': 2, 'quantum_width': 889,
        'classical_bits': 208169, 'hmr_count_unchanged': True,
        'independent_kraus_entries': kraus_entries,
        'exact_scope': 'Kraus equality for each measurement outcome on arbitrary inputs and entangled references. '
                       'All middle instruments act trivially on the measured target; fresh bits are outside the '
                       'entire old classical address range. Original outcome bits are copied only at original HMR times.',
        'blocks': groups, 'unchanged_ranges': gaps, 'middle_operation_families': dict(middle_families),
        'all_register_bytes_identical': True, 'all_other_operation_columns_identical': True,
        'header_changes_only_expected_counts': True, 'candidate_read_only': True,
        'new_native_or_official_run': False,
        'root_native_minimal_receipt': cert['native_minimal_instrument'],
        'root_certificate_sha256': sha(cert_path), 'root_patch_sha256': sha(args.build/'patch.json'),
        'review_script_sha256': sha(__file__), 'elapsed_seconds': time.monotonic()-begun,
        'public_score': None, 'submission_performed': False}
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: result[k] for k in ('status', 'candidate_sha256', 'unconditional_ccx_reduction',
                                           'quantum_width', 'classical_bits', 'elapsed_seconds')}, indent=2))


if __name__ == '__main__':
    main()
