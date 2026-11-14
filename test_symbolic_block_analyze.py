"""Compare exact symbolic propagation to independent exhaustive truth tables."""
import json
from pathlib import Path
from boolean_block_analyze import analyze as exhaustive
from symbolic_block_analyze import analyze as symbolic


def main():
    root = Path(__file__).resolve().parent
    fixtures = root / "boolean_block_testfixtures"
    checks = []
    for name, n in [("frobenius_six_inputs", 6),
                    ("nonlinear_six_inputs_rank_twelve", 6), ("gf12_power_1_pure", 12)]:
        text = (fixtures / (name + ".kmx")).read_text()
        ins = [f"q{i}" for i in range(n)]
        outs = [f"q{i}" for i in range(n, n + 12)]
        a = exhaustive(text, ins, outs, outs, [])
        b = symbolic(text, ins, outs, outs, [])
        assert a["output_anf"] == b["output_anf"]
        assert a["phase_anf"] == b["phase_anf"]
        assert a["all_inputs_restored"] == b["all_inputs_restored"]
        assert a["affine_compression"]["rank"] == b["affine_compression"]["rank"]
        checks.append({"case": name, "assignments_crosschecked": 1 << n,
                       "rank": b["affine_compression"]["rank"],
                       "max_degree": b["max_output_degree"]})
    for text, ins, outs, zero, one in [
        ("CCX q0 q1 q2\nZ q2\nCCX q0 q1 q2\n", ["q0", "q1"], ["q2"], ["q2"], []),
        ("CSWAP q0 q1 q2\nCZ q1 q2\nNEG\n", ["q0", "q1"], ["q2"], [], ["q2"]),
    ]:
        a = exhaustive(text, ins, outs, zero, one)
        b = symbolic(text, ins, outs, zero, one)
        assert a["output_anf"] == b["output_anf"] and a["phase_anf"] == b["phase_anf"]
        checks.append({"case": "phase_or_cswap", "assignments_crosschecked": 1 << len(ins)})
    ins = [f"q{i}" for i in range(24)]
    outs = [f"q{i}" for i in range(24, 48)]
    text = "\n".join(f"CCX q{i} q{12+i} q{24+i}\nCX q{24+i} q{36+i}" for i in range(12)) + "\n"
    b = symbolic(text, ins, outs, outs, [])
    assert b["affine_compression"]["rank"] == 12
    assert b["max_output_degree"] == 2 and b["all_inputs_restored"]
    (fixtures / "bilinear_24_inputs.kmx").write_text(text)
    (fixtures / "bilinear_24_inputs_symbolic_result.json").write_text(json.dumps(b, indent=2) + "\n")
    checks.append({"case": "24_inputs_24_outputs_bilinear", "rank": 12,
                   "max_degree": 2, "enumeration_used": False})
    for kwargs in [{"max_degree": 1}, {"max_terms": 1}, {"max_products": 1}]:
        try:
            symbolic("CX q0 q3\nCX q1 q3\nCCX q2 q3 q4\n", ["q0", "q1", "q2"],
                     ["q3", "q4"], ["q3", "q4"], [], **kwargs)
        except ValueError as exc:
            assert "aborted" in str(exc)
        else:
            raise AssertionError(kwargs)
    checks.append({"case": "resource_caps_fail_without_approximation", "limits_checked": 3})
    for text in ["HMR q2 b0", "CCX q0 q9 q2", "CX q0 q2 if b0", "PUSH_CONDITION b0"]:
        try:
            symbolic(text, ["q0", "q1"], ["q2"], ["q2"], [])
        except ValueError:
            pass
        else:
            raise AssertionError(text)
    result = {"status": "PASS", "user_block_tested": False, "checks": checks}
    (root / "symbolic_block_validation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
