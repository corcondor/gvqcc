"""Exact operand-column splicing for tag-free KMB v2 circuits.

Whole-circuit semantics must be checked independently. This tool first checks
that the old prefix and suffix are instruction-identical to the baseline;
it never searches for an approximate or hash-only matching boundary.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

import kmb_profile as kp
from dqi_ccx_peephole import BinaryCircuit, COLUMN_RANKS


def open_circuit(path, profile_path=None):
    p = Path(path)
    if profile_path:
        report = json.loads(Path(profile_path).read_text())
        h = hashlib.sha256()
        with p.open('rb') as f:
            for block in iter(lambda: f.read(1 << 22), b''):
                h.update(block)
        if h.hexdigest() != report['raw_kmb_sha256']:
            raise ValueError('Cached profile belongs to a different circuit')
    else:
        report = kp.profile(p, max_register_summaries=0)
    if report['header']['num_info_tags']:
        raise ValueError('INFO_TAG payload splicing is not implemented')
    return BinaryCircuit(p, report)


def register_bytes(c):
    return c.data[kp.HEADER.size:c.packets[1]['header_offset']]


def column_bytes(c, kind, start, stop):
    a, b = c.column_range(kind, start, stop)
    off = c.packets[kind]['payload_offset']
    return memoryview(c.data)[off+a:off+b]


def compare_ranges(left, la, lb, right, ra, rb):
    result = {'operation_count': lb-la, 'columns': {}}
    if lb-la != rb-ra:
        return {'equal': False, 'reason': 'different operation counts'}
    for kind in range(1, 11):
        a = column_bytes(left, kind, la, lb)
        b = column_bytes(right, kind, ra, rb)
        same = len(a) == len(b)
        first = None
        if same:
            for pos in range(0, len(a), 1 << 20):
                aa = a[pos:pos+(1 << 20)]
                bb = b[pos:pos+(1 << 20)]
                if aa != bb:
                    same = False
                    first = pos + next(i for i, (x, y) in enumerate(zip(aa, bb)) if x != y)
                    break
        result['columns'][str(kind)] = {'equal': same, 'left_bytes': len(a),
                                        'right_bytes': len(b), 'first_mismatch_byte': first}
    result['equal'] = all(x['equal'] for x in result['columns'].values())
    return result


def write_segments(path, template, segments):
    path = Path(path)
    if path.exists():
        raise FileExistsError(path)
    lengths = {k: 0 for k in range(1, 11)}
    for c, start, stop in segments:
        if not 0 <= start <= stop <= len(c.opcodes):
            raise ValueError('Invalid operation range')
        if register_bytes(c) != register_bytes(template):
            raise ValueError('Register declarations differ')
        for k in lengths:
            a, b = c.column_range(k, start, stop)
            lengths[k] += b-a
    header = dict(template.profile['header'])
    header.update(num_ops=lengths[1], num_ops_with_3_target_qubits=lengths[2]//4,
                  num_ops_with_2_target_qubits=lengths[5]//4,
                  num_ops_with_1_target_qubits=lengths[7]//4,
                  num_ops_with_1_target_bit=lengths[8]//4,
                  num_ops_with_1_condition_bit=lengths[9]//4,
                  num_ops_with_angle=lengths[10]//16,
                  num_bits=max(c.profile['header']['num_bits'] for c, _, _ in segments),
                  num_qubits=max(c.profile['header']['num_qubits'] for c, _, _ in segments),
                  num_info_tags=0, num_info_tag_chars=0)
    with path.open('xb') as f:
        f.write(kp.HEADER.pack(kp.MAGIC, *(header[x] for x in kp.HEADER_FIELDS)))
        f.write(register_bytes(template))
        for kind in range(1, 11):
            f.write(kp.PACKET.pack(kind, lengths[kind]))
            for c, start, stop in segments:
                view = column_bytes(c, kind, start, stop)
                for pos in range(0, len(view), 1 << 22):
                    f.write(view[pos:pos+(1 << 22)])
        f.write(kp.PACKET.pack(11, 8))
        f.write(struct.pack('<Q', 0))
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 22), b''):
            h.update(block)
    return {'header': header, 'sha256': h.hexdigest(), 'bytes': path.stat().st_size}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--profile', type=Path)
    p.add_argument('--pieces', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    meta = json.loads((args.pieces/'gauge_pieces.json').read_text())
    labels = meta['labels']
    base = open_circuit(args.baseline, args.profile)
    old = open_circuit(args.pieces/'gauge64_pair.kmb')
    new = open_circuit(args.pieces/f'gauge{labels}_pair.kmb')
    old_prefix = meta['baseline_prefix']['instructions']
    new_prefix = meta['expanded_prefix']['instructions']
    old_suffix = len(old.opcodes)-old_prefix
    cut = len(base.opcodes)-old_suffix
    report = {
        'baseline_sha256': base.profile['raw_kmb_sha256'],
        'labels': labels,
        'prefix_comparison': compare_ranges(base, 0, old_prefix, old, 0, old_prefix),
        'suffix_comparison': compare_ranges(base, cut, len(base.opcodes),
                                            old, old_prefix, len(old.opcodes)),
    }
    if report['prefix_comparison']['equal'] and report['suffix_comparison']['equal']:
        report['output'] = write_segments(args.out, base, [
            (new, 0, new_prefix), (base, old_prefix, cut),
            (new, new_prefix, len(new.opcodes)),
        ])
        report['status'] = 'SPLICED_REQUIRES_FULL_DECODER_VERIFICATION'
        report['body_preserved_byte_for_byte'] = True
    else:
        report['status'] = 'REFUSED_BOUNDARY_MISMATCH'
    args.out.with_suffix('.splice.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
