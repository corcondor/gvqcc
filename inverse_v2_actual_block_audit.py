"""Reproduce the exact audit of one extracted block of DQI821bf8d157c0.

The checked block is the complete pure multiplier immediately before the
24-SWAP burst at legacy index10534482. The block was extracted from the
actual KMB through the condition-preserving audit. This script does not
modify the KMB or assert a full-circuit score improvement.
"""
from pathlib import Path
import json

import inverse_v2_optimize as arithmetic
from symbolic_block_analyze import analyze


LEFT = list(range(432, 456))
RIGHT = list(range(840, 864))
OUTPUTS = list(range(865, 889))
FIELD_ORDER = [868,867,865,866,872,871,869,870,876,875,885,886,
               880,879,881,882,874,887,888,883,884,873,878,877]
EXPECTED_BLOCK_SHA256 = "f97f2a437fb9b538d85608ce5ae5393c87e5f8b8dcab750ca8af9eae754b5aac"


def mul24(x, y):
    x0, x1, y0, y1 = x & 4095, x >> 12, y & 4095, y >> 12
    aa = arithmetic.mul(x0, y0, 12)
    bb = arithmetic.mul(x1, y1, 12)
    return ((aa ^ arithmetic.mul(2048, bb, 12)) |
            ((arithmetic.mul(x0 ^ x1, y0 ^ y1, 12) ^ aa) << 12))


def main():
    directory = Path(__file__).parent
    text = directory.joinpath("inverse_v2_actual_eea_product.kmx").read_text()
    inputs = LEFT+RIGHT
    r = analyze(text, [f"q{q}" for q in inputs], [f"q{q}" for q in OUTPUTS],
                [f"q{q}" for q in OUTPUTS], [])
    assert r["block_sha256"] == EXPECTED_BLOCK_SHA256
    assert r["gate_counts"] == {"CCX": 99, "CX": 6122}
    assert r["all_inputs_restored"]
    assert r["phase_anf"]["term_count"] == 0
    assert r["affine_compression"]["rank"] == 24
    polynomials = [set(r["output_anf"][f"q{q}"]["monomial_masks"]) for q in FIELD_ORDER]
    assert all(m.bit_count() == 2 and (m & ((1 << 24)-1)).bit_count() == 1
               for terms in polynomials for m in terms)
    for i in range(24):
        for j in range(24):
            m = (1 << i) | (1 << (24+j))
            actual = sum((m in terms) << bit for bit, terms in enumerate(polynomials))
            x = 1 << i
            conjugate = x ^ (x >> 12)
            assert actual == mul24(conjugate, 1 << j), (i, j)
    # Track initial output variables separately to prove arbitrary-target
    # XOR, and rank the existing99quadratic product forms.
    parities = {q: 1 << i for i, q in enumerate(inputs)}
    output_rows = {q: 1 << i for i, q in enumerate(OUTPUTS)}
    forms = []
    for line in text.splitlines():
        op, *args = line.split()
        q = [int(x[1:]) for x in args]
        if op == "CX":
            c, t = q
            if t in parities:
                assert c in parities
                parities[t] ^= parities[c]
            else:
                assert c in output_rows and t in output_rows
                output_rows[t] ^= output_rows[c]
        elif op == "CCX":
            a, b, t = q
            assert a in parities and b in parities and t in output_rows
            u, v = parities[a], parities[b]
            if u >> 24:
                u, v = v, u
            assert u and u < (1 << 24) and v and not (v & ((1 << 24)-1))
            v >>= 24
            forms.append(sum(v << (24*i) for i in range(24) if (u >> i) & 1))
        else:
            raise AssertionError(op)
    assert all(parities[q] == 1 << i for i, q in enumerate(inputs))
    assert all(output_rows[q] == 1 << i for i, q in enumerate(OUTPUTS))
    pivots = {}
    for row in forms:
        while row:
            p = row.bit_length()-1
            if p not in pivots:
                pivots[p] = row
                break
            row ^= pivots[p]
    assert len(forms) == len(pivots) == 99
    report = {
        "status": "PASS_EXACT_ACTUAL_BLOCK",
        "legacy_start_inclusive": 10528261, "legacy_stop_exclusive": 10534482,
        "kmb_start_inclusive": 12581893, "kmb_stop_exclusive": 12588114,
        "block_sha256": r["block_sha256"], "ccx_count": 99, "cx_count": 6122,
        "input_left": LEFT, "input_right": RIGHT, "output_qubits_in_field_order": FIELD_ORDER,
        "field12_modulus": 0x1053, "field24_relation": "t^2+t+2048=0 over GF(2^12)",
        "operation": "output ^= conjugate(left)*right; inputs restored",
        "basis_pairs_checked": 576, "all_input_pairs_proven_by_bilinearity": True,
        "output_affine_rank": 24, "simple_12bit_linear_output_compression_possible": False,
        "all_inputs_restored": True, "arbitrary_target_xor_proven": True,
        "existing_product_form_span_rank": 99, "existing_product_forms_count": 99,
        "limitations": ["No impossibility claim for nonlinear or in-place resynthesis.",
                        "No full-circuit optimization or score improvement."]}
    directory.joinpath("inverse_v2_actual_eea_product_certificate.json").write_text(json.dumps(report, indent=2)+"\n")
    directory.joinpath("inverse_v2_actual_eea_product_analysis.json").write_text(json.dumps(r, indent=2)+"\n")
    print(json.dumps({k: report[k] for k in ("status", "ccx_count", "basis_pairs_checked", "output_affine_rank", "existing_product_form_span_rank")}))


if __name__ == "__main__":
    main()
