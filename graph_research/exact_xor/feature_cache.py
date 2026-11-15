"""Compile ANGLE in a rotating feature bank with two work lanes reserved for tags."""
from __future__ import annotations

import argparse
from collections import Counter
from functools import lru_cache
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
import shutil
import sys

import kickmix as km


def union(values, start=0):
    for value in values:
        start |= value
    return start


def lane_mask(wires):
    return sum(1 << (wire + 1) for wire in wires)


def choose_plan(supports, valid_pairs, start, neighbors, beam_width):
    """Greedy warm start, then beam search over masks of completed products."""
    all_terms = (1 << len(supports)) - 1
    cover = {
        pair: sum(1 << i for i, support in enumerate(supports)
                  if not (support & lane_mask(pair)))
        for pair in valid_pairs
    }
    uncovered = all_terms & ~union(cover.values())
    if uncovered:
        raise ValueError(f"{uncovered.bit_count()} products cannot fit any tested cache")
    full_cover = max(c.bit_count() for c in cover.values())
    sets = {p: frozenset(p) for p in valid_pairs}

    def transitions(current, remaining):
        for other in neighbors[current]:
            if (others := cover[other] & remaining):
                yield other, remaining ^ others, len(sets[current] - sets[other])

    # Width applies to the entire frontier, score estimates the remaining cache exchanges.
    beam = {(start, all_terms): (0, [])}
    best = None
    for _ in supports:
        next_beam = {}
        for (current, remaining), (paid, route) in beam.items():
            for other, rest, delta in transitions(current, remaining):
                cost = paid + delta
                if best and cost >= best[0]:
                    continue
                path = [*route, (other, remaining ^ rest)]
                if rest == 0 and start in neighbors[other]:
                    total = cost + len(sets[other] - sets[start])
                    if best is None or total < best[0]:
                        best = total, path
                    continue
                if rest == 0:
                    continue
                key = other, rest
                if key not in next_beam or cost < next_beam[key][0]:
                    next_beam[key] = cost, path
        if not next_beam:
            break
        beam = dict(sorted(next_beam.items(), key=lambda r: (
            r[1][0] + r[0][1].bit_count() * 1.5 / full_cover,
            r[0][1].bit_count(), r[1][0], r[0][0]))[:beam_width])
    if best is None:
        raise ValueError("beam did not reach a complete route")
    return best


def exact_work_functions(prefix, n, tags, keep):
    """All legal addresses with the five programmed tag bits."""
    values = [sum(1 << a for a in range(1220) if a >> q & 1) for q in range(11)]
    values += [0] * (n - len(values))
    for q, (a, b) in zip(tags, keep):
        values[q] = values[a] & values[b]
    for gate, wires, _ in prefix:
        if gate == "X":
            values[wires[0]] ^= (1 << 1220) - 1
        elif gate == "CX":
            a, b = wires
            values[b] ^= values[a]
        elif gate == "CCX":
            a, b, t = wires
            values[t] ^= values[a] & values[b]
        else:
            assert gate == "R"
    return values


@lru_cache(maxsize=8)
def cache_transitions(values, pool):
    by_product = {}
    for a, b in combinations(pool, 2):
        by_product.setdefault(values[a] & values[b], []).append((a, b))
    regenerations = {
        q: [p for p in by_product.get(values[q], ()) if q not in p]
        for q in range(51, len(values))
    }
    regenerations = {q:ps for q,ps in regenerations.items() if ps}
    pairs = list(combinations(sorted(regenerations), 2))
    sets = {p:frozenset(p) for p in pairs}

    def recipe(q, avoid):
        return next((p for p in regenerations[q] if not avoid.intersection(p)), None)
    neighbors = {
        p:[r for r in pairs if all(recipe(q, sets[p] | sets[r]) is not None
                                    for q in sets[p] ^ sets[r])]
        for p in pairs
    }
    return pairs, neighbors, recipe


