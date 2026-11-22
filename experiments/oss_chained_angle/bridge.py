#!/usr/bin/env python3
"""Run the upstream Apache-2.0 chained_and on actual ANGLE truth tables.

This is a prescreen, NOT a 128Q KMB emitter or an official score.
Original upstream source is vendored unchanged under third_party/manwithacat/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "third_party" / "manwithacat"))
import chained_and as ca  # noqa: E402


def analyze(path: Path, write_cnf: Path | None = None, cnf_rows: int = 2,
            k: int = 4, chained: int = 1) -> dict:
    target = ca.Target.from_json(path)
    full = target.full
    # No general_lower_bound() with 35 outputs: it enumerates 2**m combinations.
    bound = ca.rank2_lower_bound(target)
    circuit, bits = ca.construct_rank2(target)
    full_count = 0
    for row, ((care, truth), setting) in enumerate(zip(target.rows, bits)):
        if care != full:
            assert setting is None
            continue
        assert setting is not None
        got = circuit.evaluate(*setting)
        assert ca.row_met(got, care, truth, full), f"row {row} disagrees"
        full_count += 1
    report = {
        "source": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "rows": len(target.rows),
        "full_rows_checked": full_count,
        "partial_rows_not_synthesized": len(target.rows) - full_count,
        "outputs": target.m,
        "low_bits": target.n,
        "rank2_affine_rank": bound["affine_rank"],
        "rank2_depth1_lower_bound": bound["bound"],
        "rank2_per_output_construction_ANDs": circuit.k,
        "construction_verified_modulo_row_constants_on_full_rows": True,
        "scope": "GF2 functional prescreen only, no high-cache costs, no KMB, no HMR check",
    }
    if write_cnf is not None:
        assert 0 <= chained < k
        # Explicitly use encode_shape; encode_cnf(depth=2) is unsupported upstream.
        cnf = ca.encode_shape(target, k, chained, rows=range(min(cnf_rows, len(target.rows))),
                              gauge=True, lex=True, force_chain=True)
        write_cnf.parent.mkdir(parents=True, exist_ok=True)
        write_cnf.write_text(cnf.dimacs())
        report["small_shape_cnf"] = {
            "path": str(write_cnf), "rows": min(cnf_rows, len(target.rows)),
            "k": k, "chained": chained, "vars": cnf.nv,
            "clauses": len(cnf.clauses), "xor_constraints": len(cnf.xors),
            "status": "encoded only; satisfiability not established",
        }
    return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument("targets", nargs="*", type=Path)
    p.add_argument("--out", type=Path, default=Path("oss_chained_report.json"))
    p.add_argument("--cnf", type=Path)
    p.add_argument("--rows", type=int, default=2)
    p.add_argument("--k", type=int, default=4)
    p.add_argument("--chained", type=int, default=1)
    a = p.parse_args()
    paths = a.targets or [Path(__file__).with_name("fixture_k8_4out_8rows.json")]
    reports = [analyze(path, a.cnf if i == 0 else None, a.rows, a.k, a.chained)
               for i, path in enumerate(paths)]
    # Positive control: a real chained (depth 2) circuit from the original code.
    witness = ca.copy_gate_example()
    assignments = [(0,0), (1,1), (2,0), (3,3)]
    toy = ca.image_target(witness, assignments)
    check = ca.verify(witness, toy, rowbits=assignments)
    assert check["all_pass"] and witness.depth() == 2
    out = {"upstream": "manwithacat/vqcc-tools, Apache-2.0, chained_and 0.3.0",
           "positive_control": "2-AND chained exact witness PASS",
           "targets": reports,
           "external_sat_binary": {s: bool(shutil.which(s)) for s in ("kissat","cadical")},
           "official_kickmix": False,
           "scored_new_KMB": False}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out,indent=2))


if __name__ == "__main__":
    main()
