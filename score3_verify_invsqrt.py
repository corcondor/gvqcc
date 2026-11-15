#!/usr/bin/env python3
"""Run the unchanged invsqrt verifier at its full domain and 64 shots/x.

Only the task-dispatch wrapper adds shared progress accounting. Circuit,
reference arithmetic, measurement seeds, per-shot tests, and cost are unchanged.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
import multiprocessing as mp
from pathlib import Path
import resource
import sys
import time


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('circuit', type=Path)
    parser.add_argument('--verifier', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--max-workers', type=int, default=4)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    sys.path.insert(0, str(args.verifier.resolve().parent))
    import verify_submission_invsqrt as verifier
    import kickmix as km
    metadata = {
        'verifier_path': str(args.verifier.resolve()),
        'verifier_sha256': digest(args.verifier),
        'kickmix_binary_sha256': digest(km.__file__),
        'kickmix_distribution_version': importlib.metadata.version('kickmix'),
        'python_version': sys.version,
        'source_file_sha256': digest(args.circuit),
        'seed': None, 'salt': '', 'max_workers': args.max_workers,
        'batch_size': verifier.DEFAULT_BATCH_SIZE,
        'verification_scope': 'full official domain, default 64 shots per x',
        'runner_sha256': digest(__file__),
    }
    circuit = km.Circuit.from_file(str(args.circuit), format='kmb')
    print(json.dumps({'event': 'loaded', **metadata, 'qubits': circuit.num_qubits,
                      'operations': len(circuit)}), flush=True)
    original_dispatch = verifier._run_parallel
    completed = mp.Value('q', 0)
    started = time.monotonic()

    def dispatch(fn, tasks, max_workers):
        def progress(task):
            result = fn(task)
            with completed.get_lock():
                completed.value += 1
                count = completed.value
            if count % 500 == 0 or count == len(tasks):
                print(json.dumps({'event': 'progress', 'completed_chunks': count,
                                  'total_chunks': len(tasks),
                                  'seconds': time.monotonic() - started}), flush=True)
            return result
        return original_dispatch(progress, tasks, max_workers)

    verifier._run_parallel = dispatch
    spec = verifier.ProblemSpecInvSqrt.for_n_p(verifier.N_P)
    result = verifier.verify(circuit, spec, max_workers=args.max_workers)
    result.update(metadata)
    result.update(verify_seconds=time.monotonic()-started,
                  parent_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  largest_child_peak_rss_kib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'event': 'result', **result}), flush=True)


if __name__ == '__main__':
    main()
