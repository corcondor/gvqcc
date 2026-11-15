"""Replace charged gates with verified Clifford action on supported states."""

from argparse import ArgumentParser
from collections import Counter
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import width_dag as dag


PAID = {"CCX", "CCZ", "CSWAP"}
REGISTERS = {"APPEND_TO_REGISTER", "REGISTER"}


def packed_trace(gates, inputs, visit):
    mask = (1 << len(inputs)) - 1
    state = [
        int.from_bytes(np.packbits((inputs >> q) & 1, bitorder="little"), "little")
        for q in range(dag.INPUTS)
    ] + [0] * (dag.QUBITS - dag.INPUTS)
    frames = []
    for index, gate in enumerate(gates):
        visit(index, state, mask)
        wires = gate.wires
        match gate.op:
            case "X":
                state[wires[0]] ^= mask
            case "CX":
                control, target = wires
                state[target] ^= state[control]
            case "CCX":
                a, b, target = wires
                state[target] ^= state[a] & state[b]
            case "SWAP":
                a, b = wires
                state[a], state[b] = state[b], state[a]
            case "CSWAP":
                control, a, b = wires
                toggles = state[control] & (state[a] ^ state[b])
                state[a] ^= toggles
                state[b] ^= toggles
            case "HMR":
                state[wires[0]] = 0
            case "PUSH_CONDITION":
                frames.append(state[:])
            case "POP_CONDITION":
                assert state == frames.pop()
    assert not frames


def terms(gate, state, mask):
    match gate.op:
        case "CCX":
            excluded = set(gate.wires[-1:])
        case "CSWAP":
            excluded = set(gate.wires[1:])
        case _:
            excluded = set()
    yield (), mask
    for q, value in enumerate(state):
        if q not in excluded and value:
            yield (q,), value
    if gate.op == "CCZ":
        for a, b in combinations(range(dag.QUBITS), 2):
            product = state[a] & state[b]
            if product:
                yield (a, b), product


def predicate(gate, state, swap=False):
    a, b, c = (state[q] for q in gate.wires)
    if gate.op == "CCX":
        return a & b
    if gate.op == "CSWAP":
        return (a & (b ^ c)) ^ ((b ^ c) if swap else 0)
    return a & b & c


def fit(gate, state, mask):
    requested = predicate(gate, state)
    alternate = predicate(gate, state, swap=True) if gate.op == "CSWAP" else None
    if requested == 0:
        return False, []
    if alternate == 0:
        return True, []
    labels = []
    basis = {}
    for label, function in terms(gate, state, mask):
        vector = function
        expression = 1 << len(labels)
        labels.append(label)
        while vector:
            pivot = vector.bit_length()
            if pivot not in basis:
                basis[pivot] = vector, expression
                break
            row, coefficient = basis[pivot]
            vector ^= row
            expression ^= coefficient
    choices = []
    for swap, target in ((False, requested), (True, alternate)):
        if target is None:
            continue
        expression = 0
        while target:
            if target.bit_length() not in basis:
                break
            row, coefficient = basis[target.bit_length()]
            target ^= row
            expression ^= coefficient
        if not target:
            fitted = [label for j, label in enumerate(labels) if expression >> j & 1]
            choices.append((swap, fitted))
    return min(choices, key=lambda v: len(v[1]) + v[0]) if choices else None


def operation_replacement(gate, swap, labels, suffix):
    def instruction(op, *qubits):
        return " ".join([op, *(f"q{q}" for q in qubits), *suffix])

    if gate.op == "CCZ":
        return [instruction(("NEG", "Z", "CZ")[len(label)], *label) for label in labels]
    if gate.op == "CCX":
        targets = gate.wires[-1:]
    else:
        targets = gate.wires[1:]
    result = [instruction("SWAP", *targets)] if swap else []
    for target in targets:
        for label in labels:
            result.append(instruction("CX" if label else "X", *label, target))
    return result


def certifies(gate, state, mask, swap, labels):
    actual = 0
    for label in labels:
        term = mask
        for q in label:
            term &= state[q]
        actual ^= term
    return actual == predicate(gate, state, swap)


def main():
    cli = ArgumentParser(description=__doc__)
    cli.add_argument("source", type=Path)
    cli.add_argument("report", type=Path)
    cli.add_argument("candidate", type=Path)
    opt = cli.parse_args()
    assert sha256(opt.source.read_bytes()).hexdigest() == dag.PIN
    raw = str(dag.km.Circuit.from_file(opt.source)).splitlines()
    metadata = [line for line in raw if line.split()[0] in REGISTERS]
    lines = [line for line in raw if line.split()[0] not in REGISTERS]
    gates = [dag.Gate.parse(line) for line in lines]
    rng = np.random.default_rng(440211)
    sample = np.unique(np.concatenate([np.arange(1, 2049),
                                      rng.integers(1, dag.DOMAIN + 1, size=4096)]))
    proposed = {}

    def propose(index, state, mask):
        if gates[index].op not in PAID:
            return
        proposal = fit(gates[index], state, mask)
        if proposal is not None:
            proposed[index] = proposal

    packed_trace(gates, sample, propose)
    print(f"Sampled {len(sample)} inputs and found {len(proposed)} prospective replacements", flush=True)
    accepted = {}

    def verify(index, state, mask):
        if index not in proposed:
            return
        gate = gates[index]
        swap, labels = proposed[index]
        if certifies(gate, state, mask, swap, labels):
            accepted[index] = (swap, labels)

    dag.packed_lifetimes(gates, verify)
    print(f"Accepted {len(accepted)} replacements on all {dag.DOMAIN} inputs", flush=True)
    output = metadata[:]
    edits = []
    for i, (gate, line) in enumerate(zip(gates, lines)):
        if i not in accepted:
            output.append(line)
            continue
        swap, labels = accepted[i]
        replacement = operation_replacement(gate, swap, labels, line.split()[1 + len(gate.wires):])
        output.extend(replacement)
        edits.append(dict(index=i, prior=line, replacement=replacement,
                          formal_test="same value update and phase factor on all pre-gate supported states"))
    report = dict(source_sha256=dag.PIN, tested_full_domain=dag.DOMAIN,
                  candidates=len(proposed), accepted=len(accepted),
                  gate_reductions=dict(Counter(gates[i].op for i in accepted)), edits=edits)
    report["sample_proposals"] = [
        dict(index=i, prior=lines[i], labels=labels, swap=swap, exact=i in accepted)
        for i, (swap, labels) in proposed.items()
    ]
    if edits:
        circ = dag.km.Circuit("\n".join(output) + "\n")
        circ.to_file(opt.candidate, format="kmb")
        report["candidate_sha256"] = sha256(opt.candidate.read_bytes()).hexdigest()
        report["candidate_qubits"] = circ.num_qubits
    opt.report.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
