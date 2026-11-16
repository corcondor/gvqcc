#!/usr/bin/env python3
"""Read-only public Kaggle frontier source and dataset provenance probe.

Source notebooks are parsed as data; downloaded Python is never executed.
This probe does not modify verifiers or competition submissions.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import urllib.request
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parent))
from frontier_hybrid_builder import decode_notebook, API

OUT=Path(os.getenv("FRONTIER_AUDIT_DIR","/tmp/gvqcc-frontier-probe"))
OUT.mkdir(parents=True,exist_ok=True)

def download(url,dest,limit):
    h=hashlib.sha256(); start=time.monotonic()
    request=urllib.request.Request(url,headers={
        "User-Agent":"gvqcc-public-provenance-check/1.0","Accept":"application/json, application/zip, */*"})
    with urllib.request.urlopen(request,timeout=120) as r, dest.open("xb") as f:
        while True:
            buf=r.read(1<<20)
            if not buf: break
            if f.tell()+len(buf)>limit: raise ValueError("Source exceeds byte cap")
            h.update(buf);f.write(buf)
        content_type=r.headers.get("Content-Type","")
    return {"status":"OK","bytes":dest.stat().st_size,"sha256":h.hexdigest(),
            "content_type":content_type,"elapsed_seconds":round(time.monotonic()-start,2)}

def main():
    report={"notebook":None,"datasets":[]}
    try:
        p=OUT/"maoxin123_v27_pull.json"
        item=download(API,p,5_000_000)
        pins,inv=decode_notebook(p.read_bytes())
        item.update(invsqrt_sha256=hashlib.sha256(inv).hexdigest(),
                    invsqrt_bytes=len(inv),pinned_file_count=len(pins),
                    pins={k:{"sha256":v[0],"bytes":v[1]} for k,v in sorted(pins.items())})
        (OUT/"public_invsqrt.kmb").write_bytes(inv)
        report["notebook"]=item
    except Exception as e:
        report["notebook"]={"status":"ERROR","error":str(e)}
    datasets=["maoxin123/qcc-frontier-dqi-chem-mirror","masumhuq/qai-c11-composite-2809"]
    for dataset in datasets:
        key=dataset.replace("/","_")
        for kind,endpoint in [
            ("metadata",f"https://www.kaggle.com/api/v1/datasets/view/{dataset}"),
            ("download",f"https://www.kaggle.com/api/v1/datasets/download/{dataset}")
        ]:
            target=OUT/(key+"_"+kind+(".zip" if kind=="download" else ".json"))
            try:
                info=download(endpoint,target,250_000_000 if kind=="download" else 5_000_000)
                if kind=="metadata":
                    d=json.loads(target.read_text())
                    info["resource_names"]=[x.get("ref",x.get("name")) for x in d.get("resources",[])][:40]
                else:
                    with zipfile.ZipFile(target) as z:
                        files=z.infolist()
                        info["zip_member_count"]=len(files)
                        info["members"]=[{"path":x.filename,"bytes":x.file_size} for x in files[:40]]
                        if report["notebook"] and "pins" in report["notebook"]:
                            matches=[]
                            for x in files:
                                if x.is_dir() or x.file_size>100_000_000: continue
                                with z.open(x) as f:
                                    digest=hashlib.sha256()
                                    for b in iter(lambda:f.read(1<<20),b""): digest.update(b)
                                for k,record in report["notebook"]["pins"].items():
                                    if record["sha256"]==digest.hexdigest():
                                        matches.append({"path":x.filename,"pinned_name":k})
                            info["pinned_sha_matches"]=matches
                report["datasets"].append({"dataset":dataset,"kind":kind,**info})
            except Exception as e:
                report["datasets"].append({"dataset":dataset,"kind":kind,"status":"ERROR","error":str(e)})
    (OUT/"probe.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(report,indent=2,ensure_ascii=False),flush=True)
    if report["notebook"]["status"]!="OK": raise SystemExit("Notebook source pin failed")

if __name__=="__main__":main()
