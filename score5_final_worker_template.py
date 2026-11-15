#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Offline pinned final score5 DQI reconstruction and portfolio packaging.

Python standard library only. Accepts a portfolio ZIP containing a known DQI
or --dqi-only with a known KMB. Preserves all17 other portfolio payloads. No
network access, simulator, scientific re-verification, or submission occurs.
"""
import argparse
import base64
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import stat
import sys
import tempfile
import time
import zipfile
import zlib

PAYLOAD_B64 = '__PAYLOAD_B64__'
PAYLOAD_SHA256 = '__PAYLOAD_SHA256__'
CHUNK = 4 << 20
DATE_TIME = (1980, 1, 1, 0, 0, 0)
MEMBER_ORDER = ['invsqrt.kmb', 'dqi.kmb', 'dfthcsos/submission.npz'] + [
    f'dfthcsos/angle_k_{i}.kmb' for i in range(15)]


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def decoded(value, expected=None):
    data = base64.b64decode(value, validate=True)
    if expected is not None:
        require(hashlib.sha256(data).hexdigest() == expected, 'Embedded artifact SHA mismatch')
    return data


def emit(event, **data):
    print(json.dumps({'event': event, **data}, sort_keys=True), flush=True)


def load_payload(target_name):
    raw = gzip.decompress(decoded(PAYLOAD_B64))
    require(hashlib.sha256(raw).hexdigest() == PAYLOAD_SHA256, 'Embedded payload SHA mismatch')
    payload = json.loads(raw)
    manifest_bytes = decoded(payload['manifest_bytes_b64'], payload['manifest_sha256'])
    manifest = json.loads(manifest_bytes)
    require(manifest == payload['manifest'], 'Manifest representations differ')
    target_name = target_name or manifest['default_target']
    require(target_name in manifest['targets'], 'Target is not in the embedded pinned manifest')
    target = manifest['targets'][target_name]
    require(len(manifest['stages']) == len(payload['patches']), 'Patch count differs from manifest')
    sizes = {}
    for row, patch in zip(manifest['stages'], payload['patches']):
        require(hashlib.sha256(canonical(patch)).hexdigest() == row['patch_sha256'], 'Embedded patch SHA mismatch')
        require(all(patch[k] == row[k] for k in ('label', 'input_sha256', 'input_bytes', 'output_sha256', 'output_bytes')),
                'Patch pins differ from manifest')
        for prefix in ('input', 'output'):
            h, n = patch[prefix+'_sha256'], patch[prefix+'_bytes']
            require(h not in sizes or sizes[h] == n, 'Inconsistent circuit size pin')
            sizes[h] = n
    require(target['sha256'] in sizes and sizes[target['sha256']] == target['bytes'], 'Unbound target')
    qbytes = decoded(payload['official_receipts_b64'][target['sha256']], target['official_receipt_sha256'])
    q = json.loads(qbytes)
    require(q['circuit_sha256'] == target['sha256'] and q['status'] == 'PASS', 'Official receipt target mismatch')
    require(q['verified_shots'] == 102400 and q['value_errors'] == q['phase_errors'] == 0, 'Wrong official check')
    require(q['seed'] is None and q['salt'] == '' and q['log2_delta'] == -128, 'Wrong official defaults')
    require(q['verifier_sha256'] == 'f14274bc0943fb9769ddb01131be6063191a15009fe1caf1d4bdd9fd25194e65',
            'Wrong verifier source pin')
    return payload, manifest, target_name, target, sizes, qbytes, q


def apply_patch(source, target, patch):
    """Same streaming whole-SHA method as outcome_dqi_chart_norm_worker.

    Every old/new changed region and the entire input/output are bound. On any
    failure only the newly-created output is removed; source remains read-only.
    """
    source, target = Path(source), Path(target)
    require(source.resolve() != target.resolve() and not target.exists(), 'Patch output must be a new file')
    require(source.stat().st_size == patch['input_bytes'], 'Wrong input KMB size')
    before_hash = hashlib.sha256()
    after_hash = hashlib.sha256()
    cursor = count = 0
    created = False
    try:
        with source.open('rb') as f, target.open('xb') as g:
            created = True
            for row in patch['replacements']:
                remaining = row['input_offset'] - cursor
                require(remaining >= 0, 'Overlapping or unordered patch')
                while remaining:
                    block = f.read(min(CHUNK, remaining))
                    require(bool(block), 'Truncated input')
                    before_hash.update(block)
                    after_hash.update(block)
                    g.write(block)
                    remaining -= len(block)
                    count += len(block)
                old = f.read(row['input_bytes'])
                require(len(old) == row['input_bytes'], 'Truncated changed region')
                require(hashlib.sha256(old).hexdigest() == row['input_sha256'], 'Wrong old changed region')
                before_hash.update(old)
                new = decoded(row['replacement_b64'], row['replacement_sha256'])
                require(len(new) == row['replacement_bytes'], 'Wrong new changed region length')
                after_hash.update(new)
                g.write(new)
                count += len(new)
                cursor = row['input_offset'] + row['input_bytes']
            for block in iter(lambda: f.read(CHUNK), b''):
                before_hash.update(block)
                after_hash.update(block)
                g.write(block)
                count += len(block)
        require(before_hash.hexdigest() == patch['input_sha256'], 'Whole input SHA mismatch')
        require(after_hash.hexdigest() == patch['output_sha256'], 'Whole output SHA mismatch')
        require(count == patch['output_bytes'], 'Wrong output KMB size')
    except BaseException:
        if created:
            target.unlink(missing_ok=True)
        raise
    return {'label': patch['label'], 'input_sha256': before_hash.hexdigest(),
            'output_sha256': after_hash.hexdigest(), 'bytes': count,
            'old_and_new_region_hashes_pass': True, 'whole_input_and_output_hashes_pass': True}


def verify_archive(path, expected=None, extract_dqi=None):
    checked = {}
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        require(len(names) == 18 and len(set(names)) == 18 and set(names) == set(MEMBER_ORDER),
                'Expected exactly the18 named portfolio files')
        for name in MEMBER_ORDER:
            info = archive.getinfo(name)
            require(not info.is_dir() and not (info.flag_bits & 1), 'Invalid or encrypted member: '+name)
            h = hashlib.sha256()
            count = crc = 0
            output = Path(extract_dqi).open('xb') if extract_dqi is not None and name == 'dqi.kmb' else None
            try:
                with archive.open(info) as f:
                    for block in iter(lambda: f.read(CHUNK), b''):
                        h.update(block)
                        count += len(block)
                        crc = zlib.crc32(block, crc)
                        if output is not None:
                            output.write(block)
            finally:
                if output is not None:
                    output.close()
            require(count == info.file_size and (crc & 0xffffffff) == info.CRC, 'Member length/CRC mismatch: '+name)
            row = {'sha256': h.hexdigest(), 'bytes': count, 'crc32': f'{crc & 0xffffffff:08x}',
                   'compressed_bytes': info.compress_size, 'sha256_pass': True, 'crc_pass': True}
            if expected is not None:
                require(all(row[k] == expected[name][k] for k in ('sha256', 'bytes')), 'Member SHA mismatch: '+name)
            checked[name] = row
    return checked


def zip_info(name, size):
    info = zipfile.ZipInfo(name, DATE_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info._compresslevel = 6
    info.create_system = 3
    info.create_version = info.extract_version = 20
    info.external_attr = (stat.S_IFREG | 0o644) << 16
    info.internal_attr = info.flag_bits = 0
    info.extra = info.comment = b''
    info.file_size = size
    return info


def package(source_zip, dqi, target_zip, expected):
    with zipfile.ZipFile(source_zip) as source, zipfile.ZipFile(target_zip, 'x',
            compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=False) as target:
        target.comment = b''
        for name in MEMBER_ORDER:
            origin = Path(dqi).open('rb') if name == 'dqi.kmb' else source.open(name)
            h = hashlib.sha256()
            count = 0
            with origin, target.open(zip_info(name, expected[name]['bytes']), 'w', force_zip64=False) as out:
                for block in iter(lambda: origin.read(CHUNK), b''):
                    h.update(block)
                    count += len(block)
                    out.write(block)
            require(h.hexdigest() == expected[name]['sha256'] and count == expected[name]['bytes'],
                    'Source member changed while packaging: '+name)
            if name == 'dqi.kmb':
                emit('dqi_compressed', sha256=h.hexdigest(), bytes=count)


def publish_new(source, target):
    """Create a separate final artifact without replacing existing paths."""
    created = False
    try:
        with Path(source).open('rb') as f, Path(target).open('xb') as g:
            created = True
            shutil.copyfileobj(f, g, CHUNK)
    except BaseException:
        if created:
            Path(target).unlink(missing_ok=True)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True, help='Portfolio ZIP, or KMB with --dqi-only')
    parser.add_argument('--output', type=Path, help='New output path; existing files are never replaced')
    parser.add_argument('--receipt', type=Path)
    parser.add_argument('--dqi-only', action='store_true')
    parser.add_argument('--target', help='A target name from the embedded pinned manifest')
    args = parser.parse_args(argv)
    started = time.monotonic()
    payload, manifest, target_name, target, sizes, qbytes, q = load_payload(args.target)
    source = args.source.resolve()
    default_name = 'dqi.kmb' if args.dqi_only else 'submission.zip'
    output = (args.output or Path('/kaggle/working')/default_name).resolve()
    receipt_path = (args.receipt or output.with_name('score5_final_worker_check.json')).resolve()
    require(source.is_file(), 'Missing source input')
    require(source != output and not output.exists(), 'Output must be a separate new path')
    require(receipt_path not in (source, output) and not receipt_path.exists(), 'Receipt must be a separate new path')
    if not args.dqi_only:
        require(output.name == 'submission.zip', 'Portfolio output must be named submission.zip')
    output.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    source_container_sha = digest(source)
    source_is_zip = zipfile.is_zipfile(source)
    require(args.dqi_only or source_is_zip, 'Portfolio mode requires a ZIP source')
    with tempfile.TemporaryDirectory(prefix='score5-patch-', dir=output.parent) as temporary:
        temp = Path(temporary)
        if source_is_zip:
            original = temp/'source.kmb'
            before = verify_archive(source, extract_dqi=original)
            source_dqi_sha = before['dqi.kmb']['sha256']
        else:
            original = source
            source_dqi_sha = source_container_sha
            before = None
        require(source_dqi_sha in manifest['accepted_external_dqi_sha256'], 'Unknown input DQI SHA256')
        require(original.stat().st_size == sizes[source_dqi_sha], 'Known input SHA has wrong size')
        emit('input_verified', dqi_sha256=source_dqi_sha, target=target_name,
             other_members=17 if before is not None else 0)
        current, current_sha = original, source_dqi_sha
        stages = []
        seen = set()
        while current_sha != target['sha256']:
            require(current_sha not in seen, 'Patch manifest contains a cycle')
            seen.add(current_sha)
            applicable = [p for p in payload['patches'] if p['input_sha256'] == current_sha]
            require(len(applicable) == 1, 'Missing or ambiguous pinned patch path')
            patch = applicable[0]
            new = temp/f'stage-{len(stages)+1}.kmb'
            stage = apply_patch(current, new, patch)
            stages.append(stage)
            current, current_sha = new, patch['output_sha256']
            emit('patch_stage_pass', **stage)
        require(current.stat().st_size == target['bytes'] and digest(current) == target['sha256'], 'Final target mismatch')
        if args.dqi_only:
            artifact = current
            checks = None
            changed = []
        else:
            expected = {name: dict(row) for name, row in before.items()}
            expected['dqi.kmb'] = {'sha256': target['sha256'], 'bytes': target['bytes']}
            artifact = temp/'submission.zip'
            package(source, current, artifact, expected)
            checks = verify_archive(artifact, expected)
            changed = [name for name in MEMBER_ORDER if checks[name]['sha256'] != before[name]['sha256']]
            require(set(changed) <= {'dqi.kmb'}, 'A non-DQI member changed')
            require(all(checks[n]['sha256'] == before[n]['sha256'] and checks[n]['bytes'] == before[n]['bytes']
                        for n in MEMBER_ORDER if n != 'dqi.kmb'), 'Non-DQI preservation failed')
        require(digest(source) == source_container_sha, 'Source input changed during packaging')
        final_hash = digest(artifact)
        final_bytes = artifact.stat().st_size
        publish_new(artifact, output)
        require(digest(output) == final_hash, 'Published output copy SHA mismatch')
    result = {'status': 'DQI_INTEGRITY_PASS' if args.dqi_only else 'PACKAGE_INTEGRITY_PASS',
        'source': str(source), 'source_container_sha256': source_container_sha,
        'source_dqi_sha256': source_dqi_sha, 'target_name': target_name,
        'candidate_dqi_sha256': target['sha256'], 'candidate_dqi_bytes': target['bytes'],
        'output': str(output), 'output_sha256': final_hash, 'output_bytes': final_bytes,
        'stages_applied': stages, 'manifest_sha256': payload['manifest_sha256'],
        'worker_payload_sha256': PAYLOAD_SHA256, 'source_provenance': payload['provenance'],
        'members': checks, 'source_members': before, 'member_count': 18 if checks else None,
        'all_member_sha256_and_crc_pass': True if checks else None,
        'preserved_non_dqi_members': 17 if checks else None, 'changed_members': changed,
        'deterministic_zip': {'timestamp': list(DATE_TIME), 'order': MEMBER_ORDER,
            'compression': 'DEFLATE', 'compression_level': 6, 'permissions': 'regular0644',
            'python': platform.python_version(), 'zlib': zlib.ZLIB_RUNTIME_VERSION} if checks else None,
        'official_dqi_receipt_sha256': target['official_receipt_sha256'],
        'prior_local_official_dqi_verification': q, 'new_official_verifier_run': False,
        'scope': 'Exact byte reconstruction and packaging only. The embedded DQI receipt is an already '
                 'completed local official run. Other17 incoming payloads are preserved, not requalified. '
                 'Known node13 N=0 failure remains; no universal correctness or Public Score claim.',
        'public_score': None, 'kaggle_submission_performed': False, 'seconds': time.monotonic()-started}
    with receipt_path.open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    # Companion evidence stays outside the exact18-member submission archive.
    for name, content in (
        ('score5_dqi_full_verification.json', qbytes),
        ('score5_patch_manifest.json', decoded(payload['manifest_bytes_b64'], payload['manifest_sha256'])),
        ('score5_sources_and_license.md', payload['notice'].encode()),
        ('LICENSE_Apache_2.0.txt', payload['license'].encode()),
    ):
        path = output.parent/name
        if path.exists():
            require(path.read_bytes() == content, 'Existing companion differs: '+name)
        else:
            with path.open('xb') as f:
                f.write(content)
    emit(result['status'], output=str(output), output_sha256=final_hash, output_bytes=final_bytes,
         candidate_dqi_sha256=target['sha256'], member_count=result['member_count'],
         preserved_non_dqi_members=result['preserved_non_dqi_members'],
         local_official_dqi_cost=q['score'], public_score=None, submitted=False,
         seconds=result['seconds'])
    return result


if __name__ == '__main__':
    main([] if 'ipykernel' in sys.modules else None)
