#!/usr/bin/env python3
"""CCX-to-X/CX resynthesis on the exact forward/reverse batch input union.

The allowed input contract is explicit: each source is used on the previous
or current declared batch at every valid address. Every replacement preserves
the full current basis-state mapping on both directions. The separately
implemented reachable-subspace proof then checks every candidate from scratch.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import resource
import shutil
import time

import kickmix as km
import numpy as np

from chemistry_affine_span_resynthesis import basis_expression, parse_line
from chemistry_reachable_exact_proof import pack, prove_one


def resynthesize(circuit, previous, current):
    count = len(previous)
    inputs = np.concatenate([previous, current], axis=0)
    addresses = np.tile(np.arange(count, dtype=np.uint64), 2)
    one = (1 << (2*count)) - 1
    values = [0] * circuit.num_qubits
    for q in range(11):
        values[q] = pack((addresses >> q) & 1)
    for j in range(5):
        for bit in range(8):
            values[11+8*j+bit] = pack((inputs[:,j] >> bit) & 1)
    rewritten = []
    hits = []
    ccx = 0
    for index, line in enumerate(str(circuit).splitlines()):
        gate, qs, condition = parse_line(line)
        replacement = [line]
        if gate in {"X", "CX", "CCX", "HMR", "R"} and condition is not None:
            raise ValueError("Classically conditioned state mutation unsupported")
        if gate == "X":
            values[qs[0]] ^= one
        elif gate == "CX":
            values[qs[1]] ^= values[qs[0]]
        elif gate == "CCX":
            a, b, target = qs
            ccx += 1
            product = values[a] & values[b]
            expression = basis_expression(values, product, target, one)
            if expression is not None:
                controls = [q for q in range(len(values)) if expression >> q & 1]
                constant = bool(expression >> len(values) & 1)
                reconstructed = one if constant else 0
                for q in controls:
                    reconstructed ^= values[q]
                assert reconstructed == product
                assert target not in controls
                replacement = ([f"X q{target}"] if constant else []) + [f"CX q{q} q{target}" for q in controls]
                hits.append({"source_line_index": index, "source_gate": line, "replacement": replacement})
            values[target] ^= product
        elif gate in {"HMR", "R"}:
            values[qs[0]] = 0
        elif gate not in {"", "REGISTER", "APPEND_TO_REGISTER", "CZ"}:
            raise ValueError("Unsupported gate: " + gate)
        rewritten.extend(replacement)
    return "\n".join(rewritten) + "\n", ccx, hits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--loaders", type=Path, required=True)
    parser.add_argument("--table", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists() or args.output_dir.exists():
        raise FileExistsError("Use fresh output paths")
    started = time.monotonic()
    with np.load(args.table, allow_pickle=False) as data:
        words = data["angle_words"].astype(np.uint64)
    assert words.shape == (1220,75)
    assert np.all(words < 256)
    address = np.arange(len(words), dtype=np.uint64)
    address_bits = [pack((address >> q) & 1) for q in range(11)]
    zero = np.zeros((len(words),5), dtype=np.uint64)
    rows, candidates = [], []
    for k in range(15):
        path = args.loaders / f"angle_k_{k}.kmb"
        source = km.Circuit.from_file(path)
        previous = words[:,5*(k-1):5*k] if k else zero
        current = words[:,5*k:5*(k+1)]
        text, ccx, hits = resynthesize(source, previous, current)
        candidate = km.Circuit(text)
        proofs = [
            prove_one(candidate, previous, current, address_bits, f"candidate k={k}/forward"),
            prove_one(candidate, current, previous, address_bits, f"candidate k={k}/reverse"),
        ]
        row = {
            "k": k, "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "source_ccx": ccx, "ccx_removed": len(hits),
            "candidate_ccx": ccx-len(hits), "num_qubits": candidate.num_qubits,
            "hits": hits, "exact_reachable_proofs": proofs,
        }
        rows.append(row)
        candidates.append(candidate)
        print(json.dumps({key:row[key] for key in ["k", "source_ccx", "ccx_removed", "candidate_ccx", "num_qubits"]}), flush=True)
    total = sum(row["ccx_removed"] for row in rows)
    report = {
        "status": "EXACT_CONTEXT_CANDIDATE_PASS" if total else "NO_CCX_REPLACEMENTS",
        "context": "all 1220 valid addresses times the exact previous and next batch inputs, simultaneously",
        "input_truth_vector_bits": 2440,
        "table_sha256": hashlib.sha256(args.table.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_ccx_per_pass": sum(row["source_ccx"] for row in rows),
        "candidate_ccx_per_pass": sum(row["candidate_ccx"] for row in rows),
        "ccx_removed_per_pass": total,
        "exact_address_transition_cases": 1220*15*2,
        "sampled_shots": 0,
        "source_files_modified": False,
        "official_score_verifier_run": False,
        "loaders": rows,
    }
    if total:
        args.output_dir.mkdir()
        for k, candidate in enumerate(candidates):
            path = args.output_dir / f"angle_k_{k}.kmb"
            candidate.to_file(path, format="kmb")
            report["loaders"][k]["candidate_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        shutil.copyfile(args.table, args.output_dir / "submission.npz")
        report["candidate_directory"] = str(args.output_dir)
    report["seconds"] = time.monotonic()-started
    report["peak_rss_mib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k:v for k,v in report.items() if k != "loaders"}, indent=2))


if __name__ == "__main__":
    main()
