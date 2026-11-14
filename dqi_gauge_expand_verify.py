"""Native checks and a discrete monotonicity certificate for expanded gauges."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import time

from dqi_gauge_expand import load_original, select_expanded


def select_oracle(words, labels):
    counts = [0] * labels
    counts[0] = 1
    for word in words:
        if int(word) < labels:
            counts[int(word)] += 1
    selected = 0
    best = min(7, counts[0])
    for label in range(1, labels):
        score = min(7, counts[label])
        if score > best:
            selected, best = label, score
    return selected, counts[selected]


def monotonicity_certificate():
    # If a newly added label replaces the incumbent then its capped count
    # is strictly larger. The incumbent therefore had an exact count<7;
    # the replacement's exact count is strictly larger. Otherwise the
    # original label remains unchanged. Applying this once per newlabel
    # proves the property for any number of added labels and everyinput.
    tested = 0
    for old in range(4027):
        for new in range(4026):
            if min(7, new) > min(7, old):
                if new <= old:
                    raise AssertionError("Nonmonotone capped strict replacement")
            tested += 1
    return {"status": "PASS", "exact_count_pairs": tested,
            "count_domain": "old0..4026; new0..4025", "cap": 7,
            "argument": "Original labels are processed first. A later label replaces only on strictly larger capped count. Then the old count is below7 and the new exact count is larger. Ties leave the original label unchanged.",
            "conclusion": "Number of zero candidate scan masks never decreases for any original classical masks."}


def native_selector_check(original, labels):
    import kickmix as km
    import numpy as np
    started = time.perf_counter()
    rng = np.random.default_rng(20261114)
    cases = []
    names = []
    for winner in range(labels):
        row = np.full(4025, 4095, dtype=np.uint16)
        row[:8] = winner
        cases.append(row)
        names.append(f"forced_winner_{winner}")
    for winner in (0, 1, 63, labels - 1, 4095):
        cases.append(np.full(4025, winner, dtype=np.uint16))
        names.append(f"all_{winner}")
    for old_count, new_count in ((0, 1), (1, 1), (6, 7), (7, 8), (7, 100), (4000, 20)):
        row = np.full(4025, 4095, dtype=np.uint16)
        row[:old_count] = 63
        row[old_count:old_count + new_count] = labels - 1
        cases.append(row)
        names.append(f"old63_{old_count}_new_{new_count}")
    for case in range(64):
        cases.append(rng.integers(0, 4096, 4025, dtype=np.uint16))
        names.append(f"uniform_{case}")
    values = np.array(cases, dtype=np.uint16)
    expected = np.array([select_oracle(row, labels)[0] for row in values], dtype=np.uint16)
    old_selected = [select_oracle(row, 64) for row in values]
    new_selected = [select_oracle(row, labels) for row in values]
    if any(new[1] < old[1] for old, new in zip(old_selected, new_selected)):
        raise AssertionError("A fixture lost zeros")
    b = km.CircuitBuilder()
    words = [b.alloc_bits(12) for _ in range(4025)]
    output, ledger = select_expanded(original, b, words, labels)
    circuit = b.finish_circuit()
    if circuit.num_qubits != 0 or circuit.operation_statistics().num_toffoli_like != 0:
        raise AssertionError("Classical selector used quantum resources")
    input_wires = km.array([bit for word in words for bit in word])
    expected_bits = (((values[:, :, None] >> np.arange(12, dtype=np.uint16)) & 1)
                     .reshape(len(values), -1).astype(bool).T.copy())
    sim = km.Simulator(batch_size=len(values), seed=20261114, debug_print=False)
    sim.write_across_shots(input_wires, expected_bits)
    sim.do(circuit)
    result_bits = sim.read_across_shots(output)
    result = (result_bits.T.astype(np.uint16) * (1 << np.arange(12, dtype=np.uint16))).sum(axis=1)
    if not np.array_equal(result, expected):
        failures = np.flatnonzero(result != expected)
        raise AssertionError([(names[i], int(result[i]), int(expected[i])) for i in failures[:8]])
    if not np.array_equal(sim.read_across_shots(input_wires), expected_bits):
        raise AssertionError("Selector changed input masks")
    output_ids = {int(str(bit)[1:]) for bit in output}
    work = km.array([km.b(i) for i in range(48300, circuit.num_bits) if i not in output_ids])
    if sim.read_across_shots(work).any():
        raise AssertionError("Selector left classical work bits nonzero")
    if sim.read_phase_flipped_across_shots().any():
        raise AssertionError("Classical selector changed quantum phase")
    return {"status": "PASS", "labels": labels, "fixtures": len(values),
            "forced_winners": labels, "qubits": circuit.num_qubits,
            "static_toffoli_like": circuit.operation_statistics().num_toffoli_like,
            "ledger": ledger, "input_masks_preserved": True, "work_bits_cleared": True,
            "fixture_sha256": hashlib.sha256(values.tobytes()).hexdigest(),
            "elapsed_seconds": time.perf_counter() - started}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-root", type=Path, required=True)
    ap.add_argument("--labels", type=int, default=128)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    original = load_original(args.source_root)
    try:
        distribution_version = importlib.metadata.version("kickmix")
    except importlib.metadata.PackageNotFoundError:
        distribution_version = "competition-bundled"
    report = {"monotonicity": monotonicity_certificate(),
              "native_selector": native_selector_check(original, args.labels),
              "kickmix_distribution_version": distribution_version,
              "scope": "Selector and pointwise scan-cost certificate only. Whole-decoder phase/correctness and score require verification after splicing."}
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
