#!/usr/bin/env python3
"""Replay selected unchanged verifier batches from a specified circuit seed."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("circuit", type=Path)
    parser.add_argument("--verifier", type=Path, required=True)
    parser.add_argument("--seed-sha256", required=True)
    parser.add_argument("--first-batch", type=int, required=True)
    parser.add_argument("--stop-batch", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.verifier.resolve().parent))
    import kickmix as km
    import numpy as np
    import verify_submission_dqi as verifier

    spec = verifier.ProblemSpecDQI.benchmark_instance()
    batch_size = 256
    base_seed = verifier._initial_seed(args.seed_sha256, "")
    seeds = np.random.SeedSequence(base_seed, pool_size=8).generate_state(
        8 * 400, dtype=np.uint64).reshape(-1, 2, 4)
    tables = verifier.FieldTables(km.GF2Field(spec.degree))
    probabilities = verifier.optimal_dqi_weights(spec.m, spec.max_errors, spec.degree, spec.r) ** 2
    start = time.monotonic()
    circuit = km.Circuit.from_file(str(args.circuit), format="kmb")
    syndrome_qubits, mbuc_bits, ancilla_qubits = verifier.validate_registers(circuit, spec)
    syndrome_array, mbuc_array = km.array(syndrome_qubits), km.array(mbuc_bits)
    batches = []
    failures = []
    for batch in range(args.first_batch, args.stop_batch):
        rng_seed = int.from_bytes(seeds[batch, 0], "little")
        sim_seed = int.from_bytes(seeds[batch, 1], "little")
        syndromes, mbuc, expected_phases = verifier.sample_shots(
            spec, tables, np.random.default_rng(rng_seed), batch_size, probabilities)
        weights = np.random.default_rng(rng_seed).choice(len(probabilities), size=batch_size, p=probabilities)
        simulator = km.Simulator(batch_size=batch_size, debug_print=False,
                                 counting_operations=True, seed=sim_seed)
        simulator.use_same_registers_as(circuit)
        input_syndromes = verifier.to_bits(syndromes, spec.degree)
        simulator.write_across_shots(syndrome_array, input_syndromes)
        simulator.write_across_shots(mbuc_array, verifier.to_bits(mbuc, spec.degree))
        simulator.do(circuit)
        phases = simulator.read_phase_flipped_across_shots()
        syndrome_output = simulator.read_across_shots(syndrome_array)
        difference = syndrome_output ^ input_syndromes
        junk = simulator.read_across_shots(ancilla_qubits)
        value_errors = difference.any(axis=0) | junk.any(axis=0)
        phase_errors = (phases ^ expected_phases) & ~value_errors
        stats = simulator.operation_statistics()
        row = {"batch_index": batch, "value_errors": int(value_errors.sum()),
               "phase_errors": int(phase_errors.sum()), "toffolis": int(stats.num_toffoli_like),
               "output_syndrome_sha256": hashlib.sha256(syndrome_output.tobytes()).hexdigest(),
               "output_ancilla_sha256": hashlib.sha256(junk.tobytes()).hexdigest(),
               "output_phase_sha256": hashlib.sha256(phases.tobytes()).hexdigest()}
        batches.append(row)
        for shot in np.flatnonzero(value_errors | phase_errors):
            failures.append({
                "batch_index": batch, "shot_in_batch": int(shot),
                "absolute_shot": batch * batch_size + int(shot),
                "sampled_error_weight": int(weights[shot]),
                "value_error": bool(value_errors[shot]), "phase_error": bool(phase_errors[shot]),
                "syndrome_difference_indices": np.flatnonzero(difference[:, shot]).tolist(),
                "nonzero_ancillas": [str(ancilla_qubits[i]) for i in np.flatnonzero(junk[:, shot])],
                "expected_phase": bool(expected_phases[shot]), "actual_phase": bool(phases[shot]),
                "input_syndromes": syndromes[shot].tolist(),
                "input_mbuc": mbuc[shot].tolist(),
            })
        print(json.dumps(row), flush=True)
    report = {"circuit_sha256": verifier._circuit_sha256(circuit),
              "seed_circuit_sha256": args.seed_sha256, "base_seed": base_seed,
              "salt": "", "batch_size": batch_size, "batches": batches,
              "failures": failures, "elapsed_seconds": time.monotonic() - start,
              "scope": "Exact input and simulator seeds from selected original 102400-shot verification batches."}
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "failures": len(failures),
                      "base_seed": base_seed, "elapsed_seconds": report["elapsed_seconds"]}), flush=True)


if __name__ == "__main__":
    main()
