"""Check if q25 can be reconstructed from the other wires in the score18 circuit."""

from argparse import ArgumentParser
from collections import Counter
import json
from pathlib import Path

from critical_cut_cover import dag, load_pinned


def affine_witness(target, terms):
    """Reduce domain-wide packed truth vectors with exact GF(2) elimination."""
    basis = {}
    for current, expression in terms:
        while current:
            pivot = current.bit_length()
            if pivot not in basis:
                basis[pivot] = (current, expression)
                break
            offset, coefficient = basis[pivot]
            current ^= offset
            expression ^= coefficient
    expression = 0
    while target:
        pivot = target.bit_length()
        if pivot not in basis:
            return None
        offset, coefficient = basis[pivot]
        target ^= offset
        expression ^= coefficient
    return [f"q{i}" for i in range(dag.QUBITS) if expression & (1 << i)] + (
        ["1"] if expression & (1 << dag.QUBITS) else []
    )


def indices(mask):
    while mask:
        bit = mask & -mask
        yield bit.bit_length() - 1
        mask ^= bit


def collision(target, others, domain_mask, positives):
    """Find two inputs that disagree on q25 and match on all other wires."""
    zeros = domain_mask ^ target
    zero_count = zeros.bit_count()
    options = []
    for value in others:
        if value == 0 or value == domain_mask:
            continue
        one_count = (value & zeros).bit_count()
        options.append((value, domain_mask ^ value, one_count, zero_count - one_count))
    for x in positives:
        constraints = [(ones, value) if (value >> x) & 1 else (off, complement)
                       for value, complement, ones, off in options]
        possible = zeros
        for _, allowed in sorted(constraints):
            possible &= allowed
            if not possible:
                break
        if possible:
            return [x + 1, (possible & -possible).bit_length()]
    return None


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    source_hash, lines, gates = load_pinned(args.source)
    wire = 25
    predicate = (1 << 63) - 1
    positives = list(indices(predicate))
    usage = Counter()
    affine = []
    collisions = []

    def probe(index, state, domain_mask):
        gate = gates[index]
        if wire not in gate.wires or wire in gate.dependencies()[1]:
            return
        target = state[wire]
        if target != predicate:
            raise ValueError(f"x < 64 does not hold at gate {index}")
        usage[gate.op] += 1
        terms = [(value, 1 << j) for j, value in enumerate(state)
                 if j not in gate.wires]
        witness = affine_witness(target, terms + [(domain_mask, 1 << dag.QUBITS)])
        if witness is not None:
            affine.append(dict(index=index, gate=lines[index], parity=witness))
        pair = collision(target, [value for j, value in enumerate(state) if j != wire],
                         domain_mask, positives)
        if pair is not None:
            collisions.append(dict(index=index, gate=lines[index], inputs=pair))

    dag.packed_lifetimes(gates, observe=probe)
    result = dict(
        source_sha256=source_hash,
        legal_inputs=dag.DOMAIN,
        wire=f"q{wire}",
        predicate_at_reads="1 <= x < 64",
        reads=sum(usage.values()),
        reads_by_gate_type=dict(usage),
        affine_hits_excluding_gate_operands=affine,
        collision_witnesses=collisions,
        indices="Zero-based KMB gate indices with register declarations omitted.",
    )
    args.report.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
