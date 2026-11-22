"""Run strict, reproducible resource comparisons on small Boolean oracles."""
from __future__ import annotations
import argparse
import json
import random
from pathlib import Path

from .reversible import verify_oracle
from .synthesis import search_affine, search_joint_affine, synthesize


def example(name: str, n: int, outputs: int, seed: int):
    if name == "affine-product":
        if n != 4:
            raise ValueError("affine-product requires --inputs 4")
        return (tuple(
            ((((x >> 0) ^ (x >> 1)) & 1) &
             (((x >> 2) ^ (x >> 3)) & 1))
            for x in range(16)
        ),)
    if name == "shared-cubic":
        if n != 4:
            raise ValueError("shared-cubic requires --inputs 4")
        return (
            tuple((x & 1) & ((x >> 1) & 1) &
                  (((x >> 2) ^ (x >> 3)) & 1) for x in range(16)),
            tuple(
                (((x & 1) & ((x >> 1) & 1) &
                  (((x >> 2) ^ (x >> 3)) & 1)) ^
                 (((x >> 2) & 1) & ((x >> 3) & 1)))
                for x in range(16)
            ),
        )
    if name == "random":
        rng = random.Random(seed)
        return tuple(
            tuple(rng.randrange(2) for _ in range(1 << n))
            for _ in range(outputs)
        )
    raise ValueError("Unknown sample")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=["affine-product", "shared-cubic", "random"],
                        default="affine-product")
    parser.add_argument("--inputs", type=int, default=4)
    parser.add_argument("--outputs", type=int, default=2)
    parser.add_argument("--seed", type=int, default=20261122)
    parser.add_argument("--affine-depth", type=int, default=2)
    parser.add_argument("--beam", type=int, default=12)
    parser.add_argument("--ancilla-limit", type=int, default=None)
    parser.add_argument("--joint", action="store_true",
                        help="Also search invertible input AND output GF(2) bases")
    parser.add_argument("--emit", type=Path, default=None,
                        help="Save winning quantum circuit as JSON")
    parser.add_argument("--train", action="store_true",
                        help="Also run optional PyTorch trainable-Boolean-DAG experiment")
    parser.add_argument("--train-steps", type=int, default=400)
    parser.add_argument("--train-restarts", type=int, default=3)
    parser.add_argument("--train-gates", type=int, default=12)
    args = parser.parse_args(argv)

    tables = example(args.case, args.inputs, args.outputs, args.seed)
    baseline = synthesize(tables, args.inputs, method="baseline")
    shared = synthesize(tables, args.inputs, method="shared",
                        max_ancillas=args.ancilla_limit)
    optimized = search_affine(
        tables, args.inputs, max_depth=args.affine_depth, beam_width=args.beam,
        max_ancillas=args.ancilla_limit
    )
    validation = verify_oracle(optimized.circuit, tables)
    report = {
        "case": args.case,
        "n_inputs": args.inputs,
        "n_outputs": len(tables),
        "truth_tables_le_index": ["0x" + format(
            sum(int(v) << i for i, v in enumerate(table)), "x"
        ) for table in tables],
        "baseline": baseline.circuit.resources().as_dict(),
        "shared": shared.circuit.resources().as_dict(),
        "optimized": optimized.circuit.resources().as_dict(),
        "method": optimized.method,
        "basis_cnots": [list(pair) for pair in optimized.basis_cnots],
        "validation": validation,
        "official_kaggle_scoring": False,
    }
    winner = optimized.circuit
    if args.joint:
        joint = search_joint_affine(
            tables, args.inputs, max_depth=args.affine_depth, beam_width=args.beam,
            max_ancillas=args.ancilla_limit
        )
        report["joint"] = joint.as_dict()
        report["joint_validation"] = verify_oracle(joint.circuit, tables)
        old_cost = optimized.circuit.resources()
        new_cost = joint.circuit.resources()
        if (new_cost.ccx, new_cost.ancillas, new_cost.cx, new_cost.depth) < (
            old_cost.ccx, old_cost.ancillas, old_cost.cx, old_cost.depth
        ):
            winner = joint.circuit
            report["winner"] = joint.method
        else:
            report["winner"] = optimized.method
    if args.train:
        from .learn import fit_truth_tables
        learned = fit_truth_tables(
            tables, args.inputs, gates=args.train_gates,
            steps=args.train_steps, restarts=args.train_restarts, seed=args.seed,
        )
        report["training"] = learned.as_dict()
    if args.emit:
        args.emit.write_text(
            json.dumps(winner.to_json(), indent=2) + "\n",
            encoding="utf-8"
        )
    print(json.dumps(report, indent=2, sort_keys=True))
    return report


if __name__ == "__main__":
    main()
