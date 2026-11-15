#!/usr/bin/env python3
"""Certify a local paid-gate lower bound on affine-hull phase polynomials.

Fix the classical outcomes so the quantum Boolean data flow is deterministic.
Write every wire as affine in the entry coordinates and the AND outputs from
CCX/CSWAP. A CZ starts with two factors, and a CCZ starts with three after
spending one paid operation of its own. When substituting an AND output in
reverse order, a square-free monomial gains at most one degree. Thus a phase
computed with p paid gates has degree at most p+2 using this gate family.
Each HMR contributes a wire value times its fixed outcome, at most p+1 degree.
"""
import argparse
from collections import defaultdict
from itertools import combinations
import json
from pathlib import Path
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--repo", type=Path, required=True)
parser.add_argument("--result", type=Path, required=True)
args = parser.parse_args()
sys.path.insert(0, str(args.repo))
import score8_invsqrt_phase_oneccz as old
import score_invsqrt_retire as circuit
from score8_invsqrt_phase_quadratic import PIN

ONE = frozenset({0})
ZERO = frozenset()


def multiply(lhs, rhs):
    out = set()
    for a in lhs:
        for b in rhs:
            out.symmetric_difference_update((a | b,))
    return frozenset(out)


def phase_polynomial(lines, ops, item, entry):
    """Track actual data operations; diagonal gates leave data unchanged."""
    a, b = item["start"], item["end"]
    groups = defaultdict(list)
    for key, indices in item["symbolic"]["terms"].items():
        for i in indices:
            groups[i].append(key)
    phase = defaultdict(lambda: ZERO)
    wires = entry[:]
    for i in range(a + 1, b):
        gate, qs = ops[i]
        for key in groups[i]:
            term = ONE
            for q in qs:
                term = multiply(term, wires[q])
            phase[key] ^= term
        if gate == "X":
            q, = qs
            wires[q] ^= ONE
        elif gate == "CX":
            c, t = qs
            wires[t] ^= wires[c]
        elif gate == "CCX":
            c1, c2, t = qs
            wires[t] ^= multiply(wires[c1], wires[c2])
        elif gate == "CSWAP":
            c, a, b = qs
            d = multiply(wires[c], wires[a] ^ wires[b])
            wires[a] ^= d
            wires[b] ^= d
        elif gate == "SWAP":
            a, b = qs
            wires[a], wires[b] = wires[b], wires[a]
        elif gate == "HMR":
            q, = qs
            wires[q] = ZERO
    return {key:p for key,p in phase.items() if p}, wires == entry


def affine_entry(values, one):
    features = [one, *values]
    basis = circuit.affine_basis(features)
    seeds = sorted((c.bit_length()-1 for _, c in basis.values()))
    assert seeds[0] == 0
    slots = {old: (0 if old == 0 else 1 << (old - 1)) for old in seeds}
    out = []
    for v in values:
        coeff = circuit.solve(basis, v)
        out.append(frozenset(slots[s] for s in seeds if coeff >> s & 1))
        assert all(coeff>>k&1 == 0 for k in range(len(features)) if k not in slots)
    return out, len(seeds)-1


def cubic_support(phase):
    """Return row span of h -> degree-2 part of f(z+h)+f(z).

    The linear map's kernel consists of precisely those directions in which
    the cubic part drops to degree <=1 on differentiation. Its codimension
    is the minimum number of coordinates needed for f modulo quadratics.
    """
    rows = defaultdict(int)
    for monomial in phase:
        if monomial.bit_count() != 3:
            continue
        bits = [1 << i for i in range(46) if monomial >> i & 1]
        for a, b in combinations(bits, 2):
            rows[a|b] ^= monomial ^ a ^ b
    return sorted(value for value, _ in circuit.affine_basis(list(rows.values())).values())


def parity(form):
    return frozenset(1 << i for i in range(46) if form >> i & 1)


def cubic(phase):
    return frozenset(m for m in phase if m.bit_count() == 3)


def evaluate(phase, values, one):
    out = 0
    for monomial in phase:
        term = one
        for i, v in enumerate(values):
            if monomial >> i & 1:
                term &= v
        out ^= term
    return out


def screen():
    src = args.repo / "score3_invsqrt_cache.kmx"
    assert old.sha(src) == PIN
    lines, ops = circuit.instructions(src)
    blocks, depth, uses = old.shape(lines, ops)
    items = []
    for block in blocks:
        if block["paid"] <= 1:
            continue
        symbolic, _ = old.symbols(lines, ops, block, depth, uses)
        if symbolic is not None:
            items.append({**block, "symbolic":symbolic})
    # Full legal input domain establishes all affine constraints, not sampled guesses.
    one, values = circuit.initial_values()
    full = old.extract(lines, ops, items, one, values)

    rows = []
    for item, values, key, target in full:
        entry, dimension = affine_entry(values, one)
        phases, restores_data = phase_polynomial(lines, ops, item, entry)
        phase = phases.pop(key, ZERO)
        assert evaluate(phase, values, one) == target
        assert all(evaluate(term, values, one) == 0 for term in phases.values())
        rank = cubic_support(phase)
        degree = max((term.bit_count() for term in phase), default=0)
        status = "DEGREE_ABOVE_THREE" if degree > 3 else "NO_ONE_CCZ_ON_AFFINE_HULL"
        if degree < 3:
            status = "QUADRATIC"
        if degree == 3 and len(rank) == 3:
            product = multiply(multiply(parity(rank[0]), parity(rank[1])), parity(rank[2]))
            assert cubic(product) == cubic(phase)
            status = "ONE_CCZ"
        row = dict(start=item["start"], end=item["end"], static_paid=item["paid"],
                   full_input_count=circuit.MAX_X, affine_hull_dimension=dimension,
                   phase_degree=degree,
                   degree_witness_coordinates=[
                       i for i in range(46)
                       if next((m for m in phase if m.bit_count() == degree), 0) >> i & 1
                   ],
                   paid_lower_bound=max(0, degree-2),
                   tight_paid_bound=restores_data and not phases and degree-2 == item["paid"],
                   symbolic_data_identity=restores_data,
                   extra_symbolic_phase_terms=len(phases), status=status,
                   cubic_terms=len(cubic(phase)), cubic_support_dimension=len(rank),
                   cubic_support_basis=[sorted(f.bit_length()-1 for f in parity(v)) for v in rank])
        print(row, flush=True)
        rows.append(row)
    return dict(
        source_sha256=PIN, rows=rows,
        tight_count=sum(row["tight_paid_bound"] for row in rows),
        gate_family=["X","CX","CCX","SWAP","CSWAP","Z","CZ","CCZ","NEG","HMR","R"],
        scope=(
            "Exact local Boolean phase degree on the affine hull of each supported "
            "block's entry states. Requires equality on that entire hull and the "
            "same block boundary, with fixed classical branches. Does not bound "
            "rewrites exploiting nonlinear reachability or Z_POW rotations."
        ),
    )

args.result.write_text(json.dumps(screen(), indent=2)+"\n")
