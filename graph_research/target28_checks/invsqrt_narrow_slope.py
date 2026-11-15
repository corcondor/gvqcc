"""Use a reversible carry chain in the loaded slope word, with a clean carry."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import kickmix as km

from multiplier_fixture import check


def controlled_add(builder, a, target, enable, carry, borrow=()):
    """Add enable*a to a target with one more bit than a, restoring a.

    Use a future clean output wire for a carry when one is available.
    Omit that external carry's inverse CCX using a corrected measurement.
    """
    assert len(target) == len(a) + 1 and a
    builder.init_and(a[0], target[0], carry)
    clean = iter(borrow)
    previous = carry
    trace = []
    for source, dest in zip(a[1:], target[1:-1]):
        external = next(clean, None)
        trace.append((source, dest, previous, external))
        if external is None:
            builder.cx(source, dest)
            builder.cx(source, previous)
            builder.ccx(dest, previous, source)
            previous = source
        else:
            builder.cx(previous, source)
            builder.cx(previous, dest)
            builder.init_and(source, dest, external)
            builder.cx(previous, external)
            builder.cx(previous, dest)
            builder.cx(previous, source)
            previous = external
    builder.ccx(enable, previous, target[-1])
    for source, dest, previous, external in reversed(trace):
        if external is None:
            builder.ccx(dest, previous, source)
            builder.ccx(enable, previous, dest)
            builder.cx(source, previous)
            builder.cx(source, dest)
        else:
            builder.cx(previous, source)
            builder.cx(previous, dest)
            builder.cx(previous, external)
            builder.del_and(source, dest, external)
            builder.ccx(enable, source, dest)
            builder.cx(previous, dest)
            builder.cx(previous, source)
    builder.del_and(a[0], target[0], carry)
    builder.ccx(enable, a[0], target[0])


def emit(width_a, width_b, cut, borrow_future_output=False):
    builder = km.CircuitBuilder()
    a = builder.create_quantum_register(width_a, "a")
    b = builder.create_quantum_register(width_b, "b")
    out = builder.create_quantum_register(width_a + width_b - cut, "product")
    carry = builder.alloc_qubits(1)[0]
    for j, enable in enumerate(b):
        lo = max(0, cut - j)
        if lo < width_a:
            stop = j + width_a + 1 - cut
            controlled_add(builder, list(a[lo:]), list(out[j+lo-cut:stop]),
                           enable, carry, out[stop:] if borrow_future_output else ())
    # Keep the carry allocated through finish for use as a caller-owned wire.
    return builder.finish_circuit()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tables", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-x", type=int, default=3_133_452)
    parser.add_argument("--borrow-future-output", action="store_true")
    args = parser.parse_args()
    design = next(row for row in json.loads(args.tables.read_text())["summaries"]
                  if row["design"]["prefix_bits"] == 8)
    a = max(max(t["slope"]).bit_length() for t in design["tables"])
    b = 21 - design["design"]["prefix_bits"]
    cut = design["truncate_low_product_diagonals"]
    circ = emit(a, b, cut, args.borrow_future_output)
    args.output.mkdir(exist_ok=True)
    path = args.output / "slope.kmb"
    circ.to_file(path, format="kmb")
    reloaded = km.Circuit.from_file(path, format="kmb")
    row = check(reloaded, design, cut, args.max_x)
    row["source"] = str(args.tables)
    row["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    assert not any(row[name] for name in ("wrong_output", "wrong_inputs",
                                         "dirty_workspace", "bad_phase"))
    (args.output / "receipt.json").write_text(json.dumps(row, indent=2) + "\n")
    print(json.dumps(row), flush=True)


if __name__ == "__main__":
    main()
