"""Apply only independently optimized weight arrays to a hash-pinned score12 ZIP."""
from __future__ import annotations

import argparse
from hashlib import sha256
import io
import json
from pathlib import Path
from zipfile import ZipFile

import numpy as np


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source_zip", type=Path)
    p.add_argument("source_receipt", type=Path)
    p.add_argument("weights", type=Path)
    p.add_argument("output", type=Path)
    p.add_argument("--xor-patch", action="store_true")
    args = p.parse_args()
    receipt = json.loads(args.source_receipt.read_text())
    assert sha256(args.source_zip.read_bytes()).hexdigest() == receipt["zip_sha256"]
    args.output.mkdir(parents=True, exist_ok=False)
    with ZipFile(args.source_zip) as archive:
        for i in range(15):
            member = f"dfthcsos/angle_k_{i}.kmb"
            data = archive.read(member)
            assert sha256(data).hexdigest() == receipt["members"][member]
            (args.output / Path(member).name).write_bytes(data)
        member = "dfthcsos/submission.npz"
        raw = archive.read(member)
        assert sha256(raw).hexdigest() == receipt["members"][member]
        with np.load(io.BytesIO(raw), allow_pickle=False) as f:
            original = dict(f)
    with np.load(args.weights, allow_pickle=False) as f:
        if not args.xor_patch:
            assert np.array_equal(f["tree_edges"], original["tree_edges"])
            assert sha256(f["angle_words"].astype(np.uint8).tobytes()).hexdigest() == "8caf7416de79102103757e3ab7ab4b6bbebfad9b1bf1ecd564c20eb948dbfcea"
        for name in ("W", "H2_I"):
            prior = original[name]
            if args.xor_patch:
                patch = f[name]
                assert patch.dtype == np.uint8 and patch.shape == (prior.nbytes,)
                raw = np.bitwise_xor(np.frombuffer(prior.tobytes(), dtype=np.uint8), patch)
                value = raw.view(prior.dtype).reshape(prior.shape)
            else:
                value = f[name]
            assert value.dtype == prior.dtype and value.shape == prior.shape
            assert np.all(np.isfinite(value))
            original[name] = value
    np.savez_compressed(args.output / "submission.npz", **original)


if __name__ == "__main__":
    main()
