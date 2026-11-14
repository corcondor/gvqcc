"""No-copy quadratic GF(2^12) power maps, with explicit CX/CCX circuits.

Experimental replacement primitive for Itoh--Tsujii doubling steps.
This is a standalone arithmetic experiment, not a patched competition entry.
Qubits 0..11 are the preserved input; 12..23 are the XOR output.
No other quantum work bits are used. The input is temporarily changed by
invertible linear maps, then restored. Circuits are valid for arbitrary targets.
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path

DEGREE = 12
MODULUS = 0x1053  # x^12 + x^6 + x^4 + x + 1


def gf_mul(a: int, b: int) -> int:
    r = 0
    while b:
        if b & 1:
            r ^= a
        b >>= 1
        a <<= 1
        if a & 0x1000:
            a ^= MODULUS
    return r


def gf_frobenius(a: int, k: int) -> int:
    for _ in range(k % 12):
        a = gf_mul(a, a)
    return a


def poly_eval(p: int, x: int) -> int:
    r = 0
    for i in range(p.bit_length() - 1, -1, -1):
        r = gf_mul(r, x) ^ ((p >> i) & 1)
    return r


def invert_rows(rows: list[int]) -> list[int]:
    n = len(rows)
    work = [r | (1 << (n + i)) for i, r in enumerate(rows)]
    for c in range(n):
        pivot = next(i for i in range(c, n) if (work[i] >> c) & 1)
        work[c], work[pivot] = work[pivot], work[c]
        for i in range(n):
            if i != c and ((work[i] >> c) & 1):
                work[i] ^= work[c]
    assert [w & ((1 << n) - 1) for w in work] == [1 << i for i in range(n)]
    return [w >> n for w in work]


def linear_gates(rows: list[int]) -> list[tuple[int, ...]]:
    """Return CX gates implementing z -> rows*z, with no extra qubits."""
    n = len(rows)
    work = rows[:]
    reduction = []
    for c in range(n):
        pivot = next(i for i in range(c, n) if (work[i] >> c) & 1)
        if pivot != c:
            work[c], work[pivot] = work[pivot], work[c]
            reduction += [(c, pivot), (pivot, c), (c, pivot)]
        for i in range(n):
            if i != c and ((work[i] >> c) & 1):
                work[i] ^= work[c]
                reduction.append((c, i))
    assert work == [1 << i for i in range(n)]
    return list(reversed(reduction))


def polynomial_mul_terms(left: list[int], right: list[int]):
    """Karatsuba tensor: (left parity, right parity, output polynomial)."""
    n = len(left)
    assert len(right) == n
    if n == 1:
        return [(left[0], right[0], 1)]
    k = (n + 1) // 2
    low = polynomial_mul_terms(left[:k], right[:k])
    high = polynomial_mul_terms(left[k:], right[k:])
    mix_left = [left[i] ^ (left[k+i] if k+i < n else 0) for i in range(k)]
    mix_right = [right[i] ^ (right[k+i] if k+i < n else 0) for i in range(k)]
    mixed = polynomial_mul_terms(mix_left, mix_right)
    return ([(u, v, w ^ (w << k)) for u, v, w in low]
            + [(u, v, (w << k) ^ (w << (2*k))) for u, v, w in high]
            + [(u, v, w << k) for u, v, w in mixed])


def parity_gates(mask: int):
    pivot = (mask & -mask).bit_length() - 1
    return pivot, [(i, pivot) for i in range(12) if i != pivot and (mask >> i) & 1]


def vector_ccx(u: int, v: int, out: int):
    """XOR vector out times parity(u)*parity(v) into the target register."""
    p, pu = parity_gates(u)
    q, pv = parity_gates(v)
    assert not u & v
    assert out
    pivot = (out & -out).bit_length() - 1
    fan = [(12+pivot, 12+i) for i in range(12) if i != pivot and (out >> i) & 1]
    return pu + pv + fan + [(p, q, 12+pivot)] + list(reversed(fan + pv + pu))


def make_power_map_fixed_subfield(a: int):
    """Build y -> target XOR y^(2^a+1); preserve y, use no work qubits."""
    g = math.gcd(a, 12)
    p = {1: 0b11, 2: 0b111, 3: 0b1011, 4: 0b10011, 6: 0b1000011}[g]
    gamma = next(x for x in range(1, 4096) if poly_eval(p, x) == 0)
    gamma_powers = [1]
    for _ in range(2*g):
        gamma_powers.append(gf_mul(gamma_powers[-1], gamma))
    assert gf_frobenius(gamma, g) == gamma
    h = 12 // g
    extension_basis = [1 << i for i in range(h)]  # 1,alpha,...,alpha^(h-1)
    columns = [gf_mul(v, gamma_powers[r]) for v in extension_basis for r in range(g)]
    rows = [sum(((col >> i) & 1) << j for j, col in enumerate(columns)) for i in range(12)]
    inverse = invert_rows(rows)
    basis_change = linear_gates(inverse)
    gates = basis_change[:]
    linear_coefficients = []
    bilinear_terms = []
    # Within one GF(2^g) coefficient, Frobenius^a fixes it, so the
    # diagonal block is a square: entirely GF(2)-linear.
    for i, vi in enumerate(extension_basis):
        weight = gf_mul(vi, gf_frobenius(vi, a))
        for r in range(g):
            coeff = gf_mul(weight, gamma_powers[2*r])
            linear_coefficients.append((i*g+r, coeff))
            gates += [(i*g+r, 12+j) for j in range(12) if (coeff >> j) & 1]
    # Cross coefficient blocks: h*(h-1)/2 subfield multiplications.
    for i in range(h):
        for j in range(i+1, h):
            vi, vj = extension_basis[i], extension_basis[j]
            weight = gf_mul(vi, gf_frobenius(vj, a)) ^ gf_mul(vj, gf_frobenius(vi, a))
            terms = polynomial_mul_terms([1 << (i*g+r) for r in range(g)],
                                         [1 << (j*g+r) for r in range(g)])
            for u, v, poly in terms:
                out = gf_mul(weight, poly_eval(poly, gamma))
                if not out:
                    continue
                bilinear_terms.append((u, v, out))
                gates += vector_ccx(u, v, out)
    gates += list(reversed(basis_change))
    return {
        "frobenius_power": a, "subfield_degree": g, "subfield_generator": gamma,
        "source_to_tower_rows": inverse, "linear_coefficients": linear_coefficients,
        "bilinear_terms": bilinear_terms, "gates": gates,
        "ccx_count": sum(len(gate) == 3 for gate in gates),
        "cx_count": sum(len(gate) == 2 for gate in gates),
        "quantum_registers": {"preserved_input": 12, "xor_target": 12, "extra_work": 0},
    }


def make_power_map_involution(a: int):
    """Use a degree-2g subfield on which Frobenius^a is an involution.

    Each diagonal coefficient norm needs one GF(2^g) multiplication.
    Each cross pair needs one GF(2^(2g)) multiplication followed by a
    linear map, since its two products are Frobenius conjugates.
    """
    g = math.gcd(a, 12)
    d = 2*g
    assert 12 % d == 0
    primitive = {1: 0b11, 2: 0b111, 3: 0b1011, 4: 0b10011, 6: 0b1000011}
    gamma_g = next(x for x in range(1, 4096) if poly_eval(primitive[g], x) == 0)
    gamma_d = next(x for x in range(1, 4096) if poly_eval(primitive[d], x) == 0)
    theta = gamma_d
    g_powers = [1]
    d_powers = [1]
    for _ in range(2*d):
        g_powers.append(gf_mul(g_powers[-1], gamma_g))
        d_powers.append(gf_mul(d_powers[-1], gamma_d))
    theta_sigma = gf_frobenius(theta, a)
    trace = theta ^ theta_sigma
    norm = gf_mul(theta, theta_sigma)
    assert trace and gf_frobenius(trace, g) == trace
    assert gf_frobenius(norm, g) == norm
    subfield_columns = g_powers[:g] + [gf_mul(theta, v) for v in g_powers[:g]]
    h = 12 // d
    extension_basis = [1 << i for i in range(h)]
    columns = [gf_mul(v, c) for v in extension_basis for c in subfield_columns]
    rows = [sum(((col >> i) & 1) << j for j, col in enumerate(columns)) for i in range(12)]
    inverse = invert_rows(rows)
    basis_change = linear_gates(inverse)
    gates = basis_change[:]
    linear_coefficients = []
    bilinear_terms = []

    # A table gives coordinates in the standard polynomial gamma_d basis.
    polynomial_coords = {}
    for bits in range(1 << d):
        value = 0
        for r in range(d):
            if (bits >> r) & 1:
                value ^= d_powers[r]
        polynomial_coords[value] = bits
    to_poly = [polynomial_coords[c] for c in subfield_columns]
    to_poly_sigma = [polynomial_coords[gf_frobenius(c, a)] for c in subfield_columns]

    def append_linear(bit, out):
        linear_coefficients.append((bit, out))
        gates.extend((bit, 12+j) for j in range(12) if (out >> j) & 1)

    def append_product(u, v, out):
        if out:
            bilinear_terms.append((u, v, out))
            gates.extend(vector_ccx(u, v, out))

    for i, vi in enumerate(extension_basis):
        weight = gf_mul(vi, gf_frobenius(vi, a))
        for r in range(g):
            append_linear(i*d+r, gf_mul(weight, g_powers[2*r]))
            append_linear(i*d+g+r, gf_mul(weight, gf_mul(norm, g_powers[2*r])))
        for u, v, poly in polynomial_mul_terms([1 << (i*d+r) for r in range(g)],
                                               [1 << (i*d+g+r) for r in range(g)]):
            append_product(u, v, gf_mul(weight, gf_mul(trace, poly_eval(poly, gamma_g))))

    for i in range(h):
        for j in range(i+1, h):
            weight = gf_mul(extension_basis[i], gf_frobenius(extension_basis[j], a))
            weight_sigma = gf_mul(extension_basis[j], gf_frobenius(extension_basis[i], a))
            left = [sum(((c >> r) & 1) << (i*d+t) for t, c in enumerate(to_poly)) for r in range(d)]
            right = [sum(((c >> r) & 1) << (j*d+t) for t, c in enumerate(to_poly_sigma)) for r in range(d)]
            for u, v, poly in polynomial_mul_terms(left, right):
                coeff = poly_eval(poly, gamma_d)
                out = gf_mul(weight, coeff) ^ gf_mul(weight_sigma, gf_frobenius(coeff, a))
                append_product(u, v, out)
    gates += list(reversed(basis_change))
    return {
        "frobenius_power": a, "subfield_degree": d, "fixed_subfield_degree": g,
        "subfield_generator": gamma_d, "construction": "quadratic-subfield-norm",
        "source_to_tower_rows": inverse, "linear_coefficients": linear_coefficients,
        "bilinear_terms": bilinear_terms, "gates": gates,
        "ccx_count": sum(len(gate) == 3 for gate in gates),
        "cx_count": sum(len(gate) == 2 for gate in gates),
        "quantum_registers": {"preserved_input": 12, "xor_target": 12, "extra_work": 0},
    }


def make_power_map(a: int):
    fixed = make_power_map_fixed_subfield(a)
    if 12 % (2 * math.gcd(a, 12)):
        return fixed
    involution = make_power_map_involution(a)
    return min((fixed, involution), key=lambda spec: (spec["ccx_count"], spec["cx_count"]))


def phase_correction_gates(spec, measurement_mask: int):
    """Classical-outcome-specialized Clifford correction after X measurement.

    Gates ('CX', c,t), ('Z',t), ('CZ',a,b), acting only on source qubits.
    The mask has one bit for each measured output qubit. All 4096 masks
    are represented by XOR composition of the 12 single-bit-mask cases.
    """
    basis_change = linear_gates(spec["source_to_tower_rows"])
    gates = [("CX", *gate) for gate in basis_change]
    for bit, out in spec["linear_coefficients"]:
        if (out & measurement_mask).bit_count() & 1:
            gates.append(("Z", bit))
    for u, v, out in spec["bilinear_terms"]:
        if (out & measurement_mask).bit_count() & 1:
            p, pu = parity_gates(u)
            q, pv = parity_gates(v)
            gates.extend(("CX", *gate) for gate in pu + pv)
            gates.append(("CZ", p, q))
            gates.extend(("CX", *gate) for gate in reversed(pu + pv))
    gates.extend(("CX", *gate) for gate in reversed(basis_change))
    return gates


def simulate_phase(gates, x: int):
    bits, phase = x, 0
    for gate in gates:
        if gate[0] == "CX":
            _, c, t = gate
            bits ^= ((bits >> c) & 1) << t
        elif gate[0] == "Z":
            phase ^= (bits >> gate[1]) & 1
        elif gate[0] == "CZ":
            phase ^= ((bits >> gate[1]) & (bits >> gate[2])) & 1
        else:
            raise ValueError(gate)
    return bits, phase


def kmx_header(a: int):
    return ([f"# GF(2^12) power map: target ^= source^(2^{a}+1)",
             "# Polynomial: x^12+x^6+x^4+x+1; little-endian polynomial basis.",
             "# Experimental kernel, not a DQI submission.",
             'REGISTER r0 "source"', 'REGISTER r1 "target"']
            + [f"APPEND_TO_REGISTER q{i} r0" for i in range(12)]
            + [f"APPEND_TO_REGISTER q{12+i} r1" for i in range(12)])


def export_kmx(spec, directory: Path):
    """Export standalone compute and compute/HMR/Clifford-correct examples.

    Syntax follows official kickmix_instructions.md. These text exports
    have not been loaded by the official Kickmix parser in this environment.
    """
    a = spec["frobenius_power"]
    header = kmx_header(a)
    forward = [f"R q{i}" for i in range(12, 24)]
    forward += [("CX" if len(gate) == 2 else "CCX") + " " + " ".join(f"q{i}" for i in gate)
                for gate in spec["gates"]]
    directory.joinpath(f"gf12_power_{a}.kmx").write_text("\n".join(header + forward)+"\n")
    cleanup = [f"HMR q{12+i} b{i}" for i in range(12)]
    basis = linear_gates(spec["source_to_tower_rows"])
    cleanup += [f"CX q{c} q{t}" for c, t in basis]

    def parity_bit(out):
        return ["BIT_STORE0 b12"] + [f"BIT_INVERT b12 if b{i}" for i in range(12) if (out >> i) & 1]

    for bit, out in spec["linear_coefficients"]:
        if out:
            cleanup += parity_bit(out) + [f"Z q{bit} if b12"]
    for u, v, out in spec["bilinear_terms"]:
        p, pu = parity_gates(u)
        q, pv = parity_gates(v)
        cleanup += parity_bit(out)
        cleanup += [f"CX q{c} q{t}" for c, t in pu + pv]
        cleanup += [f"CZ q{p} q{q} if b12"]
        cleanup += [f"CX q{c} q{t}" for c, t in reversed(pu + pv)]
    cleanup += [f"CX q{c} q{t}" for c, t in reversed(basis)]
    cleanup += ["BIT_STORE0 b12"]
    directory.joinpath(f"gf12_power_{a}_roundtrip.kmx").write_text("\n".join(header+forward+cleanup)+"\n")


def simulate(gates, x: int, target: int = 0):
    bits = x | (target << 12)
    for gate in gates:
        if len(gate) == 2:
            a, t = gate
            bits ^= ((bits >> a) & 1) << t
        else:
            a, b, t = gate
            bits ^= (((bits >> a) & (bits >> b)) & 1) << t
    return bits & 4095, bits >> 12


def tower_eval(spec, x: int):
    coords = sum(((row & x).bit_count() & 1) << i
                 for i, row in enumerate(spec["source_to_tower_rows"]))
    out = 0
    for i, c in spec["linear_coefficients"]:
        if (coords >> i) & 1:
            out ^= c
    for u, v, c in spec["bilinear_terms"]:
        if (coords & u).bit_count() & (coords & v).bit_count() & 1:
            out ^= c
    return out


def main():
    start = time.perf_counter()
    reports = []
    for a in range(1, 6):
        spec = make_power_map(a)
        t0 = time.perf_counter()
        for x in range(4096):
            wanted = gf_mul(x, gf_frobenius(x, a))
            assert tower_eval(spec, x) == wanted, (a, x, "tower")
            for target in (0, (x * 1237 + 19) & 4095):
                observed_input, observed_output = simulate(spec["gates"], x, target)
                assert observed_input == x, (a, x, "input restored")
                assert observed_output == target ^ wanted, (a, x, "output")
        for j in range(12):
            correction = phase_correction_gates(spec, 1 << j)
            for x in range(4096):
                wanted = gf_mul(x, gf_frobenius(x, a))
                restored, phase = simulate_phase(correction, x)
                assert restored == x, (a, j, x, "phase input restored")
                assert phase == ((wanted >> j) & 1), (a, j, x, "phase")
        report = {k:v for k,v in spec.items() if k not in ("gates", "bilinear_terms", "linear_coefficients")}
        report["exhaustive_inputs"] = 4096
        report["target_cases_per_input"] = 2
        report["gate_simulations"] = 8192
        report["phase_correction_basis_masks"] = 12
        report["phase_correction_cases"] = 4096 * 12
        report["phase_mask_coverage"] = "All 4096 outcomes by linearity in mask, checked on 12 mask basis vectors."
        report["verification_seconds"] = time.perf_counter() - t0
        report["status"] = "PASS"
        reports.append(report)
        export_kmx(spec, Path(__file__).parent)
        print(json.dumps(report), flush=True)
    result = {"modulus": MODULUS, "maps": reports,
              "elapsed_seconds": time.perf_counter()-start,
              "scope": "Exact classical basis permutation of explicit CX/CCX circuits; no DQI integration or official validator run."}
    Path(__file__).with_name("inverse_specialized_results.json").write_text(json.dumps(result, indent=2)+"\n")


if __name__ == "__main__":
    main()
