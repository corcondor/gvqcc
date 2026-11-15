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

PAYLOAD_B64 = '__SCORE4_PAYLOAD_B64__'
PAYLOAD_SHA256 = '__SCORE4_PAYLOAD_SHA256__'
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
