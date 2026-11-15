"""Find reachable-domain compressions of adjacent pair nonlinearities."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import random
from zipfile import ZipFile

import kickmix as km
import numpy as np

from audit import data_update, MAX_X, PIN, WIRES


def basis(forms):
    pivots = {}
    for i, function in enumerate(forms):
        coefficients = 1 << i
        while function:
            pivot = function.bit_length() - 1
            if pivot not in pivots:
                pivots[pivot] = function, coefficients
                break
            function ^= pivots[pivot][0]
            coefficients ^= pivots[pivot][1]
    return pivots


def solve(pivots, function):
    coefficients = 0
    while function:
        pivot = function.bit_length() - 1
        if pivot not in pivots:
            return None
        function ^= pivots[pivot][0]
        coefficients ^= pivots[pivot][1]
    return coefficients


def apply_combination(form, values):
    answer = 0
    while form:
        bit = form & -form
        answer ^= values[bit.bit_length() - 1]
        form ^= bit
    return answer


def affine_control_span(masks):
    space = {0}
    for mask in masks:
        space |= {v ^ mask for v in space}
    return sorted(space - {0})


def scan(lines, xs, selected=None):
    one = (1 << len(xs)) - 1
    n = 46
    qmask = (1 << n) - 1
    identity = [1 << q for q in range(n)]
    values = [
        int.from_bytes(np.packbits((xs >> q) & 1, bitorder="little").tobytes(), "little")
        for q in range(22)
    ] + [0] * (n - 22)
    first = None
    branches = []
    hits = []
    for i, line in enumerate(lines):
        op = line.split()[0]
        wires = tuple(map(int, WIRES.findall(line)))
        if op == "PUSH_CONDITION":
            branches.append(values.copy())
        elif op == "POP_CONDITION":
            assert branches.pop() == values
        if op == "CCX":
            a, b, t = wires
            p2 = values[a] & values[b]
            if first is not None and (selected is None or i in selected):
                j, old_a, old_b, old_t, p1, before = first
                output_mask = sum(1 << q for q in range(n) if rows[q] >> old_t & 1)
                pivots = basis(before + [one])
                common = {"lines_1based": [j + 1, i + 1]}
                if output_mask == 1 << t:
                    goal = p1 ^ p2
                    choices = affine_control_span([1 << old_a, 1 << old_b,
                                                    rows[a] & qmask, rows[b] & qmask])
                    terms = {f: apply_combination(f, before) for f in choices}
                    for k, left in enumerate([0] + choices):
                        if not left:
                            cases = [(0, goal)]
                        else:
                            cases = [(right, goal ^ (terms[left] & terms[right]))
                                     for right in choices[k:]]
                        for right, residual in cases:
                            code = solve(pivots, residual)
                            if code is not None:
                                hits.append(dict(common, case="codirectional", factors=[left, right],
                                                 affine_mask=code))
                else:
                    for name, prospective in (("first", p1), ("second", p2), ("sum", p1 ^ p2)):
                        code = solve(pivots, prospective)
                        if code is not None:
                            hits.append(dict(common, case=name, affine_mask=code))
            first = (i, a, b, t, p2, values.copy())
            rows = identity.copy()
        elif first is not None:
            if " if " in line:
                first = None
            elif op == "X":
                t, = wires
                rows[t] ^= 1 << n
            elif op == "CX":
                a, t = wires
                rows[t] ^= rows[a]
            elif op == "SWAP":
                a, b = wires
                rows[a], rows[b] = rows[b], rows[a]
            else:
                first = None
        data_update(op, wires, values, one)
    assert not branches
    return hits


def wide_screen(lines, xs, tests=None):
    one = (1 << len(xs)) - 1
    n = 46
    values = [
        int.from_bytes(np.packbits((xs >> q) & 1, bitorder="little").tobytes(), "little")
        for q in range(22)
    ] + [0] * (n - 22)
    first = None
    hits = []
    examined = 0
    branches = []
    for i, line in enumerate(lines):
        op = line.split()[0]
        wires = tuple(map(int, WIRES.findall(line)))
        if op == "PUSH_CONDITION":
            branches.append(values.copy())
        elif op == "POP_CONDITION":
            assert branches.pop() == values
        if op == "CCX":
            a, b, t = wires
            p2 = values[a] & values[b]
            if first is not None and direction == 1 << t and (tests is None or i in tests):
                first_i, p1, before = first
                goal = p1 ^ p2
                affine_terms = before + [one]
                masks = {1 << q for q in range(n)}
                masks |= {(1 << a) ^ (1 << b) for a in range(n) for b in range(a)}
                if tests is not None:
                    masks &= tests[i]
                for mask in sorted(masks):
                    left = apply_combination(mask, before)
                    pivots = basis(affine_terms + [left & right for right in before])
                    coeff = solve(pivots, goal)
                    examined += 1
                    if coeff is not None:
                        hits.append({"lines_1based": [first_i + 1, i + 1], "left_mask": mask,
                                     "affine_mask": coeff & ((1 << len(affine_terms)) - 1),
                                     "right_mask": coeff >> len(affine_terms)})
            first = (i, p2, values.copy())
            direction = 1 << t
        elif first is not None:
            if " if " in line:
                first = None
            elif op == "CX":
                a, t = wires
                direction ^= ((direction >> a) & 1) << t
            elif op == "SWAP":
                a, b = wires
                if ((direction >> a) ^ (direction >> b)) & 1:
                    direction ^= (1 << a) ^ (1 << b)
            elif op != "X":
                first = None
        data_update(op, wires, values, one)
    assert not branches
    return hits, examined


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("archive", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    with ZipFile(args.archive) as archive:
        kmb = archive.read("invsqrt.kmb")
    assert hashlib.sha256(kmb).hexdigest() == PIN
    circuit = km.Circuit.from_file(io.BytesIO(kmb), format="kmb")
    lines = str(circuit).splitlines()
    rng = random.Random(202611151957)
    sample = sorted(set(list(range(1, 257)) + [rng.randint(1, MAX_X) for _ in range(2048)]))
    hits = scan(lines, np.array(sample, dtype=np.uint32))
    targets = {hit["lines_1based"][-1] - 1 for hit in hits}
    confirmed = scan(lines, np.arange(1, MAX_X + 1, dtype=np.uint32), targets) if targets else []
    broad, tested = wide_screen(lines, np.array(sample, dtype=np.uint32))
    broad_tests = {}
    for hit in broad:
        broad_tests.setdefault(hit["lines_1based"][-1] - 1, set()).add(hit["left_mask"])
    broad_confirmed, _ = wide_screen(lines, np.arange(1, MAX_X + 1, dtype=np.uint32), broad_tests) if broad_tests else ([], 0)
    report = {"source_sha256": PIN, "candidate_windows": 431, "sample_inputs": len(sample),
              "sample_hits": hits, "full_domain_hits": confirmed,
              "wide_screen_left_factors_tested": tested, "wide_screen_sample_hits": broad,
              "wide_screen_full_domain_hits": broad_confirmed,
              "scope": "For independent output directions, test if either actual update or their XOR is affine on reached wires. For same output direction, test if XOR is affine plus a product from the span of the original four controls or from a factor of at most two live wires and an arbitrary linear second factor."}
    args.output.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
