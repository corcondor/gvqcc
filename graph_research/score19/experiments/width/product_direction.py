"""Route an exact repeated product through reversible dataflow without a cache."""

from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path

from state_supported_rewrite import dag, np, packed_trace, REGISTERS


def pushed_depth(gates):
    depth = 0
    for gate in gates:
        yield depth
        depth += int(gate.op == "PUSH_CONDITION") - int(gate.op == "POP_CONDITION")
    assert depth == 0


def on_wire(direction, wire):
    return (direction >> wire) & 1


def phase_delta(gate, state, product, direction):
    old = new = product
    for wire in gate.wires:
        old &= state[wire]
        new &= state[wire] ^ (product if on_wire(direction, wire) else 0)
    return old ^ new


def propagate(gate, state, product, direction):
    """Transport the pending direction through the basis-state gate or reject."""
    op, wires = gate.op, gate.wires
    if not any(on_wire(direction, wire) for wire in wires):
        return direction
    if op == "CX":
        control, target = wires
        return direction ^ (on_wire(direction, control) << target)
    if op == "SWAP":
        a, b = wires
        return direction ^ ((1 << a) | (1 << b)) if on_wire(direction, a) != on_wire(direction, b) else direction
    if op == "CCX":
        a, b, target = wires
        changes = phase_delta(gate.__class__(op, (a, b), ()), state, product, direction)
        if changes not in (0, product):
            return None
        return direction ^ ((1 << target) if changes else 0)
    if op == "CSWAP":
        c, a, b = wires
        difference = state[a] ^ state[b]
        dc = product if on_wire(direction, c) else 0
        delta_difference = product if on_wire(direction, a) ^ on_wire(direction, b) else 0
        # The two swapped values have the same XOR before and after CSWAP.
        changes = product & ((state[c] & difference)
                             ^ ((state[c] ^ dc) & (difference ^ delta_difference)))
        if changes not in (0, product):
            return None
        return direction ^ (((1 << a) | (1 << b)) if changes else 0)
    if op in {"HMR", "R", "Z_POW"}:
        return None
    return direction


def try_plan(gates, states, first, last, product):
    direction = 1 << gates[last].wires[-1]
    scopes = [{"exit": None, "phase": 0}]
    for index in range(last - 1, first, -1):
        gate = gates[index]
        state = states[index]
        if gate.op == "POP_CONDITION":
            scopes.append({"exit": direction, "phase": 0})
            continue
        if gate.op == "PUSH_CONDITION":
            scope = scopes.pop()
            if scope["phase"] or direction != scope["exit"]:
                return None
            continue
        if gate.op in {"Z", "CZ", "CCZ"}:
            delta = phase_delta(gate, state, product, direction)
            if gate.bits and delta:
                return None
            scopes[-1]["phase"] ^= delta
            continue
        direction = propagate(gate, state, product, direction)
        if direction is None:
            return None
    assert len(scopes) == 1
    if scopes[0]["phase"]:
        return None
    controls = sum(1 << q for q in gates[first].wires[:2])
    injected = direction ^ (1 << gates[first].wires[-1])
    return injected if not injected & controls else None


def operations(gate, update):
    wires = [q for q in range(dag.QUBITS) if on_wire(update, q)]
    if not wires:
        return []
    pivot, *other = wires
    fanout = [f"CX q{pivot} q{q}" for q in other]
    a, b, _ = gate.wires
    return fanout + [f"CCX q{a} q{b} q{pivot}"] + fanout[::-1]


def reduce(value, basis):
    coefficient = 0
    while value:
        leading = value.bit_length() - 1
        if leading not in basis:
            break
        row, label = basis[leading]
        value ^= row
        coefficient ^= label
    return value, coefficient


def basis_without(state, target, mask):
    basis = {}
    for wire, function in enumerate(state + [mask]):
        if wire == target:
            continue
        remaining, label = reduce(function, basis)
        if remaining:
            basis[remaining.bit_length() - 1] = (remaining, label ^ (1 << wire))
    return basis


