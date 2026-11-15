#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Extend the frozen6a worker with the independently audited HMR2 target.

Build only after the final target's full official receipt exists. All circuit,
recipe, previous-worker, and review pins are fixed; no arbitrary patch input.
"""
import argparse
import ast
import base64
import gzip
import hashlib
import json
from pathlib import Path
import struct

import kmb_profile as K
from dqi_ccx_peephole import BinaryCircuit
from score5_patch_build import canonical, digest, operation, sha, virtual_hash

ROOT = Path(__file__).resolve().parent
SCRATCH = Path('/workspace/scratch/3815fb5fae06')
SOURCE = '6a998c4688dc22b33f52e41be46c5e51f7ea927fab40d9141bc5e99ebf6a2e02'
TARGET = 'e4e110436080b8538f50511dc7064185e1708c2bd386ea0e36322d7791311355'
OLD_WORKER = '93222577d134739a3a0b1e005ac518b458548b33b023b92e92d3cfe7c6b290ea'
RECIPE_SHA = 'c14c603002ea9587af84e17fd01e12b3c8a8f6ef852045875b0495ac6064c211'


def strict_columns(operations):
    """Encode only the five opcodes in the audited HMR rewrite.

    HMR and classical stores are intentional here; the earlier fan-out writer
    correctly forbids them in generic commuting-gate rewrites.
    """
    specification = {0x31: (3, False, False), 0x50: (1, True, False),
                     0xa0: (2, False, True), 0x40: (0, True, False),
                     0xc2: (0, True, True)}
    qcols = {3: (2, 3, 4), 2: (5, 6), 1: (7,), 0: ()}
    result = {i: bytearray() for i in range(1, 11)}
    for op in operations:
        assert op.opcode in specification and op.angle == b''
        nq, has_bit, has_condition = specification[op.opcode]
        assert len(op.qubits) == nq and len(set(op.qubits)) == nq
        assert (op.bit is not None) == has_bit and (op.condition is not None) == has_condition
        assert all(0 <= q < 889 for q in op.qubits)
        assert op.bit is None or 0 <= op.bit < 208169
        assert op.condition is None or 0 <= op.condition < 208169
        result[1].append(op.opcode)
        for col, value in zip(qcols[nq], op.qubits):
            result[col].extend(struct.pack('<I', value))
        if has_bit:
            result[8].extend(struct.pack('<I', op.bit))
        if has_condition:
            result[9].extend(struct.pack('<I', op.condition))
    return {i: bytes(value) for i, value in result.items()}


def export_hmr_patch(source, target):
    recipe_path = target.parent/'patch.json'
    raw = recipe_path.read_bytes()
    assert sha(raw) == RECIPE_SHA
    recipe = json.loads(raw)
    assert recipe['source_sha256'] == SOURCE and recipe['candidate_sha256'] == TARGET
    assert recipe['header_num_bits'] == 208169 and len(recipe['edits']) == 4
    profile = json.loads((source.parent/'profile.json').read_text())
    assert digest(source) == profile['raw_kmb_sha256'] == SOURCE
    assert digest(target) == TARGET
    c = BinaryCircuit(source, profile)
    try:
        splices = {i: [] for i in range(1, 12)}
        assert [x['index'] for x in recipe['edits']] == sorted({x['index'] for x in recipe['edits']})
        for edit in recipe['edits']:
            index = edit['index']
            before = operation(edit['old'])
            assert list(c.operations(index, index+1)) == [before]
            old = strict_columns([before])
            new = strict_columns([operation(row) for row in edit['new']])
            for kind in range(1, 11):
                low, high = c.column_range(kind, index, index+1)
                base = c.packets[kind]['payload_offset']
                assert c.data[base+low:base+high] == old[kind]
                if old[kind] != new[kind]:
                    splices[kind].append((low, high, new[kind]))
        sizes = {kind: row['payload_bytes'] for kind, row in c.packets.items()}
        for kind, changes in splices.items():
            sizes[kind] += sum(len(value)-(high-low) for low, high, value in changes)
        header = dict(profile['header'])
        header['num_bits'] = recipe['header_num_bits']
        for field, kind, width in (
            ('num_ops', 1, 1), ('num_ops_with_3_target_qubits', 2, 4),
            ('num_ops_with_2_target_qubits', 5, 4), ('num_ops_with_1_target_qubits', 7, 4),
            ('num_ops_with_1_target_bit', 8, 4), ('num_ops_with_1_condition_bit', 9, 4),
            ('num_ops_with_angle', 10, 16),
        ):
            header[field] = sizes[kind] // width
        replacement_header = K.HEADER.pack(K.MAGIC, *(header[n] for n in K.HEADER_FIELDS))
        with target.open('rb') as f:
            assert f.read(K.HEADER.size) == replacement_header
        replacements = []
        def append(offset, count, replacement, role):
            old = c.data[offset:offset+count]
            if old != replacement:
                replacements.append({'input_offset': offset, 'input_bytes': count,
                    'input_sha256': sha(old), 'replacement_bytes': len(replacement),
                    'replacement_sha256': sha(replacement),
                    'replacement_b64': base64.b64encode(replacement).decode(), 'role': role})
        append(0, K.HEADER.size, replacement_header, 'kmb_header')
        for kind in range(1, 12):
            packet = c.packets[kind]
            append(packet['header_offset'], K.PACKET.size, K.PACKET.pack(kind, sizes[kind]),
                   f'packet_{kind}_header')
            for i, (low, high, value) in enumerate(splices[kind]):
                append(packet['payload_offset']+low, high-low, value, f'column_{kind}_edit_{i}')
        replacements.sort(key=lambda row: row['input_offset'])
    finally:
        c.close()
    reconstructed, count = virtual_hash(source, replacements)
    assert reconstructed == TARGET and count == target.stat().st_size
    patch = {'schema': 'gvqcc-exact-byte-patch-v1', 'label': 'hmr2',
        'input_sha256': SOURCE, 'input_bytes': source.stat().st_size,
        'output_sha256': TARGET, 'output_bytes': count, 'replacements': replacements,
        'virtual_stream_reconstruction_sha256': reconstructed,
        'operation_recipe_sha256': RECIPE_SHA,
        'scope': 'Exactly two measured-target Kraus rewrites; old outcome bits retain their publication times.'}
    (ROOT/'score5_final_worker_hmr_recipe.json').write_bytes(raw)
    (ROOT/'score5_final_worker_hmr_patch.json.gz').write_bytes(gzip.compress(canonical(patch), compresslevel=9, mtime=0))
    return patch


def read_previous_payload():
    path = ROOT/'score5_patch_worker.py'
    raw = path.read_bytes()
    assert sha(raw) == OLD_WORKER
    constants = {}
    for node in ast.parse(raw).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id in ('PAYLOAD_B64', 'PAYLOAD_SHA256'):
                constants[node.targets[0].id] = ast.literal_eval(node.value)
    payload_raw = gzip.decompress(base64.b64decode(constants['PAYLOAD_B64'], validate=True))
    assert sha(payload_raw) == constants['PAYLOAD_SHA256']
    return json.loads(payload_raw)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', type=Path, default=SCRATCH/'score5_norm_fanout_fanin/dqi.kmb')
    ap.add_argument('--candidate', type=Path, default=SCRATCH/'score5_norm_final/dqi.kmb')
    ap.add_argument('--official', type=Path, default=ROOT/'score5_dqi_final_full_verification.json')
    args = ap.parse_args()
    qbytes = args.official.read_bytes()
    q = json.loads(qbytes)
    assert q['status'] == 'PASS' and q['circuit_sha256'] == TARGET
    assert q['verified_shots'] == 102400 and q['value_errors'] == q['phase_errors'] == 0
    assert q['seed'] is None and q['salt'] == '' and q['log2_delta'] == -128
    assert q['num_qubits'] == 889 and q['num_bits'] == 208169 and q['max_toffoli_count'] == 382894
    review_path = ROOT/'score5_dqi_hmr_independent_review.json'
    review = json.loads(review_path.read_text())
    assert review['status'] == 'INDEPENDENT_KRAUS_AND_FULL_BINARY_BINDING_PASS'
    assert review['source_sha256'] == SOURCE and review['candidate_sha256'] == TARGET
    patch = export_hmr_patch(args.source, args.candidate)
    payload = read_previous_payload()
    manifest = payload['manifest']
    manifest['default_target'] = 'score5_e4'
    manifest['accepted_external_dqi_sha256'].append(TARGET)
    manifest['targets']['score5_e4'] = {'sha256': TARGET, 'bytes': patch['output_bytes'],
                                       'official_receipt_sha256': sha(qbytes)}
    manifest['stages'].append({k: patch[k] for k in ('label', 'input_sha256', 'input_bytes', 'output_sha256', 'output_bytes')}
                             | {'patch_sha256': sha(canonical(patch))})
    manifest_bytes = (json.dumps(manifest, indent=2)+'\n').encode()
    (ROOT/'score5_final_worker_manifest.json').write_bytes(manifest_bytes)
    payload['manifest_sha256'] = sha(manifest_bytes)
    payload['manifest_bytes_b64'] = base64.b64encode(manifest_bytes).decode()
    payload['patches'].append(patch)
    payload['official_receipts_b64'] = {SOURCE: payload.pop('official_receipt_bytes_b64'),
                                      TARGET: base64.b64encode(qbytes).decode()}
    payload['provenance'].update(previous_6a_worker_sha256=OLD_WORKER,
        hmr_operation_recipe_sha256=RECIPE_SHA, hmr_independent_review_sha256=digest(review_path),
        final_official_receipt_sha256=sha(qbytes))
    payload['notice'] += ('\nThe final e4 target additionally replaces two final measured-target CCX writes '
                         'with exact HMR phase corrections. Fresh classical bits preserve the publication '
                         'times of original measurement outcomes. The6a predecessor remains an explicitly '
                         'selectable qualified target; existing artifacts are unchanged.\n')
    raw = canonical(payload)
    packed = gzip.compress(raw, compresslevel=9, mtime=0)
    template = (ROOT/'score5_final_worker_template.py').read_text()
    worker = template.replace('__PAYLOAD_B64__', base64.b64encode(packed).decode()).replace('__PAYLOAD_SHA256__', sha(raw))
    assert '__PAYLOAD_' not in worker
    compile(worker, 'score5_final_worker.py', 'exec')
    (ROOT/'score5_final_worker.py').write_text(worker)
    build = {'status': 'QUALIFIED_FINAL_PINNED_WORKER_BUILT', 'worker_sha256': sha(worker.encode()),
        'worker_bytes': len(worker.encode()), 'payload_raw_sha256': sha(raw),
        'manifest_sha256': sha(manifest_bytes), 'candidate_sha256': TARGET,
        'previous_worker_sha256': OLD_WORKER, 'previous_worker_unchanged': digest(ROOT/'score5_patch_worker.py') == OLD_WORKER,
        'hmr_patch_raw_sha256': sha(canonical(patch)),
        'hmr_patch_gzip_sha256': digest(ROOT/'score5_final_worker_hmr_patch.json.gz'),
        'hmr_virtual_complete_output_sha256': patch['virtual_stream_reconstruction_sha256'],
        'strict_hmr_encoder_opcodes': ['0x31', '0x50', '0xa0', '0x40', '0xc2'],
        'official_receipt_sha256': sha(qbytes), 'independent_review_sha256': digest(review_path),
        'builder_sha256': digest(__file__), 'template_sha256': digest(ROOT/'score5_final_worker_template.py'),
        'new_official_run': False, 'public_score': None, 'submission_performed': False}
    (ROOT/'score5_final_worker_build.json').write_text(json.dumps(build, indent=2)+'\n')
    print(json.dumps(build, indent=2))


if __name__ == '__main__':
    main()
