"""Run unchanged official verifiers and preserve candidate-specific receipts.

The Chemistry score is sampled when a paid gate is HMR-conditioned; a new salt
is not a cost optimization. InvSqrt comparison must use identical sampling
arguments. No submission or remote repository write is performed here.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time


def sha(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidate", type=Path, required=True)
    ap.add_argument("--official", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--task", choices=("chem", "inv"), required=True)
    ap.add_argument("--salt", default="")
    ap.add_argument("--seed", type=int, default=20261127)
    ap.add_argument("--batch", type=int, default=292)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    if a.task == "chem":
        verifier = a.official / "verifiers/dfthcsos/verify.py"
        expected = "0775be7a528922367caebe9e4d051d6199811f1aefeaa4b793eaaa4621b8ec9d"
        command = [sys.executable, str(verifier), str(a.candidate)]
        if a.salt:
            command += ["--salt", a.salt]
        inputs = sorted(p for p in a.candidate.iterdir() if p.suffix in (".npz", ".kmb"))
        shots = 78016
        scope = "All 1219 legal addresses, 64 shots per address."
    else:
        verifier = a.official / "verifiers/invsqrt/verify_submission_invsqrt.py"
        expected = "ddef520dec6b68d1cf0a6f328ddd36d79eb84570b9192cf3f7acaf073f06733a"
        command = [sys.executable, str(verifier), str(a.candidate), "--shots-per-x", "1",
                   "--batch-size", str(a.batch), "--max-workers", "1", "--seed", str(a.seed)]
        inputs = [a.candidate]
        shots = 3133452
        scope = "All 3133452 legal inputs, one shot each; not 64 shots per input."
    assert sha(verifier) == expected, "Official source hash mismatch"
    receipt = {"command": command, "verifier_sha256": expected,
               "candidate_hashes": {p.name: sha(p) for p in inputs}, "scope": scope}
    (a.out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    env = dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1",
               MKL_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1")
    started = time.monotonic()
    with (a.out / "stdout.txt").open("wb") as out, (a.out / "stderr.txt").open("wb") as err:
        r = subprocess.run(command, stdout=out, stderr=err, env=env)
    receipt.update(returncode=r.returncode, seconds=time.monotonic() - started,
                   stdout_sha256=sha(a.out / "stdout.txt"), stderr_sha256=sha(a.out / "stderr.txt"))
    receipt["status"] = "NO_OFFICIAL_VERDICT"
    if r.returncode == 0:
        result = json.loads((a.out / "stdout.txt").read_text())
        assert result["status"] == "PASS", result
        assert result["verified_shots"] == shots, result
        receipt["status"] = "OFFICIAL_PASS"
        (a.out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        receipt["result"] = result
    (a.out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2), flush=True)
    raise SystemExit(0 if receipt["status"] == "OFFICIAL_PASS" else 1)


if __name__ == "__main__":
    main()