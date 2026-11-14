#!/usr/bin/env python3
"""Run an unchanged competition DQI verifier with reproducible provenance.

Default confidence, seed, salt and sample count follow the supplied verifier.
Progress wraps its sequential task callback without changing task inputs.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import resource
import sys
import time


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(data)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("circuit", type=Path)
    parser.add_argument("--verifier", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--shots", type=int, default=102400)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--log2-delta", type=float)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--progress-every", type=int, default=5)
    args = parser.parse_args()

    sys.path.insert(0, str(args.verifier.resolve().parent))
    import verify_submission_dqi as verifier
    import kickmix as km

    verifier_path = Path(verifier.__file__).resolve()
    engine_path = Path(km.__file__).resolve()
    try:
        distribution_version = importlib.metadata.version("kickmix")
    except importlib.metadata.PackageNotFoundError:
        distribution_version = "competition-bundled"
    metadata = {
        "verifier_sha256": sha256(verifier_path),
        "verifier_path": str(verifier_path),
        "kickmix_binary_sha256": sha256(engine_path),
        "kickmix_binary_path": str(engine_path),
        "kickmix_distribution_version": distribution_version,
        "kickmix_runtime_version": getattr(km, "__version__", None),
        "python_version": sys.version,
        "seed": args.seed,
        "salt": "",
        "max_workers": 1,
        "batch_size": args.batch_size,
        "verification_scope": (
            "full competition verifier defaults"
            if args.shots == 102400 and args.seed is None and args.log2_delta is None
            else "custom shot count/seed/confidence, see explicit parameters"
        ),
    }
    print(json.dumps({"event": "provenance", **metadata}), flush=True)
    started = time.monotonic()
    circuit = km.Circuit.from_file(str(args.circuit), format="kmb")
    metadata["load_seconds"] = time.monotonic() - started
    print(json.dumps({"event": "loaded", "seconds": metadata["load_seconds"],
                      "qubits": circuit.num_qubits, "bits": circuit.num_bits,
                      "operations": len(circuit)}), flush=True)

    original_run_parallel = verifier._run_parallel
    verify_started = time.monotonic()

    def progress_run(fn, tasks, max_workers):
        completed = 0
        value_errors = 0
        phase_errors = 0
        toffolis = 0

        def wrapped(task):
            nonlocal completed, value_errors, phase_errors, toffolis
            result = fn(task)
            completed += 1
            value_errors += result[0]
            phase_errors += result[1]
            toffolis += result[2]
            if completed % args.progress_every == 0 or completed == len(tasks):
                print(json.dumps({
                    "event": "progress", "batches": completed,
                    "total_batches": len(tasks), "shots": completed * args.batch_size,
                    "value_errors": value_errors, "phase_errors": phase_errors,
                    "mean_toffolis": toffolis / (completed * args.batch_size),
                    "seconds": time.monotonic() - verify_started,
                }), flush=True)
            return result

        return original_run_parallel(wrapped, tasks, max_workers)

    verifier._run_parallel = progress_run
    options = {"max_workers": 1, "batch_size": args.batch_size}
    if args.seed is not None:
        options["seed"] = args.seed
    if args.log2_delta is not None:
        options["log2_delta"] = args.log2_delta
    result = verifier.verify(
        circuit,
        verifier.ProblemSpecDQI.benchmark_instance(num_shots=args.shots),
        **options,
    )
    metadata["verify_seconds"] = time.monotonic() - verify_started
    metadata["max_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result.update(metadata)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"event": "result", **result}), flush=True)


if __name__ == "__main__":
    main()
