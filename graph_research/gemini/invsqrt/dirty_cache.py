"""Reuse a CCX product in a dirty target when the old target enters the identity."""

import argparse
from collections import defaultdict
from pathlib import Path
import hashlib
import json
import random
import re
import sys
import time

import kickmix as km

PIN = "684106f101730ca193627229920a0501bef9ea10ccfb34aa453fcf63edadb50a"


def test(gates, caps, ops, initial, one, ones, structure, exact_plan=None):
    r, cache = structure
    values = initial.copy()
    stack = []
    active = []
    queries = 0
    hits = []
    if exact_plan is not None:
        by_end = defaultdict(list)
        for h in exact_plan:
            by_end[h["last"]].append(h)
        keep = {h["first"] for h in exact_plan}
        products = {}
    for i, (op, qs) in enumerate(ops):
        if i in gates:
            a, b, target = qs
            p = values[a] & values[b]
            if exact_plan is None:
                active = [(j, prod) for j, prod in active if caps[j]["end_exclusive"] > i]
                candidates = active
            else:
                candidates = [(h["first"], products[h["first"]]) for h in by_end.get(i, [])]
            if candidates:
                available = [one] + [0 if q == target else v for q, v in enumerate(values)]
                basis = r.affine_basis(available)
                for first, old_product in candidates:
                    queries += 1
                    coeff = r.solve(basis, p ^ old_product ^ values[target])
                    if coeff is None:
                        continue
                    plan = cache.at_end(caps[first], i, ones)
                    holder = plan["final_holder"]
                    if coeff >> (holder + 1) & 1:
                        coeff ^= 1 << (holder+1)
                        if ones[i] >> holder & 1:
                            coeff ^= 1
                    assert not (coeff >> (target + 1) & 1)
                    hits.append(dict(plan, affine_mask=coeff))
            if exact_plan is None and i in caps:
                active.append((i,p))
            elif exact_plan is not None and i in keep:
                products[i] = p
        cache.execute(op, qs, values, one, stack)
    assert not stack
    return queries, hits


def render(lines, ops, plan):
    first, last = plan["first"], plan["last"]
    coeff = plan["affine_mask"]
    holder = plan["initial_holder"]
    hopmap = {h["index"]: h for h in plan["hops"]}
    fresh = 1 + max(map(int, re.findall(r'\bb(\d+)\b','\n'.join(lines))))
    out = []
    edits = {}
    for i, line in enumerate(lines):
        prefix = []
        if i in hopmap:
            hop = hopmap[i]
            old, new = hop["old"], hop["new"]
            assert old == holder
            if hop["new_constant"]:
                prefix.append(f"X q{new}")
            prefix.extend([f"CX q{old} q{new}", f"CX q{new} q{old}"])
            if hop["old_constant"]:
                prefix.append(f"X q{old}")
            holder = new
        if i == first:
            a,b,t = ops[i][1]
            if plan["initial_constant"]:
                prefix.append(f"X q{holder}")
            prefix.extend([f"CCX q{a} q{b} q{holder}", f"CX q{holder} q{t}"])
        elif i == last:
            a,b,t = ops[i][1]
            linear = [q for q in range(46) if coeff >> (q + 1) & 1]
            assert t not in linear and holder not in linear
            prefix.extend([f"HMR q{t} b{fresh}", f"CZ q{a} q{b} if b{fresh}", f"Z q{holder} if b{fresh}"])
            prefix.extend(f"Z q{q} if b{fresh}" for q in linear)
            if coeff & 1:
                prefix.extend([f"NEG if b{fresh}",f"X q{t}"])
            prefix.append(f"CX q{holder} q{t}")
            prefix.extend(f"CX q{q} q{t}" for q in linear)
            prefix.extend([f"HMR q{holder} b{fresh+1}",f"Z q{t} if b{fresh+1}"])
            prefix.extend(f"Z q{q} if b{fresh+1}" for q in linear)
            if coeff & 1:
                prefix.append(f"NEG if b{fresh+1}")
            if plan["final_constant"]:
                prefix.append(f"X q{holder}")
        else:
            prefix.append(line)
        if prefix != [line]:
            edits[i] = prefix
        out.extend(prefix)
    return "\n".join(out)+"\n", edits


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--reference", type=Path, required=True)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    sys.path.insert(0, str(args.reference))
    import score_invsqrt_retire as r
    import score4_invsqrt_affine_cache as cache
    import score4_invsqrt_cache_route as route
    begin = time.monotonic()
    lines, ops, depth, refs, constant, ones, _, total = route.profile(args.source, route.PIN)
    gates = {i for i, (op, _) in enumerate(ops) if op == "CCX" and depth[i] == 0 and " if " not in lines[i]}
    caps = {i: cap for i in gates if (cap := cache.capacity(i, refs, constant, ones)) is not None}
    rng = random.Random(2026111504)
    xs = list(range(1, 129))
    for k in range(1, 23):
        lo, hi = 1 << (k - 1), min((1 << k) - 1, r.MAX_X)
        if lo <= hi:
            xs.extend(rng.randrange(lo, hi + 1) for _ in range(12))
    xs = list(dict.fromkeys(xs))
    while len(xs) < 512:
        x = rng.randrange(1, r.MAX_X + 1)
        if x not in xs:
            xs.append(x)
    bits = [sum(((x >> q) & 1) << j for j,x in enumerate(xs)) for q in range(22)] + [0]*24
    queries, samples = test(gates, caps, ops, bits, (1 << len(xs)) - 1, ones, (r,cache))
    if samples:
        one, values = r.initial_values()
        full_count, hits = test(gates, caps, ops, values, one, ones, (r,cache), samples)
    else:
        full_count, hits = 0, []
    print(json.dumps({"queries":queries,"sample_hits": len(samples),"full_hits":len(hits)}), flush=True)
    summary = {"pin":PIN,"queries":queries,"sample_hits":samples,"full_count":full_count,"full_hits":hits}
    if hits:
        plan = min(hits,key=lambda h:(len(h["hops"]),h["last"]-h["first"]))
        text, edits = render(lines, ops, plan)
        candidate = km.Circuit(text)
        original = km.Circuit(args.source.read_text())
        assert candidate.num_qubits == original.num_qubits
        assert original.operation_statistics().num_toffoli_like - candidate.operation_statistics().num_toffoli_like == 1
        target_path = args.out.with_suffix(".kmb")
        candidate.to_file(target_path,format="kmb")
        summary["chosen"] = plan
        summary["edits"] = edits
        summary["candidate_sha256"] = hashlib.sha256(target_path.read_bytes()).hexdigest()
    summary["seconds"] = time.monotonic()-begin
    args.out.write_text(json.dumps(summary,indent=2)+"\n")


if __name__ == "__main__":
    main()
