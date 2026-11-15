"""Exact linear-span substitution scan of fixed CCX sites in ANGLE loaders."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

import kickmix as km
import numpy as np

N = 1220
ONES = (1 << N) - 1
TAGS = dict(zip((18, 26, 34, 42, 50), ((0, 1), (0, 2), (1, 2), (0, 3), (1, 3))))
WIRES = re.compile(r"\bq(\d+)\b")


def bitmap(values):
    return int.from_bytes(np.packbits(values, bitorder="little").tobytes(), "little")


def establish_basis(state, exclude):
    basis = {}
    for q, value in enumerate([*state, ONES]):
        if q == exclude or not value:
            continue
        word = 1 << q
        while value:
            pivot = value.bit_length()
            if pivot not in basis:
                basis[pivot] = value, word
                break
            row, direction = basis[pivot]
            value ^= row
            word ^= direction
    return basis


def witness(target, basis):
    value, coeff = target, 0
    while value:
        pivot = value.bit_length()
        if pivot not in basis:
            return None
        row, direction = basis[pivot]
        coeff ^= direction
        value ^= row
    return coeff


def scan(path, k, words, strict):
    circuit = km.Circuit.from_file(path)
    n = circuit.num_qubits
    x = np.arange(N)
    state = [bitmap((x >> q) & 1) for q in range(11)] + [0] * (n - 11)
    initial_readout = state[:11]
    for i in range(40):
        q = 11 + i
        if not strict and k > 0 and q in TAGS:
            a, b = TAGS[q]
            state[q] = (1 << (N + i - 1)) ^ (state[a] & state[b])
        else:
            state[q] = 1 << (N + i)
    input_z = state[11:51]
    pending = None
    encoded = []
    prefix_rank = None
    prefix_paid = 0
    counters = Counter()
    records = []
    output = []
    for line_no, line in enumerate(str(circuit).splitlines(), 1):
        op = line.split()[0]
        q = tuple(map(int, WIRES.findall(line)))
        assert pending is None or op == "CZ", (path, line_no, line)
        patch = None
        if not strict and k and op == "CX" and q[1] in TAGS and q[0] == q[1] - 1 and len(encoded) < len(TAGS):
            encoded.append(q[1])
        if op == "X":
            state[q[0]] ^= ONES
        elif op == "CX":
            state[q[1]] ^= state[q[0]]
        elif op == "SWAP":
            a, b = q
            state[a], state[b] = state[b], state[a]
        elif op == "CCX":
            a, b, t = q
            assert state[a] <= ONES and state[b] <= ONES, (path, line_no, line)
            product = state[a] & state[b]
            basis = establish_basis(state, t)
            coeff = witness(product, basis)
            kind = "workspace_or_tag" if t >= 51 or t in TAGS else "word"
            counters["examined_" + kind] += 1
            if coeff is not None:
                patch = [f"CX q{i} q{t}" for i in range(n) if coeff >> i & 1]
                if coeff >> n & 1:
                    patch.append(f"X q{t}")
                records.append({"line": line_no, "old": line, "replacement": patch})
            state[t] ^= product
            if not strict and k and t >= 51 and not counters["examined_word"]:
                assert set(encoded) == set(TAGS)
                inherited = [*state[:11], *(state[j] for j in TAGS)]
                work = state[51:]
                input_rank = len(establish_basis(inherited, None))
                rank = len(establish_basis([*inherited, *work], None))
                prefix_paid += 1
                prefix_rank = {"original_ccx": prefix_paid,
                               "input_rank_with_constant": input_rank,
                               "output_rank_with_constant": rank,
                               "same_bank_ccx_lower_bound": rank - input_rank}
        elif op == "R":
            assert state[q[0]] == 0
        elif op == "HMR":
            assert line.endswith(" b0") and state[q[0]] <= ONES
            pending = state[q[0]]
            state[q[0]] = 0
        elif op == "CZ":
            assert line.endswith(" if b0")
            assert pending == state[q[0]] & state[q[1]]
            pending = None
        else:
            assert op in {"REGISTER", "APPEND_TO_REGISTER"}
        output.extend(patch if patch is not None else [line])
    assert state[:11] == initial_readout and not any(state[51:])
    delta = words[:,5*k:5*k+5].copy()
    if k:
        delta ^= words[:,5*k-5:5*k]
    for i in range(40):
        assert state[11+i] == input_z[i] ^ bitmap((delta[:,i//8] >> i%8) & 1), (path, i)
    return {
        "file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        **counters, "found": len(records), "substitutions": records,
        "full_feature_bank_prefix_rank": prefix_rank,
    }, output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("family", type=Path)
    parser.add_argument("words", type=Path)
    parser.add_argument("report", type=Path)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()
    words = np.load(args.words, allow_pickle=False)[:N]
    if args.destination:
        assert args.strict
        args.destination.mkdir(exist_ok=False)
        (args.destination / "submission.npz").write_bytes((args.family / "submission.npz").read_bytes())
    reports = []
    for k in range(15):
        path = args.family / f"angle_k_{k}.kmb"
        report, output = scan(path, k, words, args.strict)
        reports.append(report)
        if args.destination:
            target = args.destination / path.name
            if not report["found"]:
                target.write_bytes(path.read_bytes())
            else:
                km.Circuit("\n".join(output)+"\n").to_file(target, format="kmb")
        print(k, report["found"], flush=True)
    args.report.write_text(json.dumps({
        "address_count": N, "input_trait": "all 40 arbitrary target bits" if args.strict
        else "canonical five logical product tags on batches 1 to 14, remaining data arbitrary",
        "batches": reports, "found": sum(x["found"] for x in reports)
    }, indent=2) + "\n")
