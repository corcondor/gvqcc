#!/usr/bin/env python3
"""Assemble a candidate using newer public 28.10729 *local* frontier circuits.

Fetches only two SHA12-named public KMB files and their public manifest from
manwithacat's Apache-2.0 archive; retains the SHA-pinned C44 chemistry family.
This is a new candidate portfolio, not a new verified or observed Kaggle score.
The archive's version-131 note reports a best-per-task local GM of 28.10729.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import shutil
import urllib.request
import zipfile

ARCHIVE = "https://www.kaggle.com/api/v1/datasets/download/manwithacat/vqcc-apache-public-circuits/"
TARGETS = {
    "invsqrt": ("0af21cb82332", "circuits%2Finvsqrt%2F0af21cb82332.kmb", 5_000_000),
    "dqi": ("66b4f18b8527", "circuits%2Fdqi%2F66b4f18b8527.kmb", 650_000_000),
}
REF = {"invsqrt": 2076774.233715282, "dqi": 24439463583672.93,
       "dfthcsos": 3355599588.3155365}
CHEM_COST = 294762632.0817748
SOURCE_NOTE = ("VQCC public circuits (Apache-2.0) dataset v131: "
               "best-per-task local GM 28.10729 (not an observed Kaggle LB).")


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def download(url, path, limit):
    request = urllib.request.Request(url, headers={"User-Agent": "GVQCC-frontier-provenance/1"})
    with urllib.request.urlopen(request, timeout=120) as src, path.open("xb") as dst:
        count = 0
        while block := src.read(1 << 20):
            count += len(block)
            if count > limit:
                raise ValueError("Exceeded public source size cap: " + url)
            dst.write(block)
    return {"sha256": sha(path), "bytes": path.stat().st_size}


def manifest_rows(path):
    raw = path.read_bytes()
    if raw[:4] == b"PK\\x03\\x04":
        with zipfile.ZipFile(path) as z:
            names = [n for n in z.namelist() if n.endswith("manifest.csv")]
            if len(names) != 1:
                raise ValueError("Unexpected manifest archive")
            raw = z.read(names[0])
    return list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))


def find_row(rows, task, prefix):
    matches = [row for row in rows if str(row.get("task", "")).lower() == task
               and (str(row.get("sha12", "")).lower() == prefix or
                    str(row.get("sha256", "")).lower().startswith(prefix))]
    if len(matches) != 1:
        raise ValueError(f"Manifest has {len(matches)} rows for {task} {prefix}")
    return matches[0]


def get_cost(row):
    for key in ("score", "cost", "verified_score", "verifier_score", "verifier_cost"):
        try:
            v = float(row.get(key, ""))
        except (TypeError, ValueError):
            continue
        if math.isfinite(v) and v > 1000:
            return v, key
    return None, None


def gm(inv, dqi, chem):
    return math.exp(sum(math.log(REF[t] / v) for t, v in (
        ("invsqrt", inv), ("dqi", dqi), ("dfthcsos", chem))) / 3)


def build(baseline, manifest, circuits, output):
    rows = manifest_rows(manifest)
    checked = {}
    for task, (prefix, _, _) in TARGETS.items():
        row = find_row(rows, task, prefix)
        actual = sha(circuits[task])
        expected = str(row.get("sha256", "")).lower()
        if len(expected) != 64 or actual != expected or not actual.startswith(prefix):
            raise ValueError(f"Manifest SHA mismatch {task}: {actual}, expected {expected}")
        cost, cost_field = get_cost(row)
        checked[task] = {"sha256": actual, "bytes": circuits[task].stat().st_size,
                         "manifest_cost": cost, "cost_field": cost_field,
                         "manifest_row": row}
    stage = output.with_name(output.name + ".incomplete")
    if output.exists() or stage.exists():
        raise FileExistsError("Candidate already exists")
    try:
        with zipfile.ZipFile(baseline) as source, zipfile.ZipFile(
            stage, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True
        ) as target:
            names = source.namelist()
            if len(names) != 18 or len(set(names)) != 18:
                raise ValueError("Expected unique 18-member baseline")
            if "invsqrt.kmb" not in names or "dqi.kmb" not in names:
                raise ValueError("Missing baseline tasks")
            for name in sorted(names):
                with target.open(name, "w", force_zip64=True) as dst:
                    if name == "invsqrt.kmb":
                        with circuits["invsqrt"].open("rb") as src:
                            shutil.copyfileobj(src, dst, 1 << 20)
                    elif name == "dqi.kmb":
                        with circuits["dqi"].open("rb") as src:
                            shutil.copyfileobj(src, dst, 1 << 20)
                    else:
                        with source.open(name) as src:
                            shutil.copyfileobj(src, dst, 1 << 20)
            target.comment = b"Public VQCC circuit credits: manwithacat archive v131; see sidecar report"
        with zipfile.ZipFile(stage) as z:
            if set(z.namelist()) != set(names) or z.testzip() is not None:
                raise ValueError("Candidate ZIP integrity failure")
        stage.rename(output)
    except BaseException:
        stage.unlink(missing_ok=True)
        raise
    inv_cost, dqi_cost = checked["invsqrt"]["manifest_cost"], checked["dqi"]["manifest_cost"]
    report = {
        "status": "PUBLIC_SOURCE_HASHED_NOT_INDEPENDENTLY_REVERIFIED",
        "source_note": SOURCE_NOTE, "archive_manifest_sha256": sha(manifest),
        "source_baseline_sha256": sha(baseline),
        "candidate_zip": str(output), "candidate_zip_sha256": sha(output),
        "component_sources": checked,
        "chemistry_source": "bdae290f, public v3 mirror; unchanged from baseline",
        "chemistry_cost_author_reported": CHEM_COST,
        "gm_if_manifest_costs_reproduce": gm(inv_cost, dqi_cost, CHEM_COST)
        if inv_cost is not None and dqi_cost is not None else None,
        "official_all_three_verified": False, "kaggle_submitted": False,
    }
    output.with_suffix(".json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "component_sources"}, indent=2), flush=True)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--baseline-zip", type=Path, required=True)
    p.add_argument("--work-dir", type=Path, required=True)
    args = p.parse_args()
    work = args.work_dir
    work.mkdir(parents=True, exist_ok=False)
    manifest = work / "manifest.csv"
    print(json.dumps({"manifest": download(ARCHIVE + "manifest.csv", manifest, 5_000_000)}), flush=True)
    rows = manifest_rows(manifest)
    circuits = {}
    for task, (prefix, path, limit) in TARGETS.items():
        row = find_row(rows, task, prefix)
        print(json.dumps({"task": task, "sha12": prefix,
                          "manifest_fields": list(row), "manifest_row": row}), flush=True)
        target = work / (task + ".kmb")
        print(json.dumps({task: download(ARCHIVE + path, target, limit)}), flush=True)
        circuits[task] = target
    build(args.baseline_zip, manifest, circuits, work / "submission_latest_public_candidate.zip")


if __name__ == "__main__":
    main()
