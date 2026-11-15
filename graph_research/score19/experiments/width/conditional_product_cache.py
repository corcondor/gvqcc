"""Reuse products across conditional and unconditional CCX gates."""

from argparse import ArgumentParser
from bisect import bisect_left
from collections import Counter, defaultdict
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
import re

from state_supported_rewrite import dag, REGISTERS


def scan(gates):
    references = [[] for _ in range(dag.QUBITS)]
    guards, scope_start = [], []
    versions = Counter()
    stack = []
    for index, gate in enumerate(gates):
        for q in gate.wires:
            references[q].append(index)
        guards.append(tuple((bit, version) for bit, version, _ in stack))
        scope_start.append(stack[0][2] if stack else index)
        if gate.op == "PUSH_CONDITION":
            (b,) = gate.bits
            stack.append((b, versions[b], index))
        elif gate.op == "POP_CONDITION":
            stack.pop()
        elif gate.op in {"HMR", "BIT_STORE0", "BIT_INVERT"}:
            versions[gate.bits[0]] += 1
    assert not stack
    available = {}
    products = defaultdict(list)

    def probe(index, state, _mask):
        gate = gates[index]
        if gate.op != "CCX" or gate.bits:
            return
        a, b, _ = gate.wires
        p = state[a] & state[b]
        if p:
            digest = sha256(p.to_bytes((dag.DOMAIN + 7) // 8, "little")).digest()
            products[digest].append(index)
            available[index] = [q for q, x in enumerate(state) if not x]

    dag.packed_lifetimes(gates, probe)
    metrics = Counter()
    plans = []
    for rows in products.values():
        for i, j in combinations(rows, 2):
            if not guards[i]:
                continue
            if guards[j] and guards[i] != guards[j]:
                continue
            same_guard = bool(guards[j])
            kind = "same_guard" if same_guard else "conditional_then_unconditional"
            metrics[kind] += 1
            for q in available[i]:
                at = bisect_left(references[q], i)
                if at < len(references[q]) and references[q][at] <= j:
                    continue
                plans.append(dict(first=i, second=j, cache=q, scope_start=scope_start[i],
                                  kind=kind, guards=guards[i]))
    return plans, metrics


def build(lines, gates, plan, fresh):
    first, last, cache = (plan[key] for key in ("first", "second", "cache"))
    flag, m = f"b{fresh}", f"b{fresh + 1}"
    a, b, t = gates[last].wires
    u = gates[first].wires[-1]
    start = [f"CX q{u} q{cache}", lines[first], f"CX q{u} q{cache}"]
    use = [f"CX q{cache} q{t}", f"HMR q{cache} {m}", f"CZ q{a} q{b} if {m}"]
    if plan["kind"] == "same_guard":
        final = use
    else:
        start.append(f"BIT_INVERT {flag}")
        final = [f"PUSH_CONDITION if {flag}", *use, "POP_CONDITION", f"BIT_INVERT {flag}",
                 f"CCX q{a} q{b} q{t} if {flag}"]
    for index, line in enumerate(lines):
        if plan["kind"] != "same_guard" and index == plan["scope_start"]:
            yield f"BIT_STORE0 {flag}"
        if index == first:
            yield from start
        elif index == last:
            yield from final
        else:
            yield line


def check_exact(gates, plan):
    i, j, cache = (plan[key] for key in ("first", "second", "cache"))
    values = []

    def prove(index, state, _mask):
        if index in (i, j):
            a, b, _ = gates[index].wires
            values.append(state[a] & state[b])
        if i <= index <= j and state[cache]:
            raise ValueError("The selected cache is not clean on every legal input")

    dag.packed_lifetimes(gates, prove)
    return len(values) == 2 and values[0] == values[1]


def main():
    cli = ArgumentParser(description=__doc__)
    cli.add_argument("source", type=Path)
    cli.add_argument("report", type=Path)
    cli.add_argument("candidate", type=Path)
    opts = cli.parse_args()
    assert sha256(opts.source.read_bytes()).hexdigest() == dag.PIN
    raw = str(dag.km.Circuit.from_file(opts.source)).splitlines()
    lines = [line for line in raw if line.split()[0] not in REGISTERS]
    metadata = [line for line in raw if line.split()[0] in REGISTERS]
    gates = [dag.Gate.parse(line) for line in lines]
    plans, metrics = scan(gates)
    report = dict(source_sha256=dag.PIN, tested_full_domain=dag.DOMAIN,
                  same_product_pairs=dict(metrics), cache_plans=plans)
    if plans:
        plan = min(plans, key=lambda item: item["second"] - item["first"])
        assert check_exact(gates, plan)
        fresh = max(map(int, re.findall(r"\bb(\d+)\b", "\n".join(raw)))) + 1
        text = "\n".join([*metadata, *build(lines, gates, plan, fresh)]) + "\n"
        candidate = dag.km.Circuit(text)
        candidate.to_file(opts.candidate, format="kmb")
        report.update(chosen=plan, candidate_sha256=sha256(opts.candidate.read_bytes()).hexdigest(),
                      candidate_qubits=candidate.num_qubits)
    print(report, flush=True)
    opts.report.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
