"""Test exact selector-conditioned CSWAP fan-out sharing on the legal domain."""

from argparse import ArgumentParser
from hashlib import sha256
from itertools import groupby
import json
from pathlib import Path

from state_supported_rewrite import dag, REGISTERS


def rank(vectors):
    basis = {}
    for vector in vectors:
        while vector:
            pivot = vector.bit_length()
            if pivot not in basis:
                basis[pivot] = vector
                break
            vector ^= basis[pivot]
    return len(basis)


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("report", type=Path)
    opts = parser.parse_args()
    assert sha256(opts.source.read_bytes()).hexdigest() == dag.PIN
    raw = str(dag.km.Circuit.from_file(opts.source)).splitlines()
    lines = [line for line in raw if line.split()[0] not in REGISTERS]
    gates = [dag.Gate.parse(line) for line in lines]
    groups = {}

    def selector(index):
        gate = gates[index]
        return (gate.wires[0], gate.bits) if gate.op == "CSWAP" else None

    for control, run in groupby(range(len(gates)), key=selector):
        indices = list(run)
        if control is None or len(indices) < 2:
            continue
        targets = [target for i in indices for target in gates[i].wires[1:]]
        if len(targets) == len(set(targets)):
            groups[indices[0]] = indices
    records = []

    def probe(index, state, _mask):
        if index not in groups:
            return
        run = groups[index]
        sel = groups[index][0]
        control = gates[sel].wires[0]
        active = state[control]
        pairs = [gates[i].wires[1:] for i in run]
        products = [active & (state[a] ^ state[b]) for a, b in pairs]
        quotient = rank([active, *products]) - int(bool(active))
        records.append(dict(start=index, end=run[-1], control=control, pairs=pairs,
                            active_inputs=active.bit_count(), paid=len(pairs),
                            rank_modulo_selector=quotient))

    dag.packed_lifetimes(gates, probe)
    report = dict(source_sha256=dag.PIN, full_domain=dag.DOMAIN, runs=len(records),
                  with_rank_reduction=sum(item["paid"] > item["rank_modulo_selector"]
                                          for item in records), records=records)
    opts.report.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
