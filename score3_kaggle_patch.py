#!/usr/bin/env python3
"""Patch an exact4096+score2 predecessor ZIP with the already verified inverse.

Use after score3_submit_worker.py, or on an attached exact4096+score2 output.
This performs packaging/checksums only; no quantum optimization or verification.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import sys
import urllib.request
import zipfile
import zlib

COMMIT = 'b46c2535f2743be0b5d558b02a76bd62ee919055'
INVERSE_URL = 'https://raw.githubusercontent.com/corcondor/gvqcc/' + COMMIT + '/score3_invsqrt_cache.kmb'
PINS = {'invsqrt.kmb': '684106f101730ca193627229920a0501bef9ea10ccfb34aa453fcf63edadb50a', 'dqi.kmb': '9a82f54226707185fa8a7f59a293e6af8ab7d59bff04a4d92919e4178d7d82f1', 'dfthcsos/submission.npz': '5f8dd37ac194b09b5ba870c4150a487b6665775375d9abc864d38b32a2cb7357', 'dfthcsos/angle_k_0.kmb': '39a74c931c745143d46ac3c3d7f76a84cc09982f0c7a9b2784e35e8cf0533b45', 'dfthcsos/angle_k_1.kmb': '753b1424a819fadcac324155a7cae1841f0ee977ce873f29c7e364c55cdd4f37', 'dfthcsos/angle_k_2.kmb': '487adc39d32a904021985241f80881fd90542fa35c0a379034fc88cc9ccfc337', 'dfthcsos/angle_k_3.kmb': '8e01cc596c3cbfd372f2b6d009e3b49c29ae9448eaf0d9f21f50d088d2404d6a', 'dfthcsos/angle_k_4.kmb': 'f9b6e68a119dc2b819c21812a136f3ae76eddb36d8964d1847bab68f880b3330', 'dfthcsos/angle_k_5.kmb': 'a17d6c663f66b3e8d9487b0b19f77075f5647ff240d258b6b7d37cb58997cd6c', 'dfthcsos/angle_k_6.kmb': '387f1a6095132fb6114682c8cc102a36cc93426860fa57b1fd972b65d4e88561', 'dfthcsos/angle_k_7.kmb': '146cb20a99a8c6005539df2b0c9f0eb11b33a71ab10d66480f51fd5590e53711', 'dfthcsos/angle_k_8.kmb': '0be2c2ec69d681f352c7e89fc94ed161f45b448110c9e617fe86181f72de646e', 'dfthcsos/angle_k_9.kmb': '3e31f13446a8a3c72bff3ac6c123d15f9c8b86039f505fe7b5510d7245246c99', 'dfthcsos/angle_k_10.kmb': '656d5eb283c54a2b934fdcf38fc56d7b3cc7b0607e7731c26eb15b574e74f5eb', 'dfthcsos/angle_k_11.kmb': 'd4eeedc38481610804ec2708e2fc02323b63d9f37487cec6cb9b42ed7c94c033', 'dfthcsos/angle_k_12.kmb': '61275eda03641d1a7b4052b36fa1df4383918f8986172e73a7f8dcaa817d0308', 'dfthcsos/angle_k_13.kmb': 'a4e43c2b183cf64de805701517fd0b56333dde662889579b824b4ee1ff0c3a72', 'dfthcsos/angle_k_14.kmb': '3b21fe0767295c6bd40c41e0c40ca1aeff02e54216ada02849c238ab66b70159'}
ORDER = list(PINS)
REFERENCE_ZIP_SHA = '5a3011d3f208a0bae3b1e1bfb9b763ac8c7201f4de35a74d772699949b971882'
CHUNK = 1 << 20


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(CHUNK),b''):
            h.update(block)
    return h.hexdigest()


def check(archive):
    if len(archive.infolist()) != 18 or set(archive.namelist()) != set(ORDER):
        raise ValueError('Expected exactly the 18 competition files, without duplicates')
    for info in archive.infolist():
        if info.is_dir() or info.flag_bits & 1:
            raise ValueError('Invalid ZIP member')


def patch(source,output,inverse_path=None):
    source,output = Path(source),Path(output)
    old_sha = digest(source)
    if inverse_path is None:
        with urllib.request.urlopen(INVERSE_URL,timeout=60) as response:
            inverse = response.read(198627)
    else:
        inverse = Path(inverse_path).read_bytes()
    if len(inverse) != 198626 or hashlib.sha256(inverse).hexdigest() != PINS['invsqrt.kmb']:
        raise ValueError('Downloaded inverse does not match the verified circuit')
    output.parent.mkdir(parents=True,exist_ok=True)
    temporary = output.with_name(output.name+'.score3-partial')
    if temporary.exists():
        raise FileExistsError(temporary)
    records=[]
    try:
        with zipfile.ZipFile(source) as old, zipfile.ZipFile(temporary,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=False) as new:
            check(old)
            for name in ORDER:
                info=zipfile.ZipInfo(name,(1980,1,1,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED;info._compresslevel=6
                info.create_system=3;info.create_version=20;info.extract_version=20
                info.external_attr=(stat.S_IFREG|0o644)<<16
                info.file_size=len(inverse) if name=='invsqrt.kmb' else old.getinfo(name).file_size
                h=hashlib.sha256();size=0
                stream=io.BytesIO(inverse) if name=='invsqrt.kmb' else old.open(name)
                with stream as src,new.open(info,'w',force_zip64=False) as dst:
                    for block in iter(lambda:src.read(CHUNK),b''):
                        h.update(block);size+=len(block);dst.write(block)
                if h.hexdigest()!=PINS[name]:
                    raise ValueError('Wrong predecessor member: '+name+'; run exact4096 score3_submit_worker first')
                records.append({'name':name,'sha256':h.hexdigest(),'bytes':size})
        with zipfile.ZipFile(temporary) as check_zip:
            check(check_zip)
            if check_zip.namelist()!=ORDER:
                raise ValueError('Unexpected output order')
            for row in records:
                h=hashlib.sha256();crc=0
                with check_zip.open(row['name']) as src:
                    for block in iter(lambda:src.read(CHUNK),b''):
                        h.update(block);crc=zlib.crc32(block,crc)
                if h.hexdigest()!=row['sha256'] or crc&0xffffffff!=check_zip.getinfo(row['name']).CRC:
                    raise ValueError('Output SHA/CRC mismatch: '+row['name'])
                row['crc32']=f'{crc&0xffffffff:08x}'
        new_sha=digest(temporary)
        # Source may equal output; replacement happens only after all checks.
        os.replace(temporary,output)
    except BaseException:
        if temporary.exists():temporary.unlink()
        raise
    receipt={'status':'MEMBER_IDENTICAL_TO_FULLY_VERIFIED_SCORE3_PACKAGE',
             'source_zip_sha256':old_sha,'output':str(output),'zip_sha256':new_sha,
             'zip_bytes':output.stat().st_size,'member_count':18,'members':records,
             'reference_zip_sha256':REFERENCE_ZIP_SHA,'exact_zip_bytes_reproduced':new_sha==REFERENCE_ZIP_SHA,
             'all_member_sha256_and_crc_pass':True,'inverse_url':INVERSE_URL,
             'zlib_runtime_version':zlib.ZLIB_RUNTIME_VERSION,
             'scope':'Exact previously verified circuit bytes; no new quantum verification or competition submission.',
             'submission_performed':False}
    output.with_name('score3_kaggle_patch_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k!='members'},indent=2),flush=True)
    return receipt


if __name__=='__main__':
    if 'ipykernel' in sys.modules:
        # Direct notebook-cell use must not parse ipykernel's -f argument.
        patch('/kaggle/working/submission.zip','/kaggle/working/submission.zip')
    else:
        p=argparse.ArgumentParser(description=__doc__)
        p.add_argument('--source',type=Path,default=Path('/kaggle/working/submission.zip'))
        p.add_argument('--output',type=Path,default=Path('/kaggle/working/submission.zip'))
        p.add_argument('--inverse-kmb',type=Path)
        a=p.parse_args();patch(a.source,a.output,a.inverse_kmb)
