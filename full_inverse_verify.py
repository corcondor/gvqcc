"""Compile and exhaustively verify complete GF(2^12) inverse schedules.

All quantum instructions are explicit CX, CCX, Z, HMR, and classically
conditioned Z/CZ. No arithmetic oracle is used by the gate simulator.
The simulator bit-packs every one of 4096 field inputs into Python integers.
Measurement outcomes are independent symbolic binary variables. Data are
outcome-independent; each outcome's phase coefficient must cancel exactly.

This validates arithmetic kernels, not the competition's full DQI circuit.
No official Kickmix parser or verifier is invoked.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import time

from inverse_specialized import (
    MODULUS, gf_mul, gf_frobenius, linear_gates, make_power_map,
    polynomial_mul_terms,
)


def mod_poly(p):
    while p.bit_length() > 12:
        p ^= MODULUS << (p.bit_length() - 13)
    return p


def gf_power(x, power):
    result = 1
    while power:
        if power & 1:
            result = gf_mul(result, x)
        power >>= 1
        x = gf_mul(x, x)
    return result


def bits_set(mask):
    while mask:
        low = mask & -mask
        yield low.bit_length() - 1
        mask ^= low


def parity(mask):
    places = list(bits_set(mask))
    p = places[0]
    return p, [("CX", q, p) for q in places[1:]]


def vector_product(u, v, out, targets):
    assert u and v and not (u & v) and out
    p, pu = parity(u)
    q, pv = parity(v)
    target_places = list(bits_set(out))
    t = targets[target_places[0]]
    fan = [("CX", t, targets[k]) for k in target_places[1:]]
    before = pu + pv + fan
    return before + [("CCX", p, q, t)] + list(reversed(before))


def frobenius_gates(qubits, power):
    cols = [gf_frobenius(1 << i, power) for i in range(12)]
    rows = [sum(((v >> j) & 1) << i for i, v in enumerate(cols)) for j in range(12)]
    return [("CX", qubits[c], qubits[t]) for c, t in linear_gates(rows)]


def compute_product(left, right, target, exponent_b):
    shift = frobenius_gates(left, exponent_b)
    terms = polynomial_mul_terms([1 << q for q in left], [1 << q for q in right])
    gates = shift[:]
    for u, v, output_poly in terms:
        out = mod_poly(output_poly)
        if out:
            gates += vector_product(u, v, out, target)
    gates += list(reversed(shift))
    assert sum(g[0] == "CCX" for g in gates) == 63
    return gates


def compute_double(source, target, a):
    spec = make_power_map(a)
    wires = source + target
    return [("CX" if len(g) == 2 else "CCX", *(wires[q] for q in g)) for g in spec["gates"]]


def erase_double(source, target, a, first_measurement):
    spec = make_power_map(a)
    records = [first_measurement + j for j in range(12)]
    gates = [("HMR", q, m) for q, m in zip(target, records)]
    basis = [("CX", source[c], source[t]) for c, t in linear_gates(spec["source_to_tower_rows"])]
    gates += basis
    for bit, out in spec["linear_coefficients"]:
        gates += [("Z_IF", source[bit], records[j]) for j in bits_set(out)]
    for u, v, out in spec["bilinear_terms"]:
        global_u = sum(1 << source[k] for k in bits_set(u))
        global_v = sum(1 << source[k] for k in bits_set(v))
        p, pu = parity(global_u)
        q, pv = parity(global_v)
        gates += pu + pv
        gates += [("CZ_IF", p, q, records[j]) for j in bits_set(out)]
        gates += list(reversed(pu + pv))
    gates += list(reversed(basis))
    return gates


def erase_product(left, right, target, exponent_b, first_measurement):
    records = [first_measurement + j for j in range(12)]
    gates = [("HMR", q, m) for q, m in zip(target, records)]
    shift = frobenius_gates(left, exponent_b)
    gates += shift
    for i in range(12):
        for j in range(12):
            coeff = mod_poly(1 << (i+j))
            gates += [("CZ_IF", left[i], right[j], records[k]) for k in bits_set(coeff)]
    gates += list(reversed(shift))
    return gates


def compile_schedule(schedule):
    cap = schedule["max_registers"]
    slot_for = {1: 0}
    gates = []
    segments = []
    measurement_count = 0
    peak = 0

    def wire(label):
        start = 12 * slot_for[label]
        return list(range(start, start+12))

    for step in schedule["steps"]:
        start = len(gates)
        action = step["action"]
        if action == "phase":
            shift = frobenius_gates(wire(11), 1)
            gates += shift + [("Z", wire(11)[0])] + list(reversed(shift))
        elif action == "compute":
            label, a, b = step["target"], step["a"], step["b"]
            slot_for[label] = next(slot for slot in range(1, cap+1) if slot not in slot_for.values())
            peak = max(peak, len(slot_for)-1)
            if a == b:
                gates += compute_double(wire(a), wire(label), a)
            else:
                gates += compute_product(wire(a), wire(b), wire(label), b)
        elif action == "erase":
            label, a, b = step["target"], step["a"], step["b"]
            if a == b:
                gates += erase_double(wire(a), wire(label), a, measurement_count)
            else:
                gates += erase_product(wire(a), wire(b), wire(label), b, measurement_count)
            measurement_count += 12
            del slot_for[label]
        else:
            raise ValueError(action)
        segments.append({"action": action, "gate_start": start, "gate_stop": len(gates),
                         "live_slots": dict(slot_for)})
    output_slot = None
    if schedule["objective"] == "retained_output":
        assert set(slot_for) == {1, 11}
        output_slot = slot_for[11]
        gates += frobenius_gates(wire(11), 1)
    else:
        assert slot_for == {1: 0}
    assert sum(g[0] == "CCX" for g in gates) == schedule["forward_cost"]
    return {"gates": gates, "segments": segments, "qubits": 12*(peak+1),
            "extra_words": peak, "measurement_count": measurement_count,
            "output_slot": output_slot}


def table_for_values(values):
    out = [0] * 12
    for x, value in enumerate(values):
        for j in bits_set(value):
            out[j] |= 1 << x
    return out


def verify(compiled, objective, expected):
    qubits = [0] * compiled["qubits"]
    qubits[:12] = expected[1]
    symbolic_phase = [0] * compiled["measurement_count"]
    constant_phase = 0
    checkpoints = {s["gate_stop"]:s for s in compiled["segments"]}
    checked_boundaries = 0
    for op_index, gate in enumerate(compiled["gates"], 1):
        op = gate[0]
        if op == "CX":
            _, c, t = gate
            qubits[t] ^= qubits[c]
        elif op == "CCX":
            _, a, b, t = gate
            qubits[t] ^= qubits[a] & qubits[b]
        elif op == "HMR":
            _, q, m = gate
            symbolic_phase[m] ^= qubits[q]
            qubits[q] = 0
        elif op == "Z_IF":
            _, q, m = gate
            symbolic_phase[m] ^= qubits[q]
        elif op == "CZ_IF":
            _, a, b, m = gate
            symbolic_phase[m] ^= qubits[a] & qubits[b]
        elif op == "Z":
            constant_phase ^= qubits[gate[1]]
        else:
            raise ValueError(gate)
        if op_index in checkpoints:
            checkpoint = checkpoints[op_index]
            slots = checkpoint["live_slots"]
            for label, slot in slots.items():
                assert qubits[12*slot:12*(slot+1)] == expected[label], (op_index, label, "wrong live value")
            for slot in range(compiled["extra_words"]+1):
                if slot not in slots.values():
                    assert not any(qubits[12*slot:12*(slot+1)]), (op_index, slot, "dirty free slot")
            assert not any(symbolic_phase), (op_index, "uncorrected HMR phase")
            checked_boundaries += 1
    assert qubits[:12] == expected[1]
    assert not any(symbolic_phase)
    if objective == "retained_output":
        slot = compiled["output_slot"]
        assert qubits[12*slot:12*(slot+1)] == expected["inverse"]
        assert constant_phase == 0
        for i, q in enumerate(qubits):
            if i >= 12 and not (12*slot <= i < 12*(slot+1)):
                assert not q
    else:
        assert not any(qubits[12:])
        assert constant_phase == expected["inverse"][0]
    return {"status": "PASS", "inputs_verified": 4096,
            "measurement_variables": compiled["measurement_count"],
            "all_measurement_outcomes": "Proved by exact cancellation of each independent symbolic phase coefficient.",
            "checked_schedule_boundaries": checked_boundaries}


def export_kmx(compiled, objective, target):
    lines = ["# Experimental GF(2^12) inverse arithmetic kernel; not a DQI submission.",
             "# Validated by full-domain bitpacked symbolic-measurement gate simulator.",
             "# Official Kickmix parser/verifier has not been run in this environment.",
             'REGISTER r0 "input"']
    lines += [f"APPEND_TO_REGISTER q{i} r0" for i in range(12)]
    if compiled["output_slot"] is not None:
        lines += ['REGISTER r1 "inverse"']
        start = 12*compiled["output_slot"]
        lines += [f"APPEND_TO_REGISTER q{i} r1" for i in range(start,start+12)]
    lines += [f"R q{i}" for i in range(12, compiled["qubits"])]
    for gate in compiled["gates"]:
        op = gate[0]
        if op in ("CX", "CCX", "Z"):
            lines.append(op + " " + " ".join(f"q{q}" for q in gate[1:]))
        elif op == "HMR":
            lines.append(f"HMR q{gate[1]} b{gate[2]}")
        elif op == "Z_IF":
            lines.append(f"Z q{gate[1]} if b{gate[2]}")
        elif op == "CZ_IF":
            lines.append(f"CZ q{gate[1]} q{gate[2]} if b{gate[3]}")
    target.write_text("\n".join(lines)+"\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--export-kmx", action="store_true")
    args = parser.parse_args()
    directory = Path(__file__).parent
    schedules = json.loads(directory.joinpath("pebble_results.json").read_text())["results"]
    schedules = [s for s in schedules if s["model"] == "specialized_weighted" and s["reachable"]
                 and s["max_registers"] in (3,4,5)]
    expected = {k:table_for_values([gf_power(x, (1 << k)-1) for x in range(4096)]) for k in range(1,12)}
    expected["inverse"] = table_for_values([gf_power(x, 4094) for x in range(4096)])
    # Independent multiplicative inverse identity checks the arithmetic oracle.
    assert all(gf_mul(x, gf_power(x,4094)) == 1 for x in range(1,4096))
    start = time.perf_counter()
    reports = []
    for schedule in schedules:
        t0 = time.perf_counter()
        compiled = compile_schedule(schedule)
        result = verify(compiled, schedule["objective"], expected)
        counts = dict(Counter(g[0] for g in compiled["gates"]))
        result.update(objective=schedule["objective"], extra_words=compiled["extra_words"],
                      qubits=compiled["qubits"], gates=len(compiled["gates"]), gate_counts=counts,
                      toffoli_count=counts["CCX"],
                      compilation_and_verification_seconds=time.perf_counter()-t0)
        if args.export_kmx:
            name = f"inverse_{schedule['objective']}_{compiled['extra_words']}words.kmx"
            export_kmx(compiled, schedule["objective"], directory/name)
            result["kmx_file"] = name
        reports.append(result)
        print(json.dumps(result), flush=True)
    output = {"field_modulus": MODULUS, "results": reports,
              "elapsed_seconds": time.perf_counter()-start,
              "scope": "Complete arithmetic-kernel gate and phase verification; no DQI integration or official validator."}
    directory.joinpath("full_inverse_verify_results.json").write_text(json.dumps(output,indent=2)+"\n")


if __name__ == "__main__":
    main()
