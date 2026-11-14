"""Expand Syed's classical adaptive gauge without altering decoder arithmetic.

Derived from the Apache-2.0 adaptive_gauge64.py by Syed Asad Ali (2026).
The original sources and their frozen certificates are left untouched.
This module creates new, explicitly unverified whole-decoder candidates.

The selector considers all original labels first, followed by new labels.
Strict comparison of capped counts preserves the original choice on ties.
Consequently its number of zero scan masks cannot decrease pointwise.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time


def load_original(source_root):
    root = Path(source_root).resolve()
    work = root / "controller_work"
    for relative in ("work/round2/milestone152/source", "night_schedule", "night_root",
                     "night_converter", "night_c27/arithmetic", "night_c27/synthesis",
                     "night_c27/census", "night_c27/mask_gauge", "after_c5/arithmetic_t",
                     "after_v3/scan", "after_v3/k24/adaptive_gauge"):
        sys.path.insert(0, str(work / relative))
    import adaptive_gauge64
    return adaptive_gauge64


def _replace_larger(code, counter, best, label, candidate, comparison, label_bits):
    equal, greater, different = comparison
    code.store(equal, True)
    code.store(greater, False)
    code.store(different, False)
    for bit in (2, 1, 0):
        code.cx(counter[bit], different)
        code.cx(best[bit], different)
        code.cx(True, best[bit])
        code.push(equal)
        code.push(counter[bit])
        code.store(greater, True, control=best[bit])
        code.pop()
        code.pop()
        code.cx(True, best[bit])
        code.store(equal, False, control=different)
        code.store(different, False)
    code.push(greater)
    code.store(best, False)
    for source, target in zip(counter, best):
        code.cx(source, target)
    for bit in range(label_bits):
        code.store(label[bit], bool(candidate >> bit & 1))
    code.pop()
    code.store(equal, False)
    code.store(greater, False)


def select_expanded(original, builder, normalized_words, labels, *, stage=lambda _: None):
    if labels < 64 or labels > 4096 or labels & (labels - 1):
        raise ValueError("Candidate count must be a power of two between64and4096")
    if len(normalized_words) != 4025 or any(len(w) != 12 for w in normalized_words):
        raise ValueError("Expected4025twelve-bit classical residual words")
    label_bits = labels.bit_length() - 1
    entry_q = builder.num_allocated_qubits
    code = original.Classical(builder)
    counters = builder.alloc_bits(3 * labels)
    decoder = builder.alloc_bits(2 * labels - 1)
    work = builder.alloc_bits(3)
    code.store(counters, False)
    code.store(counters[0], True)  # virtual pivot contributes one zero atlabel0
    code.store(decoder[1:], False)
    code.store(work, False)
    initialized = code.instructions
    for ordinal, word in enumerate(normalized_words):
        code.store(decoder[0], True)
        for high in word[label_bits:]:
            code.store(decoder[0], False, control=high)
        for depth in range(label_bits):
            for parent in range((1 << depth) - 1, (1 << (depth + 1)) - 1):
                left, right = 2 * parent + 1, 2 * parent + 2
                code.and_into_zero(decoder[parent], word[label_bits - 1 - depth], decoder[right])
                code.cx(decoder[parent], decoder[left])
                code.cx(decoder[right], decoder[left])
        for candidate in range(labels):
            original._increment_saturated(code, counters[3*candidate:3*candidate+3],
                                          decoder[labels-1+candidate], work)
        code.store(decoder, False)
        if (ordinal + 1) % 512 == 0:
            stage({"stage": "expanded_histogram", "labels": labels, "words": ordinal + 1})
    histogram = code.instructions - initialized
    expected_per_word = 25 * labels + 7 - label_bits
    if histogram != 4025 * expected_per_word:
        raise AssertionError("Histogram instruction ledger mismatch")
    builder.free(decoder)
    best = work
    label = builder.alloc_bits(12)
    comparison = builder.alloc_bits(3)
    code.store(label, False)
    for source, target in zip(counters[:3], best):
        code.cx(source, target)
    for candidate in range(1, labels):
        _replace_larger(code, counters[3*candidate:3*candidate+3], best, label,
                        candidate, comparison, label_bits)
    builder.free(comparison)
    code.store(counters, False)
    code.store(best, False)
    builder.free(counters)
    builder.free(best)
    if builder.num_allocated_qubits != entry_q:
        raise AssertionError("Selector allocated quantum workspace")
    return label, {"labels": labels, "label_bits": label_bits, "cap": 7,
                   "selector_instructions": code.instructions,
                   "histogram_instructions": histogram,
                   "peak_classical_work_bits": 5 * labels + 2,
                   "additional_quantum_bits": 0, "static_toffoli_like": 0}


def initialize_builder(reserve_classical_through=0):
    import kickmix as km
    b = km.CircuitBuilder()
    S = [b.create_quantum_register(12, f"S{i}") for i in range(70)]
    E = [b.create_classical_register(12, f"E{i}") for i in range(4095)]
    if reserve_classical_through > 49140:
        b.alloc_bits(reserve_classical_through - 49140)
    return b, S, E


def open_expanded(original, builder, S, E, labels, fixed_pivot, *, stage=lambda _: None):
    import kickmix as km
    geometry = original.geometry()
    original.OriginalMasks.open_gauge(builder, S, E, geometry["plan"], stage=stage)
    normalization = sum(original.scale_mask(builder, E[i], geometry["inverses"][i])
                        for i in geometry["residual_indices"])
    selected, ledger = select_expanded(original, builder,
        [E[i] for i in geometry["residual_indices"]], labels, stage=stage)
    pivot = km.array([km.b(i) for i in fixed_pivot])
    if set(pivot) & set(selected):
        raise ValueError("Fixed pivot must not alias selector storage")
    builder.bit_store(pivot, False)
    builder.cx(selected, pivot)
    builder.bit_store(selected, False)
    builder.free(selected)
    width = ledger["label_bits"]
    for i in geometry["residual_indices"]:
        for bit in range(width):
            builder.cx(pivot[bit], E[i][bit])
    compensation = 0
    for scalar, syndrome in zip(geometry["coefficients"], S):
        for output in range(12):
            column = original.F.mul(scalar, 1 << output)
            for source in range(width):
                if column >> source & 1:
                    builder.cz(pivot[source], syndrome[output])
                    compensation += 1
    ledger.update(normalization_instructions=normalization,
                  compensation_CZ=compensation, pivot=[int(str(b)[1:]) for b in pivot])
    return pivot, ledger


def close_expanded(original, builder, E, pivot, labels, *, stage=lambda _: None):
    geometry = original.geometry()
    width = labels.bit_length() - 1
    for i in geometry["residual_indices"]:
        for bit in range(width):
            builder.cx(pivot[bit], E[i][bit])
    for i in geometry["residual_indices"]:
        original.scale_mask(builder, E[i], geometry["inverses"][i], inverse=True)
    builder.bit_store(pivot, False)
    original.OriginalMasks.close_gauge(builder, E, geometry["plan"], stage=stage)


def save_circuit(builder, path):
    c = builder.finish_circuit()
    c.to_file(str(path), format="kmb")
    result = {"instructions": len(c), "bits": c.num_bits, "qubits": c.num_qubits,
              "static_toffoli_like": c.operation_statistics().num_toffoli_like,
              "bytes": path.stat().st_size}
    with path.open("rb") as f:
        result["sha256"] = hashlib.file_digest(f, "sha256").hexdigest()
    return result


def build_pieces(original, output, labels, reserved=154157):
    output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    def progress(row):
        if isinstance(row, dict) and (row.get("blocks", 0) % 20 == 0 or "labels" in row):
            print(json.dumps(row), flush=True)
    b, S, E = initialize_builder()
    record = original.open_gauge(b, S, E, stage=progress)
    fixed_pivot = [int(str(bit)[1:]) for bit in record.pivot]
    baseline_prefix = save_circuit(b, output / "gauge64_prefix.kmb")
    original.close_gauge(b, E, record, stage=progress)
    baseline_pair = save_circuit(b, output / "gauge64_pair.kmb")
    del b
    b, S, E = initialize_builder(reserved)
    pivot, ledger = open_expanded(original, b, S, E, labels, fixed_pivot, stage=progress)
    expanded_prefix = save_circuit(b, output / f"gauge{labels}_prefix.kmb")
    close_expanded(original, b, E, pivot, labels, stage=progress)
    expanded_pair = save_circuit(b, output / f"gauge{labels}_pair.kmb")
    del b
    report = {"status": "BUILT_GAUGE_PIECES_NOT_DECODER_VERIFIED", "labels": labels,
              "fixed_pivot": fixed_pivot, "reserved_classical_through": reserved,
              "baseline_prefix": baseline_prefix, "baseline_pair": baseline_pair,
              "expanded_prefix": expanded_prefix, "expanded_pair": expanded_pair,
              "selector_ledger": ledger, "elapsed_seconds": time.perf_counter() - started,
              "splice_contract": "Compare baseline prefix and suffix instructions exactly before replacing. Suffix is pair[prefix_instructions:]. Preserve original registers and decoder body; update maximum classical bit count.",
              "scope": "No old frozen certificate is reused as evidence for the new candidate."}
    (output / "gauge_pieces.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-root", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--labels", type=int, default=128)
    ap.add_argument("--reserve-classical-through", type=int, default=154157)
    args = ap.parse_args()
    original = load_original(args.source_root)
    build_pieces(original, args.out_dir, args.labels, args.reserve_classical_through)


if __name__ == "__main__":
    main()
