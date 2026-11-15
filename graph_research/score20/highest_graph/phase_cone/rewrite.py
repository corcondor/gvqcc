"""Remove paid gates from a data cone while compensating its measurement phases."""

import argparse
from bisect import bisect_right
from collections import Counter
from hashlib import sha256
from itertools import combinations, islice
import json
from pathlib import Path
import re

import kickmix as km
import numpy as np

PIN = "684106f101730ca193627229920a0501bef9ea10ccfb34aa453fcf63edadb50a"
DOMAIN = 3_133_452
PAID = {"CCX", "CSWAP"}
DATA = PAID | {"X", "CX", "SWAP", "HMR"}
PHASE = {"Z", "CZ", "CCZ"}


def parse(line):
    return line.split()[0], tuple(map(int, re.findall(r"\bq(\d+)\b", line))), line.partition(" if ")[2]


def initial_state(inputs):
    return [int.from_bytes(np.packbits((inputs >> q) & 1, bitorder="little"), "little")
            for q in range(22)] + [0] * 24


def apply(op, wires, state, one):
    if op == "X":
        state[wires[0]] ^= one
    elif op == "CX":
        a, b = wires
        state[b] ^= state[a]
    elif op == "CCX":
        a, b, c = wires
        state[c] ^= state[a] & state[b]
    elif op == "SWAP":
        a, b = wires
        state[a], state[b] = state[b], state[a]
    elif op == "CSWAP":
        c, a, b = wires
        change = state[c] & (state[a] ^ state[b])
        state[a] ^= change
        state[b] ^= change
    elif op == "HMR":
        state[wires[0]] = 0


def product(values, wires, one):
    for wire in wires:
        one &= values[wire]
    return one


def make_trace(gates, inputs):
    state = initial_state(inputs)
    one = (1 << len(inputs)) - 1
    pending = []
    for op, wires, guard in gates:
        if op == "PUSH_CONDITION":
            pending.append(state.copy())
        elif op == "POP_CONDITION":
            assert state == pending.pop()
        elif op in DATA:
            assert not guard
            apply(op, wires, state, one)
        yield tuple(state)
    assert not pending


def phase_columns(cuts, one):
    yield cuts[0][0], "NEG", one
    seen = {one, 0}
    for site, state in cuts:
        live = [(q, value) for q, value in enumerate(state) if value]
        for q, value in live:
            if value not in seen:
                seen.add(value)
                yield site, f"Z q{q}", value
        for (a, left), (b, right) in combinations(live, 2):
            value = left & right
            if value not in seen:
                seen.add(value)
                yield site, f"CZ q{a} q{b}", value


def quadratic_phase(value, cuts, one):
    basis = {}
    remaining, used = value, 0
    terms = []
    for i, (site, term, predicate) in enumerate(phase_columns(cuts, one)):
        terms.append((site, term))
        mask = 1 << i
        while predicate:
            pivot = predicate.bit_length()
            if pivot not in basis:
                basis[pivot] = predicate, mask
                break
            old, indices = basis[pivot]
            predicate ^= old
            mask ^= indices
        while remaining.bit_length() in basis:
            old, indices = basis[remaining.bit_length()]
            remaining ^= old
            used ^= indices
        if not remaining:
            return tuple(item for j, item in enumerate(terms) if (used >> j) & 1)
    return None


def phase_term(value, state, one):
    if value == one:
        return "NEG"
    if value in state:
        return f"Z q{state.index(value)}"
    # A viable product cannot contain a set bit outside either factor.
    eligible = [(q, mask) for q, mask in enumerate(state) if (mask & value) == value]
    for i, (a, left) in enumerate(eligible):
        for b, right in eligible[i + 1:]:
            if left & right == value:
                return f"CZ q{a} q{b}"
    for a, left in enumerate(state):
        right = value ^ left
        if right in state[a + 1:]:
            b = state.index(right, a + 1)
            return (f"Z q{a}", f"Z q{b}")
    return None


def audit_phase(terms, states, one):
    phase = 0
    for index, term in terms:
        _, wires, _ = parse(term)
        phase ^= product(states[index], wires, one)
    return phase


