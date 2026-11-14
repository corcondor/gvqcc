#!/usr/bin/env python3
"""Offline Kaggle build/verification/packaging worker; never submits to Kaggle.

Generated with pinned public materials by build_kaggle_score_worker.py.
Required attached inputs: competition, 4033 chemistry loaders, an exact821
DQI cache, and Syed's own-circuit portfolio containing dqi_source_zip.
"""
from __future__ import annotations

import base64
from datetime import datetime, timezone
import hashlib
import io
import json
import lzma
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import zipfile


EMBEDDED_PAYLOAD_B64 = "__PAYLOAD_BASE64__"
EMBEDDED_PAYLOAD_SHA256 = "__PAYLOAD_SHA256__"
VARIANT = "__VARIANT__"
WORKER_TITLE = "__WORKER_TITLE__"

INPUT = Path("/kaggle/input")
OUTPUT = Path("/kaggle/working")
BASELINE_SHA = "821bf8d157c03c3e868a0099b0ab1438cfba664ab1bc6fec3210654099b672a3"
CANDIDATE_SHA = "__CANDIDATE_SHA256__"
SOURCE_SHA = "49e2b331d4008afb724985caf1038765b7a910f08838b590bf6e8fb692772763"
INVERSE_SHA = "e46d90c36d1beb3ce7731a3e0b5c3659b3cda7f5f290b73c6c34513d96c005b6"
CHEMISTRY_SHA = "809063291b8af401b4075db850afb216b6cfca398468ed2e47e4c0623eb3fae5"
BASE_CHEMISTRY_SHA = "3f864a7aeaa4d78984c8822761782b63be2d553b229f487e79640a73be147c44"
REFIT_SHA = "67f711e1a9656f1af9e630e11d491791009971a8c6ec30f95f092bad74ce6073"


def log(event, **values):
    print(json.dumps({"event": event, **values}, ensure_ascii=False), flush=True)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while block := stream.read(1 << 20):
            digest.update(block)
    return digest.hexdigest()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def pin(path, expected):
    require(Path(path).is_file(), f"Missing pinned file: {path}")
    actual = sha256(path)
    require(actual == expected, f"SHA-256 mismatch for {path}: {actual}")
    return Path(path)


