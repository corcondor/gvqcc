#!/usr/bin/env python3
"""Offline, pinned score3 -> score4 DQI patch and deterministic ZIP packaging.

Generated cell embeds the two unchanged stdlib modules, exact 32-edit recipe,
and all eighteen member pins. No simulator, network request, or submission.
"""
from __future__ import annotations
import argparse
import base64
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import platform
import stat
import sys
import tempfile
import time
import types
import zipfile
import zlib

PAYLOAD_B64 = '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'
PAYLOAD_SHA256 = '99cfe420a659595af23a7f4a9dce07ed32a0a778f767341c5a053227c67bce7b'
CHUNK = 1 << 20
DATE_TIME = (1980, 1, 1, 0, 0, 0)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(CHUNK), b''):
            h.update(block)
    return h.hexdigest()


def load_payload():
    raw = zlib.decompress(base64.b64decode(PAYLOAD_B64, validate=True))
    require(hashlib.sha256(raw).hexdigest() == PAYLOAD_SHA256,
            'Embedded payload checksum mismatch')
    value = json.loads(raw)
    for name, module in value['modules'].items():
        require(hashlib.sha256(module['source'].encode()).hexdigest() == module['sha256'],
                'Embedded module checksum mismatch: ' + name)
    return value


@contextmanager
def embedded_modules(payload):
    saved = {name: sys.modules.get(name) for name in payload['modules']}
    try:
        for name in ('kmb_profile', 'dqi_ccx_peephole'):
            module = types.ModuleType(name)
            module.__file__ = '<score4 embedded ' + name + '.py>'
            sys.modules[name] = module
            exec(compile(payload['modules'][name]['source'], module.__file__, 'exec'),
                 module.__dict__)
        yield sys.modules['kmb_profile'], sys.modules['dqi_ccx_peephole']
    finally:
        for name, old in saved.items():
            if old is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old


def expected_rows(payload, candidate=False):
    rows = [dict(row) for row in payload['members']]
    if candidate:
        row = next(row for row in rows if row['name'] == 'dqi.kmb')
        row.update(sha256=payload['candidate_dqi_sha256'],
                   bytes=payload['candidate_dqi_bytes'])
    return rows


def verify_archive(path, rows, extract_dqi=None):
    checked = []
    with zipfile.ZipFile(path) as archive:
        require(archive.namelist() == [row['name'] for row in rows],
                'Wrong member order, duplicate name, or non-18-member archive')
        require(not archive.comment, 'Archive comment differs')
        for row, info in zip(rows, archive.infolist()):
            require(not info.is_dir() and not (info.flag_bits & 1),
                    'Invalid or encrypted member: ' + row['name'])
            require(info.date_time == DATE_TIME and info.compress_type == zipfile.ZIP_DEFLATED,
                    'Unexpected timestamp/compression: ' + row['name'])
            require(not info.extra and not info.comment and info.create_system == 3
                    and info.external_attr == (stat.S_IFREG | 0o644) << 16,
                    'Unexpected ZIP metadata: ' + row['name'])
            require(info.file_size == row['bytes'], 'Wrong member size: ' + row['name'])
            h = hashlib.sha256()
            crc = size = 0
            output = Path(extract_dqi).open('xb') if extract_dqi and row['name'] == 'dqi.kmb' else None
            try:
                with archive.open(info) as source:
                    for block in iter(lambda: source.read(CHUNK), b''):
                        h.update(block)
                        crc = zlib.crc32(block, crc)
                        size += len(block)
                        if output is not None:
                            output.write(block)
            finally:
                if output is not None:
                    output.close()
            require(h.hexdigest() == row['sha256'] and size == row['bytes'],
                    'Member SHA/length mismatch: ' + row['name'])
            require((crc & 0xffffffff) == info.CRC, 'Member CRC mismatch: ' + row['name'])
            checked.append(dict(name=row['name'], sha256=h.hexdigest(), bytes=size,
                                compressed_bytes=info.compress_size, crc32=f'{info.CRC:08x}',
                                sha256_pass=True, crc_pass=True))
    return checked


