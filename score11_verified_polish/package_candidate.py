#!/usr/bin/env python3
"""Package the verified chemistry update with the pinned unchanged score10 members."""
from argparse import ArgumentParser
from hashlib import sha256
from io import BytesIO
import json
from math import prod
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

CHEM = "dfthcsos/submission.npz"
KEYS = ("U", "W", "H2_I", "H1_I", "Hsym_lower", "tree_edges")


def main():
    parser = ArgumentParser(description=__doc__)
    for flag in ("score6", "joint", "baseline", "chemistry", "verified", "output", "receipt"):
        parser.add_argument("--"+flag, type=Path, required=True)
    args = parser.parse_args()
    baseline = json.loads(args.baseline.read_text())
    verifier = json.loads(args.verified.read_text())
    assert verifier["status"] == "PASS" and verifier["verified_shots"] == 78080
    assert (verifier["angles_within_cap"] if "angles_within_cap" in verifier
            else verifier["resources"]["angles_within_cap"])
    with ZipFile(args.score6) as score6, ZipFile(args.joint) as joint:
        names = sorted(joint.namelist())
        assert len(names) == 18 and set(names) == set(score6.namelist()) == set(baseline["members"])
        original = {n: (joint if n.startswith("dfthcsos/") else score6).read(n) for n in names}
    assert {n: sha256(b).hexdigest() for n,b in original.items()} == baseline["members"]
    new_factorization = (args.chemistry / "submission.npz").read_bytes()
    with ZipFile(BytesIO(original[CHEM])) as old, ZipFile(BytesIO(new_factorization)) as new:
        assert set(old.namelist()) == set(new.namelist())
        changed = sorted(n for n in old.namelist() if old.read(n) != new.read(n))
        assert changed == ["H2_I.npy", "W.npy"], changed
        digest = sha256()
        for i in range(15):
            loader = f"angle_k_{i}.kmb"
            assert (args.chemistry / loader).read_bytes() == original[f"dfthcsos/{loader}"]
            digest.update(original[f"dfthcsos/{loader}"])
        for key in KEYS:
            digest.update(new.read(f"{key}.npy"))
    assert digest.hexdigest() == verifier["submission_sha256"]
    with ZipFile(args.output, "x", compression=ZIP_DEFLATED, compresslevel=6) as package:
        for name, content in original.items():
            package.writestr(name, new_factorization if name == CHEM else content)
    with ZipFile(args.output) as package:
        assert package.testzip() is None
        assert sorted(package.namelist()) == names
        assert [n for n in names if package.read(n) != original[n]] == [CHEM]
        assert package.read(CHEM) == new_factorization
        member_hashes = {n: sha256(package.read(n)).hexdigest() for n in names}
    costs = {**baseline["costs"], "chemistry": verifier["score"]}
    refs = baseline["references"]
    score = prod(refs[k]/costs[k] for k in refs)**(1/3)
    previous_score = baseline["local_score_recomputed"]
    assert score > previous_score and costs["chemistry"] < baseline["costs"]["chemistry"]
    receipt = {
        "local_score": score, "baseline_local_score": previous_score,
        "local_improvement": score-previous_score, "costs": costs,
        "baseline_costs": baseline["costs"], "reference_costs": refs,
        "chemistry_new_verifier": verifier,
        "invsqrt_and_dqi_source": "byte-identical score10",
        "kaggle_submitted": False,
        "changed_members": [CHEM], "changed_npz_entries": changed,
        "members": member_hashes,
        "zip_sha256": sha256(args.output.read_bytes()).hexdigest(),
        "zip_size": args.output.stat().st_size,
    }
    args.receipt.write_text(json.dumps(receipt, indent=2)+"\n")
    print(json.dumps({k:receipt[k] for k in ("local_score","baseline_local_score","local_improvement","zip_sha256","zip_size")},indent=2))


if __name__=="__main__":
    main()
