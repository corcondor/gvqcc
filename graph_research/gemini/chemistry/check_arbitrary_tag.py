#!/usr/bin/env python3
"""Compare arbitrary-input effects of one flipped word tag in score11/score12."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import kickmix as km
import numpy as np


def run(circuit, incoming, perturbation):
    n = incoming.shape[0]
    full = (1 << n) - 1
    addresses = [sum(1 << a for a in range(n) if (a >> j) & 1) for j in range(11)]
    state = addresses.copy() + [
        sum(1 << a for a in range(n) if (int(incoming[a, w]) >> j) & 1)
        for w in range(5) for j in range(8)
    ]
    state += [0] * (circuit.num_qubits - len(state))
    if perturbation is not None:
        state[perturbation] ^= full
    phase = None
    for line in str(circuit).splitlines():
        gate, *args = line.split()
        if gate in {"REGISTER", "APPEND_TO_REGISTER"}:
            continue
        wires = [int(arg[1:]) for arg in args if arg.startswith("q")]
        if gate == "X":
            state[wires[0]] ^= full
        elif gate == "CX":
            state[wires[1]] ^= state[wires[0]]
        elif gate == "CCX":
            state[wires[2]] ^= state[wires[0]] & state[wires[1]]
        elif gate == "R":
            assert state[wires[0]] == 0
        elif gate == "HMR":
            assert phase is None and args[1] == "b0"
            phase = state[wires[0]]
            state[wires[0]] = 0
        elif gate == "CZ":
            assert args[2:] == ["if", "b0"] and phase is not None
            assert phase == state[wires[0]] & state[wires[1]]
            phase = None
        else:
            raise ValueError(gate)
    assert phase is None and state[:11] == addresses and not any(state[51:])
    ordinary = np.array([[sum(((state[11 + 8*w + j] >> a) & 1) << j for j in range(8))
                          for w in range(5)] for a in range(n)], dtype=np.uint8)
    return ordinary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--score11", type=Path, required=True)
    parser.add_argument("--score12", type=Path, required=True)
    parser.add_argument("--table", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with np.load(args.table, allow_pickle=False) as f:
        table = f["angle_words"].astype(np.uint8)
    incoming, expected = table[:, :5], table[:, 5:10]
    assert sha256(table.tobytes()).hexdigest() == "8caf7416de79102103757e3ab7ab4b6bbebfad9b1bf1ecd564c20eb948dbfcea"
    name = "angle_k_1.kmb"
    with TemporaryDirectory() as tmp:
        old_path = Path(tmp) / name
        with ZipFile(args.score11) as zip_file:
            old_path.write_bytes(zip_file.read("dfthcsos/" + name))
        new_path = args.score12 / name
        old, new = (km.Circuit.from_file(p) for p in (old_path, new_path))
        assert np.array_equal(run(old, incoming, None), expected)
        assert np.array_equal(run(new, incoming, None), expected)
        records = []
        for w in range(5):
            p = 11 + 8*w + 7
            old_words = run(old, incoming, p)
            new_words = run(new, incoming, p)
            assert np.array_equal(old_words, new_words)
            theoretical = expected.copy()
            theoretical[:, w] ^= 128
            mismatch = np.flatnonzero(np.any(old_words != theoretical, axis=1))
            row = {"perturbed_input": p, "different_addresses": int(mismatch.size)}
            if mismatch.size:
                a = int(mismatch[0])
                input_words = incoming[a].copy()
                input_words[w] ^= 128
                row["witness"] = dict(selection=a, incoming_words=input_words.tolist(),
                                      xor_contract_expected=theoretical[a].tolist(),
                                      score11_actual=old_words[a].tolist(),
                                      score12_actual=new_words[a].tolist())
            records.append(row)
        result = {
            "angle_batch": 1,
            "addresses": int(len(incoming)),
            "all_hmr_branch_phases_cancelled": True,
            "same_output_score11_score12_for_all_tested_inputs": True,
            "sha256": {label: sha256(p.read_bytes()).hexdigest()
                       for label, p in (("score11", old_path), ("score12", new_path))},
            "tag_flip_results": records,
        }
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
