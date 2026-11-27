#!/usr/bin/env python3
"""Check one native circuit on the saved 316k panel, without external chart selection.

This is a regression check, not an unchanged official verifier invocation or a
proof of correctness on all legal inputs. Exit status 1 means a real mismatch.
The high-inverse panel transports old counterexamples through the inverse of
the proposed fixed rotation. All masks, syndromes, phase and dirty wires are
checked; raw phase mismatches and official disjoint phase errors are separate.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

import kickmix as km
import numpy as np


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load_verifier(path: Path):
    spec = importlib.util.spec_from_file_location("dqi_repair_official_helpers", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("circuit", type=Path)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--verifier", type=Path, required=True)
    parser.add_argument("--panel", choices=("all", "high", "high-inverse"), default="all")
    parser.add_argument("--rotation-receipt", type=Path)
    parser.add_argument("--strict-316k", action="store_true",
                        help="One unwrapped <=900Q candidate; saved, inverse-rotation, and zero-mask cases")
    parser.add_argument("--prefix", type=Path)
    parser.add_argument("--suffix", type=Path)
    parser.add_argument("--seeds", type=int, nargs="+", default=[12680, 12681])
    parser.add_argument("--batch", type=int, default=128)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.batch <= 0:
        parser.error("batch must be positive")
    if bool(args.prefix) != bool(args.suffix):
        parser.error("prefix and suffix must be specified together")
    if args.strict_316k and (args.panel != "all" or not args.rotation_receipt or args.prefix):
        parser.error("strict-316k requires panel=all, a rotation receipt, and no prefix/suffix")
    verifier = load_verifier(args.verifier)
    started = time.perf_counter()
    with np.load(args.cases, allow_pickle=False) as data:
        syndromes = data["S"].copy()
        masks = data["M"].copy()
        phases = data["expected"].copy()
        weights = data["weights"].copy()
    if not (syndromes.ndim == 2 and syndromes.shape[1] == 70 and
            masks.shape == (len(syndromes), 4095) and
            phases.shape == weights.shape == (len(syndromes),) and len(syndromes)):
        parser.error("invalid or empty saved fixture")
    ids = np.arange(len(syndromes))
    if args.panel == "high":
        ids = np.flatnonzero(weights >= 18)
    if args.panel == "high-inverse":
        if not args.rotation_receipt:
            parser.error("high-inverse requires the original failure-id receipt")
        ids = np.asarray(json.loads(args.rotation_receipt.read_text())["failure_case_ids"]["0"])
    if ids.size == 0 or np.any(ids < 0) or np.any(ids >= len(syndromes)):
        parser.error("invalid or empty selected fixture")
    syndromes, masks, phases = syndromes[ids], masks[ids], phases[ids]
    labels = np.full(len(ids), args.panel, dtype="<U32")
    if args.panel == "high-inverse":
        field = km.GF2Field(12)
        factors = [field.pow(field.primitive_element, (-j) % 4095) for j in range(1, 71)]
        syndromes = np.asarray([
            [field.mul(int(word), factor) for word, factor in zip(row, factors)]
            for row in syndromes
        ], dtype=np.int64)
        masks = np.roll(masks, -1, axis=1)
    if args.strict_316k:
        raw = json.loads(args.rotation_receipt.read_text())["failure_case_ids"]["0"]
        if not raw or any(type(i) is not int or not 0 <= i < len(ids) for i in raw):
            parser.error("invalid inverse-rotation counterexample ids")
        inverse_ids = np.asarray(raw, dtype=np.int64)
        if np.any(weights[inverse_ids] < 18):
            parser.error("inverse-rotation fixture must be high-weight")
        field = km.GF2Field(12)
        factors = [field.pow(field.primitive_element, (-j) % 4095) for j in range(1, 71)]
        rotated = np.asarray([
            [field.mul(int(word), factor) for word, factor in zip(row, factors)]
            for row in syndromes[inverse_ids]
        ], dtype=np.int64)
        syndromes = np.concatenate((syndromes, rotated), axis=0)
        masks = np.concatenate((masks, np.roll(masks[inverse_ids], -1, axis=1)), axis=0)
        phases = np.concatenate((phases, phases[inverse_ids]), axis=0)
        ids = np.concatenate((ids, inverse_ids))
        labels = np.concatenate((labels, np.full(len(inverse_ids), "high-inverse", dtype="<U32")))
        # For every syndrome, zero mask independently requires +1 phase.
        syndromes = np.concatenate((syndromes, syndromes), axis=0)
        masks = np.concatenate((masks, np.zeros_like(masks)), axis=0)
        phases = np.concatenate((phases, np.zeros_like(phases)), axis=0)
        ids = np.concatenate((ids, ids))
        labels = np.concatenate((labels, np.char.add(labels, "/zero-mask")))
    circuit = km.Circuit.from_file(str(args.circuit))
    if args.strict_316k and circuit.num_qubits > 900:
        parser.error("strict-316k candidate exceeds 900 qubits")
    files = {"circuit": digest(args.circuit), "cases": digest(args.cases),
             "verifier": digest(args.verifier)}
    if args.rotation_receipt:
        files["rotation_receipt"] = digest(args.rotation_receipt)
    if args.prefix:
        circuit = km.Circuit.from_file(str(args.prefix)) + circuit + km.Circuit.from_file(str(args.suffix))
        files.update(prefix=digest(args.prefix), suffix=digest(args.suffix))
    quantum, classical, ancilla = verifier.validate_registers(
        circuit, verifier.ProblemSpecDQI.benchmark_instance())
    quantum, classical = km.array(quantum), km.array(classical)
    result = {
        "scope": "one fixed native circuit; no input-dependent external chart choice",
        "official_verifier_run": False, "whole_domain_proof": False,
        "submitted": False, "files_sha256": files,
        "panel": args.panel, "strict_316k": args.strict_316k,
        "cases": len(ids), "seeds": args.seeds,
        "case_counts": {str(k): int((labels == k).sum()) for k in np.unique(labels)},
        "qubits": circuit.num_qubits, "operations": len(circuit),
        "static_paid": int(circuit.operation_statistics().num_toffoli_like),
        "shots": 0, "value_errors": 0, "phase_errors": 0,
        "raw_phase_mismatches": 0, "dirty_errors": 0,
        "mask_restore_errors": 0, "paid_sum": 0, "failures": [],
    }
    for seed in args.seeds:
        for start in range(0, len(ids), args.batch):
            end = min(start + args.batch, len(ids))
            ib = verifier.to_bits(syndromes[start:end], 12)
            mb = verifier.to_bits(masks[start:end], 12)
            sim = km.Simulator(batch_size=end-start, seed=seed+start,
                               counting_operations=True, debug_print=False)
            sim.use_same_registers_as(circuit)
            sim.write_across_shots(quantum, ib)
            sim.write_across_shots(classical, mb)
            sim.do(circuit)
            restored = (sim.read_across_shots(quantum) ^ ib).any(axis=0)
            dirty = sim.read_across_shots(ancilla).any(axis=0)
            mask_bad = (sim.read_across_shots(classical) ^ mb).any(axis=0)
            value = restored | dirty
            phase = sim.read_phase_flipped_across_shots() ^ phases[start:end]
            result["shots"] += end-start
            for key, flag in (("value_errors", value), ("phase_errors", phase & ~value),
                              ("raw_phase_mismatches", phase), ("dirty_errors", dirty),
                              ("mask_restore_errors", mask_bad)):
                result[key] += int(flag.sum())
            result["paid_sum"] += int(sim.operation_statistics().num_toffoli_like)
            for offset in np.flatnonzero(value | phase | mask_bad):
                result["failures"].append({
                    "case_id": int(ids[start+offset]), "seed": seed,
                    "case_type": str(labels[start+offset]),
                    "value": bool(value[offset]), "phase": bool(phase[offset]),
                    "mask": bool(mask_bad[offset]),
                })
            del sim
    result["mean_paid"] = result["paid_sum"] / result["shots"]
    result["mean_paid_scope"] = "diagnostic panel; not official distribution or score"
    result["elapsed_seconds"] = time.perf_counter() - started
    result["pass"] = not result["failures"]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key != "failures"}, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
