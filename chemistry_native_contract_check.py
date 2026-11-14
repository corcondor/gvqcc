#!/usr/bin/env python3
"""Independent native Kickmix check of arbitrary-z XOR behavior.

This diagnostic does not implement the competition verifier and does not claim
that its input domain matches the currently binding competition contract.
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


def bits(values, width):
    return ((values[None, :] >> np.arange(width, dtype=np.uint64)[:, None]) & 1).astype(bool)


def read_integer(sim, start, width):
    data = sim.read_across_shots(km.array([km.q(i) for i in range(start, start + width)]))
    return (data.astype(np.uint64) * (np.uint64(1) << np.arange(width, dtype=np.uint64))[:, None]).sum(axis=0, dtype=np.uint64)


def check(loaders, table_path, k, address_count, seed):
    path = loaders / f"angle_k_{k}.kmb"
    circuit = km.Circuit.from_file(path)
    states = [(a, z) for a in range(address_count) for z in [0] + [1 << i for i in range(40)]]
    address = np.array([a for a, _ in states], dtype=np.uint64)
    z = np.array([z for _, z in states], dtype=np.uint64)
    sim = km.Simulator(batch_size=len(states), debug_print=False, seed=seed, counting_operations=True)
    sim.use_same_registers_as(circuit)
    sim.write_across_shots(km.array([km.q(i) for i in range(11)]), bits(address, 11))
    sim.write_across_shots(km.array([km.q(i) for i in range(11, 51)]), bits(z, 40))
    sim.do(circuit)
    result = read_integer(sim, 11, 40)
    zero_output = result.reshape(address_count, 41)[:, 0]
    xor_from_zero = np.repeat(zero_output, 41) ^ z
    xor_structure_bad = np.flatnonzero(result != xor_from_zero)
    with np.load(table_path, allow_pickle=False) as data:
        words = data["angle_words"].astype(np.uint64)
    packed = np.zeros(address_count, dtype=np.uint64)
    for j in range(5):
        delta = words[:address_count, 5*k+j].copy()
        if k:
            delta ^= words[:address_count, 5*(k-1)+j]
        packed ^= delta << np.uint64(8*j)
    expected = packed[address.astype(np.int64)] ^ z
    expected_bad = np.flatnonzero(result != expected)
    phase_errors = int(np.count_nonzero(sim.read_phase_flipped_across_shots()))
    selection_errors = int(np.count_nonzero(read_integer(sim, 0, 11) != address))
    work = sim.read_across_shots(km.array([km.q(i) for i in range(51, circuit.num_qubits)]))
    workspace_errors = int(np.count_nonzero(np.any(work, axis=0)))
    return {
        "k": k,
        "circuit": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "table_sha256": hashlib.sha256(table_path.read_bytes()).hexdigest(),
        "shots": len(states), "seed": seed,
        "address_count": address_count,
        "initial_z_patterns": "zero and each of 40 single bits",
        "arbitrary_z_structure_mismatches": int(len(xor_structure_bad)),
        "declared_table_xor_mismatches": int(len(expected_bad)),
        "phase_errors": phase_errors, "selection_errors": selection_errors,
        "workspace_errors": workspace_errors,
        "first_counterexamples": [{
            "a": int(address[i]), "z": int(z[i]), "actual": int(result[i]),
            "zero_output": int(zero_output[int(address[i])]),
            "xor_from_zero_expected": int(xor_from_zero[i]),
            "declared_table_xor_expected": int(expected[i]),
        } for i in xor_structure_bad[:8]],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--loaders", type=Path, required=True)
    parser.add_argument("--table", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--batch", type=int, default=1, choices=range(15))
    parser.add_argument("--addresses", type=int, default=8)
    parser.add_argument("--seed", type=int, default=123456789)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError("Use a fresh report path")
    if not 1 <= args.addresses <= 1220:
        raise ValueError("Address count must be between 1 and 1220")
    started = time.monotonic()
    report = check(args.loaders, args.table, args.batch, args.addresses, args.seed)
    report["status"] = "DIAGNOSTIC_COMPLETE_NOT_OFFICIAL_SCORE"
    report["script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["seconds"] = time.monotonic() - started
    report["peak_rss_mib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
