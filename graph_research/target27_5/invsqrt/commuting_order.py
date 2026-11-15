"""Schedule the pinned invsqrt tape with commutation-aware wire dependencies."""

from argparse import ArgumentParser
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from random import Random
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import width_dag as dag


REGISTERS = {"REGISTER", "APPEND_TO_REGISTER"}


def dependencies(atoms):
    """On each wire, adjacent reads and adjacent XOR writes commute."""
    epochs = {}
    predecessors = []
    successors = [[] for _ in atoms]
    for index, atom in enumerate(atoms):
        read, written = atom.dependencies()
        shared = set()
        for wire in read | written:
            if wire not in written:
                kind = "READ"
            elif wire < dag.QUBITS and atom.op in {"X", "CX", "CCX"}:
                kind = "XOR"
            else:
                kind = "EXCLUSIVE"
            last, before, current = epochs.get(wire, (None, [], []))
            if kind == last and kind != "EXCLUSIVE":
                current.append(index)
            else:
                before, current = current, [index]
            epochs[wire] = (kind, before, current)
            shared.update(before)
        predecessors.append(sorted(shared))
        for parent in shared:
            successors[parent].append(index)
    return predecessors, successors


def initial_state(xs):
    return [
        int.from_bytes(np.packbits((xs >> q) & 1, bitorder="little"), "little")
        for q in range(dag.INPUTS)
    ] + [0] * (dag.QUBITS - dag.INPUTS)


def execute(gate, state, mask):
    qs = gate.wires
    match gate.op:
        case "X":
            state[qs[0]] ^= mask
        case "CX":
            control, target = qs
            state[target] ^= state[control]
        case "CCX":
            a, b, target = qs
            state[target] ^= state[a] & state[b]
        case "SWAP":
            a, b = qs
            state[a], state[b] = state[b], state[a]
        case "CSWAP":
            control, a, b = qs
            diff = state[control] & (state[a] ^ state[b])
            state[a] ^= diff
            state[b] ^= diff
        case "HMR":
            state[qs[0]] = 0
        case "R":
            if state[qs[0]]:
                raise ValueError("Reset of a nonzero wire")


def live_intervals(gates):
    mask = (1 << dag.DOMAIN) - 1
    initial = initial_state(np.arange(1, dag.DOMAIN + 1, dtype=np.uint32))
    state = initial[:]
    started = {q: -1 for q in range(dag.INPUTS)}
    intervals = []
    counts = Counter()
    scopes = []
    for index, gate in enumerate(gates):
        if gate.op == "PUSH_CONDITION":
            scopes.append(state[:])
        elif gate.op == "POP_CONDITION":
            assert state == scopes.pop()
        else:
            execute(gate, state, mask)
        previous = set(started)
        following = {q for q, value in enumerate(state) if value not in (0, mask)}
        for q in previous - following:
            intervals.append((q, started.pop(q), index))
        for q in following - previous:
            started[q] = index
        counts[len(started)] += 1
    assert not scopes and state == initial
    intervals.extend((q, index, len(gates)) for q, index in started.items())
    return intervals, counts


def forced_cuts(gates, atoms, origin, intervals, pred, succ):
    atom_for_gate = []
    for at, source in enumerate(origin):
        stop = origin[at + 1] if at + 1 < len(origin) else len(gates)
        atom_for_gate.extend([at + 1] * (stop - source))
    starts = [0] * (len(atoms) + 2)
    ends = [0] * len(starts)
    for i, (_, birth, death) in enumerate(intervals):
        a = atom_for_gate[birth] if birth >= 0 else 0
        b = atom_for_gate[death] if death < len(gates) else len(atoms) + 1
        if a != b:
            starts[a] |= 1 << i
            ends[b] |= 1 << i
    pred = [[]] + [[j + 1 for j in p] + [0] for p in pred] + [list(range(1, len(atoms) + 1))]
    succ = [list(range(1, len(atoms) + 1))] + [
        [j + 1 for j in children] + [len(atoms) + 1] for children in succ
    ] + [[]]
    ancestors = dag.closures(pred, starts)
    descendants = dag.closures(succ, ends, reverse=True)
    return Counter((a & (b ^ death)).bit_count()
                   for a, b, death in zip(ancestors, descendants, ends))