def emit_cache(circuit, S, parse_line, data, tags, initial_leaves, beam):
    lines = str(circuit).splitlines()
    ops = [parse_line(line) for line in lines]
    n = circuit.num_qubits
    assert n == 125
    pool = tuple(sorted(set(range(n)) - set(data)))
    start = 1 + max(i for i, (g, q, _) in enumerate(ops) if g == "CCX" and q[-1] >= 51)
    stop = next(i for i, (g, _, _) in enumerate(ops) if g == "HMR")
    assert stop > start
    frame, terms = S.get_frame(ops[start:stop], data, n)
    assert all(frame[q] == 1 << (q + 1) for q in pool), "nontrivial feature exit frame"
    tag_controls = [(0, 1), (0, 2), (1, 2), (0, 3), (1, 3)]
    encoding = [f"CX q{tag - 1} q{tag}" for tag in tags]
    enc_start = lines.index(encoding[0])
    assert lines[enc_start:enc_start+5] == encoding and lines[-5:] == encoding
    values = exact_work_functions(ops[enc_start+5:start], n, tags, tag_controls)
    pairs, neighbors, recipe = cache_transitions(tuple(values), pool)
    initial = [p for p in pairs if all(q in initial_leaves for q in p)]
    if not initial:
        raise ValueError("no pair of independently regenerable lanes")
    start_pair = min(initial, key=lambda p: sum(bool((a | b) & lane_mask(p))
                                                 for a,b,_ in terms))
    backup = [*start_pair, 125, 126, 127]
    _, inverse = S.affine_path(frame, data)
    data_mask = lane_mask(data)
    linear_only_frame = [row & data_mask if q in data else row for q,row in enumerate(frame)]
    linear, _ = S.affine_path(linear_only_frame, data)
    inject = {}
    for i, q in enumerate(data):
        for bit in S.bit_positions(frame[q] & ~data_mask):
            inject[bit] = inject.get(bit, 0) | (1 << i)
    transformed = S.preimage_directions([(bit,bit,w) for bit,w in sorted(inject.items())],
                                        data,inverse)
    preimage = S.preimage_directions(terms, data, inverse)
    supports = [a | b for a,b,_ in preimage] + [1 << bit for bit,_,_ in transformed]
    cost, path = choose_plan(supports, pairs, start_pair, neighbors, beam)

    def retain_bank_lines(i, end, omit):
        while i < end:
            gate, wires, _ = ops[i]
            if gate == "HMR" and wires[0] in omit:
                assert ops[i+1][0] == "CZ"
                i += 2
                continue
            if (gate == "R" and wires[0] in omit
                    or gate == "CCX" and wires[2] in omit):
                i += 1
                continue
            assert not set(wires) & omit, (i, lines[i], omit)
            yield lines[i]
            i += 1

    out = lines[:enc_start+5]
    for q, tmp, (a, b) in zip(tags, backup, tag_controls):
        out.extend((f"SWAP q{q} q{tmp}", f"CCX q{a} q{b} q{q}"))
    missing = set(start_pair)
    out.extend(retain_bank_lines(enc_start+5, start, missing))
    physical = {q:q for q in pool if q not in missing}

    def move(pair):
        nonlocal missing
        target = set(pair)
        free = []
        for q in sorted(target - missing):
            a, b = recipe(q, missing | target)
            # Caller ensures tap dependencies survive the transition.
            x = physical.pop(q)
            free.append(x)
            out.extend((f"HMR q{x} b0", f"CZ q{physical[a]} q{physical[b]} if b0"))
        for q, x in zip(sorted(missing - target), free, strict=True):
            a, b = recipe(q, missing | target)
            out.append(f"CCX q{physical[a]} q{physical[b]} q{x}")
            physical[q] = x
        missing = target

    import re
    token = re.compile(r"q(\d+)")

    def remap(line):
        return token.sub(lambda m: "q" + str(physical.get(int(m[1]), int(m[1]))), line)

    for pair, selected in path:
        move(pair)
        chosen = [preimage[i] for i in S.bit_positions(selected) if i < len(terms)]
        program = S.schedule_products(chosen, sorted(physical), data)
        check_frame, check_terms = S.get_frame(
            [parse_line(s) for s in program], data, n)
        assert all(check_frame[q] == 1 << (q+1) for q in range(n))
        assert Counter(check_terms) == Counter(chosen)
        out.extend(map(remap, program))
        for i in S.bit_positions(selected):
            if i >= len(terms):
                bit, _, directions = transformed[i-len(terms)]
                out.extend(f"CX q{physical[bit-1]} q{data[k]}" if bit else f"X q{data[k]}"
                           for k in S.bit_positions(directions))

    # At the original basis layout, the terminal affine map can be applied.
    move(start_pair)
    inverse_physical = {x:q for q,x in physical.items()}
    for q in sorted(physical):
        x = physical[q]
        if x != q:
            other = inverse_physical[q]
            out.append(f"SWAP q{x} q{q}")
            physical[q],physical[other] = q,x
            inverse_physical[q],inverse_physical[x] = q,other
    out.extend(linear)
    out.extend(retain_bank_lines(stop, len(lines)-5, missing))
    for q, tmp, (a, b) in zip(tags, backup, tag_controls):
        out.extend((f"HMR q{q} b0", f"CZ q{a} q{b} if b0", f"SWAP q{q} q{tmp}"))
    out.extend(encoding)
    result = km.Circuit("\n".join(out)+"\n")
    assert result.num_qubits == 128
    return result, {"removable_pairs":len(pairs), "products":len(terms),
                    "groups":len(path), "rematerialized":cost, "missing_start":start_pair}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "output", "repo", "scheduler", "leaf-census"):
        p.add_argument(f"--{name}", type=Path, required=True)
    p.add_argument("--batches", nargs="+", type=int, default=list(range(1,15)))
    p.add_argument("--beam", type=int, default=8)
    a = p.parse_args()
    sys.path[:0] = [str(a.repo), str(a.scheduler)]
    import schedule_angle as S
    from chemistry_affine_span_resynthesis import parse_line
    from chemistry_joint_product_resynthesis import DATA, TAGS
    a.output.mkdir(parents=True, exist_ok=True)
    rows = json.loads(a.leaf_census.read_text())
    results = []
    for k in a.batches:
        source = a.source / f"angle_k_{k}.kmb"
        c = km.Circuit.from_file(source)
        recipes = {r["wire"]:r["sources"] for r in rows[k-1]["eligible"]}
        try:
            compiled, report = emit_cache(c, S, parse_line, DATA, sorted(TAGS), recipes, a.beam)
            dest = a.output / source.name
            compiled.to_file(dest, format="kmb")
            report.update(sha256=sha256(dest.read_bytes()).hexdigest(),
                          ccx=compiled.operation_statistics().num_toffoli_like)
        except (ValueError, AssertionError, KeyError) as e:
            report = {"error":f"{type(e).__name__}: {e}"}
        results.append({"batch":k, **report})
        print(json.dumps(results[-1]), flush=True)
    if len(a.batches) == 14:
        for name in ("angle_k_0.kmb", "submission.npz"):
            shutil.copyfile(a.source / name, a.output / name)
    (a.output / "cache_receipt.json").write_text(json.dumps(results, indent=2)+"\n")


if __name__ == "__main__":
    main()
