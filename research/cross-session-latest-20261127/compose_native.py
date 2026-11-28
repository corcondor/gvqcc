#!/usr/bin/env python3
"""Construct a byte-preserving, per-task cross-session combination of two saved GVQCC archives.

This script does NOT claim a new official or Kaggle score, a DQI repair, or a global qubit width reduction.
The three task payloads are independently sourced from the pinned archive hashes below.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

V112_NAME = "GVQCC_V112_AllTasks_62078069_Verified_Rewrites_NOT_SUBMITTED.zip"
V110_NAME = "GVQCC_V110_Checked_Extended_62030143_AllTasks.zip"
V112_REPORT_NAME = "GVQCC_V112_Joint_Transport_Code_Proofs_and_Research.zip"
V110_MANIFEST_NAME = "GVQCC_V110_Review_Results_and_Manifest.json"

EXPECTED_ARCHIVE_SHA256 = {
    V112_NAME: "030588b9ceeb604cc20406ac3c56ad54e89af555a2ce8d3b1c5bc78a0ad6ee39",
    V110_NAME: "4e75bdf2a7b31c3ae70f91073eb15bd550ab1bd3137852e17581f7af9abd8919",
}


def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(4*1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_member(zf, name):
    h=hashlib.sha256()
    with zf.open(name) as src:
        for buf in iter(lambda: src.read(4*1024*1024), b""):
            h.update(buf)
    return h.hexdigest()


def main():
    pa=argparse.ArgumentParser()
    pa.add_argument("--v112",type=Path,required=True)
    pa.add_argument("--v110",type=Path,required=True)
    pa.add_argument("--v112-research",type=Path,required=True)
    pa.add_argument("--v110-manifest",type=Path,required=True)
    pa.add_argument("--out",type=Path,required=True)
    pa.add_argument("--manifest",type=Path,required=True)
    args=pa.parse_args()
    sources=[args.v112,args.v110]
    for p in sources:
        assert sha256_file(p)==EXPECTED_ARCHIVE_SHA256[p.name],f"archive SHA mismatch {p}"
    v110_report=json.loads(args.v110_manifest.read_text(encoding="utf-8"))
    with zipfile.ZipFile(args.v112_research) as rz:
        v112_report=json.loads(rz.read("FINAL_MANIFEST.json"))
        v112_results=json.loads(rz.read("RESULTS.json"))
    assert v112_results['chemistry']['new_ops']==299691
    assert v110_report['overview']['invsqrt']['after_ops']==27533
    assert v110_report['overview']['dqi']['after_ops']==61700935
    assert v112_results['chemistry']['expected_paid_per_pass']==v110_report['overview']['chemistry']['expected_paid_per_pass']==3262.5
    expected_total=299691+27533+61700935
    assert expected_total==62028159

    info={
        "schema":"gvqcc-cross-session-2026-11-27-1",
        "status":"BYTE_PRESERVING_TASK_COMPOSITION_REQUIRES_OFFICIAL_CROSS_REVERIFY",
        "kaggle_submitted":False,
        "new_official_score_claim":False,
        "v3260_verified":False,
        "claim_33_3465":"conditional estimate only; not verified",
        "known_dqi_value_failure_fixed":False,
        "source_archives": {p.name:{"sha256":EXPECTED_ARCHIVE_SHA256[p.name],"size":p.stat().st_size} for p in sources},
        "task_origins":{"dfthcsos":"V112","invsqrt.kmb":"V110_extended","dqi.kmb":"V110_extended"},
        "task_metrics":{"chemistry":{"instructions":299691,"width":405,"loader_width":128,"toffoli_per_pass":3262.5,"official_component_pass":True},"invsqrt":{"instructions":27533,"width":37,"official_component_pass":True},"dqi":{"instructions":61700935,"width":900,"static_paid":318584,"known_value_failures":True,"official_final_pass":False}},
        "total_instructions":expected_total,
        "component_checksums_verified":False,
        "output_archive":{"name":args.out.name},
        "files":{},
        "limitations":[
            "Each task payload is copied byte-for-byte from the independently checked source archive. No gates are edited.",
            "Cross-session combined ZIP has CRC/SHA checks; the unchanged official task verifiers were not rerun for this assembled ZIP.",
            "No new paid-gate savings, Q36 InvSqrt, Q888 DQI, DQI error repair, or new leaderboard score.",
            "The 3260/pass claim has no matching verified native source; remains excluded.",
            "Existing expected leaderboard estimate ~33.34224 is not an actual Kaggle submission.",
        ],
    }
    with zipfile.ZipFile(args.v112) as z112,zipfile.ZipFile(args.v110) as z110:
        files112=set(z112.namelist());files110=set(z110.namelist());assert files112==files110
        assert len(files112)==18
        assert sum(1 for n in files112 if n.startswith("dfthcsos/angle_k_"))==15
        for name in sorted(files112):
            z,origin=(z112,"V112") if name.startswith("dfthcsos/") else (z110,"V110_extended")
            h=sha256_member(z,name)
            if origin=="V112":
                source_meta=v112_report["files"][name]
            else:
                source_meta=v110_report["native_files"][name]
            assert h==source_meta["sha256"],(name,h,source_meta["sha256"])
            assert z.getinfo(name).file_size==source_meta["bytes"]
            info["files"][name]={"sha256":h,"bytes":z.getinfo(name).file_size,"origin":origin}
            if name.endswith('.kmb'):
                info["files"][name]["instructions"]=source_meta["ops"]
            if name=="dfthcsos/submission.npz":
                assert sha256_member(z110,name)==h,"npz mismatch across source archives"
        assert sum(v.get("instructions",0) for v in info["files"].values())==expected_total
        args.out.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(args.out,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as out:
            for name in sorted(files112):
                z=z112 if name.startswith("dfthcsos/") else z110
                # Fixed timestamp avoids host-dependent ZIP timestamps; compressed bytes are deterministic in a fixed zlib environment.
                m=zipfile.ZipInfo(name,date_time=(2026,11,27,0,0,0))
                m.compress_type=zipfile.ZIP_DEFLATED
                m.external_attr=(0o644&0xffff)<<16
                with z.open(name) as src, out.open(m,"w",force_zip64=True) as dst:
                    shutil.copyfileobj(src,dst,4*1024*1024)
    with zipfile.ZipFile(args.out) as out:
        assert set(out.namelist())==set(info['files'])
        assert out.testzip() is None, "CRC corruption"
        for name,v in info['files'].items():
            assert sha256_member(out,name)==v['sha256'],name
    info["component_checksums_verified"]=True
    info["output_archive"]["sha256"]=sha256_file(args.out)
    info["output_archive"]["bytes"]=args.out.stat().st_size
    args.manifest.write_text(json.dumps(info,ensure_ascii=False,indent=2)+"\n",encoding='utf-8')
    print(json.dumps({"status":info["status"],"total_instructions":expected_total,"file_count":len(info["files"]),"archive_sha256":info["output_archive"]["sha256"]},indent=2))

if __name__=="__main__":main()