"""Certify the KMB oracle on all legal addresses and all 40 initial word bits."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import re

import kickmix as km
import numpy as np

ADDRESS_COUNT = 1220
ALL_ADDRESSES = (1 << ADDRESS_COUNT) - 1
WIRE = re.compile(r"\bq(\d+)\b")


def bitmap(values):
    return int.from_bytes(np.packbits(values, bitorder="little").tobytes(), "little")


def prove(path, delta):
    circuit = km.Circuit.from_file(path)
    assert circuit.num_qubits <= 128
    addresses = np.arange(ADDRESS_COUNT)
    selection = [(bitmap((addresses >> q) & 1), 0) for q in range(11)]
    word = [(0, 1 << q) for q in range(40)]
    zero = (0, 0)
    state = selection + word + [zero] * (circuit.num_qubits - 51)
    uncorrected = None
    measurements = 0

    def permute(target, value):
        result, coefficient = state[target]
        state[target] = (result ^ value[0], coefficient ^ value[1])

    def and_value(a, b):
        assert state[a][1] == state[b][1] == 0
        return state[a][0] & state[b][0]

    for row, line in enumerate(str(circuit).splitlines(), start=1):
        op = line.split()[0]
        qs = tuple(map(int, WIRE.findall(line)))
        assert uncorrected is None or op == "CZ", (path, row, line)
        assert " if " not in line or op == "CZ"
        if op == "X":
            permute(qs[0], (ALL_ADDRESSES, 0))
        elif op == "CX":
            permute(qs[1], state[qs[0]])
        elif op == "CCX":
            permute(qs[2], (and_value(*qs[:2]), 0))
        elif op == "SWAP":
            a, b = qs
            state[a], state[b] = state[b], state[a]
        elif op == "R":
            assert state[qs[0]] == zero
        elif op == "HMR":
            assert line.endswith(" b0") and state[qs[0]][1] == 0
            uncorrected = state[qs[0]][0]
            state[qs[0]] = zero
            measurements += 1
        elif op == "CZ":
            assert line.endswith(" if b0")
            assert uncorrected == and_value(*qs), (path, row, line)
            uncorrected = None
        else:
            assert op in {"REGISTER", "APPEND_TO_REGISTER"}

    assert uncorrected is None
    assert state[:11] == selection and all(value == zero for value in state[51:])
    for i in range(40):
        word_value = bitmap((delta[:, i // 8] >> (i % 8)) & 1)
        assert state[i+11] == (word_value, 1 << i), (path, i)
    return {
        "file": path.name, "sha256": sha256(path.read_bytes()).hexdigest(),
        "addresses": ADDRESS_COUNT, "arbitrary_word_bits": 40,
        "certified_hmr_branches": measurements, "qubits": circuit.num_qubits,
        "toffoli_per_pass": circuit.operation_statistics().num_toffoli_like,
    }


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("family", type=Path)
    parser.add_argument("words", type=Path)
    parser.add_argument("--batches", type=int, nargs="+", default=range(15))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    words = np.load(args.words, allow_pickle=False)[:ADDRESS_COUNT].astype(np.uint8)
    assert words.shape == (1220,75)
    assert sha256(words.tobytes()).hexdigest() == "8caf7416de79102103757e3ab7ab4b6bbebfad9b1bf1ecd564c20eb948dbfcea"
    proof = []
    for k in args.batches:
        delta = words[:,5*k:5*k+5].copy()
        if k:
            delta ^= words[:,5*k-5:5*k]
        proof.append(prove(args.family / f"angle_k_{k}.kmb", delta))
        print(json.dumps(proof[-1]), flush=True)
    args.out.write_text(json.dumps(proof, indent=2)+"\n")
