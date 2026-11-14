"""Meaningful fixtures for the pure-block analyzer; no user block is included."""
from pathlib import Path
import json

from boolean_block_analyze import analyze
from inverse_specialized import gf_frobenius, gf_mul, make_power_map


def main():
    root = Path(__file__).resolve().parent
    fixtures = root / "boolean_block_testfixtures"
    fixtures.mkdir(exist_ok=True)
    inputs = [f"q{i}" for i in range(6)]
    outputs = [f"q{i}" for i in range(6, 18)]
    summaries = []

    # A six-dimensional linear subspace, embedded by a genuine GF(2^12)
    # Frobenius map, plus a nonzero affine offset.
    lines = []
    for i in range(6):
        column = gf_frobenius(1 << i, 3)
        lines += [f"CX q{i} q{6+j}" for j in range(12) if column & (1 << j)]
    lines += ["X q6", "X q17"]
    text = "\n".join(lines) + "\n"
    (fixtures / "frobenius_six_inputs.kmx").write_text(text)
    r = analyze(text, inputs, outputs, outputs, [])
    assert r["all_inputs_restored"]
    assert r["image_count"] == 64 and r["output_map_injective"]
    assert r["affine_compression"]["rank"] == 6
    assert len(r["affine_compression"]["zero_output_wires_after_network"]) == 6
    for row in r["truth_table"]:
        assert row["output"] == gf_frobenius(row["input"], 3) ^ 1 ^ (1 << 11)
    (fixtures / "frobenius_six_inputs_result.json").write_text(json.dumps(r, indent=2) + "\n")
    summaries.append({"name": "frobenius_six_inputs", "assignments": 64,
                      "image_count": 64, "affine_rank": 6})

    # Six inputs can have twelve linearly independent output functions.
    lines = [f"CX q{i} q{6+i}" for i in range(6)]
    lines += [f"CCX q{i} q{(i+1)%6} q{12+i}" for i in range(6)]
    text = "\n".join(lines) + "\n"
    (fixtures / "nonlinear_six_inputs_rank_twelve.kmx").write_text(text)
    r = analyze(text, inputs, outputs, outputs, [])
    assert r["all_inputs_restored"]
    assert r["image_count"] == 64
    assert r["affine_compression"]["rank"] == 12
    assert max(v["degree"] for v in r["output_anf"].values()) == 2
    summaries.append({"name": "nonlinear_six_inputs_rank_twelve", "assignments": 64,
                      "image_count": 64, "affine_rank": 12})

    # Check phase, not only output bits: this block implements CZ on its input.
    r = analyze("CCX q0 q1 q2\nZ q2\nCCX q0 q1 q2\n",
                ["q0", "q1"], ["q2"], ["q2"], [])
    assert r["affine_compression"]["rank"] == 0
    assert r["phase_anf"]["monomial_masks"] == [3]
    assert [v["phase_sign"] for v in r["truth_table"]] == [1, 1, 1, -1]
    summaries.append({"name": "phase_is_preserved_in_analysis", "assignments": 4})

    # Existing experimental arithmetic primitive, independently checked against
    # scalar finite-field multiplication on all 4096 inputs.
    spec = make_power_map(1)
    text = "\n".join(("CX" if len(g) == 2 else "CCX") + " " +
                     " ".join(f"q{i}" for i in g) for g in spec["gates"]) + "\n"
    (fixtures / "gf12_power_1_pure.kmx").write_text(text)
    r = analyze(text, [f"q{i}" for i in range(12)],
                [f"q{i}" for i in range(12, 24)],
                [f"q{i}" for i in range(12, 24)], [])
    assert r["all_inputs_restored"]
    for row in r["truth_table"]:
        x = row["input"]
        assert row["output"] == gf_mul(x, gf_frobenius(x, 1))
        assert row["phase_sign"] == 1
    assert r["affine_compression"]["rank"] == 12
    assert r["image_count"] == 1366
    summaries.append({"name": "existing_gf12_power_1", "assignments": 4096,
                      "image_count": r["image_count"], "affine_rank": 12,
                      "gate_counts": r["gate_counts"]})

    # The analyzer must fail closed on missing context and nonunitary control.
    rejected = ["HMR q2 b0", "R q2", "CX q0 q2 if b0", "PUSH_CONDITION b0",
                "POP_CONDITION", "REGISTER r0 \"input\"", "CCX q0 q9 q2",
                "CX q0 q0", "Z_POW q2 0.25"]
    for text in rejected:
        try:
            analyze(text, ["q0", "q1"], ["q2"], ["q2"], [])
        except ValueError:
            pass
        else:
            raise AssertionError(f"must reject: {text}")
    # Constant-one context and arbitrary changes to input wires are reported.
    r = analyze("CSWAP q0 q1 q2\n", ["q0", "q1"], ["q2"], [], ["q2"])
    assert not r["all_inputs_restored"]
    assert [x["output"] for x in r["truth_table"]] == [1, 0, 1, 1]
    summaries.append({"name": "reject_unsupported_or_ungrounded", "rejections": len(rejected)})
    result = {"status": "PASS", "user_block_tested": False, "tests": summaries}
    (root / "boolean_block_validation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
