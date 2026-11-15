#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build a self-contained stdlib score5 worker from pinned, audited recipes.

The worker imports none of this repository. This build step uses the existing
binary reader solely to export exact byte patches and validates each patch by
hashing a virtual reconstruction of its complete expected output.
"""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path

import kmb_profile as K
from dqi_ccx_peephole import BinaryCircuit, Operation, encode_columns

ROOT = Path(__file__).resolve().parent
SCRATCH = Path('/workspace/scratch/3815fb5fae06')
CHUNK = 4 << 20
BASE = '9a82f54226707185fa8a7f59a293e6af8ab7d59bff04a4d92919e4178d7d82f1'
NORM = 'ebfb770f6fc8abc7f48287a0fa4ee6404a2e32a9facdd38449b4f7b73be05d0e'
FANOUT = '98ad7b39a630a4152c54b39fbb14dece22fcaf34b00410ab8a45629db87e0b6f'
FINAL = '6a998c4688dc22b33f52e41be46c5e51f7ea927fab40d9141bc5e99ebf6a2e02'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def operation(row):
    return Operation(row['opcode'], tuple(row['qubits']), row['bit'],
                     row['condition'], bytes.fromhex(row['angle_hex']), row['source_index'])


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def virtual_hash(path, replacements):
    h = hashlib.sha256()
    cursor = count = 0
    with Path(path).open('rb') as f:
        for row in replacements:
            remaining = row['input_offset'] - cursor
            assert remaining >= 0, 'Overlapping byte edits'
            while remaining:
                block = f.read(min(CHUNK, remaining))
                assert block
                h.update(block)
                count += len(block)
                remaining -= len(block)
            old = f.read(row['input_bytes'])
            assert len(old) == row['input_bytes'] and sha(old) == row['input_sha256']
            new = base64.b64decode(row['replacement_b64'], validate=True)
            assert len(new) == row['replacement_bytes'] and sha(new) == row['replacement_sha256']
            h.update(new)
            count += len(new)
            cursor = row['input_offset'] + row['input_bytes']
        for block in iter(lambda: f.read(CHUNK), b''):
            h.update(block)
            count += len(block)
    return h.hexdigest(), count


def export_recipe(source, target, profile_path, recipe_path, label):
    recipe_bytes = Path(recipe_path).read_bytes()
    recipe = json.loads(recipe_bytes)
    profile = json.loads(Path(profile_path).read_text())
    assert digest(source) == recipe['source_sha256'] == profile['raw_kmb_sha256']
    assert digest(target) == recipe['candidate_sha256']
    circuit = BinaryCircuit(source, profile)
    try:
        splices = {kind: [] for kind in range(1, 12)}
        indices = [x['index'] for x in recipe['edits']]
        assert indices == sorted(set(indices))
        for edit in recipe['edits']:
            index = edit['index']
            before = operation(edit['old'])
            assert list(circuit.operations(index, index+1)) == [before]
            old = encode_columns([before])
            new = encode_columns([operation(row) for row in edit['new']])
            for kind in range(1, 11):
                low, high = circuit.column_range(kind, index, index+1)
                base = circuit.packets[kind]['payload_offset']
                assert circuit.data[base+low:base+high] == old[kind]
                if old[kind] != new[kind]:
                    splices[kind].append((low, high, new[kind]))
        sizes = {kind: row['payload_bytes'] for kind, row in circuit.packets.items()}
        for kind, changes in splices.items():
            sizes[kind] += sum(len(value)-(high-low) for low, high, value in changes)
        header = dict(profile['header'])
        for field, kind, width in (
            ('num_ops', 1, 1), ('num_ops_with_3_target_qubits', 2, 4),
            ('num_ops_with_2_target_qubits', 5, 4), ('num_ops_with_1_target_qubits', 7, 4),
            ('num_ops_with_1_target_bit', 8, 4), ('num_ops_with_1_condition_bit', 9, 4),
            ('num_ops_with_angle', 10, 16),
        ):
            header[field] = sizes[kind] // width
        replacements = []
        def append(offset, old_size, new, role):
            old = circuit.data[offset:offset+old_size]
            if old == new:
                return
            replacements.append({'input_offset': offset, 'input_bytes': old_size,
                'input_sha256': sha(old), 'replacement_bytes': len(new),
                'replacement_sha256': sha(new), 'replacement_b64': base64.b64encode(new).decode(),
                'role': role})
        append(0, K.HEADER.size, K.HEADER.pack(K.MAGIC, *(header[x] for x in K.HEADER_FIELDS)), 'kmb_header')
        for kind in range(1, 12):
            packet = circuit.packets[kind]
            append(packet['header_offset'], K.PACKET.size, K.PACKET.pack(kind, sizes[kind]),
                   f'packet_{kind}_header')
            for index, (low, high, value) in enumerate(splices[kind]):
                append(packet['payload_offset']+low, high-low, value, f'column_{kind}_edit_{index}')
        # Stable ordering keeps multiple zero-length inserts in operation order,
        # and end-of-packet inserts before the next packet header.
        replacements.sort(key=lambda row: row['input_offset'])
    finally:
        circuit.close()
    reconstructed, count = virtual_hash(source, replacements)
    assert reconstructed == recipe['candidate_sha256'] and count == Path(target).stat().st_size
    patch = {'schema': 'gvqcc-exact-byte-patch-v1', 'label': label,
        'input_sha256': recipe['source_sha256'], 'input_bytes': Path(source).stat().st_size,
        'output_sha256': recipe['candidate_sha256'], 'output_bytes': count,
        'replacements': replacements, 'virtual_stream_reconstruction_sha256': reconstructed,
        'operation_recipe_sha256': sha(recipe_bytes),
        'scope': 'Exact published fan-in/fan-out identities; no search or arbitrary rewrite.'}
    (ROOT/f'score5_patch_{label}_recipe.json').write_bytes(recipe_bytes)
    return patch


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--norm', type=Path, default=SCRATCH/'score5_norm_restore/dqi.kmb')
    ap.add_argument('--fanout', type=Path, default=SCRATCH/'score5_norm_fanout/dqi.kmb')
    ap.add_argument('--final', type=Path, default=SCRATCH/'score5_norm_fanout_fanin/dqi.kmb')
    args = ap.parse_args()
    norm_bytes = (ROOT/'outcome_dqi_chart_norm_patch.json.gz').read_bytes()
    assert sha(norm_bytes) == '44aa1782e6dedaa0fe8e85b568ad1bfe02b63bcb38e99ba7474aac3b5c976657'
    norm_patch = json.loads(gzip.decompress(norm_bytes))
    assert norm_patch['input_sha256'] == BASE and norm_patch['output_sha256'] == NORM
    fanout_patch = export_recipe(args.norm, args.fanout, args.fanout.parent/'before_profile.json',
                                args.fanout.parent/'patch.json', 'fanout16')
    fanin_patch = export_recipe(args.fanout, args.final, args.fanout.parent/'after_profile.json',
                               args.final.parent/'patch.json', 'fanin8')
    assert (fanout_patch['input_sha256'], fanout_patch['output_sha256']) == (NORM, FANOUT)
    assert (fanin_patch['input_sha256'], fanin_patch['output_sha256']) == (FANOUT, FINAL)
    receipt_bytes = (ROOT/'score5_dqi_full_verification.json').read_bytes()
    receipt = json.loads(receipt_bytes)
    assert receipt['circuit_sha256'] == FINAL and receipt['status'] == 'PASS'
    assert receipt['verified_shots'] == 102400 and receipt['value_errors'] == receipt['phase_errors'] == 0
    assert receipt['seed'] is None and receipt['salt'] == '' and receipt['log2_delta'] == -128
    stages = [dict(norm_patch, label='projective_norm'), fanout_patch, fanin_patch]
    manifest = {'schema': 'gvqcc-score5-pinned-patch-chain-v1', 'default_target': 'score5_6a',
        'accepted_external_dqi_sha256': [BASE, NORM, FINAL],
        'targets': {'score5_6a': {'sha256': FINAL, 'bytes': fanin_patch['output_bytes'],
                               'official_receipt_sha256': sha(receipt_bytes)}},
        'stages': [{k: patch[k] for k in ('label', 'input_sha256', 'input_bytes', 'output_sha256', 'output_bytes')}
                   | {'patch_sha256': sha(canonical(patch))} for patch in stages],
        'scope': 'Only pinned DQI variants are accepted. Other17 portfolio member payloads are preserved '
                 'and hash checked, not replaced or scientifically requalified.'}
    manifest_bytes = (json.dumps(manifest, indent=2)+'\n').encode()
    (ROOT/'score5_patch_manifest.json').write_bytes(manifest_bytes)
    upstream = ROOT.parent/'official_sources/Syed_v12/source/dqi_source'
    notice = ((upstream/'NOTICE').read_text() + '\n\n## Modifications, 2026-11-15\n\n'
              'The third public pivot uses the qualified projective norm repair, then sixteen exact '
              'fan-out and eight exact fan-in Toffoli reductions. The full DQI target is pinned by SHA-256. '
              'The remaining known node13 N=0 failure is outside the repaired class. The portable worker '
              'uses the exact-byte patch application method from outcome_dqi_chart_norm_worker_template.py '
              'and streams a complete SHA-bound patch chain. It performs no submission and claims no Public '
              'Score. Other portfolio members retain their incoming payload bytes and provenance.\n')
    payload = {'manifest': manifest, 'manifest_sha256': sha(manifest_bytes),
               'manifest_bytes_b64': base64.b64encode(manifest_bytes).decode(),
               'patches': stages, 'official_receipt_bytes_b64': base64.b64encode(receipt_bytes).decode(),
               'notice': notice, 'license': (upstream/'LICENSE').read_text(),
               'provenance': {'norm_patch_gzip_sha256': sha(norm_bytes),
                   'norm_worker_source_sha256': digest(ROOT/'outcome_dqi_chart_norm_worker_template.py'),
                   'fanin_independent_review_sha256': digest(ROOT/'score5_dqi_failure_fanin_review.json'),
                   'dqi_ccx_peephole_source_sha256': digest(ROOT/'dqi_ccx_peephole.py'),
                   'kmb_profile_source_sha256': digest(ROOT/'kmb_profile.py')}}
    raw = canonical(payload)
    zipped = gzip.compress(raw, compresslevel=9, mtime=0)
    template = (ROOT/'score5_patch_worker_template.py').read_text()
    worker = template.replace('__PAYLOAD_B64__', base64.b64encode(zipped).decode()).replace('__PAYLOAD_SHA256__', sha(raw))
    assert '__PAYLOAD_' not in worker
    compile(worker, 'score5_patch_worker.py', 'exec')
    (ROOT/'score5_patch_worker.py').write_text(worker)
    build = {'status': 'PINNED_EXACT_PATCH_WORKER_BUILT', 'worker_sha256': sha(worker.encode()),
             'worker_bytes': len(worker.encode()), 'payload_raw_sha256': sha(raw),
             'payload_compressed_bytes': len(zipped), 'manifest_sha256': sha(manifest_bytes),
             'builder_sha256': digest(__file__), 'template_sha256': digest(ROOT/'score5_patch_worker_template.py'),
             'candidate_sha256': FINAL, 'source_immutable': True,
             'virtual_full_stream_checks': [{k: patch[k] for k in ('label', 'output_sha256', 'output_bytes',
                                                                   'virtual_stream_reconstruction_sha256')}
                                            for patch in stages],
             'new_official_run': False, 'public_score': None, 'submission_performed': False}
    (ROOT/'score5_patch_worker_build.json').write_text(json.dumps(build, indent=2)+'\n')
    print(json.dumps(build, indent=2))


if __name__ == '__main__':
    main()
