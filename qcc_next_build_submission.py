#!/usr/bin/env python3
"""Build the fully verified W/H2_I variant of the exact public v27 submission.

Requires NumPy and these adjacent files:
  chem_next_apply_public4030_patch.py
  chem_next_public4030_weights.npz
  qcc_next_public_v27_manifest.json

Example:
  python qcc_next_build_submission.py --source original_v27.zip --out submission.zip

No circuits are changed and this script does not submit anything to Kaggle.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile


HERE = Path(__file__).resolve().parent
NPZ = "dfthcsos/submission.npz"
VERIFIED_NPZ_SHA = "df226db938dc440a37391091fba46c90ebcd14acfda88ec84939361ebcf9a955"


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def members(z: zipfile.ZipFile) -> dict:
    names = z.namelist()
    if len(names) != len(set(names)):
        raise ValueError("Duplicate ZIP members")
    result = {}
    for info in z.infolist():
        h = hashlib.sha256()
        with z.open(info) as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        result[info.filename] = {"size_bytes": info.file_size, "sha256": h.hexdigest()}
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    out = args.out.resolve()
    receipt_path = out.with_suffix(".receipt.json")
    if out.exists() or receipt_path.exists():
        raise FileExistsError("Use a fresh output path; existing files are never overwritten")
    expected = json.loads((HERE / "qcc_next_public_v27_manifest.json").read_text())
    with zipfile.ZipFile(args.source) as source:
        actual = members(source)
        if actual != expected:
            mismatch = sorted(k for k in set(actual) | set(expected) if actual.get(k) != expected.get(k))
            raise ValueError("Source is not the exact pinned public v27 member set: " + repr(mismatch))
        out.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="qcc-joint-", dir=out.parent) as temporary:
            td = Path(temporary)
            patched = td / "submission.npz"
            subprocess.run([
                sys.executable, str(HERE / "chem_next_apply_public4030_patch.py"),
                "--source", str(args.source.resolve()), "--out", str(patched),
            ], check=True, stdout=subprocess.PIPE, text=True)
            if sha_file(patched) != VERIFIED_NPZ_SHA:
                raise ValueError("Rebuilt NPZ differs from the 78,080-shot verified NPZ")
            temporary_zip = td / "submission.zip"
            with zipfile.ZipFile(temporary_zip, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as destination:
                for name in sorted(expected):
                    info = zipfile.ZipInfo(name, date_time=(2026, 11, 15, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o644 << 16
                    if name == NPZ:
                        with patched.open("rb") as src, destination.open(info, "w") as dst:
                            shutil.copyfileobj(src, dst, 1024 * 1024)
                    else:
                        with source.open(name) as src, destination.open(info, "w") as dst:
                            shutil.copyfileobj(src, dst, 1024 * 1024)
            with zipfile.ZipFile(temporary_zip) as check:
                final_members = members(check)
            assert len(final_members) == 18
            assert final_members[NPZ]["sha256"] == VERIFIED_NPZ_SHA
            unchanged = [name for name in sorted(expected) if name != NPZ]
            assert all(final_members[name] == expected[name] for name in unchanged)
            # A hard link creates the final path atomically without overwriting it.
            os.link(temporary_zip, out)
    receipt = {
        "status": "READY_COMPLETE_SUBMISSION_ZIP",
        "source_zip_sha256": sha_file(args.source),
        "output_zip_sha256": sha_file(out),
        "size_bytes": out.stat().st_size,
        "member_count": len(final_members),
        "members": final_members,
        "changed_members": [NPZ],
        "changed_npz_arrays": ["W", "H2_I"],
        "byte_identical_other_members": unchanged,
        "verification": {
            "chemistry_status": "PASS",
            "chemistry_verified_shots": 78080,
            "chemistry_cost": 294887890.976471,
            "chemistry_toffoli": 14722,
            "chemistry_qubits": 427,
            "scope": "Exact NPZ and 15 loaders match the separately recorded full official verifier run. DQI and invsqrt retain public v27 bytes and were not reverified by this builder.",
        },
        "kaggle_submitted": False,
        "observed_public_score": None,
    }
    with receipt_path.open("x") as f:
        json.dump(receipt, f, indent=2)
        f.write("\n")
    print(json.dumps({k: receipt[k] for k in ("status", "output_zip_sha256", "size_bytes", "member_count", "changed_members", "kaggle_submitted")}, indent=2))


if __name__ == "__main__":
    main()
