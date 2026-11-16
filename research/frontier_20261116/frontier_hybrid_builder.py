#!/usr/bin/env python3
"""Reuse the actual Apache-2.0 Kaggle 44Q invsqrt and public chemistry KMBs.

This does NOT execute public notebook source: only literal AST assignments are
read. All 18 members are individually SHA256-checked. Our DQI562 is pinned to
a past official local receipt. The result is an unsubmitted candidate ZIP.
"""
from __future__ import annotations
import argparse
import ast
import base64
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request
import zipfile
import zlib

API = ("https://www.kaggle.com/api/v1/kernels/pull/maoxin123/"
       "qcc-v27-a-44-qubit-invsqrt-on-the-28-09-frontier")
EXPECTED_INVSQRT = "f2cdab0b7afc2e76aca12451113ef618e6f7e575a35a29f58264602dafb48726"
EXPECTED_OWN_DQI = "102716664a883baaab1874dc176c52dde23451c99de3006cb261832130a53fd6"
EXPECTED_OWN_ZIP = "f5496ab49daf607feb75c057f464804c3e2e51e59bcf915b62854befeaf0078f"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def literal_assignment(cell: str, name: str):
    try:
        tree = ast.parse(cell)
    except SyntaxError:
        return None
    for line in tree.body:
        if isinstance(line, ast.Assign):
            if any(isinstance(x, ast.Name) and x.id == name for x in line.targets):
                return ast.literal_eval(line.value)
    return None


def decode_notebook(raw: bytes):
    if len(raw) > 3_000_000:
        raise ValueError("Notebook API JSON too large")
    response = json.loads(raw)
    payload = response.get("blob", {}).get("source") or response.get("blob", {}).get("sourceNullable")
    if not isinstance(payload, str):
        raise ValueError("Kaggle pull API returned no notebook JSON string")
    notebook = json.loads(payload)
    pinned = None
    encoded = None
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        src = cell.get("source", "")
        src = "".join(src) if isinstance(src, list) else src
        if "PINNED" in src and pinned is None:
            pinned = literal_assignment(src, "PINNED")
        if "INV =" in src and encoded is None:
            encoded = literal_assignment(src, "INV")
    expected_names = {"dqi.kmb", "dfthcsos/submission.npz"} | {
        f"dfthcsos/angle_k_{i}.kmb" for i in range(15)
    }
    if not isinstance(pinned, dict) or set(pinned) != expected_names:
        raise ValueError("Unexpected pinned notebook member set")
    for name, item in pinned.items():
        if not (isinstance(item, (tuple, list)) and len(item) == 2
                and isinstance(item[0], str) and len(item[0]) == 64
                and isinstance(item[1], int) and item[1] > 0):
            raise ValueError(f"Malformed SHA/size pin: {name}")
    if not isinstance(encoded, str) or len(encoded) > 2_000_000:
        raise ValueError("Missing or oversized embedded invsqrt")
    compressed = base64.b64decode(encoded, validate=True)
    decomp = zlib.decompressobj()
    inv = decomp.decompress(compressed, 10_000_001)
    if (not decomp.eof or len(inv) > 10_000_000 or
            decomp.unconsumed_tail or sha(inv) != EXPECTED_INVSQRT):
        raise ValueError("Embedded public invsqrt SHA or compressed length mismatch")
    return pinned, inv


def component_file(root: Path, name: str) -> Path:
    p = root / name
    if not p.is_file():
        p = root / name.replace("/", "__")
    if not p.is_file() or p.is_symlink():
        raise FileNotFoundError(name)
    return p


@contextmanager
def own_dqi(raw_path: Path | None, zip_path: Path | None):
    if (raw_path is None) == (zip_path is None):
        raise ValueError("Provide exactly one own DQI KMB or verified ZIP")
    if raw_path is not None:
        with raw_path.open("rb") as stream:
            yield stream
    else:
        with zipfile.ZipFile(zip_path) as source:
            if "dqi.kmb" not in source.namelist():
                raise ValueError("Own ZIP has no dqi.kmb")
            with source.open("dqi.kmb") as stream:
                yield stream


def build(raw: bytes, chem_root: Path, own_kmb: Path | None,
          own_zip: Path | None, output: Path):
    pins, inv = decode_notebook(raw)
    if own_zip is not None and sha_file(own_zip) != EXPECTED_OWN_ZIP:
        raise ValueError("Own official DQI562 ZIP pin mismatch")
    chem = {}
    for name, (expected, size) in pins.items():
        if name == "dqi.kmb":
            continue
        path = component_file(chem_root, name)
        if path.stat().st_size != size or sha_file(path) != expected:
            raise ValueError(f"Public KMB/NPZ file pin mismatch: {name}")
        chem[name] = path
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    expected = {"invsqrt.kmb": EXPECTED_INVSQRT,
                "dqi.kmb": EXPECTED_OWN_DQI,
                **{k: pins[k][0] for k in chem}}
    try:
        with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED,
                             compresslevel=6, allowZip64=True) as target:
            target.writestr("invsqrt.kmb", inv)
            for name, path in sorted(chem.items()):
                target.write(path, name)
            dig = hashlib.sha256()
            with own_dqi(own_kmb, own_zip) as src, target.open("dqi.kmb", "w",
                                                               force_zip64=True) as dst:
                for buf in iter(lambda: src.read(1 << 20), b""):
                    dig.update(buf)
                    dst.write(buf)
            if dig.hexdigest() != EXPECTED_OWN_DQI:
                raise ValueError("Own DQI KMB hash mismatch")
            target.comment = (
                b"Public 44Q invsqrt: maoxin123 Apache-2.0; "
                b"chemistry: maoxin123/Boristown coded loaders (see public source); "
                b"own corcondor DQI562. All upstream attribution/licences retained "
                b"via accompanying public provenance. Official re-verification required."
            )
        with zipfile.ZipFile(output) as archive:
            if set(archive.namelist()) != set(expected):
                raise ValueError("Unexpected archive member set")
            if archive.testzip() is not None:
                raise ValueError("CRC failure")
            for name, expected_hash in expected.items():
                h = hashlib.sha256()
                with archive.open(name) as stream:
                    for block in iter(lambda: stream.read(1 << 20), b""):
                        h.update(block)
                if h.hexdigest() != expected_hash:
                    raise ValueError(f"Archive mismatch: {name}")
    except BaseException:
        output.unlink(missing_ok=True)
        raise
    receipt = {
        "status": "HASHED_ONLY_NEEDS_OFFICIAL_ALL_TASK_VERIFICATION",
        "zip": str(output), "zip_sha256": sha_file(output),
        "members": expected, "member_count": len(expected),
        "public_notebook": API, "public_source_sha256": sha(raw),
        "kaggle_submitted": False, "official_verified_as_composite": False,
    }
    output.with_suffix(".json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n"
    )
    return receipt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--public-notebook-raw", type=Path,
                   help="Saved full JSON from Kaggle kernels/pull API, not a .ipynb")
    p.add_argument("--public-chemistry-dir", type=Path, required=True)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--own-dqi-kmb", type=Path)
    g.add_argument("--own-verified-zip", type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.public_notebook_raw:
        raw = args.public_notebook_raw.read_bytes()
    else:
        req = urllib.request.Request(API, headers={"User-Agent":"GVQCC-source-pin-verifier/1"})
        with urllib.request.urlopen(req, timeout=40) as response:
            raw = response.read(3_000_001)
    print(json.dumps(build(raw, args.public_chemistry_dir,
                           args.own_dqi_kmb, args.own_verified_zip,
                           args.output), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