def tracks_for(gates, lines):
    parent, scopes, closes, writes = [], [], {}, {}
    conditions = {}
    for i, (op, _, _) in enumerate(gates):
        if op == "PUSH_CONDITION":
            parent.append(i)
            bit = gates[i][2]
            conditions[i] = (bit, len(writes.get(bit, ())))
        if op == "POP_CONDITION":
            closes[parent.pop()] = i
        scopes.append(tuple(parent))
        if op in {"HMR", "BIT_STORE0", "BIT_INVERT"}:
            target = lines[i].split()[2 if op == "HMR" else 1]
            writes.setdefault(target, []).append(i)
    return scopes, closes, writes, conditions


def phase_groups(events, track):
    scopes, _, writes, conditions = track
    by_version = {}
    for site, predicate, guard in events:
        active = {conditions[scope] for scope in scopes[site]}
        if guard:
            active.add((guard, bisect_right(writes.get(guard, ()), site)))
        key = frozenset(active)
        first, accumulated, first_guard = by_version.get(key, (site, 0, guard))
        by_version[key] = first, predicate ^ accumulated, first_guard
    return sorted((site, value, guard) for site, value, guard in by_version.values() if value)


def temporal_cuts(site, guard, track, state_at, window):
    scopes, closes, writes, _ = track
    scope = scopes[site]
    stop = min(site + window, len(scopes) - 1)
    if scope:
        stop = min(stop, closes[scope[-1]] - 1)
    if guard in writes:
        versions = writes[guard]
        next_version = bisect_right(versions, site)
        if next_version < len(versions):
            stop = min(stop, versions[next_version] - 1)
    cuts = [(site, state_at(site))]
    for delta in (2, 5, 10, 19, 33, 64, 107, 181, 288):
        cut = min(site + delta, stop)
        if cut == cuts[-1][0]:
            break
        if scopes[cut] == scope:
            cuts.append((cut, state_at(cut)))
    return cuts


def search(cone, skipped, stop, lines, gates, inputs, counter, proposals=None, failures=None,
           timing=None, merge=None):
    start = skipped[0]
    one = (1 << len(inputs)) - 1
    trace = iter(cone)
    before = next(trace)
    alt = list(before)
    scopes = []
    events = []
    alt_states = {}
    certification_sites = {cut for terms in (proposals or {}).values() for cut, _ in terms}
    for index, after in zip(range(start, stop), trace):
        op, wires, guard = gates[index]
        diff = 0
        if index in skipped:
            assert op in PAID
        elif op in DATA:
            if op == "HMR":
                diff = before[wires[0]] ^ alt[wires[0]]
                guard = lines[index].split()[2]
            apply(op, wires, alt, one)
        elif op in PHASE:
            diff = product(before, wires, one) ^ product(alt, wires, one)
        elif op == "Z_POW":
            if before[wires[0]] != alt[wires[0]]:
                counter["rotation"] += 1
                return None
        elif op == "PUSH_CONDITION":
            scopes.append((tuple(alt), before))
        elif op == "POP_CONDITION":
            entry = scopes.pop()[0] if scopes else after
            if tuple(alt) != entry:
                counter["data_at_join"] += 1
                return None
        if diff:
            events.append((index, diff, guard))
        if timing is not None or index in certification_sites or diff:
            alt_states[index] = tuple(alt)
        if index >= skipped[-1] and tuple(alt) == after and all(new == original for new, original in scopes):
            counter["data_converged"] += 1
            corrections = []
            tested = proposals or {}
            if merge is not None:
                grouped = phase_groups(events, merge)
                counter["merged_phase_events"] += len(events) - len(grouped)
                events = grouped
            if proposals is not None and certification_sites:
                last = max(certification_sites)
                for future, values in zip(range(index + 1, last + 1), trace):
                    if future in certification_sites:
                        alt_states[future] = values
            for site, predicate, guard in events:
                state = alt_states[site]
                if proposals is not None:
                    terms = tested.get(site, ())
                    if audit_phase(terms, alt_states, one) != predicate:
                        terms = None
                else:
                    form = phase_term(predicate, state, one)
                    if form is not None:
                        terms = tuple((site, term) for term in ((form,) if isinstance(form, str) else form))
                    else:
                        cuts = [(site, state)]
                        if timing is not None:
                            track, global_states, window = timing
                            cuts = temporal_cuts(site, guard, track,
                                                 lambda j: alt_states.get(j, global_states[j]), window)
                        terms = quadratic_phase(predicate, cuts, one)
                if terms is None:
                    counter["phase_not_represented"] += 1
                    if failures is not None:
                        failures.setdefault(site, []).append(start)
                    return None
                suffix = f" if {guard}" if guard else ""
                corrections.extend((site, cut, term if proposals is not None else term + suffix)
                                   for cut, term in terms)
            if proposals is not None and not set(tested).issubset(site for site, *_ in events):
                return None
            return {"start": start, "end": index, "removed": skipped,
                    "removed_gates": [lines[j] for j in skipped], "corrections": corrections}
        before = after
    counter["replay_limit"] += 1
    return None


