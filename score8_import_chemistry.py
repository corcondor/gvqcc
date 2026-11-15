#!/usr/bin/env python3
"""Import a pinned public chemistry family and run its unmodified verifier.

The importer never mixes a numerical table with loaders from another family.
It does not submit anything to Kaggle. The public v27 chemistry is maoxin123's
CC0 work; this script only performs reproducible integration and verification.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import zipfile

VERIFIER_SHA256 = "ca84ca08e6e9280922cda3b539d4776ae58990b2b03b5619a53d65de67df9d2b"
PUBLIC_URL = "https://www.kaggle.com/datasets/maoxin123/qcc-chemistry-4030-toffoli-loaders"
DOWNLOAD_URL = "https://www.kaggle.com/api/v1/datasets/download/maoxin123/qcc-chemistry-4030-toffoli-loaders"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--pins", type=Path, required=True)
    p.add_argument("--destination", type=Path, required=True)
    p.add_argument("--verifier", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    p.add_argument("--python", default=sys.executable)
    p.add_argument("--module-path", type=Path)
    a = p.parse_args()
    start = time.monotonic()
    pins = json.loads(a.pins.read_text())
    expected = {
        k.removeprefix("dfthcsos/"): v
        for k, v in pins["members"].items() if k.startswith("dfthcsos/")
    }
    assert set(expected) == {"submission.npz", *(f"angle_k_{k}.kmb" for k in range(15))}
    assert digest(a.verifier) == VERIFIER_SHA256, "The official verifier changed"
    members = []
    with zipfile.ZipFile(a.archive) as z:
        assert len(z.namelist()) == len(set(z.namelist())), "Duplicate ZIP member"
        assert set(z.namelist()) == set(expected), "Unexpected/missing ZIP member"
        assert z.testzip() is None, "ZIP CRC error"
        # Validate all payloads before writing any of them.
        for name in sorted(expected):
            b = z.read(name)
            h = hashlib.sha256(b).hexdigest()
            assert len(b) == expected[name]["bytes"] and h == expected[name]["sha256"], name
            members.append({"name": name, "bytes": len(b), "sha256": h})
        a.destination.mkdir(parents=True, exist_ok=True)
        assert not any(q.name not in expected for q in a.destination.iterdir())
        for item in members:
            q = a.destination / item["name"]
            if q.exists():
                assert digest(q) == item["sha256"], f"Refusing to overwrite {q}"
            else:
                q.write_bytes(z.read(item["name"]))
    env = dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1")
    if a.module_path:
        env["PYTHONPATH"] = str(a.module_path) + os.pathsep + env.get("PYTHONPATH", "")
    cmd = [a.python, str(a.verifier), str(a.destination)]
    run = subprocess.run(cmd, text=True, capture_output=True, env=env)
    a.receipt.parent.mkdir(parents=True, exist_ok=True)
    a.receipt.with_suffix(".stdout.log").write_text(run.stdout)
    a.receipt.with_suffix(".stderr.log").write_text(run.stderr)
    result = json.loads(run.stdout[run.stdout.index("{"):]) if "{" in run.stdout else None
    receipt = {
        "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": "PASS" if run.returncode == 0 and result and result.get("status") == "PASS" else "FAIL",
        "provenance": {"owner": "maoxin123", "license": "CC0", "dataset_url": PUBLIC_URL,
                       "download_url": DOWNLOAD_URL, "version": 1,
                       "notebook_script_version_id": pins["script_version_id"]},
        "archive": {"path": str(a.archive), "bytes": a.archive.stat().st_size, "sha256": digest(a.archive)},
        "members": members, "destination": str(a.destination),
        "verifier_sha256": digest(a.verifier), "importer_sha256": digest(Path(__file__)),
        "command": cmd, "returncode": run.returncode, "official_result": result,
        "submission_performed": False, "public_score": None, "seconds": time.monotonic() - start,
    }
    a.receipt.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    if receipt["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
