"""Resynthesize paid conditional phase blocks using one three-parity CCZ."""

from argparse import ArgumentParser
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
from random import Random
import re
import sys

from state_supported_rewrite import dag


def find_pivots(parities):
    candidates = [q for q in range(dag.QUBITS) if any(q in f for f in parities)]
    for wires in combinations(candidates, 3):
        rows = [sum(1 << j for j, q in enumerate(wires) if q in ones) for ones in parities]
        if all(rows) and len(set(rows)) == 3 and rows[0] ^ rows[1] ^ rows[2]:
            return wires
    raise ValueError("The three parity forms are dependent")


def emit(parities, quadratics):
    output = [" ".join([("NEG", "Z", "CZ")[len(m)], *(f"q{q}" for q in m)])
              for m in quadratics]
    if not parities:
        return output
    pivots = find_pivots(parities)
    rows = [set(row) for row in parities]
    undo = []
    for i, row in enumerate(rows):
        for index in sorted(row - set(pivots)):
            row.remove(index)
            undo.append(f"CX q{index} q{pivots[i]}")
    for i, q in enumerate(pivots):
        swap = next(j for j in range(i, 3) if q in rows[j])
        if swap != i:
            rows[i], rows[swap] = rows[swap], rows[i]
            undo.append(f"SWAP q{q} q{pivots[swap]}")
        for j, row in enumerate(rows):
            if i != j and q in row:
                row.symmetric_difference_update(rows[i])
                undo.append(f"CX q{q} q{pivots[j]}")
    assert rows == [{q} for q in pivots]
    return output + undo[::-1] + ["CCZ " + " ".join(f"q{q}" for q in pivots)] + undo


def value(state, mask, controls):
    result = mask
    for control in controls:
        parity = 0
        for q in control:
            parity ^= state[q]
        result &= parity
    return result


def symbolic_pairs(region):
    """Extract pairs of affine control forms visible in the original block."""
    state = [1 << q for q in range(dag.QUBITS)]
    constant = 1 << dag.QUBITS
    known = (constant << 1) - 1
    products = {}
    pairs = set()

    def product(a, b):
        if not (a | b) & ~known:
            pair = tuple(sorted([a & (constant - 1), b & (constant - 1)]))
            if pair[0] and pair[0] != pair[1]:
                pairs.add(pair)
        key = tuple(sorted([a, b]))
        if key not in products:
            products[key] = 1 << (dag.QUBITS + 1 + len(products))
        return products[key]

    for op, wires in region:
        if op == "X":
            state[wires[0]] ^= constant
        elif op == "CX":
            control, target = wires
            state[target] ^= state[control]
        elif op == "CCX":
            a, b, target = wires
            state[target] ^= product(state[a], state[b])
        elif op == "SWAP":
            a, b = wires
            state[a], state[b] = state[b], state[a]
        elif op == "CSWAP":
            control, a, b = wires
            delta = product(state[control], state[a] ^ state[b])
            state[a] ^= delta
            state[b] ^= delta
        elif op == "HMR":
            state[wires[0]] = 0
        elif op == "CCZ":
            for a, b in combinations(wires, 2):
                product(state[a], state[b])
    return [
        ([q for q in range(dag.QUBITS) if a >> q & 1],
         [q for q in range(dag.QUBITS) if b >> q & 1])
        for a, b in sorted(pairs)
    ]