def full_trace(gates, xs, start, stop):
    yield from trace_slice(make_trace(gates, xs), start, stop)


def trace_slice(trace, start, stop):
    yield from islice(trace, start - 1, stop)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--span", type=int, default=1_200)
    parser.add_argument("--phase-span", type=int, default=0)
    parser.add_argument("--merge-phases", action="store_true")
    args = parser.parse_args()
    assert sha256(args.source.read_bytes()).hexdigest() == PIN
    lines = str(km.Circuit.from_file(args.source)).splitlines()
    gates = [parse(line) for line in lines]
    rng = np.random.default_rng(19205)
    xs = np.unique(np.r_[np.arange(1, 257), rng.integers(1, DOMAIN + 1, 1_792)]).astype(np.uint32)
    sample = list(make_trace(gates, xs))
    track = tracks_for(gates, lines)
    timing = (track, sample, args.phase_span) if args.phase_span else None
    merge = track if args.merge_phases else None
    counts = Counter()
    failures = {}
    sample_hits = []
    for start, (op, _, _) in enumerate(gates):
        if op in PAID:
            stop = min(start + args.span, len(gates))
            hit = search(sample[start - 1:stop], (start,), stop, lines, gates, xs, counts,
                         failures=failures, timing=timing, merge=merge)
            if hit:
                sample_hits.append(hit)
    pair_counts = Counter()
    for sites in failures.values():
        for begin, end in combinations(sites, 2):
            stop = min(end + args.span, len(gates))
            pair_counts["checked"] += 1
            hit = search(sample[begin - 1:stop], (begin, end), stop, lines, gates, xs, pair_counts,
                         timing=timing, merge=merge)
            if hit:
                sample_hits.append(hit)
    print(json.dumps({"sample_hits": sample_hits, "single": counts, "paired": pair_counts}), flush=True)

    validated = []
    full_xs = np.arange(1, DOMAIN + 1, dtype=np.uint32)
    for row in sample_hits:
        start = row["start"]
        stop = max([row["end"], *(cut for _, cut, _ in row["corrections"])]) + 1
        corrections = {}
        for site, cut, term in row["corrections"]:
            corrections.setdefault(site, []).append((cut, term))
        hit = search(full_trace(gates, full_xs, start, stop), tuple(row["removed"]), stop, lines, gates,
                     full_xs, counts, proposals=corrections, merge=merge)
        if hit:
            hit["end"] = stop - 1
            validated.append(hit)
    selected = []
    for row in sorted(validated, key=lambda item: item["end"]):
        if not selected or row["start"] > selected[-1]["end"]:
            selected.append(row)
    if selected:
        skip = {j for row in selected for j in row["removed"]}
        after = {}
        for row in selected:
            for _, index, correction in row["corrections"]:
                after.setdefault(index, []).append(correction)
        result = []
        for index, line in enumerate(lines):
            if index not in skip:
                result.append(line)
            result.extend(after.get(index, ()))
        km.Circuit("\n".join(result) + "\n").to_file(args.output / "candidate.kmb", format="kmb")
    report = {"source_sha256": PIN, "samples": len(xs), "validation_domain": DOMAIN,
              "max_compensation_span": args.phase_span, "merge_phases": args.merge_phases,
              "sample_hits": sample_hits, "validated": validated, "selected": selected,
              "single": counts, "paired": pair_counts,
              "phase_buckets": {site: len(sites) for site, sites in failures.items()}}
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
