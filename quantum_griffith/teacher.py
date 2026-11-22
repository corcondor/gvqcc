"""Exact ANF/affine teacher used to warm-start differentiable Boolean DAGs.

This does not claim the neural optimizer discovered the circuit. The teacher
is a known-correct constructive synthesis; the learner must beat it in exact
CCX/width after hard collapse to demonstrate a genuine improvement.
"""
from __future__ import annotations
from typing import Sequence

from .logic_dag import LogicDAG, LogicGate
from .synthesis import anf_terms, search_affine


def make_teacher(tables: Sequence[Sequence[int]], n_inputs: int, *,
                 affine: bool = True) -> LogicDAG:
    if n_inputs < 1 or n_inputs > 8 or not tables:
        raise ValueError("Teacher is limited to small Boolean truth tables")
    expected = tuple(tuple(int(v) for v in t) for t in tables)
    if any(len(t) != (1 << n_inputs) or any(v not in (0, 1) for v in t)
           for t in expected):
        raise ValueError("Invalid truth tables")
    basis = (search_affine(expected, n_inputs, max_depth=2, beam_width=12)
             if affine else None)
    moves = basis.basis_cnots if basis is not None else ()
    n = n_inputs
    rows = [1 << i for i in range(n)]
    for c, t in moves:
        rows[t] ^= rows[c]
    transformed = [[0] * (1 << n) for _ in expected]
    for x in range(1 << n):
        u = sum(((x & row).bit_count() & 1) << i for i, row in enumerate(rows))
        for o in range(len(expected)):
            transformed[o][u] = expected[o][x]

    gates: list[LogicGate] = []
    cache: dict[tuple[int, int, int], int] = {}

    def append(tt: int, a: int, b: int) -> int:
        if tt in (6, 8) and a > b:
            a, b = b, a  # XOR and AND are commutative
        key = (tt, a, b)
        if key not in cache:
            cache[key] = n + len(gates)
            gates.append(LogicGate(a, b, tt))
        return cache[key]

    # Model the input CNOT basis change as explicit XOR nodes in a DAG.
    u_refs = list(range(n))
    for c, t in moves:
        u_refs[t] = append(6, u_refs[t], u_refs[c])

    monomial_cache: dict[int, int] = {}

    def product(mask: int) -> int:
        if mask in monomial_cache:
            return monomial_cache[mask]
        bits = [i for i in range(n) if (mask >> i) & 1]
        if not bits:
            ref = append(15, 0, 0)  # constant one
        else:
            ref = u_refs[bits[0]]
            for bit in bits[1:]:
                ref = append(8, ref, u_refs[bit])
        monomial_cache[mask] = ref
        return ref

    outs = []
    for table in transformed:
        terms = anf_terms(table, n)
        if not terms:
            outs.append(append(0, 0, 0))
            continue
        refs = [product(mask) for mask in terms]
        current = refs[0]
        for other in refs[1:]:
            current = append(6, current, other)
        outs.append(current)
    graph = LogicDAG(n, tuple(gates), tuple(outs))
    if graph.truth_tables() != expected:
        raise AssertionError("Internal teacher synthesis bug")
    return graph
