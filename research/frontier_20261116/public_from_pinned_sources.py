#!/usr/bin/env python3
"""Build pinned 28.09486 public source bytes from two independent Kaggle datasets.

Uses file-specific immutable SHA12 archive lookup for f2cd invsqrt, and the
maoxin123 mirror for the 15 angle loaders, C44 factor and ccc2 DQI.
No downloaded Python executes. All 18 member SHA256s are checked.
This is provenance only; no new official verification or submission.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import lzma
from pathlib import Path
import shutil
import urllib.request
import zipfile

INV_URL = ("https://www.kaggle.com/api/v1/datasets/download/manwithacat/"
           "vqcc-apache-public-circuits/circuits%2Finvsqrt%2Ff2cdab0b7afc.kmb")
MIRROR_URL = "https://www.kaggle.com/api/v1/datasets/download/maoxin123/qcc-frontier-dqi-chem-mirror"
INV_SHA = "f2cdab0b7afc2e76aca12451113ef618e6f7e575a35a29f58264602dafb48726"
DQI_SHA = "ccc2ab84ed713901c5642c58890fc664a16a4842c1ebdc80edb56b11c96d6c8d"
CHEM_SHA = "f6e12f023a20f7aa44b7e981bc399d535c3920a2bc579bcea0aa713a6337367d"
ANGLE_PINS = [["aed6aa7cde8cefae06376546c276208a667a1a402ebfe9e57cb33881868ab089",415169],["72b79b56514e657650ed3258d90e7a533568ade86db407990a34bfb4380b6e60",421737],["42ea507daa22d0464e16d8f8d8f091e684d025998a32b574fee34672414b18ad",371346],["423968d4ab8219b164a27284c4b889b67a864ead9322b7703599fc839d7d8035",368418],["cf7c413468b0fe51cfb7ff457b1f9ab76dc80df01dbfba87cd190c9686078d68",356845],["8c8a6281407052dbc2bfaa2a90d7cc34f936b406ad83b11a3a0586f2d32f1896",354694],["0ebb575aef372a33941a1a9b8e317351dda7746389ec31c1b52f40f2280ad329",350614],["77c35bb2ee9c699693ee581a510b53f0c9cf4a3c3a58b02882913ca048fd09ab",352233],["9c5ced81d9a7378b763603f0bdd61322369e1bc3c72628a224b0445486e48663",357510],["611fe155e4e060d0cca795236b0f1abd6e41225b7bbca135cfaec8da5a4334f9",354915],["2926a709c9d0ed2824073bef29347d2beee6282e1e08aff5b982512e345f6220",357811],["7aed38f94ef86b504f985dcee98ed33dd6b341114147c55d0407b88495a1015d",354943],["d73ee72ed6661082acd273d3bbf4d3511330d688bec8e64e6a8d647a975b9655",353554],["38b56f2fc07b7bd5a378c7d25650f62a430fe42d5595d6184d5ae930b258bec3",353477],["ab06b98fc22fce8a33b591db9caf73e93d407342a6c0f3d2e2e1416dffffdfd7",362314]]


def sha_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def download(url, target, limit):
    req = urllib.request.Request(url, headers={"User-Agent": "GVQCC-pinned-frontier/1"})
    with urllib.request.urlopen(req, timeout=120) as src, target.open("xb") as dst:
        total = 0
        while block := src.read(1 << 20):
            total += len(block)
            if total > limit:
                raise ValueError("Source exceeded download cap")
            dst.write(block)
    return {"bytes": total, "sha256": sha_file(target)}


def build(inv, mirror, output):
    if sha_file(inv) != INV_SHA:
        raise ValueError("Public invsqrt hash mismatch: " + sha_file(inv))
    if output.exists() or output.with_name(output.name + ".incomplete").exists():
        raise FileExistsError("Output already exists")
    stage = output.with_name(output.name + ".incomplete")
    expected = {"invsqrt.kmb": INV_SHA, "dqi.kmb": DQI_SHA,
                "dfthcsos/submission.npz": CHEM_SHA}
    expected.update({f"dfthcsos/angle_k_{i}.kmb": h for i,(h,_) in enumerate(ANGLE_PINS)})
    report = {"members": {}, "source_invsqrt": INV_URL, "source_mirror": MIRROR_URL}
    try:
        with zipfile.ZipFile(mirror) as src, zipfile.ZipFile(
            stage, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True
        ) as dst:
            names = src.namelist()
            if len(names) != len(set(names)):
                raise ValueError("Duplicate mirror member")
            with inv.open("rb") as f, dst.open("invsqrt.kmb", "w", force_zip64=True) as g:
                shutil.copyfileobj(f, g, 1 << 20)
            report["members"]["invsqrt.kmb"] = INV_SHA
            for i, (want, size) in enumerate(ANGLE_PINS):
                name = f"angle_k_{i}.kmb"
                if name not in names or src.getinfo(name).file_size != size:
                    raise ValueError("Missing or wrong-sized ANGLE " + name)
                h = hashlib.sha256()
                with src.open(name) as f, dst.open("dfthcsos/" + name, "w", force_zip64=True) as g:
                    while block := f.read(1 << 20):
                        h.update(block); g.write(block)
                if h.hexdigest() != want:
                    raise ValueError("ANGLE source hash mismatch " + name)
                report["members"]["dfthcsos/" + name] = want
            name = "submission.npz"
            if name not in names or src.getinfo(name).file_size != 1847692:
                raise ValueError("Missing chemistry factor")
            h = hashlib.sha256()
            with src.open(name) as f, dst.open("dfthcsos/submission.npz", "w", force_zip64=True) as g:
                while block := f.read(1 << 20):
                    h.update(block); g.write(block)
            if h.hexdigest() != CHEM_SHA:
                raise ValueError("Chemistry factor source hash mismatch " + h.hexdigest())
            report["members"]["dfthcsos/submission.npz"] = CHEM_SHA
            if "dqi.kmb.xz" not in names:
                raise ValueError("Missing compressed DQI")
            h = hashlib.sha256(); count = 0
            with src.open("dqi.kmb.xz") as z, lzma.LZMAFile(z, "rb") as f, dst.open(
                "dqi.kmb", "w", force_zip64=True
            ) as g:
                while block := f.read(1 << 20):
                    count += len(block)
                    if count > 486988897:
                        raise ValueError("DQI decompression cap exceeded")
                    h.update(block); g.write(block)
            if h.hexdigest() != DQI_SHA or count != 486988897:
                raise ValueError("DQI source hash or size mismatch " + h.hexdigest())
            report["members"]["dqi.kmb"] = DQI_SHA
            dst.comment = b"Public f2cd / ccc2 / f6e circuits; upstream author licences retained"
        with zipfile.ZipFile(stage) as z:
            if set(z.namelist()) != set(expected):
                raise ValueError("Unexpected 18-member ZIP")
        stage.rename(output)
    except BaseException:
        stage.unlink(missing_ok=True)
        raise
    report.update(status="PUBLIC_BYTES_PINNED_ONLY", member_count=len(expected),
                  zip=str(output), zip_sha256=sha_file(output),
                  official_reverification=False, kaggle_submitted=False)
    output.with_suffix(".json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--invsqrt", type=Path)
    p.add_argument("--mirror", type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    inv = args.invsqrt or args.output.with_name("f2cdab0b7afc.kmb")
    mirror = args.mirror or args.output.with_name("maoxin123_mirror.zip")
    if args.invsqrt is None:
        print(json.dumps({"download_invsqrt": download(INV_URL, inv, 5_000_000)}), flush=True)
    if args.mirror is None:
        print(json.dumps({"download_mirror": download(MIRROR_URL, mirror, 100_000_000)}), flush=True)
    print(json.dumps(build(inv, mirror, args.output), indent=2), flush=True)


if __name__ == "__main__":
    main()
