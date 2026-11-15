"""Early HMR of the idle eleven-bit A slice in the raw-window F pass."""

from argparse import ArgumentParser
from hashlib import file_digest
from itertools import combinations
import json
from pathlib import Path
import sys

import numpy as np


def factor_groups(terms):
    """Cover the remaining left factors by explicit spaces of rank at most 3."""
    uncovered = list(terms)
    groups = []
    while uncovered:
        best = None
        choices = sorted({a for a, _, _ in uncovered})
        for size in range(1, min(3, len(choices)) + 1):
            for rows in combinations(choices, size):
                coordinates = {0: 0}
                for j, row in enumerate(rows):
                    coordinates.update({p ^ row: c | 1 << j for p, c in coordinates.items()})
                if len(coordinates) != 1 << size:
                    continue
                hits = [term for term in uncovered if term[0] in coordinates]
                score = (len(hits), -size)
                if best is None or score > best[0]:
                    best = (score, rows, hits, coordinates)
        _, rows, hits, coordinates = best
        groups.append((rows, [(coordinates[a], b, w) for a, b, w in hits]))
        uncovered = [term for term in uncovered if term not in hits]
    return groups


def emit_masked_upper(builder, flag, q1, h1, upper, groups, field_tensor):
    for rows, terms in groups:
        masked = builder.alloc_qubits(len(rows))
        for row, bit in zip(rows, masked):
            pivot = field_tensor.parity_pivot(builder, q1, row)
            builder.init_and(flag, pivot, bit)
            field_tensor.parity_pivot(builder, q1, row)
        field_tensor.accumulate_product(builder, masked, h1, upper, terms)
        for row, bit in zip(rows, masked):
            pivot = field_tensor.parity_pivot(builder, q1, row)
            builder.del_and(flag, pivot, bit)
            field_tensor.parity_pivot(builder, q1, row)
        builder.free(masked)


def emit_f(builder, F_low, q1, rhs_low, h1, h2, flag, middle, groups, early):
    import kickmix as km
    import field_tensor
    from monic_forney import add_scaled
    from tower_inverse import kernel, phase_product, xor_product

    product = builder.alloc_qubits(12)
    xor_product(builder, q1, h1, product)
    builder.ccx(flag, h1, product)
    # The omitted bit of A is parked in flag under f*middle=0.
    builder.ccx(middle, product[0], flag)
    builder.ccx(middle, flag, product[0])
    if early:
        debt = builder.alloc_bits(11)
        cell = builder.alloc_qubits(1)
        for j, p in enumerate(product[1:]):
            builder.init_and(middle, p, cell[0])
            builder.cx(cell[0], p)
            builder.hmr(cell[0], debt[j])
        builder.free(cell)
    else:
        upper = builder.alloc_qubits(11)
        builder.init_and(middle, product[1:], upper)
        builder.cx(upper, product[1:])
    builder.cswap(middle, h1, h2)
    for point, (coefficient, target) in enumerate(zip(F_low, rhs_low)):
        add_scaled(builder, product, h2, point)
        xor_product(builder, coefficient, h2, target)
        add_scaled(builder, product, h2, point)
    builder.cswap(middle, h1, h2)
    mask = builder.alloc_bits(12)
    builder.hmr(product, mask)
    builder.free(product)
    if early:
        upper = builder.alloc_qubits(11)
        emit_masked_upper(builder, middle, q1, h1, upper, groups, field_tensor)
        builder.cz(debt, upper)
        builder.free(debt)
    first = builder.alloc_qubits(1)
    builder.init_and(middle, flag, first[0])
    builder.cx(first[0], flag)
    A = km.array([*first, *upper])
    phase_product(builder, q1, h1, mask, kernel(12))
    builder.cz(mask, A)
    builder.ccz(mask, flag, h1)
    builder.free(mask)
    return A


