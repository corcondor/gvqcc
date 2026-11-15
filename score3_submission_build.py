#!/usr/bin/env python3
"""Package the pinned score3 circuits as a deterministic 18-member submission.

No simulator or verifier runs here.  Component receipts are read and bound to
the exact archived member hashes.  A ZIP can be built while official runs are
pending; --refresh-manifest rechecks its members and updates only the external
manifest after those runs finish.  No candidate bytes are modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import stat
import time
import zipfile
import zlib


DQI_SHA = '9a82f54226707185fa8a7f59a293e6af8ab7d59bff04a4d92919e4178d7d82f1'
INVSQRT_SHA = '684106f101730ca193627229920a0501bef9ea10ccfb34aa453fcf63edadb50a'
NPZ_SHA = '5f8dd37ac194b09b5ba870c4150a487b6665775375d9abc864d38b32a2cb7357'
CHEMISTRY_RECEIPT_SHA = '0d2410ba7ab526f4a0828b6af671996d64c9e8a683f185859e2244343319e661'
LOADER_SHA = [
    '39a74c931c745143d46ac3c3d7f76a84cc09982f0c7a9b2784e35e8cf0533b45',
    '753b1424a819fadcac324155a7cae1841f0ee977ce873f29c7e364c55cdd4f37',
    '487adc39d32a904021985241f80881fd90542fa35c0a379034fc88cc9ccfc337',
    '8e01cc596c3cbfd372f2b6d009e3b49c29ae9448eaf0d9f21f50d088d2404d6a',
    'f9b6e68a119dc2b819c21812a136f3ae76eddb36d8964d1847bab68f880b3330',
    'a17d6c663f66b3e8d9487b0b19f77075f5647ff240d258b6b7d37cb58997cd6c',
    '387f1a6095132fb6114682c8cc102a36cc93426860fa57b1fd972b65d4e88561',
    '146cb20a99a8c6005539df2b0c9f0eb11b33a71ab10d66480f51fd5590e53711',
    '0be2c2ec69d681f352c7e89fc94ed161f45b448110c9e617fe86181f72de646e',
    '3e31f13446a8a3c72bff3ac6c123d15f9c8b86039f505fe7b5510d7245246c99',
    '656d5eb283c54a2b934fdcf38fc56d7b3cc7b0607e7731c26eb15b574e74f5eb',
    'd4eeedc38481610804ec2708e2fc02323b63d9f37487cec6cb9b42ed7c94c033',
    '61275eda03641d1a7b4052b36fa1df4383918f8986172e73a7f8dcaa817d0308',
    'a4e43c2b183cf64de805701517fd0b56333dde662889579b824b4ee1ff0c3a72',
    '3b21fe0767295c6bd40c41e0c40ca1aeff02e54216ada02849c238ab66b70159',
]
PINNED_VERIFIERS = {
    'dqi': 'f14274bc0943fb9769ddb01131be6063191a15009fe1caf1d4bdd9fd25194e65',
    'invsqrt': 'ddef520dec6b68d1cf0a6f328ddd36d79eb84570b9192cf3f7acaf073f06733a',
    'dfthcsos': 'ca84ca08e6e9280922cda3b539d4776ae58990b2b03b5619a53d65de67df9d2b',
}
DATE_TIME = (1980,1,1,0,0,0)
COMPRESSION_LEVEL = 6
CHUNK = 1 << 20


def file_digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda:handle.read(CHUNK),b''):
            h.update(block)
    return h.hexdigest()


def members(args):
    result = [dict(name='invsqrt.kmb',source=args.invsqrt,pin=INVSQRT_SHA),
              dict(name='dqi.kmb',source=args.dqi,pin=DQI_SHA),
              dict(name='dfthcsos/submission.npz',source=args.chemistry_dir/'submission.npz',pin=NPZ_SHA)]
    result.extend(dict(name=f'dfthcsos/angle_k_{k}.kmb',
                       source=args.chemistry_dir/f'angle_k_{k}.kmb',pin=digest)
                  for k,digest in enumerate(LOADER_SHA))
    assert len(result) == 18 and len({x['name'] for x in result}) == 18
    for row in result:
        if not row['source'].is_file():
            raise FileNotFoundError(row['source'])
        actual = file_digest(row['source'])
        if actual != row['pin']:
            raise ValueError(f"Pinned input hash mismatch: {row['source']}: {actual}")
        row['bytes'] = row['source'].stat().st_size
    return result


def zip_info(row):
    info = zipfile.ZipInfo(row['name'],DATE_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    # ZipFile.open(ZipInfo,'w') takes the level from this field on Python 3.12.
    info._compresslevel = COMPRESSION_LEVEL
    info.create_system = 3
    info.create_version = 20
    info.extract_version = 20
    info.external_attr = (stat.S_IFREG | 0o644) << 16
    info.internal_attr = 0
    info.flag_bits = 0
    info.extra = b''
    info.comment = b''
    info.file_size = row['bytes']
    return info


def write_zip(path,rows):
    if path.exists():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    partial = path.with_name(path.name+'.partial')
    if partial.exists():
        raise FileExistsError(partial)
    try:
        with zipfile.ZipFile(partial,'x',compression=zipfile.ZIP_DEFLATED,
                             compresslevel=COMPRESSION_LEVEL,allowZip64=False) as archive:
            archive.comment = b''
            for row in rows:
                digest = hashlib.sha256()
                with row['source'].open('rb') as source, archive.open(zip_info(row),'w',force_zip64=False) as target:
                    for block in iter(lambda:source.read(CHUNK),b''):
                        digest.update(block)
                        target.write(block)
                if digest.hexdigest() != row['pin']:
                    raise ValueError(f"Input changed while packaging: {row['source']}")
        verify_zip(partial,rows)
        os.replace(partial,path)
    except BaseException:
        if partial.exists():
            partial.unlink()
        raise


def verify_zip(path,rows):
    expected = [row['name'] for row in rows]
    checked = []
    with zipfile.ZipFile(path,'r') as archive:
        if archive.namelist() != expected:
            raise ValueError('Archive order or exact 18-member set differs')
        if archive.comment != b'':
            raise ValueError('Unexpected archive comment')
        for row,info in zip(rows,archive.infolist()):
            if info.is_dir() or info.date_time != DATE_TIME or info.compress_type != zipfile.ZIP_DEFLATED:
                raise ValueError(f"Unexpected ZIP member metadata: {row['name']}")
            if info.flag_bits & 1 or info.extra or info.comment:
                raise ValueError(f"Encrypted member or unexpected ZIP extras: {row['name']}")
            if info.create_system != 3 or info.external_attr != (stat.S_IFREG | 0o644) << 16:
                raise ValueError(f"Unexpected ZIP permissions: {row['name']}")
            digest = hashlib.sha256()
            crc = 0
            size = 0
            # ZipExtFile independently enforces ZIP CRC at EOF.  We also compare
            # an explicitly computed CRC and SHA to the pinned source bytes.
            with archive.open(info,'r') as source:
                for block in iter(lambda:source.read(CHUNK),b''):
                    digest.update(block)
                    crc = zlib.crc32(block,crc)
                    size += len(block)
            if digest.hexdigest() != row['pin'] or size != row['bytes'] or size != info.file_size:
                raise ValueError(f"Archive member hash/size mismatch: {row['name']}")
            if crc & 0xffffffff != info.CRC:
                raise ValueError(f"Archive member CRC mismatch: {row['name']}")
            checked.append(dict(name=row['name'],source=str(row['source']),sha256=row['pin'],
                                bytes=size,compressed_bytes=info.compress_size,
                                crc32=f'{info.CRC:08x}',sha256_matches_pinned_source=True,crc_pass=True))
    return checked


def read_receipt(path,component):
    result = dict(path=str(path),component=component,state='PENDING',passes_bound_official_check=False)
    if not path.is_file():
        result['reason'] = 'Official receipt not present yet'
        return result
    raw = path.read_bytes()
    result['sha256'] = hashlib.sha256(raw).hexdigest()
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        result['reason'] = 'Official receipt is not complete JSON yet'
        return result
    check = value.get('official_result',{}) if component == 'dfthcsos' else value
    result['reported_status'] = check.get('status')
    if check.get('status') != 'PASS':
        result['state'] = 'NONPASS'
        result['reason'] = 'Official receipt does not report PASS'
        return result
    if value.get('verifier_sha256') != PINNED_VERIFIERS[component]:
        result['state'] = 'UNBOUND'
        result['reason'] = 'Official verifier hash differs'
        return result
    if component == 'dfthcsos':
        bound = (result['sha256'] == CHEMISTRY_RECEIPT_SHA
                 and value.get('candidate_sha256') == NPZ_SHA
                 and value.get('factorization',{}).get('sha256') == NPZ_SHA
                 and value.get('circuit_words_match_candidate_npz') is True
                 and check.get('verified_shots') == 78080
                 and {x['name']:x['sha256'] for x in value.get('loaders',[])} ==
                     {f'angle_k_{k}.kmb':digest for k,digest in enumerate(LOADER_SHA)})
    else:
        pin = DQI_SHA if component == 'dqi' else INVSQRT_SHA
        shots = 102400 if component == 'dqi' else 200540928
        bound = (value.get('circuit_sha256') == pin and value.get('verified_shots') == shots
                 and value.get('seed','absent') is None and value.get('salt','absent') == '')
        if component == 'dqi':
            bound = bound and value.get('log2_delta') == -128.0
        else:
            bound = bound and value.get('source_file_sha256') == pin
    if not bound:
        result['state'] = 'UNBOUND'
        result['reason'] = 'Receipt does not bind the pinned candidate and complete default official scope'
        return result
    result.update(state='PASS',passes_bound_official_check=True,
                  official_metrics={k:check[k] for k in (
                      'status','score','verified_shots','toffoli_equivalent','toffoli_count',
                      'max_toffoli_count','num_qubits','num_ops','lambda_eff','value_errors',
                      'phase_errors','effective_error_rate','log2_delta','metrics') if k in check})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dqi',type=Path,required=True)
    parser.add_argument('--invsqrt',type=Path,required=True)
    parser.add_argument('--chemistry-dir',type=Path,required=True)
    parser.add_argument('--dqi-receipt',type=Path,required=True)
    parser.add_argument('--invsqrt-receipt',type=Path,required=True)
    parser.add_argument('--chemistry-receipt',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--refresh-manifest',action='store_true',help='Read existing ZIP; update only its external receipt manifest')
    parser.add_argument('--require-official-pass',action='store_true')
    args = parser.parse_args()
    started = time.monotonic()
    if args.output.name != 'submission.zip':
        raise ValueError('The final upload artifact must be named submission.zip')
    rows = members(args)
    if args.refresh_manifest:
        if not args.output.is_file():
            raise FileNotFoundError(args.output)
    else:
        write_zip(args.output,rows)
    checked = verify_zip(args.output,rows)
    receipts = {component:read_receipt(path,component) for component,path in (
        ('dqi',args.dqi_receipt),('invsqrt',args.invsqrt_receipt),('dfthcsos',args.chemistry_receipt))}
    official_pass = all(row['passes_bound_official_check'] for row in receipts.values())
    status = ('PACKAGE_AND_ALL_COMPONENT_OFFICIAL_VERIFICATIONS_PASS' if official_pass
              else 'PACKAGE_VERIFIED_OFFICIAL_VERIFICATION_PENDING')
    if any(row['state'] in ('NONPASS','UNBOUND') for row in receipts.values()):
        status = 'PACKAGE_VERIFIED_WITH_NONPASS_OR_UNBOUND_RECEIPT'
    report = dict(status=status,package_structure_and_integrity_pass=True,
                  all_component_official_verifications_pass=official_pass,
                  archive=dict(path=str(args.output),sha256=file_digest(args.output),bytes=args.output.stat().st_size,
                               member_count=len(checked),uncompressed_member_bytes=sum(x['bytes'] for x in checked),
                               exact_member_order=[x['name'] for x in checked]),
                  deterministic_zip=dict(timestamp=list(DATE_TIME),compression='DEFLATE',compression_level=COMPRESSION_LEVEL,
                                         file_permissions='regular 0644',creator_system='Unix',extra_fields=False,
                                         comments=False,directory_entries=False,zip64=False,
                                         runtime_python=platform.python_version(),zlib_compile_version=zlib.ZLIB_VERSION,
                                         zlib_runtime_version=zlib.ZLIB_RUNTIME_VERSION,
                                         scope='Byte-identical for pinned inputs, fixed metadata/order, and the recorded zlib implementation.'),
                  members=checked,official_receipts=receipts,
                  builder=dict(path=str(Path(__file__).resolve()),sha256=file_digest(__file__)),
                  verification_runs_started_by_builder=False,candidate_bytes_modified=False,
                  kaggle_submission_performed=False,observed_public_score=None,
                  seconds=time.monotonic()-started)
    args.manifest.parent.mkdir(parents=True,exist_ok=True)
    temporary = args.manifest.with_name(args.manifest.name+'.partial')
    temporary.write_text(json.dumps(report,indent=2)+'\n')
    os.replace(temporary,args.manifest)
    print(json.dumps({k:v for k,v in report.items() if k not in ('members','deterministic_zip')},indent=2),flush=True)
    if args.require_official_pass and not official_pass:
        raise SystemExit('Required bound full official PASS is not yet available for every component')


if __name__ == '__main__':
    main()
