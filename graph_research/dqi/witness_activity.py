#!/usr/bin/env python3
"""Report native operations touching the fixed-timeline width-888 cut witnesses."""

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

import numpy as np


def operation_dict(op):
    return dict(index=op.source_index, opcode=hex(op.opcode), quantum=list(op.qubits),
                classical=op.bit, condition=op.condition)


def profile_lifetime(circuit, interval, witness, quantum_columns):
    first, stop, wire, _ = interval
    actions = Counter()
    mates = Counter()
    nearest_left = None
    nearest_right = None
    chunk_size = 1 << 20
    for lo in range(first, stop, chunk_size):
        hi = min(stop, lo + chunk_size)
        opcodes = np.frombuffer(circuit.opcodes[lo:hi], dtype=np.uint8)
        arities = (opcodes & 0x30) >> 4
        for n in (1, 2, 3):
            indexes = np.flatnonzero(arities == n)
            start = circuit.rank(f"q{n}", lo)
            columns = [
                np.frombuffer(circuit.data, dtype="<u4", count=len(indexes),
                              offset=circuit.packets[k]["payload_offset"] + 4 * start)
                for k in quantum_columns[n]
            ]
            touches = np.zeros(len(indexes), dtype=bool)
            for j, values in enumerate(columns):
                active = values == wire
                for opcode, count in zip(*np.unique(opcodes[indexes[active]], return_counts=True)):
                    actions[(hex(int(opcode)), j)] += int(count)
                touches |= active
            for values in columns:
                for partner, count in zip(*np.unique(values[touches], return_counts=True)):
                    if partner != wire:
                        mates[int(partner)] += int(count)
            pos = indexes[touches] + lo
            left = pos[pos <= witness]
            right = pos[pos >= witness]
            if len(left):
                candidate = int(left[-1])
                nearest_left = max(candidate, nearest_left or candidate)
            if len(right):
                candidate = int(right[0])
                nearest_right = min(candidate, nearest_right or candidate)
    def at(index):
        return operation_dict(next(circuit.operations(index, index + 1))) if index is not None else None
    return dict(
        qubit=wire, first_operation=at(first), last_operation=at(stop - 1), witness=witness,
        nearest_touch_at_or_before_witness=at(nearest_left),
        nearest_touch_at_or_after_witness=at(nearest_right),
        actions=[dict(opcode=opcode, operand=operand, count=count)
                 for (opcode, operand), count in sorted(actions.items())],
        distinct_companion_wires=len(mates), most_frequent_companions=mates.most_common(8),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--tape", type=Path, required=True)
    parser.add_argument("--cut", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.repo))
    from dqi_ccx_peephole import QUANTUM_COLUMNS
    from kmb_splice import open_circuit

    cut = json.loads(args.cut.read_text())
    circuit = open_circuit(args.tape)
    if circuit.profile["raw_kmb_sha256"] != cut["input_sha256"]:
        raise ValueError("width cut belongs to a different tape")
    code = cut["q888_certificate"]
    rows = [profile_lifetime(circuit, interval, witness, QUANTUM_COLUMNS)
            for interval, witness in zip(code["selected_lifetimes"], code["witnesses"])]
    circuit.close()
    args.out.write_text(json.dumps(dict(input_sha256=cut["input_sha256"], lifetimes=rows),
                                   indent=2) + "\n")


if __name__ == "__main__":
    main()
