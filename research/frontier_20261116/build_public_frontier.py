#!/usr/bin/env python3
"""Build an exact, SHA-pinned public 28.09 circuit portfolio.

All source files are public Kaggle Apache-2.0 resources. No downloaded Python
is run, no random-seed search is performed and no Kaggle submission is made.
"""
import argparse
import hashlib
import json
import lzma
from pathlib import Path, PurePosixPath
import zipfile
from frontier_hybrid_builder import decode_notebook, sha

def file_hash(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def build(source, mirror, output):
    pins,inv=decode_notebook(source.read_bytes())
    if output.exists():raise FileExistsError(output)
    stage=output.with_name(output.name+".incomplete")
    if stage.exists():raise FileExistsError(stage)
    expected={"invsqrt.kmb":sha(inv),**{k:p[0] for k,p in pins.items()}}
    members={"invsqrt.kmb":{"sha256":sha(inv),"bytes":len(inv)}}
    try:
        with zipfile.ZipFile(mirror) as upstream, zipfile.ZipFile(stage,"x",compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as target:
            names=upstream.namelist()
            if len(names)!=len(set(names)):raise ValueError("Duplicate source ZIP member")
            target.writestr("invsqrt.kmb",inv)
            for dest in sorted(pins):
                required_hash,size=pins[dest]
                if dest!="dqi.kmb":
                    path=PurePosixPath(dest).name
                    if path not in names:raise FileNotFoundError(path)
                    if size>5_000_000:raise ValueError("Unexpected chemistry input size")
                    with upstream.open(path) as f:data=f.read(5_000_001)
                    if len(data)!=size or sha(data)!=required_hash:raise ValueError("Public SHA mismatch "+dest)
                    target.writestr(dest,data)
                    members[dest]={"sha256":sha(data),"bytes":len(data)}
                else:
                    if "dqi.kmb.xz" not in names:raise FileNotFoundError("dqi.kmb.xz")
                    count=0; digest=hashlib.sha256()
                    with upstream.open("dqi.kmb.xz") as xz, lzma.LZMAFile(xz,"rb") as unxz, target.open("dqi.kmb","w",force_zip64=True) as dst:
                        while True:
                            block=unxz.read(1<<20)
                            if not block:break
                            count+=len(block)
                            if count>size:raise ValueError("DQI compressed bomb / wrong size")
                            digest.update(block);dst.write(block)
                    if count!=size or digest.hexdigest()!=required_hash:raise ValueError("DQI decompressed hash mismatch")
                    members[dest]={"sha256":required_hash,"bytes":count}
            target.comment=b"Public v27: maoxin123, Boristown, Syed et al. Apache-2.0 / source licenses available in original dataset."
        with zipfile.ZipFile(stage) as zipped:
            if set(zipped.namelist())!=set(expected):raise ValueError("Submission member set mismatch")
            for name,wanted in expected.items():
                h=hashlib.sha256()
                with zipped.open(name) as src:
                    for block in iter(lambda:src.read(1<<20),b""):h.update(block)
                if h.hexdigest()!=wanted:raise ValueError("Packaged SHA mismatch "+name)
        stage.rename(output)
    except BaseException:
        stage.unlink(missing_ok=True)
        raise
    receipt={"status":"PUBLIC_MEMBER_BYTES_VERIFIED_ONLY","zip":str(output),
       "zip_sha256":file_hash(output),"zip_bytes":output.stat().st_size,
       "members":members,"member_count":len(members),
       "public_notebook":"maoxin123/qcc-v27-a-44-qubit-invsqrt-on-the-28-09-frontier",
       "original_public_score":28.09486,"official_new_composite_qualification":False,
       "kaggle_submitted":False}
    output.with_suffix(".json").write_text(json.dumps(receipt,indent=2)+"\n")
    return receipt

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True,type=Path)
    p.add_argument("--mirror",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    print(json.dumps(build(args.source,args.mirror,args.output),indent=2),flush=True)
