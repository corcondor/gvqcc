"""Extract graphs from a hash-pinned, verified ANGLE KMB and its exact rerun."""
from argparse import ArgumentParser
from functools import reduce
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory

import kickmix as km


WIRE = re.compile(r"\bq(\d+)\b")
N_ADDRESSES = 1220
KICKMIX_SCHEMA = 1


def checksum(path):
    return sha256(path.read_bytes()).hexdigest()


def load_circuit(path):
    return km.Circuit.from_file(path)


def parse(line):
    parts = line.split()
    return parts[0], [int(hit[1]) for hit in WIRE.finditer(line)]


def data_phase_prefix(lines, n):
    """Symbolic computational basis values: address bitset plus word mask."""
    all_addresses = (1 << N_ADDRESSES) - 1
    values = [
        (sum(1 << a for a in range(N_ADDRESSES) if (a >> q) & 1), 0)
        for q in range(11)
    ] + [(0, 1 << z) for z in range(40)] + [(0, 0)] * (n - 51)
    pending = None
    for line in lines:
        gate, q = parse(line)
        assert pending is None or gate == "CZ"
        assert " if " not in line or gate == "CZ"
        if gate == "R":
            assert values[q[0]] == (0, 0)
        elif gate == "X":
            values[q[0]] = values[q[0]][0] ^ all_addresses, values[q[0]][1]
        elif gate == "CX":
            a, t = q
            values[t] = tuple(x ^ y for x, y in zip(values[t], values[a]))
        elif gate in {"CCX", "CZ"}:
            a, b, *target = q
            assert values[a][1] == values[b][1] == 0
            and_mask = values[a][0] & values[b][0]
            if gate == "CCX":
                t, = target
                values[t] = values[t][0] ^ and_mask, values[t][1]
            else:
                assert line.endswith(" if b0") and pending == and_mask
                pending = None
        elif gate == "HMR":
            assert line.endswith(" b0") and values[q[0]][1] == 0
            pending = values[q[0]][0]
            values[q[0]] = (0, 0)
        elif gate == "SWAP":
            a, b = q
            values[a], values[b] = values[b], values[a]
        else:
            assert gate in {"REGISTER", "APPEND_TO_REGISTER"}
    assert pending is None
    return values


def locate(lines, expected, start):
    if not expected:
        return None
    end = len(lines) - len(expected) + 1
    return next(i for i in range(start, end) if lines[i:i + len(expected)] == expected)


