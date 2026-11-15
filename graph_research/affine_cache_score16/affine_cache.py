"""Compile ANGLE with both workspace features and logical tag products in the cache graph."""
from __future__ import annotations

import argparse
from collections import Counter
from functools import lru_cache
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
import subprocess
import shutil
import sys

import kickmix as km


def union(values, start=0):
    for value in values:
        start |= value
    return start


def lane_mask(wires):
    return sum(1 << (wire + 1) for wire in wires)


def choose_plan(supports, valid_pairs, initial, terminal, regenerations, beam_width,
                weight, incumbent):
    all_terms = (1 << len(supports)) - 1
    cover = [
        sum(1 << i for i, support in enumerate(supports) if not support & lane_mask(pair))
        for pair in valid_pairs
    ]
    if all_terms & ~union(cover):
        raise ValueError("an output term does not fit any omission pair")
    words = (len(supports) + 63) // 64
    low = (1 << 64) - 1
    lines = [f"{len(valid_pairs)} {len(supports)} {beam_width} {weight} {incumbent}"]
    initial_set, terminal_set = set(initial), set(terminal)
    for pair, value in zip(valid_pairs, cover, strict=True):
        row = f"{pair[0]} {pair[1]} {int(pair in initial_set)} {int(pair in terminal_set)}"
        lines.append(row + " " + " ".join(str((value >> (64 * w)) & low) for w in range(words)))
    lines.append(str(len(regenerations)))
    for q, recipes in regenerations.items():
        masks = [(a | b) >> 1 for a, b in recipes]
        lines.append(f"{q} {len(masks)} " + " ".join(f"{m & low} {m >> 64}" for m in masks))
    solver = Path(__file__).with_name("search_routes")
    result = subprocess.run([solver], input="\n".join(lines) + "\n",
                            capture_output=True, text=True, check=True).stdout
    if result.startswith("no improvement"):
        return None
    head, body = result.splitlines()
    cost, start, end = map(int, head.split())
    remaining = all_terms
    path = []
    for q in map(int, body.split()):
        selected = cover[q] & remaining
        remaining ^= selected
        path.append((valid_pairs[q], selected))
    assert not remaining and cost < incumbent
    return cost, path, valid_pairs[start], valid_pairs[end]


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


def prefix_recipes(prefix, n):
    unit = [1 << (q + 1) for q in range(n)]
    frame = unit[:]
    products = {}
    for op, wires, _ in prefix:
        if op == "X":
            frame[wires[0]] ^= 1
        elif op == "CX":
            a, b = wires
            frame[b] ^= frame[a]
        elif op == "CCX":
            a, b, out = wires
            assert out >= 51 and out not in products
            products[out] = frame[a], frame[b]
        else:
            assert op == "R"
    assert frame[:11] == unit[:11]
    return products


@lru_cache(maxsize=8)
def cache_transitions(values, pool, tags, prefix_recipes):
    regeneration = {}
    candidates = list(combinations(pool, 2))
    targets = {values[q]: q for q in (*tags, *range(51, len(values)))}
    assert len(targets) == 74 + len(tags)

    for a, b in candidates:
        q = targets.get(values[a] & values[b])
        if q is not None and q not in (a,b):
            regeneration.setdefault(q, []).append((1 << (a + 1), 1 << (b + 1)))

    def value(mask):
        result = 0 if not mask & 1 else (1 << 1220) - 1
        for q in pool:
            if mask & (1 << (q + 1)):
                result ^= values[q]
        return result

    pool_mask = lane_mask(pool) | 1
    for q, a, b in prefix_recipes:
        assert not ((a | b) & ~pool_mask)
        assert value(a) & value(b) == values[q], (q,a,b)
        assert not ((a | b) & (1 << (q + 1)))
        candidate = (a,b)
        choices = regeneration.setdefault(q, [])
        if candidate not in choices:
            choices.append(candidate)

    pairs = list(combinations(sorted(regeneration), 2))
    return pairs, regeneration


