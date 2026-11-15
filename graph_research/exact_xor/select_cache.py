"""Keep the least paid-cost KMB for each batch across beam searches."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
from shutil import copyfile


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--variants", type=Path, nargs="+", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    variants = [json.loads((v / "cache_receipt.json").read_text()) for v in args.variants]
    assert all([row["batch"] for row in v] == list(range(1,15)) for v in variants)
    args.out.mkdir(parents=True, exist_ok=False)
    selected = []
    for batch, alternatives in enumerate(zip(*variants, strict=True), 1):
        pick = min(range(len(alternatives)), key=lambda i: alternatives[i]["ccx"])
        row = alternatives[pick]
        name = f"angle_k_{batch}.kmb"
        source = args.variants[pick] / name
        assert sha256(source.read_bytes()).hexdigest() == row["sha256"]
        copyfile(source, args.out / name)
        selected.append(dict(variant=pick, **row))
    for name in ("angle_k_0.kmb", "submission.npz"):
        content = (args.variants[0] / name).read_bytes()
        assert all((v / name).read_bytes() == content for v in args.variants)
        (args.out / name).write_bytes(content)
    (args.out / "cache_receipt.json").write_text(json.dumps(selected, indent=2)+"\n")


if __name__ == "__main__":
    main()
