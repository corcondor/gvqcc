#!/usr/bin/env python3
"""
V7 Deep Search on Real 60,766-op 37Q invsqrt.kmb:
  1) Centralized Phase-Basis Compression:
       phi(x, m) = XOR_{i=1}^r h_i(m) P_i(x)
     Extracts all classically-controlled diagonal phase blocks (IF c_j: Z/CZ/CCZ/S/T),
     groups commuting phase windows (across which support qubits are not X-modified),
     and computes exact GF(2) rank compression (k blocks -> r basis polynomials,
     eliminating k - r quantum phase blocks via classical XORs h_i(m)!).
  2) Deep Structural Dissection of the 37Q Arithmetic Hotspots:
     - 8 period-112 7-bit arithmetic rows (8099..9014)
     - 3 large 19-21-bit ripple chains (7706..8032, 9526..9788, 9850..10185)
     - Tail uncomputation plateau (57893..60664)
     Measures exact active wire sets, carry-ancilla reuse, and Pattern A2 (Hybrid
     Gidney-Cuccaro/Takahashi) vs V4/V6 paid-gate budget.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, r"c:\Users\81808\.openclaw\gvqcc\verifiers")
import kickmix

KMB_PATH = Path(r"c:\Users\81808\.openclaw\gvqcc_v2832\v3317\invsqrt.kmb")
Q_RE = re.compile(r"\bq(\d+)\b")
B_RE = re.compile(r"\bb(\d+)\b")


def parse_ops(path: Path):
    c = kickmix.Circuit.from_file(str(path))
    ops = []
    for line in str(c).splitlines():
        s = line.strip()
        if not s or s.startswith("APPEND_TO_REGISTER"):
            continue
        parts = s.split()
        name = parts[0]
        qs = [int(m) for m in Q_RE.findall(s)]
        bs = [int(m) for m in B_RE.findall(s)]
        ops.append((name, qs, bs, s))
    return c, ops


def gf2_rank(vecs: list[int]) -> int:
    basis = {}
    for v in vecs:
        x = v
        while x:
            hb = x.bit_length() - 1
            if hb in basis:
                x ^= basis[hb]
            else:
                basis[hb] = x
                break
    return len(basis)


def analyze_classical_phase_compression(ops):
    """
    Scan all classically-controlled diagonal phase gates (e.g. IF b_k: CZ/Z/CCZ)
    and track commuting windows where qubits are only read diagonally (Z/CZ/CCZ/S/T/RZ
    or control-only of CX/CCX — i.e., not written in computational basis!).
    """
    # First inspect exact syntax of classically-controlled / IF / CZ / CCZ ops
    diag_names = Counter()
    ctrl_ops = []
    for t, (name, qs, bs, s) in enumerate(ops):
        if bs:
            diag_names[name] += 1
            ctrl_ops.append((t, name, qs, bs, s))

    # Group contiguous classically-controlled diagonal corrections per measurement bit b_k
    # In kickmix, classical-control gates have `b<k>` in their instruction string (e.g. `IF b12 CZ q1 q2` or `CZ b12 q1 q2`).
    # Let's track for every qubit q its "write epoch" (incremented whenever q is target of X/CX/CCX/H/HMR/SWAP).
    write_epoch = [0] * 37
    # Map each measurement bit b_k -> list of (t, monomial_key, is_paid)
    # monomial_key = tuple of (q, write_epoch[q]) sorted, so two phase terms commute & share the exact same
    # physical Boolean monomial iff their (q, write_epoch[q]) tuples are identical!
    bit_polys = defaultdict(list)
    monomial_to_bits = defaultdict(set)
    paid_ctrl_ops = 0

    for t, (name, qs, bs, s) in enumerate(ops):
        u = name.upper()
        # Check if classically controlled diagonal gate
        if bs and u in ("Z", "CZ", "CCZ", "S", "SDAG", "T", "TDAG", "IF_Z", "IF_CZ", "IF_CCZ", "CZ_IF", "Z_IF"):
            key = tuple(sorted((q, write_epoch[q]) for q in qs))
            is_paid = (len(qs) >= 3) or ("CCZ" in u) or ("T" in u)
            if is_paid:
                paid_ctrl_ops += 1
            for b in bs:
                bit_polys[b].append((t, key, len(qs), u))
                monomial_to_bits[key].add(b)
        elif bs and any(k in s.upper() for k in ("CZ", "CCZ", " Z ")):
            key = tuple(sorted((q, write_epoch[q]) for q in qs))
            is_paid = (len(qs) >= 3) or ("CCZ" in s.upper())
            if is_paid:
                paid_ctrl_ops += 1
            for b in bs:
                bit_polys[b].append((t, key, len(qs), s.split()[0]))
                monomial_to_bits[key].add(b)

        # Update write_epoch for non-diagonal target writes
        if u in ("X", "H", "HMR", "M", "MR", "RESET", "SX", "RX", "RY"):
            for q in qs:
                if q < 37:
                    write_epoch[q] += 1
        elif u in ("CX", "CNOT", "CY"):
            if qs and qs[-1] < 37:
                write_epoch[qs[-1]] += 1
        elif u in ("CCX", "TOFFOLI", "CCNOT"):
            if qs and qs[-1] < 37:
                write_epoch[qs[-1]] += 1
        elif u == "SWAP":
            for q in qs:
                if q < 37:
                    write_epoch[q] += 1

    # Also check ALL CZ and CCZ (even unconditional) and IF-blocks!
    sample_b_ops = [(t, s) for t, (n, qs, bs, s) in enumerate(ops) if bs][:20]

    # Build GF(2) matrix of bit_polys (rows = measurement bits b_k, cols = unique (q, epoch) monomials)
    all_keys = sorted(monomial_to_bits.keys())
    key_idx = {k: i for i, k in enumerate(all_keys)}
    deg2_keys = [k for k in all_keys if len(k) == 2]
    deg3_keys = [k for k in all_keys if len(k) >= 3]
    shared_deg2 = [k for k in deg2_keys if len(monomial_to_bits[k]) >= 2]
    shared_deg3 = [k for k in deg3_keys if len(monomial_to_bits[k]) >= 2]

    # Compute GF(2) rank of measurement-conditioned phase polynomials!
    row_vecs = []
    for b, items in sorted(bit_polys.items()):
        v = 0
        for _, key, deg, _ in items:
            if deg >= 2:
                v ^= (1 << key_idx[key])
        if v:
            row_vecs.append(v)
    rk_deg2plus = gf2_rank(row_vecs)

    return {
        "classical_bit_op_counts": dict(diag_names.most_common(15)),
        "sample_b_ops": sample_b_ops[:12],
        "num_bits_with_phase": len(bit_polys),
        "total_unique_monomials": len(all_keys),
        "deg2_monomials": len(deg2_keys),
        "deg3plus_monomials": len(deg3_keys),
        "shared_deg2_monomials": len(shared_deg2),
        "shared_deg3plus_monomials": len(shared_deg3),
        "nonzero_deg2plus_bit_polys": len(row_vecs),
        "gf2_rank_deg2plus_bit_polys": rk_deg2plus,
        "exact_basis_compression_delta": len(row_vecs) - rk_deg2plus,
        "paid_ctrl_ops": paid_ctrl_ops,
    }


def dissect_37q_hotspots(ops):
    """Inspect exact structure of period-112 7-bit rows and large ripple chains."""
    targets = [
        ("ripple_21_A", 9526, 9788),
        ("ripple_21_B", 9850, 10185),
        ("ripple_19", 7706, 8032),
        ("ripple_16", 13606, 13723),
        ("row7_0", 8099, 8150),
        ("row7_1", 8291, 8342),
        ("row7_2", 8403, 8454),
        ("row7_3", 8515, 8566),
        ("row7_4", 8627, 8678),
        ("row7_5", 8739, 8790),
        ("row7_6", 8851, 8902),
        ("row7_7", 8963, 9014),
        ("tail_plateau", 57893, 60664),
    ]
    rows_out = []
    for name, s0, s1 in targets:
        seg = ops[s0 : min(s1 + 1, len(ops))]
        gcnt = Counter(n for n, _, _, _ in seg)
        qset = sorted({q for _, qs, _, _ in seg for q in qs})
        ccx_n = gcnt["CCX"]
        hmr_n = gcnt["HMR"]
        ccz_n = gcnt["CCZ"]
        # Compare V4 (+2 CCX/peak) vs Pattern A2 (+1 CCX/peak) if 1 peak bit shaved
        rows_out.append({
            "name": name,
            "span": [s0, s1],
            "ops": len(seg),
            "touched_qubits": len(qset),
            "CCX": ccx_n,
            "CCZ": ccz_n,
            "HMR": hmr_n,
            "CX": gcnt["CX"],
            "IF_ops": sum(1 for _, _, bs, _ in seg if bs),
            "pattern_A2_peak1_overhead": 1 if ccx_n > 0 else 0,
            "v4_1stage_overhead": 2 if ccx_n > 0 else 0,
        })
    return rows_out


def main():
    c, ops = parse_ops(KMB_PATH)
    print(f"Loaded {len(ops)} ops, {c.num_qubits} qubits, {c.num_bits} classical bits.")
    phase_res = analyze_classical_phase_compression(ops)
    print("\n=== V7 Deep Search 1: Centralized Phase-Basis Compression ===")
    for k, v in phase_res.items():
        if k == "sample_b_ops":
            print("  sample_b_ops:")
            for idx, s in v[:6]:
                print(f"    [{idx}] {s}")
        else:
            print(f"  {k}: {v}")

    hotspots = dissect_37q_hotspots(ops)
    print("\n=== V7 Deep Search 2: 37Q Arithmetic & Uncomputation Hotspots ===")
    for h in hotspots:
        print(
            f"  {h['name']:13s} [{h['span'][0]:5d},{h['span'][1]:5d}] ops={h['ops']:4d} "
            f"touchedQ={h['touched_qubits']:2d} CCX={h['CCX']:2d} CCZ={h['CCZ']:2d} "
            f"HMR={h['HMR']:2d} IF={h['IF_ops']:3d}"
        )

    out = {"phase_compression": phase_res, "hotspots": hotspots}
    Path(r"c:\Users\81808\.openclaw\gvqcc_v2832\v7_deep_search_audit.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8"
    )
    print("\nSaved v7_deep_search_audit.json")


if __name__ == "__main__":
    main()
