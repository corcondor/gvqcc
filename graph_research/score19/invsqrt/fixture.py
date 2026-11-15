"""Exercise the postponed correction on an eight-input complete truth table."""

from collections import Counter
import json

import kickmix as km
import numpy as np

from rewrite import make_trace, parse, search, tracks_for


def phase_and_bits(lines):
    circuit = km.Circuit("\n".join(lines) + "\n")
    inputs = np.tile(np.arange(8, dtype=np.uint32), 16)
    sim = km.Simulator(batch_size=len(inputs), seed=9356)
    sim.use_same_registers_as(circuit)
    sim.write_across_shots(km.array([km.q(j) for j in range(3)]),
                           ((inputs[None, :] >> np.arange(3)[:, None]) & 1).astype(bool))
    sim.do(circuit)
    phases = [sim.read_shot_phase(sh) for sh in range(len(inputs))]
    bits = sim.read_across_shots(km.array([km.q(j) for j in range(circuit.num_qubits)]))
    return phases, np.asarray(bits)


def main():
    source = [
        "CCX q0 q1 q22", "CCX q22 q2 q23", "HMR q22 b1", "CZ q0 q1 if b1",
        "HMR q23 b2", "CCX q0 q1 q24", "CZ q24 q2 if b2", "HMR q24 b3", "CZ q0 q1 if b3",
    ]
    xs = np.arange(8, dtype=np.uint32)
    gates = [parse(s) for s in source]
    trace = list(make_trace(gates, xs))
    start = 1
    old_cone = trace[start - 1:]
    counter = Counter()
    assert search(old_cone, (start,), len(gates), source, gates, xs, counter) is None
    timing = (tracks_for(gates, source), trace, 8)
    result = search(old_cone, (start,), len(gates), source, gates, xs, counter, timing=timing)
    assert result is not None
    assert all(site < cut for site, cut, _ in result["corrections"])
    corrections = {}
    for _, cut, gate in result["corrections"]:
        corrections.setdefault(cut, []).append(gate)
    compiled = []
    for index, line in enumerate(source):
        if index != start:
            compiled.append(line)
        compiled.extend(corrections.get(index, ()))
    original, before = phase_and_bits(source)
    phases, after = phase_and_bits(compiled)
    assert original == phases
    np.testing.assert_array_equal(before, after)
    assert km.Circuit("\n".join(source)).operation_statistics().num_toffoli_like == 3
    assert km.Circuit("\n".join(compiled)).operation_statistics().num_toffoli_like == 2
    after_overwrite = source.copy()
    after_overwrite.insert(5, "BIT_STORE0 b2")
    altered_gates = list(map(parse, after_overwrite))
    altered = list(make_trace(altered_gates, xs))
    altered_timing = (tracks_for(altered_gates, after_overwrite), altered, 8)
    assert search(altered, (start,), len(altered), after_overwrite, altered_gates, xs,
                  Counter(), timing=altered_timing) is None
    print(json.dumps({"inputs": len(xs), "kickmix_shots": len(phases),
                      "same_values": True, "same_phases": True, "before_toffoli": 3,
                      "after_toffoli": 2, "overwrite_guard_rejected": True, **result}, indent=2))


if __name__ == "__main__":
    main()
