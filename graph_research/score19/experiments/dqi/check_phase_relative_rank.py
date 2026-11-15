"""Exercise the native scanner on exact positive and negative KMB fixtures."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import subprocess
import tempfile

import kickmix as km


CASES = {
    "repeated_product": (
        "CCX q0 q1 q2\nCCX q0 q1 q3\n", {(0, 2, 0, 2, 1), (0, 2, 1, 2, 1)}
    ),
    "moved_selector": (
        "CCX q0 q1 q2\nSWAP q0 q3\nCCX q3 q1 q4\n", {(0, 3, 0, 2, 1), (0, 3, 1, 2, 1)}
    ),
    "mixed_controlled_linear": (
        "CSWAP q0 q1 q2\nCX q1 q2\nCCX q0 q2 q1\n", {(0, 3, 0, 2, 0)}
    ),
    "independent_products": ("CCX q0 q1 q2\nCCX q0 q3 q4\n", set()),
    "wrapped_selector": (
        "CCX q0 q1 q2\nCX q3 q0\nCX q3 q0\nCCX q0 q1 q4\n",
        {(0, 4, 0, 2, 1), (0, 4, 1, 2, 1)},
    ),
    "phase_passive": (
        "CCX q0 q1 q2\nCZ q2 q3\nCCX q0 q1 q4\n",
        {(0, 3, 0, 2, 1), (0, 3, 1, 2, 1)},
    ),
    "nested_passive_phase": (
        "CCX q0 q1 q2\nPUSH_CONDITION if b0\nCZ q2 q3\nPOP_CONDITION\nCCX q0 q1 q4\n",
        {(0, 5, 0, 2, 1), (0, 5, 1, 2, 1)},
    ),
    "nested_quantum_update": (
        "CCX q0 q1 q2\nPUSH_CONDITION if b0\nX q3\nPOP_CONDITION\nCCX q0 q1 q4\n",
        set(),
    ),
    "reset_remains_barrier": ("CCX q0 q1 q2\nR q3\nCCX q0 q1 q4\n", set()),
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scanner", type=Path)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    records = {}
    with tempfile.TemporaryDirectory() as inner:
        directory = Path(inner)
        for name, (source, expected) in CASES.items():
            tape = directory / f"{name}.kmb"
            hits = directory / f"{name}.tsv"
            km.Circuit(source).to_file(str(tape), format="kmb")
            result = subprocess.run(
                [str(args.scanner.resolve()), str(tape), str(hits)],
                check=True, capture_output=True, text=True,
            )
            with hits.open() as file:
                actual = {tuple(map(int, row)) for row in list(csv.reader(file, delimiter="\t"))[1:]}
            assert actual == expected, (name, sorted(actual), sorted(expected))
            records[name] = {"expected_and_observed": sorted(actual), "scan": json.loads(result.stdout)}
    args.receipt.write_text(json.dumps(records, indent=2) + "\n")


if __name__ == "__main__":
    main()
