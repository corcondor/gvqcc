"""Official stock DQI verifier on pinned archive members."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory
from time import monotonic
from zipfile import ZipFile

import kickmix as km
import numpy as np
import scipy
import verify_submission_dqi as verifier

HERE = Path(__file__).resolve().parent
BASELINE = "204f1c0c1fe51513f55ebef0a651e33fab83fcfb2297e23e0445920876ac5f6e"
DONOR = "e986d41663fa78ea2ed4ab0a47ebc4d99441ad1660b80e02872e7508cbce92a7"
STOCK_VERIFIER = "f14274bc0943fb9769ddb01131be6063191a15009fe1caf1d4bdd9fd25194e65"

def digest(path):
    with Path(path).open("rb") as src:
        return hashlib.file_digest(src, "sha256").hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("archive", type=Path)
    p.add_argument("--variant", choices=("v7", "replacement"), required=True)
    p.add_argument("--salt", default="")
    p.add_argument("--matched-v7-default", action="store_true")
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    expected = BASELINE if args.variant == "v7" else DONOR
    spec = verifier.ProblemSpecDQI.benchmark_instance()
    verifier_hash = digest(verifier.__file__)
    assert verifier_hash == STOCK_VERIFIER
    with TemporaryDirectory() as temp:
        path = Path(temp) / "dqi.kmb"
        with ZipFile(args.archive) as archive, archive.open("dqi.kmb") as read, path.open("wb") as write:
            shutil.copyfileobj(read, write, 4 << 20)
        member_hash = digest(path)
        assert member_hash == expected, (member_hash, expected)
        circuit = km.Circuit.from_file(path, format="kmb")
    started = monotonic()
    seed = int(BASELINE, 16) if args.matched_v7_default else None
    result = verifier.verify(circuit, spec, salt=args.salt, seed=seed)
    assert result["circuit_sha256"] == member_hash
    record = {"verifier": result, "salt": args.salt, "variant": args.variant,
              "member_sha256": member_hash, "canonical_sha256": result["circuit_sha256"],
              "official_verifier_sha256": verifier_hash,
              "kickmix_binary_sha256": digest(km.__file__), "kickmix_version": km.__version__,
              "python": sys.version, "numpy": np.__version__, "scipy": scipy.__version__,
              "explicit_seed": str(seed) if seed is not None else None,
              "elapsed_seconds": monotonic() - started}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(record, indent=2))

if __name__ == "__main__":
    main()
