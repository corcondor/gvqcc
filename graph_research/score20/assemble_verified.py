"""Build a local portfolio using only full-verifier, lower-cost replacements."""

import argparse
from hashlib import file_digest
import json
from math import prod
from pathlib import Path
from shutil import copyfileobj
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


REQUIRED_SHOTS = {"dqi": 102_400, "invsqrt": 200_540_928}


def digest(path):
    with path.open("rb") as file:
        return file_digest(file, "sha256").hexdigest()


def verified_replacement(task, circuit, receipt, cost):
    info = json.loads(receipt.read_text())
    if info["status"] != "PASS" or info["verified_shots"] != REQUIRED_SHOTS[task]:
        raise ValueError(f"{task} lacks the full official PASS")
    if task == "dqi" and (info["value_errors"] or info["phase_errors"]):
        raise ValueError("DQI has failed shots")
    if task == "invsqrt" and info["worst_error_over_tolerance"] > 1:
        raise ValueError("Inverse square root has a phase outside tolerance")
    if info["circuit_sha256"] != digest(circuit):
        raise ValueError(f"{task} circuit hash differs from the verifier receipt")
    if not info["score"] < cost:
        raise ValueError(f"{task} has no official cost gain")
    return info


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--zip", type=Path, required=True)
    p.add_argument("--baseline", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    for task in REQUIRED_SHOTS:
        p.add_argument("--" + task, type=Path, nargs=2, metavar=("KMB", "OFFICIAL_JSON"))
    args = p.parse_args()
    base = json.loads(args.baseline.read_text())
    if digest(args.zip) != base["zip_sha256"]:
        raise ValueError("Portfolio digest differs from the pinned scorecard")
    changes = {}
    costs = dict(base["costs"])
    metadata = {}
    expected_hashes = dict(base["members"])
    for task in REQUIRED_SHOTS:
        pair = getattr(args, task)
        if pair is not None:
            circuit, receipt = pair
            info = verified_replacement(task, circuit, receipt, costs[task])
            name = task + ".kmb"
            changes[name] = circuit
            costs[task] = info["score"]
            expected_hashes[name] = info["circuit_sha256"]
            metadata[task] = info
    if not changes:
        p.error("Provide at least one verified replacement")
    score = prod(base["reference_costs"][k] / costs[k] for k in costs) ** (1 / 3)
    assert score > base["local_score"]
    with ZipFile(args.zip) as old, ZipFile(args.out, "x", compression=ZIP_DEFLATED) as new:
        assert set(old.namelist()) == set(base["members"]) and len(old.infolist()) == 18
        for name in old.namelist():
            entry = ZipInfo(name)
            entry.compress_type = ZIP_DEFLATED
            read = changes[name].open("rb") if name in changes else old.open(name)
            with read, new.open(entry, "w", force_zip64=True) as write:
                copyfileobj(read, write, length=1 << 20)
    with ZipFile(args.out) as build:
        assert set(build.namelist()) == set(expected_hashes) and len(build.infolist()) == 18
        for name, expected in expected_hashes.items():
            with build.open(name) as member:
                assert file_digest(member, "sha256").hexdigest() == expected
    record = {"local_score": score, "baseline_local_score": base["local_score"],
              "local_improvement": score - base["local_score"], "costs": costs,
              "reference_costs": base["reference_costs"], "full_verifications": metadata,
              "members": expected_hashes, "zip_size": args.out.stat().st_size,
              "zip_sha256": digest(args.out), "kaggle_submitted": False}
    args.receipt.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({key: record[key] for key in ("local_score", "local_improvement", "costs", "zip_sha256")}))


if __name__ == "__main__":
    main()
