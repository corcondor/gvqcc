"""Audit exact one-CCX cleanup and immediate HMR correction on the submitted circuit."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from zipfile import ZipFile

import kickmix as km
import numpy as np

MAX_X = 3_133_452
PIN = "684106f101730ca193627229920a0501bef9ea10ccfb34aa453fcf63edadb50a"
WIRES = re.compile(r"\bq(\d+)\b")


def data_update(op, wires, values, one):
    if op == "X":
        (target,) = wires
        values[target] ^= one
    elif op in {"CX", "CCX"}:
        *controls, target = wires
        values[target] ^= product(controls, values, one)
    elif op == "CSWAP":
        control, left, right = wires
        delta = values[control] & (values[left] ^ values[right])
        values[left] ^= delta
        values[right] ^= delta
    elif op == "SWAP":
        left, right = wires
        values[left], values[right] = values[right], values[left]
    elif op == "HMR":
        (target,) = wires
        values[target] = 0


def product(wires, values, one):
    value = one
    for wire in wires:
        value &= values[wire]
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    with ZipFile(args.archive) as archive:
        source = archive.read("invsqrt.kmb")
    assert hashlib.sha256(source).hexdigest() == PIN
    import io
    circuit = km.Circuit.from_file(io.BytesIO(source), format="kmb")
    lines = str(circuit).splitlines()
    ops = [(line.split()[0], tuple(map(int, WIRES.findall(line)))) for line in lines]
    histogram = Counter(op for op, _ in ops)

    xs = np.arange(1, MAX_X + 1, dtype=np.uint32)
    one = (1 << len(xs)) - 1
    values = [
        int.from_bytes(np.packbits((xs >> q) & 1, bitorder="little").tobytes(), "little")
        for q in range(22)
    ] + [0] * (circuit.num_qubits - 22)
    counts = Counter()
    joins = []
    direct_ccx_cleanup = []
    no_op_ccx = []
    simple_hmr_examples = []
    cczs = []

    for i, (op, wires) in enumerate(ops):
        if op == "PUSH_CONDITION":
            joins.append(values.copy())
        elif op == "POP_CONDITION":
            assert values == joins.pop(), (i, lines[i])
            counts["data_identity_joins"] += 1
        elif op in {"X", "CX", "CCX", "CSWAP", "SWAP", "HMR"}:
            assert " if " not in lines[i], (i, lines[i])
            if op == "CCX":
                *controls, target = wires
                multiplier = product(controls, values, one)
                post_value = values[target] ^ multiplier
                counts["ccx_clean_target_before"] += not values[target]
                counts["ccx_post_changed_in_some_input"] += bool(multiplier)
                if not post_value:
                    direct_ccx_cleanup.append({"line_1based": i + 1, "text": lines[i]})
                if not multiplier:
                    no_op_ccx.append({"line_1based": i + 1, "text": lines[i]})
            elif op == "HMR" and i + 1 < len(ops) and ops[i+1][0] == "CZ":
                (_, measured, bit) = lines[i].split()
                condition = lines[i+1].partition(" if ")[2]
                q, = wires
                controls = ops[i+1][1]
                if condition == bit and q not in controls:
                    counts["hmr_next_cz_same_bit"] += 1
                    if product(controls, values, one) == values[q]:
                        counts["hmr_next_cz_matches_entire_erased_value"] += 1
                        if len(simple_hmr_examples) < 4:
                            simple_hmr_examples.append({"line_1based": i + 1, "text": lines[i:i+2]})
            data_update(op, wires, values, one)
        elif op == "CCZ":
            cczs.append({"line_1based": i + 1, "wires": wires, "condition_depth": len(joins)})
    assert not joins

    result = {
        "source_sha256": PIN, "domain": [1, MAX_X], "num_qubits": circuit.num_qubits,
        "instruction_counts": dict(sorted(histogram.items())), "counts": dict(counts),
        "direct_ccx_cleanup": direct_ccx_cleanup, "no_op_ccx": no_op_ccx,
        "simple_hmr_examples": simple_hmr_examples, "ccz_sites": cczs,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
