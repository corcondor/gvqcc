#!/usr/bin/env python3
"""Build an 18-member submission ZIP from hash-bound official PASS receipts.

Unchanged DQI/invsqrt bytes retain their original full verifier receipts.
A replaced chemistry family must bind every loader and the NPZ. This tool
only packages files and calculates a LOCAL score; it never submits them.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import math
from pathlib import Path
import shutil
import zipfile

BASE_ZIP_SHA256 = "938e08143c113817ca1c3749a361911a0f60b2db745735d4f8f4b1fc0a1e2b71"
EXPECTED_VERIFIERS = {
    "dqi": "f14274bc0943fb9769ddb01131be6063191a15009fe1caf1d4bdd9fd25194e65",
    "invsqrt": "ddef520dec6b68d1cf0a6f328ddd36d79eb84570b9192cf3f7acaf073f06733a",
    "dfthcsos": "ca84ca08e6e9280922cda3b539d4776ae58990b2b03b5619a53d65de67df9d2b",
}


def stream_digest(stream):
    h, count = hashlib.sha256(), 0
    for data in iter(lambda: stream.read(1 << 20), b""):
        h.update(data)
        count += len(data)
    return h.hexdigest(), count


def sha(path):
    with Path(path).open("rb") as f:
        return stream_digest(f)[0]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base-zip", type=Path, required=True)
    p.add_argument("--prior-scorecard", type=Path, required=True)
    p.add_argument("--invsqrt-receipt", type=Path, required=True)
    p.add_argument("--dqi-receipt", type=Path, required=True)
    p.add_argument("--dqi", type=Path)
    p.add_argument("--chemistry", type=Path, required=True)
    p.add_argument("--loader-directory", type=Path, help="Optional separate directory containing the fifteen bound loaders")
    p.add_argument("--chemistry-receipt", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--scorecard", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    a = p.parse_args()
    assert sha(a.base_zip) == BASE_ZIP_SHA256
    old = json.loads(a.prior_scorecard.read_text())
    docs = {"dqi": json.loads(a.dqi_receipt.read_text()),
            "invsqrt": json.loads(a.invsqrt_receipt.read_text()),
            "dfthcsos": json.loads(a.chemistry_receipt.read_text())}
    results = {k: v.get("official_result", v) for k, v in docs.items()}
    for k, r in results.items():
        assert r["status"] == "PASS", k
        assert docs[k]["verifier_sha256"] == EXPECTED_VERIFIERS[k], k
        assert r["verified_shots"] == {"dqi": 102400, "invsqrt": 200540928, "dfthcsos": 78080}[k]
    ci = docs["dfthcsos"]
    npz_sha = ci["factorization"]["sha256"]
    chemistry_pins = {q["name"]: q["sha256"] for q in ci["loaders"]}
    chemistry_pins["submission.npz"] = npz_sha
    names = {"invsqrt.kmb", "dqi.kmb", *("dfthcsos/"+s for s in chemistry_pins)}
    assert len(names) == 18
    expected = {"invsqrt.kmb": results["invsqrt"]["circuit_sha256"],
                "dqi.kmb": results["dqi"]["circuit_sha256"],
                **{"dfthcsos/"+s: h for s, h in chemistry_pins.items()}}
    def chemistry_source(name):
        directory = a.chemistry if name == "submission.npz" or not a.loader_directory else a.loader_directory
        return directory / name
    for name, h in chemistry_pins.items():
        assert sha(chemistry_source(name)) == h, name
    if a.dqi:
        assert sha(a.dqi) == expected["dqi.kmb"]
    chem = results["dfthcsos"]
    metrics = chem["metrics"]
    assert metrics["error_1"] <= .02 and metrics["error_2"] <= .02
    assert metrics["E_gap"] > 3.914898 and metrics["Lambda"] > 49 and metrics["gap_in_domain"]
    calculated = {
        "dqi": results["dqi"]["repetition_factor"] * results["dqi"]["num_qubits"] ** 2 * results["dqi"]["toffoli_count"],
        "invsqrt": results["invsqrt"]["num_qubits"] * results["invsqrt"]["toffoli_equivalent"],
        "dfthcsos": chem["lambda_eff"] * chem["num_qubits"] * chem["toffoli_count"],
    }
    for k, v in calculated.items():
        assert math.isclose(v, results[k]["score"], rel_tol=1e-13), k
    score = math.prod(old["reference_costs"][k] / v for k, v in calculated.items()) ** (1/3)
    assert score > old["local_combined_score"], "Refusing to package a non-improving main candidate"
    assert not a.output.exists(), "Choose a new output path; prior candidates are frozen"
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(a.base_zip) as src, zipfile.ZipFile(a.output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as dst:
        assert set(src.namelist()) == names and len(src.namelist()) == 18
        for name in sorted(names):
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 15, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            path = chemistry_source(name.removeprefix("dfthcsos/")) if name.startswith("dfthcsos/") else (a.dqi if name == "dqi.kmb" else None)
            if path is not None:
                with path.open("rb") as f, dst.open(info, "w", force_zip64=True) as g:
                    shutil.copyfileobj(f, g, 1 << 20)
            else:
                with src.open(name) as f, dst.open(info, "w", force_zip64=True) as g:
                    shutil.copyfileobj(f, g, 1 << 20)
    members = []
    with zipfile.ZipFile(a.output) as z:
        assert z.testzip() is None
        for name in sorted(names):
            with z.open(name) as f:
                h, n = stream_digest(f)
            assert h == expected[name], name
            members.append({"name": name, "sha256": h, "bytes": n})
    receipts = {"dqi": {"path": str(a.dqi_receipt), "sha256": sha(a.dqi_receipt)},
                "invsqrt": {"path": str(a.invsqrt_receipt), "sha256": sha(a.invsqrt_receipt)},
                "dfthcsos": {"path": str(a.chemistry_receipt), "sha256": sha(a.chemistry_receipt)}}
    card = {"status": "HASH_BOUND_LOCAL_PORTFOLIO_SCORE", "reference_costs": old["reference_costs"],
            "candidate_costs": calculated, "previous_local_score": old["local_combined_score"],
            "local_combined_score": score, "local_combined_increase": score-old["local_combined_score"],
            "local_combined_score_5dp": f"{score:.5f}", "target": 28,
            "remaining_cost_product_reduction_percent": 100*(1-(score/28)**3),
            "chemistry_metrics": metrics, "chemistry_resources": chem["resources"],
            "verification_receipts": receipts, "public_score": None, "submission_performed": False,
            "dqi_limit": "The inherited node13 numerator-zero failure remains. Finite default PASS is not universal correctness.",
            "attribution": "Public4030 chemistry: maoxin123(CC0) and original credited lineage; new H2_I constrained solve and integration in this repository.",
            "zip": {"path": str(a.output), "bytes": a.output.stat().st_size, "sha256": sha(a.output)}}
    manifest = {"created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "archive": card["zip"], "members": members, "crc_pass": True, "all_member_hashes_pass": True,
                "base_zip_sha256": BASE_ZIP_SHA256, "builder_sha256": sha(Path(__file__)),
                "verification_receipts": receipts, "submission_performed": False}
    a.scorecard.write_text(json.dumps(card, indent=2)+"\n")
    a.manifest.write_text(json.dumps(manifest, indent=2)+"\n")
    print(json.dumps(card, indent=2))


if __name__ == "__main__":
    main()