def affine_gates(coefficient, target):
    output = [f"CX q{wire} q{target}" for wire in range(dag.QUBITS)
              if on_wire(coefficient, wire)]
    if on_wire(coefficient, dag.QUBITS):
        output.append(f"X q{target}")
    return output


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("report", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--max-span", type=int, default=512)
    parser.add_argument("--affine-remainder", action="store_true")
    opts = parser.parse_args()
    assert sha256(opts.source.read_bytes()).hexdigest() == dag.PIN
    raw = str(dag.km.Circuit.from_file(opts.source)).splitlines()
    lines = [line for line in raw if line.split()[0] not in REGISTERS]
    gates = [dag.Gate.parse(line) for line in lines]
    depth = list(pushed_depth(gates))
    states = []
    paid = []
    sample_mask = None

    def visit(index, state, mask):
        nonlocal sample_mask
        sample_mask = mask
        states.append(state[:])
        gate = gates[index]
        if gate.op == "CCX" and depth[index] == 0 and not gate.bits:
            a, b, _ = gate.wires
            product = state[a] & state[b]
            if product:
                paid.append((index, product))

    rng = np.random.default_rng(460889)
    xs = np.unique(np.concatenate([np.arange(1, 2049), rng.integers(1, dag.DOMAIN + 1, size=2048)]))
    packed_trace(gates, xs, visit)
    screened, plans = 0, []
    matching = 0
    for position, (last, final_product) in enumerate(paid):
        loan = basis_without(states[last], gates[last].wires[-1], sample_mask) if opts.affine_remainder else {}
        for first, product in reversed(paid[:position]):
            if last - first > opts.max_span:
                break
            screened += 1
            residual, remainder = reduce(product ^ final_product, loan)
            if residual:
                continue
            matching += 1
            update = try_plan(gates, states, first, last, product)
            if update is not None:
                plans.append((first, last, update, remainder))
    states.clear()
    print(f"Screened {screened} pairs, {matching} matching products, {len(plans)} sample hits", flush=True)

    exact = []
    if plans:
        observations = set()
        for first, last, _, _ in plans:
            observations.update(range(first, last + 1))
        full_states = {}

        def observe(index, state, mask):
            if index in observations:
                full_states[index] = state[:]

        dag.packed_lifetimes(gates, observe)
        mask = (1 << dag.DOMAIN) - 1
        for first, last, update, remainder in plans:
            a, b = gates[first].wires[:2]
            c, d = gates[last].wires[:2]
            p = full_states[first][a] & full_states[first][b]
            remainder_delta = p ^ (full_states[last][c] & full_states[last][d])
            for wire, truth in enumerate(full_states[last] + [mask]):
                if on_wire(remainder, wire):
                    remainder_delta ^= truth
            if p and not remainder_delta:
                exact_update = try_plan(gates, full_states, first, last, p)
                if exact_update is not None:
                    exact.append((first, last, exact_update, remainder))
    print(f"Exact full-domain hits: {len(exact)}", flush=True)
    # Separate windows are independent since their complete state and phase match.
    replacements = {}
    results = []
    end = -1
    for first, last, update, remainder in sorted(exact, key=lambda hit: hit[1]):
        if first <= end:
            continue
        end = last
        repl = operations(gates[first], update)
        replacements[first] = repl
        last_ops = affine_gates(remainder, gates[last].wires[-1])
        replacements[last] = last_ops
        results.append(dict(first=first, last=last, first_gate=lines[first], last_gate=lines[last],
                            replacement=repl, affine_remainder=last_ops,
                            saved_toffoli=2 - int(bool(update))))
    report = dict(baseline_sha256=dag.PIN, legal_inputs=dag.DOMAIN, pairs=screened,
                  matching_products=matching, sample_hits=len(plans),
                  exact_hits=len(exact), applied=results)
    if results:
        out = [line for line in raw if line.split()[0] in REGISTERS]
        for index, line in enumerate(lines):
            out.extend(replacements.get(index, [line]))
        candidate = dag.km.Circuit("\n".join(out) + "\n")
        candidate.to_file(opts.candidate, format="kmb")
        report["candidate_sha256"] = sha256(opts.candidate.read_bytes()).hexdigest()
        report["candidate_qubits"] = candidate.num_qubits
    opts.report.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
