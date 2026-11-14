#!/usr/bin/env python3
"""Exact small-state reversible-pebbling search for GF(2^12) inversion.

beta_k(x) = x**(2**k - 1); beta_1 is the preserved input. Each state
contains a subset of beta_2 ... beta_11. A compute can use any a+b=k
whose parents are present. A measurement erase has cost zero but still
requires those parents. The model includes a clean output destination.

Models differ in temporary Frobenius-copy words and forward gate costs.
This is arithmetic scheduling, NOT verification of the user's circuit.
The specialized costs are supplied separately by a gate-construction audit.
"""
from __future__ import annotations

import argparse
import heapq
import json
import platform
import time
from pathlib import Path

M = 12
MAX_K = M - 1
N_VALUES = MAX_K - 1
PHASE_BIT = 1 << N_VALUES
VALUE_MASK = PHASE_BIT - 1
OUTPUT_BIT = 1 << (MAX_K - 2)
FACTORS = {k: [(a, k - a) for a in range(1, k // 2 + 1)]
           for k in range(2, MAX_K + 1)}
SPECIALIZED_DOUBLING_COSTS = {1: 51, 2: 36, 3: 35, 4: 27, 5: 51}


def live_values(mask: int) -> list[int]:
    return [k for k in range(2, MAX_K + 1) if mask & (1 << (k - 2))]


def present(mask: int, k: int) -> bool:
    return k == 1 or bool(mask & (1 << (k - 2)))


def model_settings(model: str) -> tuple[bool, bool, bool]:
    """Return (copy on double compute, copy on double erase, weighted)."""
    return {
        "abstract": (False, False, False),
        "copy_compute": (True, False, False),
        "copy_compute_and_erase": (True, True, False),
        "specialized_weighted": (False, False, True),
    }[model]


def search(cap: int, model: str, objective: str) -> dict:
    t0 = time.perf_counter()
    copy_compute, copy_erase, weighted = model_settings(model)
    phase_objective = objective == "phase_then_clear"
    goal = PHASE_BIT if phase_objective else OUTPUT_BIT
    # Distance tuple prioritizes forward cost, then multiplier calls, then
    # operations. The latter two only break ties in the primary objective.
    distance = {0: (0, 0, 0)}
    predecessor: dict[int, tuple[int, dict]] = {}
    queue = [(0, 0, 0, 0)]
    explored = 0
    final_distance = None
    while queue:
        cost, n_mult, n_ops, state = heapq.heappop(queue)
        if distance.get(state) != (cost, n_mult, n_ops):
            continue
        explored += 1
        if state == goal:
            final_distance = (cost, n_mult, n_ops)
            break
        mask = state & VALUE_MASK
        seen_phase = state & PHASE_BIT
        count = mask.bit_count()
        transitions = []
        if phase_objective and not seen_phase and mask & OUTPUT_BIT:
            transitions.append((state | PHASE_BIT, 0, 0, {
                "action": "phase", "target": MAX_K,
                "registers_during": count,
            }))
        for k, decompositions in FACTORS.items():
            bit = 1 << (k - 2)
            erasing = bool(mask & bit)
            for a, b in decompositions:
                if not (present(mask, a) and present(mask, b)):
                    continue
                copy_word = a == b and (copy_erase if erasing else copy_compute)
                peak = count + (0 if erasing else 1) + int(copy_word)
                if peak > cap:
                    continue
                next_mask = mask ^ bit
                step_cost = 0 if erasing else (
                    SPECIALIZED_DOUBLING_COSTS[a] if weighted and a == b
                    else 63 if weighted else 1)
                transitions.append((next_mask | seen_phase, step_cost,
                                    0 if erasing else 1, {
                    "action": "erase" if erasing else "compute",
                    "target": k, "a": a, "b": b,
                    "forward_cost": step_cost,
                    "registers_during": peak,
                }))
        for next_state, step_cost, mult_delta, step in transitions:
            next_distance = (cost + step_cost, n_mult + mult_delta, n_ops + 1)
            if next_distance >= distance.get(next_state, (10**18,) * 3):
                continue
            step = dict(step)
            step["live_before"] = live_values(mask)
            step["live_after"] = live_values(next_state & VALUE_MASK)
            distance[next_state] = next_distance
            predecessor[next_state] = (state, step)
            heapq.heappush(queue, (*next_distance, next_state))
    steps = []
    if final_distance is not None:
        cursor = goal
        while cursor:
            previous, step = predecessor[cursor]
            steps.append(step)
            cursor = previous
        steps.reverse()
    result = {
        "model": model, "objective": objective, "max_registers": cap,
        "reachable": final_distance is not None,
        "forward_cost_unit": "Toffoli" if weighted else "GF multiplication",
        "forward_cost": final_distance[0] if final_distance else None,
        "multiplications": final_distance[1] if final_distance else None,
        "peak_registers": max((s["registers_during"] for s in steps), default=0)
                          if final_distance else None,
        "steps": steps,
        "explored_states": explored,
        "discovered_states": len(distance),
        "wall_seconds": time.perf_counter() - t0,
    }
    return result


def poly_mod(a: int, p: int) -> int:
    while a.bit_length() >= p.bit_length():
        a ^= p << (a.bit_length() - p.bit_length())
    return a


def poly_gcd(a: int, b: int) -> int:
    while b:
        a, b = b, poly_mod(a, b)
    return a


def gf_mul(a: int, b: int, p: int) -> int:
    value = 0
    while b:
        if b & 1:
            value ^= a
        b >>= 1
        a <<= 1
        if a & (1 << M):
            a ^= p
    return value


def gf_power(a: int, exponent: int, p: int) -> int:
    result = 1
    while exponent:
        if exponent & 1:
            result = gf_mul(result, a, p)
        exponent >>= 1
        a = gf_mul(a, a, p)
    return result


def irreducible(p: int) -> bool:
    # Rabin criterion for m=12; prime divisors of m are 2 and 3.
    x_frob = 2
    for i in range(1, M + 1):
        x_frob = gf_mul(x_frob, x_frob, p)
        if i in (M // 2, M // 3) and poly_gcd(x_frob ^ 2, p) != 1:
            return False
    return x_frob == 2


def verify_paths(results: list[dict], p: int) -> dict:
    t0 = time.perf_counter()
    assert irreducible(p), f"Reducible field polynomial: {p:#x}"
    # Deduplicate paths; caps often share identical optimal paths.
    paths = {}
    for result in results:
        if not result["reachable"]:
            continue
        key = (result["objective"], tuple(
            (s["action"], s["target"], s.get("a"), s.get("b"))
            for s in result["steps"]))
        paths.setdefault(key, result)
    operations = 0
    for x in range(1 << M):
        reference = {k: gf_power(x, (1 << k) - 1, p)
                     for k in range(1, MAX_K + 1)}
        for result in paths.values():
            registers = {1: x}
            phase_seen = False
            for step in result["steps"]:
                action, k = step["action"], step["target"]
                if action == "phase":
                    assert registers[k] == reference[k]
                    phase_seen = True
                    continue
                a, b = step["a"], step["b"]
                assert a in registers and b in registers
                shifted = gf_power(registers[a], 1 << b, p)
                product = gf_mul(shifted, registers[b], p)
                assert product == reference[k], (x, step)
                if action == "compute":
                    assert k not in registers
                    registers[k] = product
                else:
                    assert registers[k] == product
                    del registers[k]
                assert sorted(v for v in registers if v != 1) == step["live_after"]
                operations += 1
            if result["objective"] == "retained_output":
                assert set(registers) == {1, MAX_K}
                inverse = gf_mul(registers[MAX_K], registers[MAX_K], p)
                assert inverse == (0 if x == 0 else gf_power(x, (1 << M) - 2, p))
                if x:
                    assert gf_mul(x, inverse, p) == 1
            else:
                assert set(registers) == {1} and phase_seen
    return {
        "verification_type": "exhaustive classical GF arithmetic and schedule checks",
        "not_verified_here": "quantum gate decomposition and HMR phase corrections",
        "field_degree": M, "field_modulus_hex": hex(p),
        "field_modulus_irreducible": True,
        "inputs_checked_per_path": 1 << M, "unique_paths_checked": len(paths),
        "arithmetic_steps_checked": operations,
        "status": "PASS", "wall_seconds": time.perf_counter() - t0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).with_name("pebble_results.json"))
    parser.add_argument("--skip-verify", action="store_true")
    parser.add_argument("--modulus", type=lambda s: int(s, 0), default=0x1053)
    args = parser.parse_args()
    started = time.perf_counter()
    results = [search(cap, model, objective)
               for model in ("abstract", "copy_compute", "copy_compute_and_erase",
                             "specialized_weighted")
               for objective in ("retained_output", "phase_then_clear")
               for cap in range(1, 11)]
    pareto = []
    best = {}
    for r in results:
        key = (r["model"], r["objective"])
        if r["reachable"] and r["forward_cost"] < best.get(key, float("inf")):
            pareto.append(r)
            best[key] = r["forward_cost"]
    payload = {
        "problem": "GF(2^12) beta-chain reversible pebbling",
        "runtime": {"python": platform.python_version(), "platform": platform.platform()},
        "state_model": {
            "input": "beta_1 permanent; excluded from register count",
            "candidate_values": list(range(2, MAX_K + 1)),
            "state_count_retained_output": 1 << N_VALUES,
            "state_count_phase_then_clear": 1 << (N_VALUES + 1),
            "final_square": "free Frobenius beta_11^2; inverse(0) is extended to 0",
            "register_bits": M,
            "erase_rule": "any present factorization beta_k=beta_a^(2^b)*beta_b",
            "specialized_forward_Toffoli_costs": SPECIALIZED_DOUBLING_COSTS,
            "distinct_parent_forward_Toffoli_cost": 63,
            "weighted_cost_status": "external gate verification report not loaded",
            "limitations": [
                "Abstract model omits transient copies and is a lower bound.",
                "specialized_weighted requires no-copy quadratic maps and HMR correction gates.",
                "A multiplication graph search does not cover all GF inverse algorithms.",
                "Clifford count/depth, classical bits, control wrappers, and existing decoder wiring are excluded.",
                "No result is asserted to describe the user's unprovided DQI circuit.",
            ],
        },
        "results": results, "pareto": pareto,
        "search_wall_seconds": time.perf_counter() - started,
        "search_expanded_states_total": sum(r["explored_states"] for r in results),
    }
    cost_report_path = Path(__file__).with_name("inverse_specialized_results.json")
    if cost_report_path.exists():
        cost_report = json.loads(cost_report_path.read_text())
        verified_costs = {m["frobenius_power"]: m["ccx_count"]
                          for m in cost_report["maps"] if m["status"] == "PASS"}
        if verified_costs == SPECIALIZED_DOUBLING_COSTS:
            payload["state_model"]["weighted_cost_status"] = (
                "Explicit CX/CCX forward maps separately checked on 4096 inputs "
                "and two target patterns each; HMR phase corrections are a separate verification.")
            payload["state_model"]["weighted_cost_report"] = cost_report_path.name
            if all(m.get("phase_correction_cases", 0) == 4096 * 12
                   for m in cost_report["maps"]):
                payload["state_model"]["weighted_cost_status"] = (
                    "Explicit CX/CCX forward maps separately checked on 4096 inputs "
                    "and two target patterns each; no-copy HMR phase correction separately "
                    "checked on all inputs and 12 basis masks, covering every mask by linearity.")
    # Checkpoint search output before exhaustive arithmetic verification.
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    print("Pareto points (model, objective, cap, cost, multiplications):", flush=True)
    for r in pareto:
        print(r["model"], r["objective"], r["max_registers"],
              r["forward_cost"], r["multiplications"], flush=True)
    print("Search seconds:", payload["search_wall_seconds"], flush=True)
    if not args.skip_verify:
        payload["classical_verification"] = verify_paths(pareto, args.modulus)
        args.output.write_text(json.dumps(payload, indent=2) + "\n")
        print(json.dumps(payload["classical_verification"]), flush=True)
    print("Output:", args.output.resolve(), flush=True)


if __name__ == "__main__":
    main()
