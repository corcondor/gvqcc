"""Test joint CCX removals inside measurement-correcting conditional blocks."""

import argparse
from collections import defaultdict
import hashlib
from itertools import combinations
import json
from pathlib import Path
import sys
import time

import kickmix as km
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "graph_inv"))
from temporal_phase_graph import (
    DATA, SIGN, MAX_X, SOURCE_SHA, advance, capture_entries, columns,
    gate, layout, make_edges, product, solve,
)


def trace(lines, ops, before, one, push, stop, guards, skip):
    baseline = before.copy()
    modified = before.copy()
    states = {}
    debts = defaultdict(int)
    for i in range(push + 1, stop):
        op, qs = ops[i]
        if op == "HMR":
            debts[i] ^= baseline[qs[0]] ^ modified[qs[0]]
        elif op in SIGN:
            delta = product(baseline, qs, one) ^ product(modified, qs, one)
            if delta:
                k = guards.get(i) if " if " in lines[i] else push
                if k is None:
                    return None
                debts[k] ^= delta
        elif op == "Z_POW" and product(baseline, qs, one) != product(modified, qs, one):
            return None
        elif op == "R" and (baseline[qs[0]] or modified[qs[0]]):
            return None
        if op in DATA:
            advance(op, qs, baseline, one)
            if i not in skip:
                advance(op, qs, modified, one)
        if i >= min(skip) and op in DATA:
            states[i] = modified.copy()
    if baseline != modified or baseline != before:
        return None
    return states, {k: f for k, f in debts.items() if f}


def search(lines, ops, x, max_cuts):
    owner, boundaries, guards, unsupported = layout(lines, ops)
    options = defaultdict(list)
    for i, (op, qs) in enumerate(ops):
        push = owner[i]
        if op in {"CCX", "CSWAP"} and push is not None and push not in unsupported:
            options[push].append(i)
    candidate_blocks = {k: v for k, v in options.items() if len(v) >= 2}
    one = (1 << len(x)) - 1
    entries = capture_entries(ops, columns(x), one, candidate_blocks)
    checks = 0
    restores = 0
    models = []
    rejects = []
    for push, candidates in candidate_blocks.items():
        stop = boundaries[push]
        for size in range(2, len(candidates)+1):
            for skip in combinations(candidates, size):
                checks += 1
                trial = trace(lines, ops, entries[push], one, push, stop, guards, skip)
                if trial is None:
                    continue
                restores += 1
                states, debts = trial
                phases = []
                for origin, f in debts.items():
                    basis, edges, _ = make_edges(states, one, origin, max_cuts)
                    coeff = solve(basis, f)
                    if coeff is None:
                        rejects.append({"removed": skip, "first_unsolved_origin": origin, "rank": len(basis)})
                        break
                    phases.append({"origin": origin, "terms": [e for j,e in enumerate(edges) if coeff >> j & 1]})
                else:
                    models.append({"push": push, "stop": stop, "removed": skip, "phases": phases})
    return {"blocks": len(candidate_blocks), "joint_trials": checks, "restored": restores,
            "sample_models": models, "unspanned": rejects}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    assert hashlib.sha256(args.source.read_bytes()).hexdigest() == SOURCE_SHA
    t0 = time.monotonic()
    c = km.Circuit.from_file(args.source,format="kmb")
    lines = str(c).splitlines()
    ops = list(map(gate, lines))
    rng = np.random.default_rng(20261115)
    xs = np.unique(np.r_[np.arange(1,257), rng.integers(1, MAX_X + 1, size=2304)]).astype(np.uint32)
    data = search(lines, ops, xs, 64)
    data.update({"samples": len(xs), "source_sha256": SOURCE_SHA, "seconds": time.monotonic() - t0})
    args.output.write_text(json.dumps(data, indent=2) + "\n")
    print({k: len(v) if isinstance(v, list) else v for k,v in data.items()})


if __name__ == "__main__":
    main()
