#!/usr/bin/env python3
"""Rebuild a public 28.09 submission-form ZIP from pinned dataset member bytes.

The Kaggle notebook's current embedded invsqrt literal may be re-published;
this route uses a fixed public dataset archive instead. No notebook code runs.
All 18 members are hashed against independently published source pins.
This is provenance-only; it is NOT a new official verification or submission.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request
import zipfile

DATASET_URL = "https://www.kaggle.com/api/v1/datasets/download/masumhuq/qai-c11-composite-2809"
DATASET_SHA = "26a5118dcfaa37f92e1a5e27da6d61778ce29c9a275c2ba94cd91bd0fd6a27ca"
ANGLE_PINS = [["aed6aa7cde8cefae06376546c276208a667a1a402ebfe9e57cb33881868ab089",415169],["72b79b56514e657650ed3258d90e7a533568ade86db407990a34bfb4380b6e60",421737],["42ea507daa22d0464e16d8f8d8f091e684d025998a32b574fee34672414b18ad",371346],["423968d4ab8219b164a27284c4b889b67a864ead9322b7703599fc839d7d8035",368418],["cf7c413468b0fe51cfb7ff457b1f9ab76dc80df01dbfba87cd190c9686078d68",356845],["8c8a6281407052dbc2bfaa2a90d7cc34f936b406ad83b11a3a0586f2d32f1896",354694],["0ebb575aef372a33941a1a9b8e317351dda7746389ec31c1b52f40f2280ad329",350614],["77c35bb2ee9c699693ee581a510b53f0c9cf4a3c3a58b02882913ca048fd09ab",352233],["9c5ced81d9a7378b763603f0bdd61322369e1bc3c72628a224b0445486e48663",357510],["611fe155e4e060d0cca795236b0f1abd6e41225b7bbca135cfaec8da5a4334f9",354915],["2926a709c9d0ed2824073bef29347d2beee6282e1e08aff5b982512e345f6220",357811],["7aed38f94ef86b504f985dcee98ed33dd6b341114147c55d0407b88495a1015d",354943],["d73ee72ed6661082acd273d3bbf4d3511330d688bec8e64e6a8d647a975b9655",353554],["38b56f2fc07b7bd5a378c7d25650f62a430fe42d5595d6184d5ae930b258bec3",353477],["ab06b98fc22fce8a33b591db9caf73e93d407342a6c0f3d2e2e1416dffffdfd7",362314]]
INVSQRT_SHA = "f2cdab0b7afc2e76aca12451113ef618e6f7e575a35a29f58264602dafb48726"
DQI_HASHES = {
    "ccc2ab84ed713901c5642c58890fc664a16a4842c1ebdc80edb56b11c96d6c8d",
    "00ac37d4ae4ee4ac6a8fe9a2aad241731c20be1c81d6332766f4f4d5a5a853a8",
}
CHEM_HASHES = {
    "f6e12f023a20f7aa44b7e981bc399d535c3920a2bc57e4937c94101",
    "0bd9c68f376b5702617512c6c6ebd2837c6a0c7faf4f738e59257e4937c94101",
}


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def download(path):
    request = urllib.request.Request(DATASET_URL, headers={"User-Agent": "GVQCC-exact-provenance/1"})
    with urllib.request.urlopen(request, timeout=120) as src, path.open("xb") as dst:
        total = 0
        while block := src.read(1 << 20):
            total += len(block)
            if total > 120_000_000:
                raise ValueError("Unexpectedly large public source")
            dst.write(block)
    if file_sha(path) != DATASET_SHA:
        raise ValueError("Public dataset archive changed; refuse unpinned source")


def build(dataset, output):
    if file_sha(dataset) != DATASET_SHA:
        raise ValueError("Source dataset archive SHA mismatch")
    stage = output.with_name(output.name + ".incomplete")
    if output.exists() or stage.exists():
        raise FileExistsError("Output or incomplete file already exists")
    members = {
        "invsqrt.kmb": ("invsqrt.kmb", INVSQRT_SHA, 179768),
        "dqi.kmb": ("dqi.kmb", DQI_HASHES, 486988897),
        "dfthcsos/submission.npz": ("dfthcsos__submission.npz", CHEM_HASHES, 1847692),
    }
    for i, (digest, size) in enumerate(ANGLE_PINS):
        members[f"dfthcsos/angle_k_{i}.kmb"] = (f"dfthcsos__angle_k_{i}.kmb", digest, size)
    audit = {}
    try:
        with zipfile.ZipFile(dataset) as src, zipfile.ZipFile(
            stage, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True
        ) as dst:
            names = src.namelist()
            if len(names) != len(set(names)):
                raise ValueError("Duplicate public dataset entry")
            for name, (member, expected, expected_bytes) in sorted(members.items()):
                if member not in names or src.getinfo(member).file_size != expected_bytes:
                    raise ValueError("Missing or wrong-sized source member: " + member)
                h = hashlib.sha256()
                count = 0
                with src.open(member) as f, dst.open(name, "w", force_zip64=True) as g:
                    while block := f.read(1 << 20):
                        count += len(block)
                        h.update(block)
                        g.write(block)
                actual = h.hexdigest()
                if actual not in expected if isinstance(expected, set) else actual != expected:
                    raise ValueError("Source hash mismatch " + name + " received " + actual)
                audit[name] = {"sha256": actual, "bytes": count}
            dst.comment = b"Public 28.09: original authors/Apache-2.0; provenance in source dataset"
        with zipfile.ZipFile(stage) as z:
            if set(z.namelist()) != set(members):
                raise AssertionError("Unexpected final submission members")
            if z.testzip() is not None:
                raise AssertionError("CRC failure")
        stage.rename(output)
    except BaseException:
        stage.unlink(missing_ok=True)
        raise
    report = {
        "status": "PUBLIC_BYTES_PINNED_ONLY",
        "dataset": DATASET_URL, "dataset_sha256": DATASET_SHA,
        "zip": str(output), "zip_sha256": file_sha(output),
        "member_count": len(audit), "members": audit,
        "official_full_verification": False, "kaggle_submitted": False,
    }
    output.with_suffix(".json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dataset", type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    dataset = args.dataset or args.output.with_name("masumhuq_public_source.zip")
    if args.dataset is None:
        download(dataset)
    print(json.dumps(build(dataset, args.output), indent=2), flush=True)


if __name__ == "__main__":
    main()