def search(state, target, mask, theory, structural, structural_only):
    wires = [q for q, signal in enumerate(state) if signal not in (0, mask)]
    quadratic = [(), *((q,) for q in wires), *combinations(wires, 2)]
    all_pairs = {pair: value(state, mask, [(q,) for q in pair]) for pair in quadratic}
    basis = theory.affine_basis(all_pairs.values())
    echelon = [(1 << i, basis[i][0]) for i in sorted(basis, reverse=True)]

    def projection(f):
        for pivot, row in echelon:
            if f & pivot:
                f ^= row
        return f

    residual = projection(target)
    if not residual:
        model = theory.solve(basis, target)
        return [], [m for i, m in enumerate(quadratic) if model & (1 << i)], 0

    trials = 0

    def solve_factors(left, right, terms):
        coeff = theory.solve(theory.affine_basis(terms), residual)
        if coeff is None:
            return None
        parities = [left, right, [q for j, q in enumerate(wires) if coeff & (1 << j)]]
        model = theory.solve(basis, target ^ value(state, mask, parities))
        assert model is not None
        return parities, [m for i, m in enumerate(quadratic) if model & (1 << i)], trials

    for left, right in structural:
        trials += 1
        pair = value(state, mask, [left, right])
        model = solve_factors(left, right, [projection(pair & state[q]) for q in wires])
        if model is not None:
            return model
    if structural_only:
        return None, None, trials

    cube = {}
    for a, b, c in combinations(wires, 3):
        cube[a, b, c] = projection(all_pairs[a, b] & state[c])

    def direct(a, b, c):
        return cube[tuple(sorted((a, b, c)))] if len({a, b, c}) == 3 else 0

    for a in wires:
        table = {b: [direct(a, b, c) for c in wires] for b in wires if a != b}
        for b, c in combinations(table, 2):
            trials += 1
            terms = [x ^ y for x, y in zip(table[b], table[c])]
            model = solve_factors([a], [b, c], terms)
            if model is not None:
                return model
    return None, None, trials


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("report", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--prior-code", type=Path, required=True)
    parser.add_argument("--structural-only", action="store_true")
    opts = parser.parse_args()
    assert sha256(opts.source.read_bytes()).hexdigest() == dag.PIN
    sys.path.insert(0, str(opts.prior_code))
    import score_invsqrt_retire as theory
    import score8_invsqrt_phase_oneccz as blocks
    lines = str(dag.km.Circuit.from_file(opts.source)).splitlines()
    ops = [(line.split()[0], tuple(map(int, re.findall(r"\bq(\d+)\b", line)))) for line in lines]
    shapes, depth, uses = blocks.shape(lines, ops)
    eligible = []
    for item in shapes:
        if item["paid"] <= 1:
            continue
        symbols, reason = blocks.symbols(lines, ops, item, depth, uses)
        if symbols is not None:
            eligible.append(dict(item, symbolic=symbols))
    rng = Random(928541)
    xs = sorted(set(range(1, 129)) | {rng.randrange(1, dag.DOMAIN + 1) for _ in range(2304)})
    mask, sample = blocks.sample_values(xs)
    data = blocks.extract(lines, ops, eligible, mask, sample)
    candidates, metrics = {}, []
    for item, state, guards, target in data:
        structural = symbolic_pairs(ops[item["start"] + 1:item["end"]])
        parities, quadratics, trials = search(state, target, mask, theory, structural,
                                             opts.structural_only)
        metrics.append(dict(start=item["start"], paid=item["paid"], tested=trials,
                            found=parities is not None))
        if parities is not None:
            candidates[item["start"]] = (parities, quadratics, guards)
        print(metrics[-1], flush=True)
    matched = {}
    if candidates:
        mask, full = theory.initial_values()
        selected = [item for item in eligible if item["start"] in candidates]
        for item, state, guards, target in blocks.extract(lines, ops, selected, mask, full):
            parities, quadratics, expected_guards = candidates[item["start"]]
            actual = value(state, mask, parities) if parities else 0
            for monomial in quadratics:
                actual ^= value(state, mask, [(q,) for q in monomial])
            if actual == target and guards == expected_guards:
                matched[item["start"]] = dict(end=item["end"], parities=parities,
                                              quadratics=quadratics, guards=guards,
                                              saved=item["paid"] - int(bool(parities)))
    report = dict(source_sha256=dag.PIN, sampled=len(xs), full_domain=dag.DOMAIN,
                  blocks=metrics, accepted=matched)
    if matched:
        result = []
        i = 0
        while i < len(lines):
            if i not in matched:
                result.append(lines[i])
                i += 1
                continue
            match = matched[i]
            result.append(lines[i])
            result.extend("PUSH_CONDITION if " + guard.removeprefix("external_")
                          for guard in match["guards"])
            result.extend(emit(match["parities"], match["quadratics"]))
            result.extend("POP_CONDITION" for _ in match["guards"])
            result.append("POP_CONDITION")
            i = match["end"] + 1
        candidate = dag.km.Circuit("\n".join(result) + "\n")
        candidate.to_file(opts.candidate, format="kmb")
        report["candidate_sha256"] = sha256(opts.candidate.read_bytes()).hexdigest()
        report["candidate_qubits"] = candidate.num_qubits
    opts.report.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