def build(km, m, groups, early):
    b = km.CircuitBuilder()
    raw = b.create_quantum_register(12 * m, "f_low")
    rhs = b.create_quantum_register(12 * m, "rhs_low")
    q1 = b.create_quantum_register(12, "q1")
    h1 = b.create_quantum_register(12, "h1")
    h2 = b.create_quantum_register(12, "h2")
    flags = b.create_quantum_register(2, "flags")
    witness = b.create_quantum_register(12, "witness")
    baseline_width = b.num_allocated_qubits
    A = emit_f(b, [raw[i:i + 12] for i in range(0, len(raw), 12)], q1,
               [rhs[i:i + 12] for i in range(0, len(rhs), 12)], h1, h2,
               flags[0], flags[1], groups, early)
    b.cx(A, witness)
    mask = b.alloc_bits(12)
    b.hmr(A, mask)
    b.cz(mask, witness)
    b.free(mask)
    b.free(A)
    assert b.num_allocated_qubits == baseline_width
    circuit = b.finish_circuit()
    return circuit, circuit.num_qubits - baseline_width


def word_bits(rows):
    return ((rows[None, :] >> np.arange(12, dtype=np.uint32)[:, None]) & 1).astype(bool)


def simulate(km, circuit, registers, count, seed):
    sim = km.Simulator(batch_size=count, seed=seed, counting_operations=True)
    sim.use_same_registers_as(circuit)
    for name, values in registers.items():
        sim.write_across_shots(circuit.register_data[name], values)
    sim.do(circuit)
    output = {name: np.asarray(sim.read_across_shots(bits))
              for name, bits in circuit.register_data.items()}
    abi = {q for reg in circuit.register_data.values() for q in reg}
    scratch = km.array([km.q(i) for i in range(circuit.num_qubits) if km.q(i) not in abi])
    assert not np.asarray(sim.read_across_shots(scratch)).any()
    assert not np.asarray(sim.read_phase_flipped_across_shots()).any()
    return output


def main():
    p = ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--points", type=int, default=5)
    p.add_argument("--shots", type=int, default=4096)
    args = p.parse_args()
    for rel in ("after_c5/extractor_width", "night_c27/arithmetic"):
        sys.path.insert(0, str(args.source / rel))
    import ew_paths  # noqa: F401
    import kickmix as km
    from tower_inverse import kernel

    groups = factor_groups([(a, b, c >> 1) for a, b, c in kernel(12) if c >> 1])
    rng = np.random.default_rng(5209611)
    count = args.shots
    words = lambda: rng.integers(0, 4096, count, dtype=np.uint32)
    f_low = np.vstack([word_bits(words()) for _ in range(args.points)])
    rhs_low = np.vstack([word_bits(words()) for _ in range(args.points)])
    f, mid = (mode := rng.integers(0, 3, count)) == 1, mode == 2
    q1 = words()
    q1[f] = 0
    registers = dict(f_low=f_low, rhs_low=rhs_low, q1=word_bits(q1),
                     h1=word_bits(words()), h2=word_bits(words()), flags=np.vstack((f, mid)))
    args.out.mkdir(parents=True, exist_ok=True)
    reference = None
    records = []
    for variant in (False, True):
        circuit, helpers = build(km, args.points, groups, variant)
        path = args.out / ("early.kmb" if variant else "reference.kmb")
        circuit.to_file(path, format="kmb")
        circuit = km.Circuit.from_file(path)
        for seed in (48918, 716425):
            output = simulate(km, circuit, registers, count, seed)
            if reference is None:
                reference = output
            assert all(np.array_equal(reference[name], out) for name, out in output.items())
        with path.open("rb") as stream:
            digest = file_digest(stream, "sha256").hexdigest()
        records.append(dict(early=variant, helpers_excluding_two_flags=helpers,
                            paid=circuit.operation_statistics().num_toffoli_like,
                            instructions=len(circuit), input_output_scratch_phase_pass=count * 2,
                            sha256=digest))
    report = dict(points=args.points, masked_subspaces=[len(rows) for rows, _ in groups],
                  total_mask_preparations=sum(len(rows) for rows, _ in groups), cases=records,
                  scope="Isolated raw-window F pass, no e4 binding or complete G rewrite")
    (args.out / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    print(report, flush=True)


if __name__ == "__main__":
    main()