def zip_info(row):
    info = zipfile.ZipInfo(row['name'], DATE_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info._compresslevel = 6
    info.create_system = 3
    info.create_version = info.extract_version = 20
    info.external_attr = (stat.S_IFREG | 0o644) << 16
    info.internal_attr = info.flag_bits = 0
    info.extra = info.comment = b''
    info.file_size = row['bytes']
    return info


def patch_dqi(source, target, payload):
    recipe = payload['recipe']
    require(recipe['source_sha256'] == payload['source_dqi_sha256']
            and recipe['candidate_sha256'] == payload['candidate_dqi_sha256'],
            'Recipe target/source pins differ')
    with embedded_modules(payload) as (kp, peephole):
        profile = kp.profile(source, max_register_summaries=0)
        circuit = peephole.BinaryCircuit(source, profile)
        def operation(value):
            return peephole.Operation(value['opcode'], tuple(value['qubits']),
                                      value['bit'], value['condition'],
                                      bytes.fromhex(value['angle_hex']), value['source_index'])
        try:
            blocks = []
            indexes = [edit['index'] for edit in recipe['edits']]
            require(indexes == sorted(set(indexes)), 'Duplicate/unordered edit indexes')
            for edit in recipe['edits']:
                index = edit['index']
                before = operation(edit['old'])
                observed = list(circuit.operations(index, index+1))
                require(observed == [before], 'Pinned old operation mismatch at ' + str(index))
                blocks.append((index, index+1, [before],
                               [operation(value) for value in edit['new']]))
            peephole.write_rewritten(circuit, target, blocks)
        finally:
            circuit.close()
    require(target.stat().st_size == payload['candidate_dqi_bytes'], 'New DQI byte length differs')
    require(digest(target) == payload['candidate_dqi_sha256'], 'New DQI SHA differs')
    old_ccx = sum((edit['old']['opcode'] & 0x7f) == 0x31 for edit in recipe['edits'])
    new_ccx = sum((op['opcode'] & 0x7f) == 0x31 for edit in recipe['edits'] for op in edit['new'])
    require(old_ccx-new_ccx == 16, 'Recipe does not remove exactly sixteen CCX')
    return dict(source_header=profile['header'], edited_original_operations=len(blocks),
                old_ccx_in_edits=old_ccx, new_ccx_in_edits=new_ccx, static_ccx_removed=16,
                source_and_old_operation_bytes_checked=True,
                unchanged_binary_columns_copied_verbatim=True)


def write_archive(source_zip, candidate_dqi, target_zip, rows):
    with zipfile.ZipFile(source_zip) as source:
        with zipfile.ZipFile(target_zip, 'x', compression=zipfile.ZIP_DEFLATED,
                             compresslevel=6, allowZip64=False) as target:
            target.comment = b''
            for row in rows:
                origin = candidate_dqi.open('rb') if row['name'] == 'dqi.kmb' else source.open(row['name'])
                h = hashlib.sha256()
                with origin, target.open(zip_info(row), 'w', force_zip64=False) as out:
                    for block in iter(lambda: origin.read(CHUNK), b''):
                        h.update(block)
                        out.write(block)
                require(h.hexdigest() == row['sha256'], 'Source changed while packaging: ' + row['name'])


def atomic_json(path, value):
    temporary = path.with_name(path.name + '.partial')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    os.replace(temporary, path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path('/kaggle/working/submission.zip'))
    parser.add_argument('--output', type=Path, default=Path('/kaggle/working/submission.zip'))
    parser.add_argument('--receipt', type=Path)
    args = parser.parse_args(argv)
    started = time.monotonic()
    payload = load_payload()
    source, output = args.source.resolve(), args.output.resolve()
    require(source.is_file(), 'Source submission.zip is missing')
    require(output.name == 'submission.zip', 'Output must be named submission.zip')
    output.parent.mkdir(parents=True, exist_ok=True)
    receipt_path = args.receipt or output.with_name('score4_package_receipt.json')
    original_hash = digest(source)
    after_rows = expected_rows(payload, candidate=True)
    if original_hash != payload['source_zip_sha256']:
        # Safe reruns accept only the already-patched exact member set.
        require(source == output, 'Wrong source score3 ZIP SHA256')
        checks = verify_archive(source, after_rows)
        result = dict(status='ALREADY_PATCHED_PACKAGE_INTEGRITY_PASS', output=str(output),
                      zip_sha256=original_hash, zip_bytes=output.stat().st_size, members=checks,
                      official_verifier_run=False, official_dqi_verification='NOT_ASSESSED_BY_PACKAGER')
        atomic_json(receipt_path, result)
        print(json.dumps(result, sort_keys=True), flush=True)
        return result
    require(not output.exists() or output == source, 'Refusing to overwrite a separate existing output')
    with tempfile.TemporaryDirectory(prefix='score4_package_', dir=output.parent) as temporary:
        directory = Path(temporary)
        old_dqi, new_dqi = directory/'source.kmb', directory/'candidate.kmb'
        before_checks = verify_archive(source, expected_rows(payload), extract_dqi=old_dqi)
        patch = patch_dqi(old_dqi, new_dqi, payload)
        partial = directory/'submission.zip'
        write_archive(source, new_dqi, partial, after_rows)
        checks = verify_archive(partial, after_rows)
        final_hash = digest(partial)
        final_size = partial.stat().st_size
        os.replace(partial, output)
    result = dict(status='PACKAGE_INTEGRITY_PASS', source=str(source), source_zip_sha256=original_hash,
                  output=str(output), zip_sha256=final_hash, zip_bytes=final_size,
                  member_count=len(checks), all_member_sha256_and_crc_pass=True,
                  preserved_other_member_count=17, source_dqi_sha256=payload['source_dqi_sha256'],
                  candidate_dqi_sha256=payload['candidate_dqi_sha256'], patch=patch,
                  members=checks, payload_sha256=PAYLOAD_SHA256,
                  embedded_module_sha256={name: x['sha256'] for name, x in payload['modules'].items()},
                  recipe_sha256=payload['recipe_sha256'],
                  source_manifest_sha256=payload['source_manifest_sha256'],
                  deterministic_zip=dict(timestamp=list(DATE_TIME), compression='DEFLATE',
                                         compression_level=6, creator_system='Unix',
                                         permissions='regular 0644', extra_fields=False,
                                         comments=False, zip64=False,
                                         python=platform.python_version(),
                                         zlib=zlib.ZLIB_RUNTIME_VERSION),
                  official_verifier_run=False, official_dqi_verification='PENDING_SEPARATE_OFFICIAL_RECEIPT',
                  kaggle_submission_performed=False, seconds=time.monotonic()-started)
    atomic_json(receipt_path, result)
    print(json.dumps({key: value for key, value in result.items() if key not in ('members','patch')},
                     sort_keys=True), flush=True)
    return result


if __name__ == '__main__':
    main([] if 'ipykernel' in sys.modules else None)
