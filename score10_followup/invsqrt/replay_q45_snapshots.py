#!/usr/bin/env python3
"""Generate or verify q45-screen snapshots with the native KickMix simulator."""
import argparse
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import kickmix as km
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    seed_input = parser.add_mutually_exclusive_group(required=True)
    seed_input.add_argument("--snapshot", type=Path)
    seed_input.add_argument("--inputs", type=Path)
    parser.add_argument("--write-snapshot", type=Path)
    parser.add_argument("--kmx", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    raw = args.kmx.read_bytes()
    snapshots = json.loads((args.snapshot or args.inputs).read_text())
    assert snapshots["source_sha256"] in {
        hashlib.sha256(raw).hexdigest(),
        hashlib.sha256(raw.removesuffix(b"\n")).hexdigest(),
    }
    assert hashlib.sha256(json.dumps(snapshots["samples"]).encode()).hexdigest() == snapshots["sample_inputs_sha256"]
    lines = raw.decode().splitlines(keepends=True)
    samples = np.array(snapshots["samples"], dtype=np.uint32)
    inputs = ((samples[None, :] >> np.arange(22, dtype=np.uint32)[:, None]) & 1).astype(bool)
    seeds = [202611151309, 202611151310]
    rows = []
    expected_states = snapshots.get("states_hex", {})
    actual_states = {}
    for cut in ("10984", "14888", "16799", "17202", "17287"):
        expected = expected_states.get(cut)
        with TemporaryDirectory() as work:
            path = Path(work) / "prefix.kmx"
            path.write_text("".join(lines[:int(cut)]))
            prefix = km.Circuit.from_file(path)
        all_wires = km.array([km.q(q) for q in range(46)])
        for seed in seeds:
            sim = km.Simulator(batch_size=len(samples), seed=seed)
            sim.use_same_registers_as(prefix)
            sim.write_across_shots(km.array(list(prefix.register_data["x"])), inputs)
            sim.do(prefix)
            states = np.asarray(sim.read_across_shots(all_wires))
            packed = np.packbits(states, axis=1, bitorder="little")
            actual = [int.from_bytes(row.tobytes(), "little") for row in packed]
            if expected is None:
                expected = [hex(value) for value in actual]
            mismatches = sum(a != int(b, 16) for a, b in zip(actual, expected, strict=True))
            rows.append(dict(cut=int(cut), seed=seed, wire_mismatches=mismatches))
        actual_states[cut] = [hex(value) for value in actual]
        print(cut, rows[-2:], flush=True)
    args.out.write_text(json.dumps({"samples": len(samples), "rows": rows}, indent=2) + "\n")
    assert not any(row["wire_mismatches"] for row in rows)
    if args.write_snapshot:
        snapshots["states_hex"] = actual_states
        args.write_snapshot.write_text(json.dumps(snapshots) + "\n")


if __name__ == "__main__":
    main()
