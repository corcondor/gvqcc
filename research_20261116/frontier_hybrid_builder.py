#!/usr/bin/env python3
"""Rebuild the 28.09 public-invsqrt/public-chemistry + independently verified DQI562 hybrid.

The original Kaggle notebook is parsed as DATA using Python ast.literal_eval,
not executed. All 18 member SHA-256s are checked. Archive is a candidate only:
neither an official verification receipt nor a Kaggle competition submission.

Example:
  python research_20261116/frontier_hybrid_builder.py \
    --public-notebook-raw /path/to/maoxin_kaggle_pull.json \
    --public-chemistry-dir /path/to/public_dfthcsos \
    --own-verified-zip /path/to/submission_graph562.zip \
    --output /tmp/frontier_hybrid_candidate.zip

Omit --public-notebook-raw to fetch the public API notebook source.
Download the chemistry KMBs and NPZ separately from the notebook's public input
dataset, and preserve upstream notices, licenses and authors' attributions.
"""
from __future__ import annotations
import argparse
import ast
import base64
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile
import zlib

API='https://www.kaggle.com/api/v1/kernels/pull/maoxin123/qcc-v27-a-44-qubit-invsqrt-on-the-28-09-frontier'
INV_SHA='f2cdab0b7afc2e76aca12451113ef618e6f7e575a35a29f58264602dafb48726'
OWN_DQI_SHA='102716664a883baaab1874dc176c52dde23451c99de3006cb261832130a53fd6'
OWN_ZIP_SHA='f5496ab49daf607feb75c057f464804c3e2e51e59bcf915b62854befeaf0078f'

def sha_file(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):h.update(block)
    return h.hexdigest()

def notebook_literal(cell,name):
    try:tree=ast.parse(cell)
    except SyntaxError:return None
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(
                isinstance(t,ast.Name) and t.id==name for t in node.targets):
            return ast.literal_eval(node.value)
    return None

def parse_public_source(raw):
    doc=json.loads(raw)
    blob=doc.get('blob',{})
    source=blob.get('source') or blob.get('sourceNullable')
    if not source:raise ValueError('No notebook source found')
    nb=json.loads(source)
    pins=None;embedded=None
    for cell in nb.get('cells',[]):
        if cell.get('cell_type')!='code':continue
        script=cell.get('source','')
        if isinstance(script,list):script=''.join(script)
        if 'PINNED' in script and pins is None:
            pins=notebook_literal(script,'PINNED')
        if 'INV =' in script and embedded is None:
            embedded=notebook_literal(script,'INV')
    needed={'dqi.kmb','dfthcsos/submission.npz'}
    needed|={f'dfthcsos/angle_k_{k}.kmb' for k in range(15)}
    if not isinstance(pins,dict) or set(pins)!=needed or not isinstance(embedded,str):
        raise ValueError('Source structure changed: manual review required')
    if len(embedded)>2_000_000:raise ValueError('Invsqrt compressed payload too large')
    inv=zlib.decompress(base64.b64decode(embedded,validate=True))
    if len(inv)>10_000_000 or hashlib.sha256(inv).hexdigest()!=INV_SHA:
        raise ValueError('Wrong public invsqrt SHA-256')
    for name,v in pins.items():
        if not isinstance(v,(tuple,list)) or len(v)!=2 or not isinstance(v[0],str) or len(v[0])!=64 or not isinstance(v[1],int) or v[1]<=0:
            raise ValueError(f'Invalid PINNED member {name}')
    return pins,inv

@contextmanager
def own_stream(kmb,archive):
    if (kmb is None)==(archive is None):
        raise ValueError('Provide exactly one own DQI source')
    if kmb:
        with kmb.open('rb') as f:yield f
    else:
        with zipfile.ZipFile(archive) as z:
            if 'dqi.kmb' not in z.namelist():raise ValueError('Missing own DQI member')
            with z.open('dqi.kmb') as f:yield f

def public_member(root,name,expected):
    p=root/name
    if not p.is_file():p=root/name.replace('/','__')
    if not p.is_file() or p.is_symlink():
        raise FileNotFoundError(f'Public file missing: {name}')
    if p.stat().st_size!=expected[1] or sha_file(p)!=expected[0]:
        raise ValueError(f'Public component SHA/size mismatch: {name}')
    return p

def build(raw,public_chem,own_dqi,own_archive,output):
    pins,inv=parse_public_source(raw)
    chem={name:public_member(public_chem,name,expect)
          for name,expect in pins.items() if name!='dqi.kmb'}
    if own_archive and sha_file(own_archive)!=OWN_ZIP_SHA:
        raise ValueError('Own verified ZIP SHA mismatch')
    if output.exists():raise FileExistsError(f'{output} already exists')
    output.parent.mkdir(parents=True,exist_ok=True)
    wanted={'dqi.kmb':OWN_DQI_SHA,'invsqrt.kmb':INV_SHA,
            **{name:pins[name][0] for name in chem}}
    try:
        with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED,allowZip64=True) as z:
            z.writestr('invsqrt.kmb',inv)
            for name,p in sorted(chem.items()):z.write(p,name)
            hd=hashlib.sha256()
            with own_stream(own_dqi,own_archive) as incoming, z.open('dqi.kmb','w',force_zip64=True) as dest:
                for block in iter(lambda:incoming.read(1<<20),b''):
                    hd.update(block);dest.write(block)
            if hd.hexdigest()!=OWN_DQI_SHA:raise ValueError('Own DQI SHA mismatch')
            z.comment=(b'Public invsqrt: maoxin123/Syed Asad Ali (Apache 2.0); '
                       b'chemistry: marculera/boristown; DQI 562: corcondor. '
                       b'Keep external source credits and full license texts. '
                       b'No full official verification performed on this hybrid.')
        with zipfile.ZipFile(output) as z:
            if set(z.namelist())!=set(wanted) or z.testzip() is not None:
                raise ValueError('Archive shape or CRC failure')
            for name,want in wanted.items():
                hh=hashlib.sha256()
                with z.open(name) as f:
                    for block in iter(lambda:f.read(1<<20),b''):hh.update(block)
                if hh.hexdigest()!=want:raise ValueError('Archive member hash mismatch: '+name)
    except BaseException:
        output.unlink(missing_ok=True)
        raise
    record={'status':'CANDIDATE_ZIP_HASH_CHECKED_ONLY','member_count':len(wanted),
            'zip_sha256':sha_file(output),'members':wanted,'source_notebook_sha256':hashlib.sha256(raw).hexdigest(),
            'full_official_verification':False,'kaggle_submitted':False}
    output.with_suffix('.json').write_text(json.dumps(record,indent=2)+'\n')
    return record

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--public-notebook-raw',type=Path)
    ap.add_argument('--public-chemistry-dir',type=Path,required=True)
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--own-dqi-kmb',type=Path)
    g.add_argument('--own-verified-zip',type=Path)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args()
    if a.public_notebook_raw:raw=a.public_notebook_raw.read_bytes()
    else:
        with urllib.request.urlopen(urllib.request.Request(API,headers={'User-Agent':'GVQCC-frontier-audit/1.0'}),timeout=40) as f:
            raw=f.read(3_000_000)
    print(json.dumps(build(raw,a.public_chemistry_dir,a.own_dqi_kmb,a.own_verified_zip,a.output),indent=2))

if __name__=='__main__':main()
