#!/usr/bin/env python3
"""One fewer masked virtual-product wire by borrowing the zero-chart leader."""
from argparse import ArgumentParser
from hashlib import file_digest
from itertools import permutations
import json
from pathlib import Path
import sys

import numpy as np


def partial_rows(m, points=None):
    """First m−1 evaluation points and unchanged leading coefficient."""
    from monic_forney import F
    from field_tensor import invert_field_matrix
    from tower_inverse import rows_from_columns
    if points is None:
        points = range(m-1)
    assert len(set(points)) == len(points) == m-1
    matrix = [[F.pow(x, k) for k in range(m)] for x in points]
    matrix.append([0]*(m-1)+[1])
    inverse = invert_field_matrix(matrix, F)

    def rows(field_matrix):
        return rows_from_columns(tuple(
            sum(F.mul(field_matrix[j][k], 1 << lane) << (12*j) for j in range(m))
            for k in range(m) for lane in range(12)))
    return rows(matrix), rows(inverse)


def walk_plan(F, m):
    degree = (m-2).bit_length()
    gray = [i ^ (i >> 1) for i in range(1 << degree)]
    weights = {delta: [F.mul(delta, 1 << k).bit_count() for k in range(12)]
               for delta in range(1 << degree)}
    best = None
    for dims in permutations(range(degree)):
        def rotate(point):
            return sum(((point >> j) & 1) << dim for j, dim in enumerate(dims))
        walk = tuple(x for p in gray if (x := rotate(p)) < m-1)
        factors = (0, *(p ^ 1 for p in walk), 0)
        moves = [a ^ b for a,b in zip(factors, factors[1:])]
        totals = [sum(weights[d][k] for d in moves) for k in range(12)]
        cost = min(totals)
        candidate = (cost, totals.index(cost), walk)
        if best is None or candidate < best:
            best = candidate
    return best


def lend(builder, C, low, q0, q1, g):
    import kickmix as km
    from monic_forney import F, flat, add_scaled
    from tower_inverse import apply_inplace_linear, xor_product

    m = len(C)
    assert m >= 5 and len(low) == m
    forward, inverse = partial_rows(m)
    cost, lane, walk = walk_plan(F, m)
    apply_inplace_linear(builder, flat(C), forward)
    witness = C[-1][0]
    masked0 = list(builder.alloc_qubits(12))
    builder.init_and(g, q0, km.array(masked0))
    builder.cswap(g, masked0[lane], witness)
    # On g=1 the original C leading word is zero. On g=0 masked0 is zero.
    builder.reset(masked0[lane])
    builder.free(masked0[lane])
    masked0[lane] = None
    masked1 = builder.alloc_qubits(12)
    builder.init_and(g, q1, masked1)

    def move(q1_factor, masked0_factor, masked1_factor):
        add_scaled(builder, q1, q0, q1_factor)
        add_scaled(builder, masked1, q0, masked1_factor)
        for k, src in enumerate(masked0):
            column = F.mul(masked0_factor, 1 << k)
            for j, dest in enumerate(q0):
                if not (column >> j & 1):
                    continue
                if k == lane:
                    builder.ccx(g, witness, dest)
                else:
                    builder.cx(src, dest)

    previous = (0, 0, 0)
    for point in walk:
        factors = (point, point ^ 1, F.mul(point, point ^ 1))
        move(*(a ^ b for a,b in zip(factors, previous)))
        xor_product(builder, C[point], q0, low[point])
        previous = factors
    move(*previous)

    builder.del_and(g, q1, masked1)
    builder.free(masked1)
    masked0[lane] = builder.alloc_qubits(1)[0]
    builder.cswap(g, masked0[lane], witness)
    builder.del_and(g, q0, km.array(masked0))
    builder.free(km.array(masked0))
    apply_inplace_linear(builder, flat(C), inverse)

    point = m - 1
    for j in range(1, m):
        add_scaled(builder, C[j], C[0], F.pow(point,j))
    add_scaled(builder, q1, q0, point)
    mask = builder.alloc_qubits(12)
    builder.init_and(g, q0, mask)
    add_scaled(builder, mask, q0, point ^ 1)
    xor_product(builder, C[0], q0, low[point])
    add_scaled(builder, mask, q0, point ^ 1)
    builder.del_and(g, q0, mask)
    builder.free(mask)
    add_scaled(builder, q1, q0, point)
    for j in range(1, m):
        add_scaled(builder, C[j], C[0], F.pow(point,j))
    return cost


