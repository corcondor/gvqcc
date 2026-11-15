"""Screen adjacent non-linear gates for exact common-factor CCX fusion."""

import argparse
import hashlib
import io
import json
import re
from pathlib import Path
from zipfile import ZipFile

import kickmix as km

PIN = "684106f101730ca193627229920a0501bef9ea10ccfb34aa453fcf63edadb50a"
WIRES = re.compile(r"\bq(\d+)\b")


def span(a, b):
    if a and b and a != b:
        return {a, b, a ^ b}
    return set()


def terms(affine_row, constant):
    answer = set()
    while affine_row:
        bit = affine_row & -affine_row
        affine_row ^= bit
        answer.add(0 if bit == constant else bit)
    return answer


def product(left, right):
    answer = set()
    for a in left:
        for b in right:
            monomial = a | b
            answer.symmetric_difference_update((monomial,))
    return answer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    with ZipFile(args.archive) as archive:
        source = archive.read("invsqrt.kmb")
    assert hashlib.sha256(source).hexdigest() == PIN
    circuit = km.Circuit.from_file(io.BytesIO(source), format="kmb")
    lines = str(circuit).splitlines()
    n = circuit.num_qubits
    identity = [1 << q for q in range(n)]
    constant = 1 << n
    first = None
    counts = {"pairs": 0, "independent": 0, "same_homogeneous_plane": 0,
              "same_direction": 0, "same_direction_shared_factor": 0,
              "dependent_second_is_affine": 0, "dependent_second_same_nonlinearity": 0}
    hits = []
    for i, line in enumerate(lines):
        op = line.split()[0]
        wires = tuple(map(int, WIRES.findall(line)))
        if op == "CCX":
            a, b, t = wires
            if first is not None:
                counts["pairs"] += 1
                j, old_a, old_b, old_t = first
                old_delta = 1 << old_t
                output_mask = sum(1 << q for q in range(n) if rows[q] & old_delta)
                if not ((rows[a] | rows[b]) & old_delta):
                    counts["independent"] += 1
                    old_span = span(1 << old_a, 1 << old_b)
                    new_span = span(rows[a] & (constant - 1), rows[b] & (constant - 1))
                    const_free = not ((rows[a] | rows[b]) & constant)
                    if old_span == new_span:
                        counts["same_homogeneous_plane"] += 1
                        hits.append({"lines_1based": [j + 1, i + 1], "type": "same_plane",
                                     "rows_as_ints": [rows[a], rows[b]], "first_output_mask": output_mask})
                    if output_mask == 1 << t:
                        counts["same_direction"] += 1
                        shared = old_span & new_span
                        if shared:
                            counts["same_direction_shared_factor"] += 1
                            hits.append({"lines_1based": [j + 1, i + 1], "type": "common_factor",
                                         "common_factor_masks": sorted(shared),
                                         "rows_as_ints": [rows[a], rows[b]], "constants_zero": const_free})
                else:
                    # The second nonlinear output direction differs from the first.
                    # Its ANF can share one product with the first exactly when its
                    # nonlinear part is zero or the same monomial as the first's.
                    assert output_mask != 1 << t
                    p = (1 << old_a) | (1 << old_b)
                    left = terms(rows[a], constant)
                    right = terms(rows[b], constant)
                    if rows[a] & old_delta:
                        left.add(p)
                    if rows[b] & old_delta:
                        right.add(p)
                    nonlinear = {term for term in product(left, right) if term.bit_count() >= 2}
                    if not nonlinear:
                        counts["dependent_second_is_affine"] += 1
                        hits.append({"lines_1based": [j + 1, i + 1], "type": "dependent_affine"})
                    elif nonlinear == {p}:
                        counts["dependent_second_same_nonlinearity"] += 1
                        hits.append({"lines_1based": [j + 1, i + 1], "type": "dependent_same_product"})
            first = (i, a, b, t)
            rows = identity.copy()
        elif first is not None:
            if " if " in line:
                first = None
            elif op == "X":
                target, = wires
                rows[target] ^= constant
            elif op == "CX":
                control, target = wires
                rows[target] ^= rows[control]
            elif op == "SWAP":
                left, right = wires
                rows[left], rows[right] = rows[right], rows[left]
            else:
                first = None
    result = {"source_sha256": PIN, "counts": counts, "hits": hits,
              "scope": "Consecutive CCX separated only by affine data gates within one guard. All free input states, with independent common planes or common factors, and dependent Boolean ANF tests."}
    args.output.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