def emit_cache(circuit, S, parse_line, data, tags, beam, weight, incumbent):
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
    prefix = ops[enc_start+5:start]
    values = exact_work_functions(prefix, n, tags, tag_controls)
    generated = tuple((q, a, b) for q, (a, b) in prefix_recipes(prefix, n).items())
    pairs, regenerations = cache_transitions(tuple(values), pool, tuple(tags), generated)
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

    def valid_at(pair, first, last):
        try:
            list(retain_bank_lines(first, last, set(pair)))
            return True
        except AssertionError:
            return False

    initial = [p for p in pairs if valid_at(p, enc_start + 5, start)]
    terminal = [p for p in pairs if valid_at(p, stop, len(lines) - 5)]
    if not initial or not terminal:
        raise ValueError("no valid boundary omissions")
    fixed_paid = circuit.operation_statistics().num_toffoli_like + 3
    result = choose_plan(supports, pairs, initial, terminal, regenerations,
                         beam, weight, incumbent - fixed_paid)
    if result is None:
        return None
    cost, path, start_pair, end_pair = result
    missing = set(start_pair)
    free_backup = iter([q for q in start_pair if q not in tags] + [125, 126, 127])
    backup = [q if q in missing else next(free_backup) for q in tags]

    out = lines[:enc_start+5]
    for q, tmp, (a, b) in zip(tags, backup, tag_controls):
        if q not in missing:
            out.extend((f"SWAP q{q} q{tmp}", f"CCX q{a} q{b} q{q}"))
    out.extend(retain_bank_lines(enc_start+5, start, missing))
    physical = {q:q for q in pool if q not in missing}

    import re
    token = re.compile(r"q(\d+)")

    def remap(line):
        return token.sub(lambda m: "q" + str(physical.get(int(m[1]), int(m[1]))), line)

    def prepare(q, forbid):
        mask = lane_mask(forbid)
        a,b = next((a,b) for a,b in regenerations[q] if not (a|b) & mask)
        support = [i-1 for i in S.bit_positions((a|b) & ~1)]
        pivots = next((p,r) for p,r in combinations(support, 2)
                      if 0 not in S.selector_pair(a,b,p,r)
                      and len(set(S.selector_pair(a,b,p,r))) == 2)
        init = tuple(1 << (q + 1) for q in pivots)
        now = (a,b)
        prepare = list(map(remap, S.emit_transition(S.parity_transition(init, now, pivots), pivots)))
        undo = list(map(remap, S.emit_transition(S.parity_transition(now, init, pivots), pivots)))
        return tuple(physical[q] for q in pivots), prepare, undo

    def move(pair):
        nonlocal missing
        target = set(pair)
        free = []
        for q in sorted(target - missing):
            (a,b), forward, back = prepare(q, missing|target)
            x = physical.pop(q)
            free.append(x)
            out.extend([*forward, f"HMR q{x} b0", f"CZ q{a} q{b} if b0", *back])
        for q, x in zip(sorted(missing - target), free, strict=True):
            (a,b), forward, back = prepare(q, missing|target)
            out.extend([*forward, f"CCX q{a} q{b} q{x}", *back])
            physical[q] = x
        missing = target

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

    move(end_pair)
    out.extend(linear)
    out.extend(map(remap, retain_bank_lines(stop, len(lines)-5, missing)))
    # Logical tag values may occupy any live cache lane. Release them all
    # before returning the saved arbitrary input tags to their formal ABI lanes.
    for q, (a, b) in zip(tags, tag_controls):
        if q not in missing:
            out.extend((f"HMR q{physical[q]} b0",
                        f"CZ q{physical[a]} q{physical[b]} if b0"))
    for q, tmp in zip(tags, backup):
        if q != tmp:
            out.append(f"SWAP q{q} q{tmp}")
    out.extend(encoding)
    result = km.Circuit("\n".join(out)+"\n")
    assert result.num_qubits == 128
    assert result.operation_statistics().num_toffoli_like == fixed_paid + cost
    return result, {"removable_pairs":len(pairs), "products":len(terms),
                    "groups":len(path), "rematerialized":cost, "missing_start":start_pair,
                    "missing_end":end_pair, "valid_start_pairs":len(initial),
                    "valid_end_pairs":len(terminal)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "output", "repo", "scheduler", "incumbent"):
        p.add_argument(f"--{name}", type=Path, required=True)
    p.add_argument("--batches", nargs="+", type=int, default=list(range(1,15)))
    p.add_argument("--beam", type=int, default=120)
    p.add_argument("--weight", type=int, default=24)
    a = p.parse_args()
    sys.path[:0] = [str(a.repo), str(a.scheduler)]
    import schedule_angle as S
    from chemistry_affine_span_resynthesis import parse_line
    from chemistry_joint_product_resynthesis import DATA, TAGS
    a.output.mkdir(parents=True, exist_ok=True)
    rows = json.loads(a.incumbent.read_text())
    baseline = {r["batch"]:r["ccx"] for r in rows}
    results = []
    for k in a.batches:
        source = a.source / f"angle_k_{k}.kmb"
        c = km.Circuit.from_file(source)
        try:
            result = emit_cache(c, S, parse_line, DATA, sorted(TAGS), a.beam,
                                a.weight, baseline[k])
            if result is None:
                report = {"no_improvement": True}
                results.append({"batch":k, **report})
                print(json.dumps(results[-1]), flush=True)
                continue
            compiled, report = result
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
