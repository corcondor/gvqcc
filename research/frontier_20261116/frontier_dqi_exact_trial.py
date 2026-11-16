#!/usr/bin/env python3
"""Deterministic exact-rewrite trial on a SHA-pinned public VQCC frontier ZIP.

Uses the repository's proved CCX fanout and input-factor transformations on
the *current* 890Q public DQI, not the older 821bf8d1. A changed hash changes
the verifier's default samples: the candidate is never declared a leaderboard
improvement from gate counts alone. Only an unchanged official full DQI PASS
with a lower measured default-salt cost permits a new submission-form ZIP.
No Kaggle submission, salt search, or verifier modification is performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import dqi_ccx_peephole as peephole

REFERENCE = {
    "invsqrt": 2076774.233715282,
    "dqi": 24439463583672.93,
    "dfthcsos": 3355599588.3155365,
}
INVSQRT_SHA = "f2cdab0b7afc2e76aca12451113ef618e6f7e575a35a29f58264602dafb48726"
DQI_COST = {
    # Public v27 28.09486, exact 890Q C8 lineage.
    "ccc2ab84ed713901c5642c58890fc664a16a4842c1ebdc80edb56b11c96d6c8d": 347375470571.73334,
    # Alex Chilton V11, published 28.09535, 890Q.
    "00ac37d4ae4ee4ac6a8fe9a2aad241731c20be1c81d6332766f4f4d5a5a853a8": 347357914646.9683,
}
CHEM_COST = {
    "f6e12f023a20f7aa44b7e981bc399d535c3920a2bc579bcea0aa713a6337367d": 294762732.97757906,
    "bdae290f5d6ba5282d3c91c9d4c96479c6dce8c161a8dbf92332a38723dd935b": 294762632.0817748,
    "0bd9c68f376b5702617512c6c6ebd2837c6a0c7faf4f738e59257e4937c94101": 294762518.6638708,
}
VERIFIER_URL = (
    "https://raw.githubusercontent.com/Inzainos/quantum-circuit-compilation/"
    "4277c767440df9efb8a90860ae2ce47028e46ba9/"
    "verifiers/dqi/verify_submission_dqi.py"
)
VERIFIER_SHA = "f14274bc0943fb9769ddb01131be6063191a15009fe1caf1d4bdd9fd25194e65"
MEMBERS = {"invsqrt.kmb", "dqi.kmb", "dfthcsos/submission.npz"} | {
    f"dfthcsos/angle_k_{i}.kmb" for i in range(15)
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def extract_baseline(source: Path, output: Path) -> dict:
    """Read exactly the known 18 members; reject duplicate/unexpected entries."""
    with zipfile.ZipFile(source) as z:
        names = z.namelist()
        if len(names) != len(set(names)) or set(names) != MEMBERS:
            raise ValueError("Expected 18 unique submission members, no extras")
        for name in names:
            info = z.getinfo(name)
            if info.is_dir() or (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("Directory or symlink in submission")
        with z.open("dqi.kmb") as src, output.open("xb") as dst:
            shutil.copyfileobj(src, dst, 1 << 20)
        with z.open("invsqrt.kmb") as src:
            inv = hashlib.sha256()
            for block in iter(lambda: src.read(1 << 20), b""):
                inv.update(block)
        with z.open("dfthcsos/submission.npz") as src:
            chem = hashlib.sha256()
            for block in iter(lambda: src.read(1 << 20), b""):
                chem.update(block)
    dqi_hash = sha(output)
    if dqi_hash not in DQI_COST or inv.hexdigest() != INVSQRT_SHA or chem.hexdigest() not in CHEM_COST:
        raise ValueError("Unrecognized frontier component hash; refusing a mixed portfolio")
    return {
        "dqi_sha256": dqi_hash, "dqi_reference_cost": DQI_COST[dqi_hash],
        "invsqrt_sha256": inv.hexdigest(), "invsqrt_cost": 75006.37653863191,
        "chemistry_npz_sha256": chem.hexdigest(), "chemistry_cost": CHEM_COST[chem.hexdigest()],
        "member_count": len(names),
    }


def gm(inv_cost: float, dqi_cost: float, chem_cost: float) -> float:
    return math.exp(sum(math.log(REFERENCE[k] / v) for k, v in (
        ("invsqrt", inv_cost), ("dqi", dqi_cost), ("dfthcsos", chem_cost))) / 3)


def repack(original: Path, new_dqi: Path, target: Path) -> None:
    """Replace only DQI; stream all bytes to avoid a 500MB Python allocation."""
    with zipfile.ZipFile(original) as old, zipfile.ZipFile(
        target, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True
    ) as new:
        for name in sorted(MEMBERS):
            with new.open(name, "w", force_zip64=True) as dst:
                if name == "dqi.kmb":
                    with new_dqi.open("rb") as src:
                        shutil.copyfileobj(src, dst, 1 << 20)
                else:
                    with old.open(name) as src:
                        shutil.copyfileobj(src, dst, 1 << 20)
        new.comment = b"Public VQCC circuits, source authors retained; exact DQI rewrite only"
    with zipfile.ZipFile(original) as old, zipfile.ZipFile(target) as new:
        if set(new.namelist()) != MEMBERS:
            raise AssertionError("New ZIP member mismatch")
        for name in MEMBERS - {"dqi.kmb"}:
            if old.getinfo(name).CRC != new.getinfo(name).CRC:
                raise AssertionError("Unchanged member CRC mismatch: " + name)


def run_trial(args) -> dict:
    start = time.monotonic()
    work = args.work_dir.resolve()
    work.mkdir(parents=True, exist_ok=False)
    original = work / "baseline_dqi.kmb"
    source = extract_baseline(args.baseline_zip, original)
    receipt = {"source": source, "status": "STARTED",
               "source_zip_sha256": sha(args.baseline_zip),
               "no_kaggle_submission": True, "salt_search": False}
    stage1 = work / "same_control.kmb"
    p1 = peephole.optimize(original, stage1, window=args.window)
    (work / "same_control.json").write_text(json.dumps(p1, indent=2) + "\n")
    receipt["same_control_ccx_saved"] = p1["static_ccx_reduction"]

    stage2 = work / "input_factor.kmb"
    scan = work / "input_factor.json"
    cmd = [sys.executable, str(ROOT / "dqi_ccx_input_factor.py"), str(stage1),
           "--window", str(args.window), "--seconds", str(args.scan_seconds),
           "--report", str(scan), "--output", str(stage2)]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    receipt["input_factor_process_returncode"] = proc.returncode
    receipt["input_factor_stderr_tail"] = proc.stderr[-2000:]
    receipt["input_factor_stdout_tail"] = proc.stdout[-2000:]
    if proc.returncode == 0 and scan.exists():
        s = json.loads(scan.read_text())
        receipt["input_factor_status"] = s["status"]
        receipt["input_factor_ccx_saved"] = s["static_ccx_reduction"]
    else:
        receipt["input_factor_status"] = "NOT_COMPLETED"
        receipt["input_factor_ccx_saved"] = 0
    candidate = stage2 if stage2.exists() and proc.returncode == 0 else stage1
    savings = p1["static_ccx_reduction"] + receipt["input_factor_ccx_saved"]
    receipt["static_ccx_saved"] = savings
    receipt["candidate_sha256"] = sha(candidate)
    receipt["elapsed_seconds_before_verifier"] = round(time.monotonic() - start, 2)

    if savings <= 0:
        receipt["status"] = "NO_PROVED_EXACT_SAVINGS"
    elif not args.verify:
        receipt["status"] = "EXACT_REWRITE_BUILT_NOT_FULLY_VERIFIED"
    else:
        verifier = work / "verify_submission_dqi.py"
        with urllib.request.urlopen(VERIFIER_URL, timeout=120) as stream, verifier.open("xb") as out:
            shutil.copyfileobj(stream, out)
        if sha(verifier) != VERIFIER_SHA:
            raise ValueError("Official verifier SHA mismatch")
        report = work / "dqi_full102400.json"
        cmd = [sys.executable, str(ROOT / "verify_dqi_candidate.py"), str(candidate),
               "--verifier", str(verifier), "--output", str(report)]
        subprocess.run(cmd, check=True)
        checked = json.loads(report.read_text())
        receipt["official_dqi_result"] = {
            k: checked.get(k) for k in
            ("status", "score", "num_qubits", "verified_shots",
             "value_errors", "phase_errors", "circuit_sha256")
        }
        if (checked.get("status") != "PASS" or checked.get("verified_shots") != 102400
                or checked.get("circuit_sha256") != receipt["candidate_sha256"]):
            receipt["status"] = "VERIFIER_FAILED"
        elif checked["score"] >= source["dqi_reference_cost"]:
            receipt["status"] = "PASS_BUT_NO_DEFAULT_COST_GAIN"
        else:
            receipt["status"] = "OFFICIAL_DEFAULT_DQI_PASS_AND_COST_GAIN"
            receipt["source_gm_model"] = gm(
                source["invsqrt_cost"], source["dqi_reference_cost"], source["chemistry_cost"])
            receipt["candidate_gm_model"] = gm(
                source["invsqrt_cost"], checked["score"], source["chemistry_cost"])
            output = work / "submission_candidate.zip"
            repack(args.baseline_zip, candidate, output)
            receipt["submission_form_zip_sha256"] = sha(output)
            receipt["zip_status"] = "UNSUBMITTED; OTHER_TASKS_NOT_REVERIFIED"
    receipt["elapsed_seconds"] = round(time.monotonic() - start, 2)
    (work / "trial.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: v for k, v in receipt.items() if k not in (
        "input_factor_stdout_tail", "input_factor_stderr_tail")}, indent=2), flush=True)
    return receipt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--baseline-zip", type=Path, required=True)
    p.add_argument("--work-dir", type=Path, required=True)
    p.add_argument("--window", type=int, default=256)
    p.add_argument("--scan-seconds", type=int, default=400)
    p.add_argument("--verify", action="store_true")
    args = p.parse_args()
    if not args.baseline_zip.is_file() or not 1 <= args.window <= 4096 or args.scan_seconds < 1:
        p.error("Missing baseline ZIP or invalid scan limits")
    run_trial(args)


if __name__ == "__main__":
    main()
