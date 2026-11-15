"""Select the cheapest independently compiled circuit for each ANGLE batch."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
from shutil import copyfile


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--incumbent", type=Path, required=True)
    parser.add_argument("--variants", type=Path, nargs="+", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(exist_ok=False, parents=True)
    variants = [args.incumbent, *args.variants]
    rows = {
        folder: {row["batch"]: row
                 for row in json.loads((folder / "cache_receipt.json").read_text())
                 if "ccx" in row}
        for folder in variants
    }

    selected = []
    for batch in range(1, 15):
        alternatives = [(folder, rows[folder][batch]) for folder in variants
                        if batch in rows[folder]]
        folder, row = min(alternatives, key=lambda x: x[1]["ccx"])
        name = f"angle_k_{batch}.kmb"
        source = folder / name
        assert sha256(source.read_bytes()).hexdigest() == row["sha256"]
        copyfile(source, args.out / name)
        selected.append({**row, "selected_from": folder.name})
    for name in ("angle_k_0.kmb", "submission.npz"):
        copyfile(args.incumbent / name, args.out / name)
    (args.out / "cache_receipt.json").write_text(json.dumps(selected, indent=2) + "\n")


if __name__ == "__main__":
    main()
