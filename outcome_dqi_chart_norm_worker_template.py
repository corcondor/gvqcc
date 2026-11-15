#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Offline deterministic packaging of the qualified projective-chart repair.

Attach the pinned public-v27 portfolio and a portfolio containing pinned9a82
DQI. This script uses only Python's standard library. It makes submission.zip
for review/the next quota slot. It never submits, accesses credentials, or uses
the network, and it does not rerun scientific verification.
"""
import argparse
import base64
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time
import zipfile

PATCH_B64 = '__PATCH_B64__'
PATCH_SHA256 = '__PATCH_SHA256__'
QUALIFICATION_B64 = '__QUALIFICATION_B64__'
QUALIFICATION_SHA256 = '__QUALIFICATION_SHA256__'
SCOPE_B64 = '__SCOPE_B64__'
SCOPE_SHA256 = '__SCOPE_SHA256__'
PUBLIC_B64 = '__PUBLIC_B64__'
PUBLIC_SHA256 = '__PUBLIC_SHA256__'
PROOF_B64 = '__PROOF_B64__'
PROOF_SHA256 = '__PROOF_SHA256__'
NOTICE_B64 = '__NOTICE_B64__'
LICENSE_B64 = '__LICENSE_B64__'
CHUNK=4<<20


def require(ok,message):
    if not ok:raise RuntimeError(message)


def digest(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def decoded(value,expected=None):
    data=base64.b64decode(value,validate=True)
    if expected:require(hashlib.sha256(data).hexdigest()==expected,'Embedded artifact hash mismatch')
    return data


def emit(event,**data):
    print(json.dumps({'event':event,**data},sort_keys=True),flush=True)


def apply_patch(source,target,patch):
    """Stream an exact byte patch into a new file, with both whole-file hashes."""
    source,target=Path(source),Path(target)
    require(source.resolve()!=target.resolve() and not target.exists(),'Output must be a new file')
    require(source.stat().st_size==patch['input_bytes'],'Wrong input KMB size')
    before_hash=hashlib.sha256();after_hash=hashlib.sha256();cursor=count=0
    try:
        with source.open('rb') as f,target.open('xb') as g:
            for row in patch['replacements']:
                remaining=row['input_offset']-cursor
                require(remaining>=0,'Overlapping or unordered patch')
                while remaining:
                    block=f.read(min(CHUNK,remaining));require(bool(block),'Truncated input')
                    before_hash.update(block);after_hash.update(block);g.write(block)
                    remaining-=len(block);count+=len(block)
                old=f.read(row['input_bytes'])
                require(len(old)==row['input_bytes'],'Truncated patch region')
                require(hashlib.sha256(old).hexdigest()==row['input_sha256'],'Wrong old patch region')
                before_hash.update(old)
                new=decoded(row['replacement_b64'],row['replacement_sha256'])
                require(len(new)==row['replacement_bytes'],'Wrong new patch region length')
                after_hash.update(new);g.write(new);count+=len(new)
                cursor=row['input_offset']+row['input_bytes']
            for block in iter(lambda:f.read(CHUNK),b''):
                before_hash.update(block);after_hash.update(block);g.write(block);count+=len(block)
        require(before_hash.hexdigest()==patch['input_sha256'],'Wrong whole input SHA256')
        require(after_hash.hexdigest()==patch['output_sha256'],'Wrong whole output SHA256')
        require(count==patch['output_bytes'],'Wrong output KMB size')
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    return {'sha256':after_hash.hexdigest(),'bytes':count}


def member_hash(z,name,expected):
    info=z.getinfo(name)
    require(info.file_size==expected['bytes'] and not info.is_dir() and not (info.flag_bits&1),
            'Wrong member size or mode: '+name)
    h=hashlib.sha256();count=0
    with z.open(info) as f:
        for block in iter(lambda:f.read(CHUNK),b''):h.update(block);count+=len(block)
    require(h.hexdigest()==expected['sha256'] and count==expected['bytes'],'Wrong member SHA256: '+name)
    return {'sha256':h.hexdigest(),'bytes':count,'crc32':'%08x'%info.CRC}


def verify_public_members(path,public):
    with zipfile.ZipFile(path) as z:
        names=z.namelist();require(len(names)==18 and len(set(names))==18,'Expected exactly18 unique members')
        require(set(names)==set(public['members']),'Wrong portfolio member set')
        for name,expected in public['members'].items():
            if name!='dqi.kmb':member_hash(z,name,expected)


def has_pinned_dqi(path,patch):
    try:
        if Path(path).suffix.lower()=='.kmb':
            return Path(path).stat().st_size==patch['input_bytes'] and digest(path)==patch['input_sha256']
        with zipfile.ZipFile(path) as z:
            if z.namelist().count('dqi.kmb')!=1:return False
            member_hash(z,'dqi.kmb',{'bytes':patch['input_bytes'],'sha256':patch['input_sha256']})
            return True
    except (RuntimeError,zipfile.BadZipFile,KeyError):return False


def input_files(root,suffix):
    """Follow Kaggle dataset mount symlinks without following a cycle twice."""
    seen=set()
    for directory,dirs,files in os.walk(root,followlinks=True):
        real=os.path.realpath(directory)
        if real in seen:
            dirs[:]=[]
            continue
        seen.add(real);dirs.sort()
        for name in sorted(files):
            if name.lower().endswith(suffix):yield Path(directory)/name


def find_inputs(root,public,patch,public_path=None,dqi_path=None):
    public_path=Path(public_path) if public_path else None
    dqi_path=Path(dqi_path) if dqi_path else None
    if public_path:verify_public_members(public_path,public)
    if dqi_path:require(has_pinned_dqi(dqi_path,patch),'Explicit donor is not pinned9a82')
    if public_path and dqi_path:return public_path,dqi_path
    paths=sorted(input_files(root,'.zip'))
    for path in paths:
        if public_path is None:
            try:verify_public_members(path,public);public_path=path
            except (RuntimeError,zipfile.BadZipFile,KeyError):pass
        if dqi_path is None and has_pinned_dqi(path,patch):dqi_path=path
        if public_path and dqi_path:break
    if dqi_path is None:
        for path in sorted(input_files(root,'.kmb')):
            if has_pinned_dqi(path,patch):dqi_path=path;break
    require(public_path is not None,'Attach a ZIP with the pinned17 public-v27 non-DQI members')
    require(dqi_path is not None,'Attach the pinned9a82 DQI output or a ZIP containing it')
    return public_path,dqi_path


def extract_dqi(source,target,patch):
    if Path(source).suffix.lower()=='.kmb':
        shutil.copyfile(source,target)
    else:
        with zipfile.ZipFile(source) as z,z.open('dqi.kmb') as f,Path(target).open('xb') as g:
            shutil.copyfileobj(f,g,CHUNK)
    require(Path(target).stat().st_size==patch['input_bytes'] and digest(target)==patch['input_sha256'],
            'Extracted donor DQI hash mismatch')


def package(public_path,dqi,target,expected):
    with zipfile.ZipFile(public_path) as base,zipfile.ZipFile(target,'x',
            compression=zipfile.ZIP_DEFLATED,compresslevel=6) as out:
        for name in sorted(expected):
            info=zipfile.ZipInfo(name,(2026,11,15,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.create_system=3;info.external_attr=0o100644<<16
            with out.open(info,'w',force_zip64=True) as g:
                if name=='dqi.kmb':
                    with Path(dqi).open('rb') as f:shutil.copyfileobj(f,g,CHUNK)
                else:
                    with base.open(name) as f:shutil.copyfileobj(f,g,CHUNK)
    with zipfile.ZipFile(target) as z:
        require(len(z.namelist())==18 and set(z.namelist())==set(expected),'Output member set changed')
        return {n:member_hash(z,n,v) for n,v in sorted(expected.items())}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input-root',default=os.environ.get('QCC_INPUT','/kaggle/input'))
    p.add_argument('--output-root',default=os.environ.get('QCC_WORKING','/kaggle/working'))
    p.add_argument('--public',default=os.environ.get('QCC_PUBLIC_ZIP'))
    p.add_argument('--dqi',default=os.environ.get('QCC_DQI_INPUT'))
    p.add_argument('--patch-only',action='store_true')
    args=p.parse_args(argv);begun=time.monotonic()
    patch_bytes=decoded(PATCH_B64,PATCH_SHA256);patch=json.loads(gzip.decompress(patch_bytes))
    qbytes=decoded(QUALIFICATION_B64,QUALIFICATION_SHA256);qualification=json.loads(qbytes)
    scope_bytes=decoded(SCOPE_B64,SCOPE_SHA256);scope=json.loads(scope_bytes)
    public=json.loads(decoded(PUBLIC_B64,PUBLIC_SHA256))
    proof=decoded(PROOF_B64,PROOF_SHA256)
    require(qualification['status']=='PASS' and qualification['verified_shots']==102400,'No fullPASS qualification')
    require(qualification['circuit_sha256']==patch['output_sha256'],'Qualification covers another circuit')
    require(scope['candidate_sha256']==patch['output_sha256'] and
            scope['official_receipt_sha256']==QUALIFICATION_SHA256,'Wrong qualification scope binding')
    require(qualification['num_qubits']==889 and qualification['max_toffoli_count']==382920,'Wrong qualified resources')
    require(qualification.get('seed') is None and qualification.get('salt')=='' and qualification['log2_delta']==-128,
            'Qualification is not the default verification')
    require(qualification['verifier_sha256']=='f14274bc0943fb9769ddb01131be6063191a15009fe1caf1d4bdd9fd25194e65',
            'Wrong verifier qualification')
    output=Path(args.output_root);output.mkdir(parents=True,exist_ok=True)
    if args.patch_only:
        require(args.dqi is not None,'--patch-only requires --dqi')
        require(has_pinned_dqi(args.dqi,patch),'Wrong pinned donor')
        with tempfile.TemporaryDirectory(prefix='qcc-chart-patch-') as folder:
            donor=Path(folder)/'donor.kmb';extract_dqi(args.dqi,donor,patch)
            changed=apply_patch(donor,output/'dqi.kmb',patch)
        emit('patched',**changed);return
    public_path,donor_path=find_inputs(args.input_root,public,patch,args.public,args.dqi)
    emit('inputs_verified',public=str(public_path),donor=str(donor_path),patch_sha256=PATCH_SHA256)
    require(not (output/'submission.zip').exists(),'Output submission.zip already exists')
    expected={n:dict(s) for n,s in public['members'].items()}
    expected['dqi.kmb']={'sha256':patch['output_sha256'],'bytes':patch['output_bytes']}
    with tempfile.TemporaryDirectory(prefix='qcc-chart-package-') as folder:
        temp=Path(folder);donor=temp/'donor.kmb';changed=temp/'dqi.kmb';archive=temp/'submission.zip'
        extract_dqi(donor_path,donor,patch);apply_patch(donor,changed,patch)
        emit('dqi_patched',sha256=patch['output_sha256'],bytes=patch['output_bytes'])
        members=package(public_path,changed,archive,expected)
        differences=[n for n in members if members[n]['sha256']!=public['members'][n]['sha256']]
        require(differences==['dqi.kmb'],'Unexpected non-DQI modification')
        archive_sha=digest(archive);archive_bytes=archive.stat().st_size
        shutil.copyfile(archive,output/'submission.zip')
    receipt={'status':'QUALIFIED_EXACT_PORTFOLIO_PACKAGED_NOT_SUBMITTED',
        'submission_performed':False,'public_score':None,'upstream_public':public,
        'source_public_zip_sha256':digest(public_path),'source_dqi_sha256':patch['input_sha256'],
        'patched_dqi_sha256':patch['output_sha256'],'patch_sha256':PATCH_SHA256,
        'qualification_sha256':QUALIFICATION_SHA256,'qualification':qualification,
        'qualification_scope_sha256':SCOPE_SHA256,'qualification_scope':scope,
        'proof_sha256':PROOF_SHA256,'members':members,'preserved_non_dqi_members':17,
        'changed_members':differences,'submission_zip_sha256':archive_sha,'submission_zip_bytes':archive_bytes,
        'scope':'Exact SHA/size/CRC packaging. Scientific verification is the embedded prior receipt, not rerun here.',
        'seconds':time.monotonic()-begun}
    (output/'outcome_dqi_chart_norm_packaging_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    (output/'outcome_dqi_chart_norm_full_verification.json').write_bytes(qbytes)
    (output/'outcome_dqi_chart_norm_qualification_scope.json').write_bytes(scope_bytes)
    (output/'outcome_dqi_chart_norm_proof.md').write_bytes(proof)
    (output/'SOURCES_AND_LICENSES.md').write_bytes(decoded(NOTICE_B64))
    (output/'LICENSE_Apache_2.0.txt').write_bytes(decoded(LICENSE_B64))
    emit('ready_for_next_quota',submission_zip_sha256=archive_sha,bytes=archive_bytes,
         submitted=False,seconds=time.monotonic()-begun)


if __name__=='__main__':main([] if 'ipykernel' in sys.modules else None)
