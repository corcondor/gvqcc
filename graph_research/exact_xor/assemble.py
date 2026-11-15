"""Build the candidate ZIP from the proof, verifier result and unchanged tasks."""
from argparse import ArgumentParser
from hashlib import file_digest, sha256
from io import BytesIO
import json
from math import prod
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def aggregate(reference, costs):
    return prod(reference[name] / costs[name] for name in reference) ** (1 / 3)


def main():
    parser = ArgumentParser(description=__doc__)
    for key in ("previous", "previous-scorecard", "family", "proof", "chemistry",
                "strict-baseline", "output", "receipt"):
        parser.add_argument("--" + key, type=Path, required=True)
    args = parser.parse_args()
    previous = json.loads(args.previous_scorecard.read_text())
    verification = json.loads(args.chemistry.read_text())
    strict_baseline = json.loads(args.strict_baseline.read_text())
    proof = json.loads(args.proof.read_text())
    assert verification["status"] == strict_baseline["status"] == "PASS"
    assert verification["verified_shots"] == 78080 and len(proof) == 15
    assert all(p["addresses"] == 1220 and p["arbitrary_word_bits"] == 40 for p in proof)
    assert sum(p["toffoli_per_pass"] for p in proof) == verification["resources"]["angles_toffoli_per_pass"]
    assert sha256(args.previous.read_bytes()).hexdigest() == previous["zip_sha256"]
    result = {}
    digest = sha256()
    for i, p in enumerate(proof):
        name = f"angle_k_{i}.kmb"
        payload = (args.family / name).read_bytes()
        assert p["file"] == name and sha256(payload).hexdigest() == p["sha256"]
        digest.update(payload)
        result[f"dfthcsos/{name}"] = payload
    npz_name = "dfthcsos/submission.npz"
    result[npz_name] = (args.family / "submission.npz").read_bytes()
    with ZipFile(BytesIO(result[npz_name])) as npz:
        for name in ("U", "W", "H2_I", "H1_I", "Hsym_lower", "tree_edges"):
            digest.update(npz.read(name + ".npy"))
    assert digest.hexdigest() == verification["submission_sha256"]
    hashes = {name: sha256(payload).hexdigest() for name, payload in result.items()}
    with ZipFile(args.previous) as source, ZipFile(args.output, "x", compression=ZIP_DEFLATED,
                                                   compresslevel=6) as target:
        for name in ("dqi.kmb", "invsqrt.kmb"):
            h = sha256()
            with source.open(name) as reader, target.open(name, "w") as writer:
                for chunk in iter(lambda: reader.read(1 << 20), b""):
                    h.update(chunk)
                    writer.write(chunk)
            hashes[name] = h.hexdigest()
            assert hashes[name] == previous["members"][name]
        for name, payload in result.items():
            target.writestr(name, payload)
    with ZipFile(args.output) as archive:
        assert len(archive.namelist()) == 18 and set(archive.namelist()) == set(hashes)
        for name, h in hashes.items():
            with archive.open(name) as reader:
                assert file_digest(reader, "sha256").hexdigest() == h
    costs = {**previous["costs"], "chemistry": verification["score"]}
    reference = previous["reference_costs"]
    score = aggregate(reference, costs)
    base = aggregate(reference, {**costs, "chemistry": strict_baseline["score"]})
    with args.output.open("rb") as file:
        archive_hash = file_digest(file, "sha256").hexdigest()
    report = {
        "local_score": score,
        "local_strict_baseline_score": base,
        "local_strict_improvement": score - base,
        "previous_streamed_only_score": previous["local_score"],
        "costs": costs,
        "reference_costs": reference,
        "chargeable_chemistry_toffoli": verification["toffoli_count"],
        "chemistry_verified_shots": verification["verified_shots"],
        "chemistry_submission_digest": digest.hexdigest(),
        "kaggle_submitted": False,
        "members": hashes,
        "zip_size": args.output.stat().st_size,
        "zip_sha256": archive_hash,
    }
    args.receipt.write_text(json.dumps(report, indent=2) + "\n")
    print({k: v for k, v in report.items() if k != "members"})


if __name__ == "__main__":
    main()
