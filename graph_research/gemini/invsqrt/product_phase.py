"""Search new paid product features against the official inverse-root tariff."""

import argparse
from collections import defaultdict
from fractions import Fraction
from itertools import combinations
import json
import math
from pathlib import Path
import sys
import time

import numpy as np

from audit import data_update, MAX_X, WIRES

BASE_COST = 78673.55534364567
BASE_T = 1478.7506100300882 + .25


def states(xs):
    one = (1 << len(xs)) - 1
    values = [int.from_bytes(np.packbits((xs >> q) & 1, bitorder="little").tobytes(), "little")
              for q in range(22)] + [0] * 24
    return one, values


def tape(lines, xs):
    one, values = states(xs)
    branches = []
    yield 0, values, "start"
    for i, line in enumerate(lines):
        op = line.split()[0]
        wires = tuple(map(int, WIRES.findall(line)))
        if op == "PUSH_CONDITION":
            branches.append(values.copy())
        elif op == "POP_CONDITION":
            assert values == branches.pop()
        else:
            data_update(op, wires, values, one)
        if not branches:
            yield i + 1, values, op
    assert not branches


def unpack(value, n):
    return np.unpackbits(np.frombuffer(value.to_bytes((n + 7) // 8, "little"), dtype=np.uint8),
                         bitorder="little")[:n]


def cost(margin, nrot):
    if margin <= 0:
        return math.inf
    return 46 * (BASE_T + 1 + nrot * (.56 * math.log2(nrot / (math.pi * margin)) + 5.3) / 4)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-repo", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--drop", nargs="*", type=int, default=[16])
    parser.add_argument("--limit", type=int, default=300)
    args = parser.parse_args()
    sys.path.insert(0, str(args.reference_repo))
    from score8_invsqrt_sparse_phase import load, SCALE
    from score8_invsqrt_global_feature import opt

    started = time.monotonic()
    lines = args.source.read_text().splitlines()
    B, e, t, desc = load(args.reference_repo.parent / "invsqrt_structural_work")
    margin = t - abs(e)
    initial = np.unique(np.r_[np.arange(2048), np.linspace(0, MAX_X - 1, 2048, dtype=int),
                              np.argpartition(margin, 1024)[:1024]])
    fixed = [(j, -float(Fraction(desc[j]["half_turns"]) / 2) / SCALE) for j in args.drop]
    fit, res, active = opt(B, e, t, None, initial, fixed=fixed)
    dual = res.ineqlin.marginals
    weights = dual[:len(active)] - dual[len(active):]
    nonzero = np.flatnonzero(abs(weights) > 1e-10)
    xs = (active + 1).astype(np.uint32)
    support = np.asarray(nonzero, dtype=int)
    sw = weights[support]
    nrot = 34 - len(args.drop)
    score_cache = {}

    def score(signature):
        if signature not in score_cache:
            score_cache[signature] = sum(weight for i, weight in enumerate(sw) if signature >> i & 1)
        return score_cache[signature]

    distinctive = {}
    paths = 0
    for cut, values, op in tape(lines, xs):
        if op not in {"HMR", "CCX", "CSWAP", "Z_POW", "POP_CONDITION"}:
            continue
        clean = next((q for q in range(22, 46) if not values[q]), None)
        if clean is None:
            continue
        paths += 1
        wires = [(q, value) for q, value in enumerate(values) if value and value.bit_count() != len(xs)]
        forms = [(q, value, sum(((value >> int(s)) & 1) << i for i, s in enumerate(support)))
                 for q, value in wires]
        seen = set(values)
        for (a, fa, sa), (b, fb, sb) in combinations(forms, 2):
            correlation = abs(score(sa & sb))
            if correlation < .002:
                continue
            candidate = fa & fb
            if candidate in seen or candidate in distinctive:
                continue
            distinctive[candidate] = (correlation, cut, a, b, clean)

    ranked = sorted(distinctive.items(), key=lambda entry: -entry[1][0])
    print(json.dumps({"stage": "generated", "cuts": paths, "products": len(ranked),
                      "baseline_drop_margin": fit["min_margin_turns"], "seconds": time.monotonic() - started}),
          flush=True)
    # Include tight original inputs and every nonzero dual weight.
    coarse = np.unique(np.r_[np.argsort(margin[active])[:384], nonzero,
                             np.linspace(0, len(active) - 1, 256, dtype=int)])
    ca = np.arange(len(coarse))
    rows = []
    shortlist = []
    BB, ee, tt = B[active][coarse], e[active][coarse], t[active][coarse]
    for signature, (corr, cut, a, b, ancilla) in ranked[:args.limit]:
        values = unpack(signature, len(active))[coarse]
        fit, _, _ = opt(BB, ee, tt, values, ca, full=False, fixed=fixed)
        bound = fit.get("upper_margin_turns", -math.inf)
        row = dict(cut=cut, controls=[a, b], ancilla=ancilla, bound=bound, correlation=corr)
        rows.append(row)
        if cost(bound, nrot) < BASE_COST:
            shortlist.append(row)
    shortlist.sort(key=lambda row: -row["bound"])
    print(json.dumps({"stage": "coarse", "checked": len(rows), "shortlist": len(shortlist),
                      "seconds": time.monotonic() - started}), flush=True)
    by_cut = defaultdict(list)
    for row in shortlist[:12]:
        by_cut[row["cut"]].append(row)
    full = []
    if by_cut:
        for cut, values, op in tape(lines, np.arange(1, MAX_X + 1, dtype=np.uint32)):
            for row in by_cut.get(cut, []):
                a, b = row["controls"]
                if values[row["ancilla"]]:
                    row["result"] = "scratch_not_clean"
                    continue
                new = unpack(values[a] & values[b], MAX_X)
                fit, _, _ = opt(B, e, t, new, active, fixed=fixed)
                predicted = cost(fit["min_margin_turns"], nrot)
                full.append(dict(row, fit=fit, predicted_cost=predicted))
                print(json.dumps({"stage": "full", **row, "cost": predicted,
                                  "seconds": time.monotonic() - started}), flush=True)
    report = {"drop": args.drop, "coarse_checked": len(rows), "promising": shortlist,
              "best_upper_bounds": sorted(rows, key=lambda r: -r["bound"])[:25],
              "full": full, "new_rotation_count": nrot, "seconds": time.monotonic() - started}
    args.out.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
