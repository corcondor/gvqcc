"""Check one exact non-star-local 3-to-2 reduction and phase-boundary controls."""
import argparse
import csv
import json
from pathlib import Path
import subprocess
import tempfile

import kickmix

FLIP_SOURCE = """CCX q0 q1 q4
CCX q0 q2 q5
CX q1 q2
CCX q3 q2 q4
CX q1 q2
"""
FLIP_TARGET = """CX q3 q0
CX q1 q2
CCX q0 q2 q4
CX q1 q2
CX q3 q0
CX q5 q4
CCX q0 q2 q5
CX q5 q4
"""
CASES = {
    "flip_only": (FLIP_SOURCE, False, {"flip-merge"}),
    "duplicate_product": ("CCX q0 q1 q2\nCCX q0 q1 q3\n", True, {"input"}),
    "common_product_output": ("CCX q0 q1 q4\nCX q0 q2\nCCX q1 q2 q4\n", False,
                              {"input", "output"}),
    "independent": ("CCX q0 q1 q2\nCCX q0 q3 q4\n", False, set()),
    "phase_transparent": ("CCX q0 q1 q2\nCZ q0 q1\nCCX q0 q1 q3\n", True, {"input"}),
    "phase_cuts": ("CCX q0 q1 q2\nCZ q0 q2\nCCX q0 q1 q3\n", False, set()),
    "nonlinear_cuts": ("CCX q0 q1 q2\nCCX q2 q3 q4\n", False, set()),
}


def eval_state(code, data):
    state = [(data >> q) & 1 for q in range(6)]
    for line in code.splitlines():
        gate, *pins = line.split()
        *controls, target = (int(q[1:]) for q in pins)
        state[target] ^= all(state[q] for q in controls)
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scanner", type=Path)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    for state in range(64):
        assert eval_state(FLIP_SOURCE, state) == eval_state(FLIP_TARGET, state)
    receipts = {}
    with tempfile.TemporaryDirectory() as name:
        path = Path(name)
        for case, (code, dependence, expected_stars) in CASES.items():
            tape = path / f"{case}.kmb"
            hits = path / f"{case}.tsv"
            kickmix.Circuit(code).to_file(str(tape), format="kmb")
            run = subprocess.run([args.scanner.absolute(), tape, hits], check=True,
                                 capture_output=True, text=True)
            stars = set()
            with Path(f"{hits}.stars").open() as file:
                for row in csv.DictReader(file, delimiter="\t"):
                    stars.add(row["type"])
            actual_dependence = len(hits.read_text().splitlines()) > 1
            assert actual_dependence == dependence, (case, actual_dependence)
            assert stars == expected_stars, (case, stars)
            receipts[case] = json.loads(run.stdout)
    args.report.write_text(json.dumps({"fixture_cases": receipts, "exact_flip_inputs": 64},
                                      indent=2) + "\n")


if __name__ == "__main__":
    main()
