#!/usr/bin/env python3
"""Exhaustive reachable-subspace proof, including every measurement branch.

Tracks each classical wire as an exact truth table over all valid addresses.
HMR outcomes are formal independent variables: each outcome's phase coefficient
must vanish before that classical bit is overwritten. There is no random trial.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import resource
import time

import kickmix as km
import numpy as np


def pack(values):
    return sum(1 << a for a, value in enumerate(values) if value)


def prove_one(circuit, incoming, expected, address_bits, label):
    count = incoming.shape[0]
    all_one = (1 << count) - 1
    state = [0] * circuit.num_qubits
    state[:11] = address_bits
    for j in range(5):
        for bit in range(8):
            state[11 + 8*j + bit] = pack((incoming[:, j] >> bit) & 1)
    phase_coefficients = {}
    measurement_count = 0
    resets = 0
    gates = {}
    for pos, line in enumerate(str(circuit).splitlines()):
        parts = line.split()
        if not parts or parts[0] in {"REGISTER", "APPEND_TO_REGISTER"}:
            continue
        gate = parts[0]
        gates[gate] = gates.get(gate, 0) + 1
        qubits = [int(p[1:]) for p in parts[1:] if p.startswith("q")]
        condition = int(parts[-1][1:]) if "if" in parts else None
        if gate in {"X", "CX", "CCX", "R", "HMR"} and condition is not None:
            raise AssertionError((label, pos, "unsupported conditioned state mutation"))
        if gate == "X":
            state[qubits[0]] ^= all_one
        elif gate == "CX":
            a, b = qubits
            state[b] ^= state[a]
        elif gate == "CCX":
            a, b, target = qubits
            state[target] ^= state[a] & state[b]
        elif gate == "HMR":
            bit = int(parts[-1][1:])
            if phase_coefficients.get(bit, 0):
                raise AssertionError((label, pos, "uncancelled previous measurement coefficient", bit))
            phase_coefficients[bit] = state[qubits[0]]
            state[qubits[0]] = 0
            measurement_count += 1
        elif gate == "R":
            if state[qubits[0]]:
                raise AssertionError((label, pos, "reset of a nonzero wire", qubits[0]))
            resets += 1
        elif gate == "CZ":
            if condition is None or condition not in phase_coefficients:
                raise AssertionError((label, pos, "unsupported phase term"))
            phase_coefficients[condition] ^= state[qubits[0]] & state[qubits[1]]
        else:
            raise AssertionError((label, pos, "unsupported gate", gate))
    if state[:11] != address_bits:
        raise AssertionError((label, "selection not restored"))
    if any(state[51:]):
        raise AssertionError((label, "dirty scratch"))
    if any(phase_coefficients.values()):
        raise AssertionError((label, "residual measurement phase"))
    for j in range(5):
        for bit in range(8):
            want = pack((expected[:, j] >> bit) & 1)
            difference = state[11 + 8*j + bit] ^ want
            if difference:
                a = (difference & -difference).bit_length() - 1
                raise AssertionError((label, "output mismatch", a, j, bit))
    return {
        "label": label, "status": "EXACT_PASS", "addresses": count,
        "output_bits_checked": 40,
        "HMR_formal_variables_cancelled": measurement_count,
        "R_zero_inputs_checked": resets,
        "selection_restored": True, "workspace_zero": True,
        "output_equals_expected_batch": True,
        "measurement_phase_identically_zero": True,
        "gate_counts": gates,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--loaders", type=Path, required=True)
    parser.add_argument("--table", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError("Use a fresh report path")
    started = time.monotonic()
    with np.load(args.table, allow_pickle=False) as data:
        words = data["angle_words"].astype(np.uint64)
    assert words.shape == (1220, 75)
    assert np.all(words < 256)
    addresses = np.arange(len(words), dtype=np.uint64)
    address_bits = [pack((addresses >> q) & 1) for q in range(11)]
    zero = np.zeros((len(words), 5), dtype=np.uint64)
    reports = []
    pins = {}
    for k in range(15):
        path = args.loaders / f"angle_k_{k}.kmb"
        pins[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        circuit = km.Circuit.from_file(path)
        previous = words[:, 5*(k-1):5*k] if k else zero
        current = words[:, 5*k:5*(k+1)]
        for direction, incoming, expected in [
            ("forward", previous, current), ("reverse", current, previous)
        ]:
            report = prove_one(circuit, incoming, expected, address_bits, f"k={k}/{direction}")
            reports.append(report)
            print(json.dumps({key:report[key] for key in ["label", "status", "HMR_formal_variables_cancelled", "R_zero_inputs_checked"]}), flush=True)
    pairs = [(0,1), (0,2), (1,2), (0,3), (1,3)]
    canonical = np.stack([((addresses >> a) & 1) & ((addresses >> b) & 1) for a,b in pairs], axis=1)
    tag_checks = []
    for k in range(15):
        batch = words[:, 5*k:5*(k+1)]
        tag = ((batch >> 6) ^ (batch >> 7)) & 1
        tag_checks.append(bool(np.array_equal(tag, canonical)))
    report = {
        "status": "EXACT_REACHABLE_SUBSPACE_PASS",
        "proof_domain": "all 1220 addresses, all 15 circuits, both specified forward and reverse input batches, all HMR measurement records",
        "address_transition_cases": 1220 * 15 * 2,
        "sampled_shots": 0,
        "HMR_formal_variables_cancelled": sum(r["HMR_formal_variables_cancelled"] for r in reports),
        "R_zero_inputs_checked": sum(r["R_zero_inputs_checked"] for r in reports),
        "circuit_sha256": pins,
        "table_sha256": hashlib.sha256(args.table.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "canonical_tag_pairs_of_address_bits": pairs,
        "canonical_tag_formula_matches_all_batches": all(tag_checks),
        "checks": reports,
        "implication": "For each specified input-batch subspace, every measurement branch has the same correct output basis mapping and zero relative phase; each HMR branch has input-independent normalization. Linearity gives the same isometry for arbitrary coherent address superpositions entangled with a reference system.",
        "limitation": "Does not establish the arbitrary-target XOR extension or resolve which extension the binding competition contract requires. Does not recheck chemistry tensor accuracy or the complete scoring package.",
        "source_files_modified": False,
        "seconds": time.monotonic() - started,
        "peak_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k:v for k,v in report.items() if k not in {"checks", "circuit_sha256"}}, indent=2))


if __name__ == "__main__":
    main()