def order(gates, origin, pred, succ, xs, seed):
    sizes = [b - a for a, b in zip(origin, origin[1:] + [len(gates)])]
    mask = (1 << len(xs)) - 1
    state = initial_state(xs)
    obligations = [len(row) for row in pred]
    ready = [i for i, need in enumerate(obligations) if not need]
    depth = [0] * len(origin)
    for index in reversed(range(len(origin))):
        depth[index] = 1 + max((depth[child] for child in succ[index]), default=0)
    rng = Random(seed)
    visits, peak, full = [], dag.INPUTS, 0
    weight = (seed // 4) % 3
    polarity = seed % 4
    while ready:
        selected, selected_state, selection = None, None, None
        for at in ready:
            start = origin[at]
            candidate = state[:]
            if sizes[at] == 1:
                execute(gates[start], candidate, mask)
            count = sum(value not in (0, mask) for value in candidate)
            # The atomic block restores external wire values. Preserve original
            # order as a tiebreaker on one lane, and vary the finish pressure.
            priority = (count, -depth[at] if weight == 1 else at if weight == 2 else 0,
                        at if polarity == 0 else -at if polarity == 1 else rng.random())
            if selection is None or priority < selection:
                selected, selected_state, selection = at, candidate, priority
        ready.remove(selected)
        visits.append(selected)
        start = origin[selected]
        if sizes[selected] > 1:
            temporary = state[:]
            for gate in gates[start:start + sizes[selected]]:
                execute(gate, temporary, mask)
                peak = max(peak, count := sum(v not in (0, mask) for v in temporary))
                full += int(count == dag.QUBITS)
            assert temporary == state
        else:
            peak = max(peak, selection[0])
            full += int(selection[0] == dag.QUBITS)
        state = selected_state
        for child in succ[selected]:
            obligations[child] -= 1
            if obligations[child] == 0:
                ready.append(child)
    assert len(visits) == len(origin) and state == initial_state(xs)
    return peak, full, [i for at in visits for i in range(origin[at], origin[at] + sizes[at])]


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("report", type=Path)
    parser.add_argument("--rounds", type=int, default=12)
    parser.add_argument("--best-kmx", type=Path)
    parser.add_argument("--source-sha", default=dag.PIN)
    args = parser.parse_args()
    assert sha256(args.source.read_bytes()).hexdigest() == args.source_sha
    raw = str(dag.km.Circuit.from_file(args.source)).splitlines()
    metadata = [line for line in raw if line.split()[0] in REGISTERS]
    lines = [line for line in raw if line.split()[0] not in REGISTERS]
    gates = [dag.Gate.parse(line) for line in lines]
    atoms, _, origin = dag.collapse_scopes(gates, [])
    orig_pred, orig_succ = dag.dependency_dag(atoms)
    pred, succ = dependencies(atoms)
    intervals, counts = live_intervals(gates)
    old_forced = forced_cuts(gates, atoms, origin, intervals, orig_pred, orig_succ)
    new_forced = forced_cuts(gates, atoms, origin, intervals, pred, succ)
    rng = np.random.default_rng(36127)
    xs = np.unique(np.concatenate([np.arange(1, 129), rng.integers(1, dag.DOMAIN + 1, size=256)]))
    rows = []
    best = None
    for seed in range(args.rounds):
        peak, full, permutation = order(gates, origin, pred, succ, xs, seed)
        rows.append(dict(seed=seed, sample_peak=peak, sample_full_width_cuts=full))
        if best is None or (peak, full) < best[:2]:
            best = (peak, full, permutation)
        print(rows[-1], flush=True)
    if best is not None:
        best_gates = [gates[i] for i in best[2]]
        _, checked = live_intervals(best_gates)
        if args.best_kmx is not None:
            args.best_kmx.write_text("\n".join(metadata + [lines[i] for i in best[2]]) + "\n")
    else:
        checked = {}
    report = dict(source_sha256=args.source_sha, full_domain=dag.DOMAIN, operations=len(gates),
                  collapsed_operations=len(atoms), original_dynamic_width=counts,
                  old_forced_cuts=old_forced, new_forced_cuts=new_forced,
                  trials=rows, best_full_domain_width=checked)
    args.report.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
