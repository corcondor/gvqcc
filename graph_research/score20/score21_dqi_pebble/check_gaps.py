"""Verify two early-release gadgets against operand-exact excerpts of e4."""
import argparse
import csv
import json
from pathlib import Path
import sys

import kickmix as km
import numpy as np


WINDOWS = ((21613492, 21614632, 877), (40486650, 40506820, 880))
NO_CONTROL = 65535


def terms(field):
    return tuple(tuple(map(int, item.split(","))) for item in field.split(";") if item)


def materialize(builder, data, target, polynomial):
    for a, b in polynomial:
        if a == NO_CONTROL:
            builder.x(data[target])
        elif b == NO_CONTROL:
            builder.cx(data[a], data[target])
        else:
            builder.ccx(data[a], data[b], data[target])


def erase_by_measurement(builder, data, target, polynomial, debt):
    builder.hmr(data[target], debt)
    for a, b in polynomial:
        if a == NO_CONTROL:
            builder.x(data[target])
            builder.cz(debt, data[target])
            builder.x(data[target])
        elif b == NO_CONTROL:
            builder.cz(debt, data[a])
        else:
            builder.ccz(debt, data[a], data[b])


def make_circuit(operations, initial, final, target, changed, measured):
    builder = km.CircuitBuilder()
    data = builder.create_quantum_register(889, "data")
    # The zero wire is used only to align native RNG outcomes in the fixture.
    zero = builder.create_quantum_register(1, "dummy")[0]
    ids = sorted({b for op in operations for b in (op.bit, op.condition) if b is not None})
    bits = builder.create_classical_register(len(ids) + 1, "bits")
    debt = bits[-1]
    classical = dict(zip(ids, bits))
    if measured:
        if changed:
            erase_by_measurement(builder, data, target, initial, debt)
        else:
            builder.hmr(zero, debt)
    elif changed:
        materialize(builder, data, target, initial)
    for op in operations:
        q = tuple(data[i] for i in op.qubits)
        if op.opcode == 0x21:
            builder.cx(*q)
        elif op.opcode == 0x22:
            builder.swap(*q)
        elif op.opcode == 0x31:
            builder.ccx(*q)
        elif op.opcode == 0x50:
            builder.hmr(*q, classical[op.bit])
        elif op.opcode == 0xA0:
            builder.ccz(classical[op.condition], *q)
        else:
            raise ValueError(f"unexpected opcode {op.opcode:#x}")
    if changed:
        materialize(builder, data, target, final)
    return builder.finish_circuit()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("gaps", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--census", type=Path, required=True)
    args = parser.parse_args()
    sys.path[:0] = [str(args.repo), str(args.census)]
    from census import PIN, digest, open_columns
    from dqi_ccx_peephole import BinaryCircuit
    import kmb_profile

    assert digest(args.source) == PIN
    source = open_columns(args.source, BinaryCircuit, kmb_profile)
    rows = {}
    with args.gaps.open() as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            key = tuple(int(row[field]) for field in ("begin", "end", "q"))
            if key in WINDOWS:
                rows[key] = row
    cases = 4096
    rng = np.random.default_rng(2026111521)
    receipts = []
    for key in WINDOWS:
        begin, end, target = key
        row = rows[key]
        later_cost = int(row["quadratics"])
        initial = terms(row["initial_terms"])
        final = terms(row["final_terms"])
        operations = list(source.operations(begin, end))
        assert all(target not in op.qubits for op in operations)
        data = rng.integers(0, 2, size=(889, cases), dtype=np.uint8).astype(bool)
        data[target] = False
        for a, b in initial:
            if a == NO_CONTROL:
                data[target] ^= True
            elif b == NO_CONTROL:
                data[target] ^= data[a]
            else:
                data[target] ^= data[a] & data[b]
        results = []
        counts = []
        for changed in (False, True):
            circuit = make_circuit(operations, initial, final, target, changed, bool(later_cost))
            sim = km.Simulator(batch_size=cases, seed=721, counting_operations=True)
            sim.use_same_registers_as(circuit)
            sim.write_across_shots(circuit.register_data["data"], data)
            sim.do(circuit)
            results.append((sim.read_across_shots(circuit.register_data["data"]),
                            sim.read_phase_flipped_across_shots(),
                            sim.read_across_shots(circuit.register_data["bits"][:-1])))
            counts.append(sim.operation_statistics().num_toffoli_like / cases)
        assert all(np.array_equal(a, b) for a, b in zip(*results))
        assert counts[1] - counts[0] == later_cost
        receipts.append(dict(gap=[begin, end], qubit=target, old_mean_Toffoli=counts[0],
                             new_mean_Toffoli=counts[1], shots=cases,
                             value_phase_classical_errors=0))
    source.close()
    args.output.write_text(json.dumps({"source_sha256": PIN, "cases": receipts}, indent=2) + "\n")


if __name__ == "__main__":
    main()
