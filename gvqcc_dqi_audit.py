#!/usr/bin/env python3
"""Independent, read-only DQI audit using streamed KMB columns.

Requires Python 3 and a C++17 compiler. Keep kmb_profile.py and
dqi_audit_scan.cpp beside this script. No kickmix import or KMX conversion.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import lzma
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

from kmb_profile import InputSource, KmbFormatError, profile


HERE = Path(__file__).resolve().parent


def nonnegative(text):
    value = int(text)
    if value < 0:
        raise argparse.ArgumentTypeError("Expected a nonnegative integer")
    return value


def interval(text):
    try:
        first, last = (int(value) for value in text.split(":"))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Use START:END, with END exclusive") from exc
    if first < 0 or last < first:
        raise argparse.ArgumentTypeError("Require 0 <= START <= END")
    return first, last


def select_input(requested):
    if requested is not None:
        path = requested.resolve()
        if not path.is_file():
            raise ValueError(f"Input is not a file: {path}")
        return path
    root = Path("/kaggle/input")
    candidates = sorted({
        path.resolve() for pattern in ("dqi.kmb", "dqi.kmb.xz")
        for path in root.rglob(pattern)
    }) if root.is_dir() else []
    if len(candidates) != 1:
        choices = "\n".join(str(path) for path in candidates[:50]) or "(none found)"
        raise ValueError(
            "Specify --circuit explicitly. Automatic Kaggle selection requires exactly "
            f"one dqi.kmb or dqi.kmb.xz; found {len(candidates)}:\n{choices}"
        )
    return candidates[0]


@contextmanager
def staged_kmb(path, member, work):
    if path.name.lower().endswith(".xz"):
        if member:
            raise ValueError("--member applies only to ZIP files")
        staged = work / "input.kmb"
        with lzma.open(path, "rb") as source, staged.open("xb") as target:
            shutil.copyfileobj(source, target, length=1 << 20)
        yield staged, {"container": "xz", "member": None}
    else:
        with InputSource(path, member) as source:
            if source.archive is None:
                yield path, {"container": "file", "member": None}
            else:
                staged = work / "input.kmb"
                with source.open() as stream, staged.open("xb") as target:
                    shutil.copyfileobj(stream, target, length=1 << 20)
                yield staged, {
                    "container": "zip", "member": source.member_info.filename,
                    "uncompressed_bytes": source.size,
                }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--circuit", type=Path, help=".kmb, .kmb.xz, or a ZIP archive")
    parser.add_argument("--member", help="Exact ZIP member name")
    parser.add_argument("--out-dir", type=Path, default=Path("dqi_audit_results"))
    parser.add_argument("--scratch-start", type=nonnegative, default=840)
    parser.add_argument(
        "--scratch-initial", choices=("zero", "unknown"), default="unknown",
        help="Use zero only when the task initializes all scratch qubits to |0>",
    )
    parser.add_argument("--index-mode", choices=("kmb", "legacy-v4"), default="kmb")
    parser.add_argument("--snapshots", default="10500000,10530000,10539000,24000000")
    parser.add_argument("--window", type=interval, default=(10529400, 10547601))
    parser.add_argument("--window-limit", type=nonnegative, default=20000)
    parser.add_argument("--region", type=interval, default=(22500000, 27500000))
    parser.add_argument("--cxx", default="g++", help="C++17 compiler executable")
    args = parser.parse_args(argv)
    started = time.perf_counter()
    try:
        snapshots = sorted({int(value) for value in args.snapshots.split(",") if value.strip()})
        if any(value < 0 for value in snapshots) or len(snapshots) > 128:
            raise ValueError("Provide at most 128 nonnegative snapshot indices")
        if args.window_limit > 100000:
            raise ValueError("--window-limit must be at most 100000")
        selected = select_input(args.circuit)
        compiler = shutil.which(args.cxx)
        if compiler is None:
            raise ValueError(f"C++ compiler not found: {args.cxx}")
        cpp = HERE / "dqi_audit_scan.cpp"
        if not cpp.is_file():
            raise ValueError(f"Keep the companion source file beside this script: {cpp}")
        out = args.out_dir.resolve()
        # A distinct directory prevents overwriting earlier audit evidence.
        out.mkdir(parents=True, exist_ok=False)
        print(f"Input: {selected}\nOutput: {out}", flush=True)
        with tempfile.TemporaryDirectory(prefix="_audit_work_", dir=out) as temporary:
            work = Path(temporary)
            with staged_kmb(selected, args.member, work) as (kmb, container):
                print("Validating and profiling the KMB with bounded buffers.", flush=True)
                binary_profile = profile(kmb, progress=True)
                nq = binary_profile["header"]["num_qubits"]
                if args.scratch_start > nq or nq > 1_000_000 or nq - args.scratch_start > 10_000:
                    raise ValueError(
                        "Require scratch-start <= num_qubits <= 1000000 and at most 10000 scratch"
                    )
                binary_profile["selected_input"] = {"path": str(selected), **container}
                (out / "profile.json").write_text(
                    json.dumps(binary_profile, indent=2) + "\n", encoding="utf-8"
                )
                executable = work / "dqi_audit_scan"
                command = [
                    compiler, "-O3", "-std=c++17", "-Wall", "-Wextra", "-pedantic",
                    str(cpp), "-o", str(executable),
                ]
                print("Compiling the small streaming scanner.", flush=True)
                compiled = subprocess.run(command, capture_output=True, text=True)
                (out / "compile.log").write_text(
                    compiled.stdout + compiled.stderr, encoding="utf-8"
                )
                compiled.check_returncode()
                print("Scanning all KMB operations without building circuit objects.", flush=True)
                scan_command = [
                    str(executable), str(kmb), str(args.scratch_start),
                    "1" if args.scratch_initial == "zero" else "0",
                    "1" if args.index_mode == "legacy-v4" else "0",
                    ",".join(map(str, snapshots)), str(args.window[0]), str(args.window[1]),
                    str(args.window_limit), str(out), str(args.region[0]), str(args.region[1]),
                ]
                scanned = subprocess.run(scan_command, capture_output=True, text=True)
                (out / "scan.log").write_text(scanned.stdout + scanned.stderr, encoding="utf-8")
                scanned.check_returncode()
        scan = json.loads((out / "scan.json").read_text())
        if scan["opcode_histogram"] != binary_profile["opcode_histogram"]:
            raise RuntimeError("Independent Python/C++ opcode histograms differ")
        summary = {
            "schema": "dqi-independent-audit-v1",
            "selected_input": {"path": str(selected), **container},
            "raw_kmb_sha256": binary_profile["raw_kmb_sha256"],
            "num_qubits": nq,
            "num_kmb_operations": binary_profile["header"]["num_ops"],
            "index_mode": args.index_mode,
            "scratch_start": args.scratch_start,
            "scratch_initial": args.scratch_initial,
            "snapshots_requested": snapshots,
            "window_inclusive_exclusive": list(args.window),
            "window_limit": args.window_limit,
            "scanner_cpp_sha256": hashlib.sha256(cpp.read_bytes()).hexdigest(),
            "wrapper_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "compiler": compiler,
            "elapsed_seconds": round(time.perf_counter() - started, 6),
            "semantic_circuit_verification": "not_run",
            "circuit_modified": False,
            "python_cpp_histograms_match": True,
            "interpretation": [
                "Possibly nonzero is a conservative support approximation, not physical liveness.",
                "The zero initial scratch option is an explicit task assumption, not inferred from KMB.",
                "All classical conditions are treated as unknown, including pushed conditions.",
                "Active pushed-condition IDs refer to values captured at push time; later writes do not change them.",
                "Only syntactically unconditional R/HMR proves a qubit zero in this analysis.",
                "X/CX/CCX may overestimate because algebraic cancellations are not tracked.",
                "Phase gates and quantum controls alone do not make a known zero possibly nonzero.",
                "A known-zero qubit is not thereby proven safe to delete or reuse across future gates.",
                "Touched-since-unconditional-reset is instruction history, not liveness.",
                "Counts are static instructions, not official average executed Toffoli cost.",
                "KMB indices include every opcode; legacy-v4 excludes INFO/DEBUG/PUSH/POP.",
                "Windows retain all operations, including CX/classical/control flow.",
                "INFO_TAG payloads are represented by their first 256 bytes in hex.",
                "Supported condition stack depth is capped at 65536; exceeding it aborts.",
            ],
            "outputs": ["profile.json", "scan.json", "events.jsonl", "compile.log", "scan.log"],
        }
        (out / "run_summary.json").write_text(
            json.dumps(summary, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps({
            "out_dir": str(out),
            "raw_kmb_sha256": summary["raw_kmb_sha256"],
            "num_qubits": nq,
            "num_kmb_operations": summary["num_kmb_operations"],
            "peak_possibly_nonzero_scratch": scan["peak_possibly_nonzero_scratch"],
            "peak_touched_since_unconditional_reset_scratch":
                scan["peak_touched_since_unconditional_reset_scratch"],
            "window_records": scan["window"]["recorded"],
            "missing_snapshot_indices": scan["missing_snapshot_indices"],
        }, indent=2), flush=True)
        return 0
    except (ValueError, OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"Audit failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