def unpack_payload(destination):
    packed = base64.b64decode(EMBEDDED_PAYLOAD_B64, validate=True)
    require(hashlib.sha256(packed).hexdigest() == EMBEDDED_PAYLOAD_SHA256,
            "Embedded source/payload archive checksum failed")
    data = lzma.decompress(packed)
    require(len(data) <= 16 << 20, "Unexpected embedded payload size")
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        seen = set()
        for member in archive.infolist():
            path = PurePosixPath(member.filename)
            require(not path.is_absolute() and ".." not in path.parts and "\\" not in member.filename,
                    "Unsafe embedded source path")
            require(member.filename not in seen and not stat.S_ISLNK(member.external_attr >> 16),
                    "Duplicate or linked embedded source file")
            seen.add(member.filename)
            target = destination.joinpath(*path.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            require(not member.is_dir(), "Embedded directory entries are not expected")
            with archive.open(member) as incoming, target.open("xb") as outgoing:
                shutil.copyfileobj(incoming, outgoing, 1 << 20)
    manifest = json.loads((destination / "payload_manifest.json").read_text())
    require(manifest.get("variant") == VARIANT and manifest.get("candidate_sha256") == CANDIDATE_SHA
            and manifest.get("worker_title") == WORKER_TITLE, "Payload variant differs from this worker")
    require(set(manifest["files"]) | {"payload_manifest.json"} == seen, "Payload manifest inventory differs")
    for name, entry in manifest["files"].items():
        target = pin(destination / name, entry["sha256"])
        require(target.stat().st_size == entry["bytes"], f"Payload size mismatch: {name}")
    return manifest


def find_competition(files, pins):
    roots = sorted({p.parents[2] for p in files if p.name == "FeMoCo76o113e.fcidump"
                    and p.stat().st_size == 128128348})
    for root in roots:
        if all((root / name).is_file() for name in pins):
            for name, expected in pins.items():
                pin(root / name, expected)
            return root
    raise RuntimeError("The attached competition does not contain the pinned verifier/engine/data files")


def find_source_archive(files):
    likely = [p for p in files if p.name in ("dqi_source_zip", "dqi_source.zip")]
    likely += [p for p in files if p not in likely and "dqi" in p.name.lower()
               and "source" in p.name.lower() and p.suffix.lower() == ".zip"]
    for path in likely:
        if path.stat().st_size <= 256 << 20 and sha256(path) == SOURCE_SHA:
            return path
    raise RuntimeError("Pinned dqi_source_zip is missing; attach syed3000/vqcc-own-circuit-portfolio")


def find_baseline(files, target):
    expected_size = 455584321
    for path in files:
        if path.name.lower().endswith(".kmb") and path.stat().st_size == expected_size:
            if sha256(path) == BASELINE_SHA:
                shutil.copyfile(path, target)
                return {"path": str(path), "format": "kmb", "sha256": BASELINE_SHA}
    compressed = [p for p in files if p.name.lower() == "dqi.kmb.xz"]
    for path in compressed:
        digest = hashlib.sha256()
        total = 0
        try:
            with lzma.open(path, "rb") as incoming, target.open("wb") as outgoing:
                while block := incoming.read(1 << 20):
                    total += len(block)
                    require(total <= expected_size, "This compressed DQI has a different size")
                    digest.update(block)
                    outgoing.write(block)
            if total == expected_size and digest.hexdigest() == BASELINE_SHA:
                return {"path": str(path), "format": "xz", "compressed_sha256": sha256(path),
                        "sha256": BASELINE_SHA}
        except (lzma.LZMAError, EOFError, RuntimeError):
            pass
        target.unlink(missing_ok=True)
    raise RuntimeError("No attached DQI file decompresses to the pinned821 baseline")


def copy_loaders(files, target, expected):
    found = {}
    for name, digest in expected.items():
        candidates = [p for p in files if p.name == name]
        match = next((p for p in candidates if sha256(p) == digest), None)
        require(match is not None, f"Missing exact public4033 loader: {name}")
        shutil.copyfile(match, target / name)
        found[name] = {"path": str(match), "sha256": digest}
    require(len(found) == 15, "Exactly15 pinned chemistry loaders are required")
    return found


def reconstruct_chemistry(files, refit_path, destination):
    import numpy as np
    candidates = [p for p in files if p.name == "submission.npz" and p.stat().st_size == 1847692]
    base = next((p for p in candidates if sha256(p) == BASE_CHEMISTRY_SHA), None)
    require(base is not None, "The exact public4033 factorization3f864a7a is not attached")
    pin(refit_path, REFIT_SHA)
    with np.load(base, allow_pickle=False) as original:
        arrays = {name: np.array(original[name]) for name in original.files}
    with np.load(refit_path, allow_pickle=False) as refit:
        require(set(refit.files) == {"W", "H2_I"}, "Unexpected refit array names")
        for name in ("W", "H2_I"):
            require(refit[name].shape == arrays[name].shape, f"Refit shape mismatch: {name}")
            arrays[name] = np.array(refit[name])
    np.savez_compressed(destination, **arrays)
    pin(destination, CHEMISTRY_SHA)
    return {"base_path": str(base), "base_sha256": BASE_CHEMISTRY_SHA,
            "embedded_refit_sha256": REFIT_SHA, "reconstructed_sha256": CHEMISTRY_SHA,
            "numpy_version": np.__version__, "method": "Replace W/H2_I; preserve array order; numpy.savez_compressed"}


def run(command, environment, *, stdout_path=None):
    log("run", command=list(map(str, command)))
    if stdout_path is None:
        subprocess.run(list(map(str, command)), env=environment, check=True)
    else:
        with Path(stdout_path).open("x", encoding="utf-8") as output:
            subprocess.run(list(map(str, command)), env=environment, stdout=output, check=True)


def main():
    started = time.monotonic()
    require(INPUT.is_dir() and OUTPUT.is_dir(), "This worker runs in a Kaggle notebook")
    final_zip = OUTPUT / "submission.zip"
    require(not final_zip.exists(), "submission.zip already exists; use a fresh notebook run")
    scratch = Path(tempfile.mkdtemp(prefix="gvqcc-score-", dir="/tmp"))
    payload = scratch / "payload"
    payload.mkdir()
    manifest = unpack_payload(payload)
    tools = payload / "tools"
    material = payload / "material"
    files = sorted(p for p in INPUT.rglob("*") if p.is_file())
    competition = find_competition(files, manifest["official_pins"])
    engine = competition / "kickmix"
    verifiers = competition / "verifiers"
    archive = find_source_archive(files)
    baseline_root = scratch / "baseline"
    chemistry = baseline_root / "dfthcsos"
    chemistry.mkdir(parents=True)
    baseline = baseline_root / "dqi.kmb"
    baseline_origin = find_baseline(files, baseline)
    loader_origins = copy_loaders(files, chemistry, manifest["chemistry_loader_pins"])
    shutil.copyfile(pin(material / "invsqrt.kmb", INVERSE_SHA), baseline_root / "invsqrt.kmb")
    chemistry_origin = reconstruct_chemistry(files, material / "asterios_refit.npz", chemistry / "submission.npz")
    upstream = json.loads((material / "invsqrt_upstream_receipt.json").read_text())
    inverse = upstream["full_task_results"]["invsqrt"]
    require(inverse["status"] == "PASS" and inverse["verified_shots"] == 200540928
            and inverse["circuit_sha256"] == INVERSE_SHA, "Unchanged inverse's upstream receipt does not match")
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join((str(engine), str(verifiers), str(tools)))
    environment["PYTHONUNBUFFERED"] = "1"
    log("inputs_verified", baseline=BASELINE_SHA, source_archive=SOURCE_SHA,
        inverse=INVERSE_SHA, chemistry_factor=CHEMISTRY_SHA, chemistry_loaders=len(loader_origins),
        variant=VARIANT, worker_title=WORKER_TITLE)

    chemistry_result_path = scratch / "chemistry_full_verify.json"
    run([sys.executable, "-u", verifiers / "dfthcsos" / "verify.py", chemistry],
        environment, stdout_path=chemistry_result_path)
    chemistry_result = json.loads(chemistry_result_path.read_text())
    require(chemistry_result.get("status") == "PASS" and chemistry_result.get("verified_shots") == 78080
            and chemistry_result.get("num_circuits") == 15, "Full official chemistry verification did not pass")
    log("chemistry_pass", score=chemistry_result["score"], shots=chemistry_result["verified_shots"])
    baseline_zip = scratch / "baseline_submission.zip"
    with zipfile.ZipFile(baseline_zip, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6,
                         allowZip64=True) as packed:
        for path in sorted(baseline_root.rglob("*")):
            if path.is_file():
                packed.write(path, path.relative_to(baseline_root).as_posix())
    reproduction = scratch / "reproduction"
    run([sys.executable, "-u", tools / "reproduce_dqi_candidate.py",
         "--work-dir", reproduction, "--baseline", baseline,
         "--source-archive", archive, "--verifier", verifiers / "dqi" / "verify_submission_dqi.py",
         "--engine-dir", engine, "--baseline-zip", baseline_zip, "--variant", VARIANT], environment)
    reproduction_receipt = json.loads((reproduction / "reproduction_receipt.json").read_text())
    require(reproduction_receipt.get("variant") == VARIANT
            and reproduction_receipt.get("candidate_sha256") == CANDIDATE_SHA,
            "Reproduction variant or final candidate differs")
    dqi_path = reproduction / "dqi_full102400.json"
    dqi = json.loads(dqi_path.read_text())
    require(dqi.get("status") == "PASS" and dqi.get("verified_shots") == 102400
            and dqi.get("log2_delta") == -128 and dqi.get("circuit_sha256") == CANDIDATE_SHA,
            "Full default-confidence DQI verification is missing or mismatched")
    require(dqi.get("seed") is None and dqi.get("salt") == "",
            "Unexpected nondefault DQI seed or salt")
    require(dqi.get("verifier_sha256") == manifest["official_pins"]["verifiers/dqi/verify_submission_dqi.py"]
            and dqi.get("kickmix_binary_sha256") == manifest["official_pins"]["kickmix/kickmix.so"],
            "DQI verification used an unexpected engine or verifier")
    package_receipt = json.loads((reproduction / "submission.receipt.json").read_text())
    require(package_receipt["non_dqi_members_byte_identical"] is True
            and package_receipt["dqi"]["after_sha256"] == CANDIDATE_SHA,
            "Final ZIP preservation receipt does not match")
    packaged = pin(reproduction / "submission.zip", package_receipt["output_archive"]["sha256"])

    receipt = {
        "status": "READY_FOR_KAGGLE_SCORING", "created_utc": datetime.now(timezone.utc).isoformat(),
        "variant": VARIANT, "worker_title": WORKER_TITLE,
        "submission_performed": False, "observed_kaggle_score": None,
        "source_payload_sha256": EMBEDDED_PAYLOAD_SHA256,
        "candidate_dqi_sha256": CANDIDATE_SHA, "baseline_dqi_origin": baseline_origin,
        "source_archive": {"path": str(archive), "sha256": SOURCE_SHA},
        "chemistry_loader_origins": loader_origins,
        "chemistry_reconstruction": chemistry_origin,
        "chemistry_factor_sha256": CHEMISTRY_SHA,
        "chemistry": chemistry_result, "dqi": dqi,
        "invsqrt": {"scope": "UNCHANGED: reused public full200540928-shot evidence, not rerun here",
                    "result": inverse, "public_receipt_sha256": sha256(material / "invsqrt_upstream_receipt.json")},
        "submission_sha256": sha256(packaged), "elapsed_seconds": time.monotonic() - started,
        "score_note": "Verifier PASS is validity evidence; a leaderboard score increase is not guaranteed.",
    }
    # Emit small evidence files first. The submission becomes available only
    # after all gates above and a checksum of its copied bytes have passed.
    exports = {
        "dqi_full102400.json": dqi_path,
        "chemistry_full_verify.json": chemistry_result_path,
        "invsqrt_upstream_receipt.json": material / "invsqrt_upstream_receipt.json",
        "submission.receipt.json": reproduction / "submission.receipt.json",
        "reproduction_receipt.json": reproduction / "reproduction_receipt.json",
        "source_payload_manifest.json": payload / "payload_manifest.json",
        "SOURCE_NOTICE.md": payload / "SOURCE_NOTICE.md",
    }
    if VARIANT == "480gauge128":
        factor = reproduction_receipt.get("input_factor", {})
        factor_path = reproduction / "dqi_input_factor384.json"
        require(factor.get("additional_static_ccx_reduction") == 384
                and factor.get("output_sha256") == CANDIDATE_SHA
                and factor.get("report_file") == factor_path.name,
                "Missing 384-rewrite input-factor reproduction evidence")
        pin(factor_path, factor["report_sha256"])
        receipt["input_factor"] = factor
        exports[factor_path.name] = factor_path
    for name, source in exports.items():
        with source.open("rb") as incoming, (OUTPUT / name).open("xb") as outgoing:
            shutil.copyfileobj(incoming, outgoing, 1 << 20)
    with (OUTPUT / "run_receipt.json").open("x", encoding="utf-8") as output:
        json.dump(receipt, output, indent=2, ensure_ascii=False)
        output.write("\n")
    staged = OUTPUT / ".submission.zip.pending"
    with packaged.open("rb") as incoming, staged.open("xb") as outgoing:
        shutil.copyfileobj(incoming, outgoing, 1 << 20)
    pin(staged, receipt["submission_sha256"])
    os.link(staged, final_zip)
    staged.unlink()
    log("ready", output=str(final_zip), submission_sha256=receipt["submission_sha256"],
        dqi_cost=dqi["score"], chemistry_cost=chemistry_result["score"],
        inverse_cost=inverse["score"], elapsed_seconds=receipt["elapsed_seconds"],
        submission_performed=False)


if __name__ == "__main__":
    main()