def extract_routes(reference, verified, leaves_path, selected_path, batch):
    import open_cache as feature_cache
    import schedule_angle as s
    from chemistry_affine_span_resynthesis import parse_line
    from chemistry_joint_product_resynthesis import DATA, TAGS

    selected = next(x for x in json.loads(selected_path.read_text()) if x["batch"] == batch)
    assert checksum(verified) == selected["sha256"]
    leaves = json.loads(leaves_path.read_text())[batch - 1]["eligible"]
    recipes = {x["wire"]: x["sources"] for x in leaves}
    groups = selected["groups"]
    planner = feature_cache.choose_plan
    capture = {}

    def traced_plan(supports, pairs, initial, terminal, neighbors, beam_width):
        chosen = planner(supports, pairs, initial, terminal, neighbors, beam_width)
        capture.update(supports=supports, start=chosen[2], end=chosen[3],
                       cost=chosen[0], path=chosen[1])
        return chosen

    feature_cache.choose_plan = traced_plan
    assert selected["variant"] == 2
    beam = 24
    try:
        regenerated, _ = feature_cache.emit_cache(
            load_circuit(reference), s, parse_line, DATA, sorted(TAGS), recipes, beam
        )
        with TemporaryDirectory() as folder:
            rebuilt = Path(folder) / verified.name
            regenerated.to_file(rebuilt, format="kmb")
            assert checksum(rebuilt) == checksum(verified)
    finally:
        feature_cache.choose_plan = planner

    source = str(load_circuit(reference)).splitlines()
    ops = [parse_line(line) for line in source]
    first = 1 + max(i for i, (g, q, _) in enumerate(ops) if g == "CCX" and q[-1] >= 51)
    encode = source.index(f"CX q{min(TAGS)-1} q{min(TAGS)}")
    values = feature_cache.exact_work_functions(
        ops[encode+5:first], 125, sorted(TAGS), [(0,1),(0,2),(1,2),(0,3),(1,3)]
    )
    pool = tuple(sorted(set(range(125)) - set(DATA)))
    pairs, neighbors, recipe = feature_cache.cache_transitions(tuple(values), pool)
    assert len(pairs) == selected["removable_pairs"]
    assert len(capture['path']) == groups
    assert capture["cost"] == selected["rematerialized"]
    assert list(capture["start"]) == selected["missing_start"]
    assert list(capture["end"]) == selected["missing_end"]
    path = capture["path"] + [(capture["end"], 0)]
    missing = capture["start"]
    physical = {q: q for q in pool if q not in missing}
    lines = str(load_circuit(verified)).splitlines()
    start = 0
    examined = []
    for group, (next_missing, mask) in enumerate(path, 1):
        assert next_missing in neighbors[missing]
        stop = set(next_missing)
        previous = set(missing)
        used = list(s.bit_positions(mask))
        assert all(not (capture["supports"][i] & feature_cache.lane_mask(stop)) for i in used)
        provisional = []
        free = []
        for f in sorted(stop - previous):
            a, b = recipe(f, stop | previous)
            wire = physical.pop(f)
            free.append(wire)
            provisional.append({"feature": f, "wire": wire, "controls": [physical[a], physical[b]],
                                "logical_controls": [a,b]})
        restored = []
        for f, wire in zip(sorted(previous - stop), free, strict=True):
            a, b = recipe(f, stop | previous)
            restored.append({"feature": f, "wire": wire, "controls": [physical[a], physical[b]],
                             "logical_controls": [a,b]})
            physical[f] = wire
        text = [op for p in provisional for op in (
            f"HMR q{p['wire']} b0", f"CZ q{p['controls'][0]} q{p['controls'][1]} if b0"
        )] + [f"CCX q{p['controls'][0]} q{p['controls'][1]} q{p['wire']}" for p in restored]
        i = locate(lines, text, start)
        if i is not None:
            start = i + len(text)
        examined.append({
            "group": group, "terminal_cleanup": group > groups,
            "missing_from": list(missing), "missing_to": list(next_missing),
            "product_ids_zero_based": [i for i in used if i < selected["products"]],
            "affine_ids_zero_based": [i for i in used if i >= selected["products"]],
            "rematerialized": len(restored),
            "evicted": provisional, "restored": restored,
            "kmx_rows": list(range(i + 1, i + len(text) + 1)) if i is not None else [],
            "instructions": text,
        })
        missing = next_missing
    assert sum(row["rematerialized"] for row in examined) == selected["rematerialized"]
    assert sum(len(row["product_ids_zero_based"]) for row in examined) == selected["products"]
    return {
        "schema_version": KICKMIX_SCHEMA,
        "member": verified.name, "sha256": checksum(verified),
        "reference_sha256": checksum(reference),
        "recompiled_sha256_matches": True, "selected": selected, "beam_width": beam,
        "directed_edges_excluding_self_loops": sum(map(len, neighbors.values())) - len(neighbors),
        "product_and_affine_terms": len(capture["supports"]),
        "moves": examined,
    }