def build(km, virtual, count, new, implementation=lend):
    b = km.CircuitBuilder()
    C = b.create_quantum_register(12*count, "coefficient")
    low = b.create_quantum_register(12*count, "target")
    q0 = b.create_quantum_register(12, "head0")
    q1 = b.create_quantum_register(12, "head1")
    g = b.create_quantum_register(1, "flag")[0]
    n = b.num_allocated_qubits
    call = implementation if new else virtual.products
    call(b, [C[j:j+12] for j in range(0,len(C),12)],
         [low[j:j+12] for j in range(0,len(low),12)], q0, q1, g)
    assert b.num_allocated_qubits == n
    return b.finish_circuit(), n


def bits(word):
    return ((word[None,:] >> np.arange(12,dtype=np.uint32)[:,None]) & 1).astype(bool)


def verify(km, virtual, args, m, implementation=lend, parked_helpers=23):
    rng = np.random.default_rng(900137114+m)
    shots = args.shots
    words = lambda: rng.integers(0, 4096, shots, dtype=np.uint32)
    g = np.arange(shots)%2 == 0
    leading = words()
    leading[g] = 0
    coefficients = [*(words() for _ in range(m-1)),leading]
    regs = dict(coefficient=np.vstack([bits(c) for c in coefficients]),
                target=np.vstack([bits(words()) for _ in range(m)]),
                head0=bits(words()), head1=bits(words()), flag=g[None,:])
    reference = None
    receipt = []
    for new in (False,True):
        tape, n = build(km, virtual, m, new, implementation)
        destination = args.out / f"{'new' if new else 'old'}_{m}.kmb"
        tape.to_file(destination, format="kmb")
        for seed in (17, 8567, 94397, 97421):
            sim = km.Simulator(batch_size=shots, seed=seed)
            sim.use_same_registers_as(tape)
            for name, matrix in regs.items():
                sim.write_across_shots(tape.register_data[name], matrix)
            sim.do(tape)
            assert not sim.read_phase_flipped_across_shots().any()
            assert not sim.read_across_shots(km.array([km.q(i) for i in range(n,tape.num_qubits)])).any()
            for name, matrix in regs.items():
                output = sim.read_across_shots(tape.register_data[name])
                if name == "target":
                    if reference is None:
                        reference = output
                    assert np.array_equal(reference,output)
                else:
                    assert np.array_equal(matrix,output), name
        with destination.open('rb') as stream:
            sha = file_digest(stream,"sha256").hexdigest()
        receipt.append(dict(new=new, Qhelper=tape.num_qubits-n, static_paid=tape.operation_statistics().num_toffoli_like,
                            ops=len(tape), gates=destination.name, sha256=sha, verified_shots=shots*4))
    assert receipt[0]["Qhelper"] == 24 and receipt[1]["Qhelper"] == parked_helpers
    return dict(m=m, records=receipt)


def main(args):
    for path in (args.source/"after_c5/extractor_width", args.source/"after_c5/converter_width",
                 args.source/"night_c27/arithmetic"):
        sys.path.insert(0, str(path))
    import ew_paths # noqa: F401
    import kickmix as km
    import gauge_park_virtual as virtual
    args.out.mkdir(parents=True,exist_ok=True)
    report = []
    for m in args.points:
        rec = verify(km, virtual,args,m)
        print(json.dumps(rec), flush=True)
        report.append(rec)
    (args.out/"result.json").write_text(json.dumps(report,indent=2)+"\n")


if __name__ == "__main__":
    p = ArgumentParser(description=__doc__)
    for name in ("source","out"):
        p.add_argument("--"+name,required=True,type=Path)
    p.add_argument("--points", type=int,nargs="+",default=[16])
    p.add_argument("--shots",type=int,default=1024)
    main(p.parse_args())
