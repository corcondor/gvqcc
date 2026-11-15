"""Replace the source weights and preserve all other arrays and loader bytes."""
import argparse
from hashlib import sha256
from pathlib import Path
from shutil import copyfile

import numpy as np


def stage(source, weights, output):
    source_npz = source / "submission.npz"
    assert sha256(source_npz.read_bytes()).hexdigest() == (
        "df226db938dc440a37391091fba46c90ebcd14acfda88ec84939361ebcf9a955"
    )
    with np.load(source_npz, allow_pickle=False) as data:
        arrays = dict(data)
    with np.load(weights, allow_pickle=False) as update:
        for name in ("W", "H2_I"):
            assert arrays[name].shape == update[name].shape
            assert np.isfinite(update[name]).all()
            arrays[name] = update[name]
    output.mkdir(parents=True, exist_ok=False)
    for k in range(15):
        name = f"angle_k_{k}.kmb"
        copyfile(source / name, output / name)
    np.savez_compressed(output / "submission.npz", **arrays)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    stage(args.source, args.weights, args.output)