def extract_slice(path, route, group):
    c = load_circuit(path)
    lines = str(c).splitlines()
    move = route["moves"][group - 1]
    start = move["kmx_rows"][0]
    assert len(move["kmx_rows"]) == 3
    work, = parse(lines[start-1])[1]
    assert move["evicted"][0]["wire"] == move["restored"][0]["wire"] == work
    first_control, second_control = move["evicted"][0]["controls"]
    new_left, new_right = move["restored"][0]["controls"]
    stop = next(i for i in range(start+3,len(lines)+1) if lines[i-1].startswith("CCX "))
    window = lines[start-1:stop]
    assert window[:3] == move["instructions"]
    _, (left, right, target) = parse(window[-1])
    assert right == work
    before = data_phase_prefix(lines[:start-1], c.num_qubits)
    after = data_phase_prefix(lines[:stop], c.num_qubits)
    assert before[work][1] == before[first_control][1] == before[second_control][1] == 0
    assert before[work][0] == (before[first_control][0] & before[second_control][0])
    new = before[new_left][0] & before[new_right][0]
    assert before[new_left][1] == before[new_right][1] == 0

    parity_rows = {left: [], right: []}
    output_rows = []
    for i, instruction in enumerate(window[3:-1], start + 3):
        gate, (a,t) = parse(instruction)
        assert gate == "CX"
        assert a not in (left,right) or (i == start + 3 and a == work and t == left)
        if t in parity_rows:
            parity_rows[t].append((i,a))
        else:
            assert a == target
            output_rows.append((i,t))
    left_value = before[left][0]
    for i, q in parity_rows[left]:
        assert before[q][1] == 0
        left_value ^= new if i == start + 3 else before[q][0]
    assert all(before[q][1] == 0 for _, q in parity_rows[right])
    right_value = new ^ reduce(int.__xor__, (before[q][0] for _, q in parity_rows[right]), 0)
    for a,b,m in product(range(2), repeat=3):
        # Projection onto the HMR outcome m contributes (-1)^(m*a*b).
        correction = m & a & b
        assert ((m & (a & b)) ^ correction) == 0
    assert after[left] == (left_value, 0) and after[right] == (right_value, 0)
    assert after[target] == (before[target][0] ^ (left_value & right_value), before[target][1])
    # The fan-out CXs in this excerpt precede the output update.
    fanout_targets = [q for _,q in output_rows]
    assert len(fanout_targets) == len(set(fanout_targets))
    changed = {left,right,target,*fanout_targets}
    for q in range(c.num_qubits):
        if q in fanout_targets:
            assert after[q] == tuple(x ^ y for x,y in zip(before[q],before[target]))
        elif q not in changed:
            assert before[q] == after[q]
    return {
        "file": path.name, "sha256": checksum(path),
        "kmx_text_rows_inclusive_1_based": [start,stop],
        "slice_sha256": sha256(("\n".join(window)+"\n").encode()).hexdigest(),
        "cache_move": move, "lines": window,
        "control_and_output_wires": [left,right,target],
        "cx_sources_by_control_wire": {q: [a for _,a in rows] for q,rows in parity_rows.items()},
        "fanout_targets_updated_before_ccx": fanout_targets,
        "symbolically_checked_addresses": N_ADDRESSES,
        "word_bits_symbolic": 40, "local_phase_cases": 8,
    }


def main():
    p = ArgumentParser(description=__doc__)
    for name in ("repo", "scheduler", "compiler", "leaves", "selected", "reference", "verified", "out"):
        p.add_argument("--" + name, required=True, type=Path)
    p.add_argument("--batch", type=int, default=13)
    p.add_argument("--slice-start", type=int, default=6922,
                   help="1-based decoded KMX row at a single-slot cache exchange")
    args = p.parse_args()
    sys.path[:0] = [str(args.repo),str(args.scheduler),str(args.compiler)]
    args.out.mkdir(parents=True, exist_ok=True)
    route = extract_routes(args.reference, args.verified, args.leaves, args.selected, args.batch)
    group = next(m["group"] for m in route["moves"]
                 if m["kmx_rows"] and m["kmx_rows"][0] == args.slice_start)
    example = extract_slice(args.verified, route, group)
    (args.out/"angle_route.json").write_text(json.dumps(route,indent=2)+"\n")
    (args.out/"angle_slice.json").write_text(json.dumps(example,indent=2)+"\n")
    print(f"Verified replay, {len(route['moves'])} moves including terminal, representative rows {example['kmx_text_rows_inclusive_1_based']}")


if __name__ == "__main__":
    main()
