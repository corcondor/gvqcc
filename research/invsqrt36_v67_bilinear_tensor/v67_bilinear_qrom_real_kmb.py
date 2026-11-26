"""
V67 Method 5 (Real Native .kmb): Don't-Care-Aware Bilinear Tensor QROM for InvSqrt C0..C4 (24 segments, 125 bits).

Uses the exact reachability/don't-care identity on 24 segments (s in 0..23):
  a4 & a3 = 0 identically for all s < 24!
Hence the 5-bit address (a0, a1 | a2, a3, a4) splits into:
  - Low basis  m (3 monomials): [a0, a1, a0&a1]                      -> 1 CCX cache
  - High basis M (5 monomials): [a2, a3, a2&a3, a4, a2&a4]           -> 2 CCX cache
  - Mixed bilinear products m_i & M_j (3 x 5 = 15 products)          -> 15 CCX (reusing 1 ancilla via zero-CCX HMR!)
TOTAL: ONLY 18 CCX (and 4 clean ancillas) to load ALL 125 bits of C0..C4 across all 24 segments!
Beats standard 24-segment unary QROM (23 CCX) by -21.7% and naive rank-1 (294 CCX) by -93.9%!

Also applies XOR-hub CNOT sharing on the 125-bit fan-out and exhaustively verifies all 24 segments
bit-for-bit (including zero HMR phase debt and clean ancilla/address restoration).
"""

import hashlib
import json
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, r"c:\Users\81808\.openclaw\gvqcc\verifiers")
sys.path.insert(0, r"C:\Users\81808\.openclaw\gvqcc_wt_v56\research\invsqrt36_nonlinear_lending")
import kickmix as km
from v55_radix4_core import C as C24


def build_c0c4_table():
    """Return (24, 125) uint8 table of magnitude bits for InvSqrt 24-segment C0..C4."""
    rows_bits = []
    col_widths = []
    for col_idx in range(5):
        vals = [int(v) for v in C24[:, col_idx]]
        B = max(abs(v) for v in vals).bit_length()
        col_widths.append(B)
        for b in range(B):
            rows_bits.append([(abs(v) >> b) & 1 for v in vals])
    return np.array(rows_bits, dtype=np.uint8).T, col_widths  # (24, 125)


def solve_gf2_basis_coeffs(table_24_O):
    """
    Exact GF(2) inversion on the 24-element basis over s in 0..23:
      1 constant + 3 low (a0, a1, a0&a1) + 5 high (a2, a3, a2&a3, a4, a2&a4) + 15 mixed (m_i & M_j) = 24 basis functions!
    Because 1 + 3 + 5 + 15 = 24, the 24x24 evaluation matrix over s=0..23 is INVERTIBLE over GF(2)!
    """
    N = 24
    O = table_24_O.shape[1]
    E = np.zeros((N, N), dtype=np.uint8)
    for s in range(N):
        a0 = (s >> 0) & 1
        a1 = (s >> 1) & 1
        a2 = (s >> 2) & 1
        a3 = (s >> 3) & 1
        a4 = (s >> 4) & 1
        m = [a0, a1, a0 & a1]
        M = [a2, a3, a2 & a3, a4, a2 & a4]
        row = [1] + m + M + [mi & Mj for mi in m for Mj in M]
        E[s] = row

    # Invert E over GF(2) via Gauss-Jordan
    aug = np.concatenate([E.copy(), np.eye(N, dtype=np.uint8)], axis=1)
    for col in range(N):
        piv = next((r for r in range(col, N) if aug[r, col]), None)
        assert piv is not None, f"Singular at col {col}"
        if piv != col:
            aug[[col, piv]] = aug[[piv, col]]
        for r in range(N):
            if r != col and aug[r, col]:
                aug[r] ^= aug[col]
    E_inv = aug[:, N:]
    assert np.array_equal((E @ E_inv) % 2, np.eye(N, dtype=np.uint8))

    coeffs = (E_inv @ table_24_O) % 2  # (24, O)
    assert np.array_equal((E @ coeffs) % 2, table_24_O)
    return coeffs


def emit_bilinear_qrom_kmb(coeffs_24_O, use_hub_compression=True):
    """
    Emit exact real native .kmb for the 24-segment 125-bit QROM.
    Qubit layout:
      q0..q4     : address a0..a4
      q5         : low cache  c_lo  = a0 & a1
      q6         : high cache c_h23 = a2 & a3
      q7         : high cache c_h24 = a2 & a4
      q8         : streaming product ancilla p (reused 15 times via zero-CCX HMR!)
      q9..q133   : 125 output qubits out[0..124]
    """
    O = coeffs_24_O.shape[1]
    a0, a1, a2, a3, a4 = 0, 1, 2, 3, 4
    c_lo, c_h23, c_h24, p = 5, 6, 7, 8
    out_base = 9
    ops = []
    meas_idx = 0

    def emit(op):
        ops.append(op)

    def hmr_uncompute(q_anc, c1, c2):
        nonlocal meas_idx
        b = meas_idx
        meas_idx += 1
        emit(f"HMR q{q_anc} b{b}")
        emit(f"CZ q{c1} q{c2} if b{b}")

    # First compute low/high caches (3 CCX):
    emit(f"CCX q{a0} q{a1} q{c_lo}")
    emit(f"CCX q{a2} q{a3} q{c_h23}")
    emit(f"CCX q{a2} q{a4} q{c_h24}")

    m_qs = [a0, a1, c_lo]
    M_qs = [a2, a3, c_h23, a4, c_h24]

    # If use_hub_compression: find greedy pairwise output-column XORs (if out[j] = out[i] ^ delta with wt(delta)+1 < wt(out[j]))
    # Compute reduced coefficient matrix on the 23 non-constant rows (rows 1..23), then apply final CX out[i] -> out[j]!
    C_work = coeffs_24_O[1:, :].copy()  # (23, O)
    post_cx = []  # list of (src_o, dst_o) to apply in REVERSE order? Wait:
    # If we want final_col[j] = work_col[j] ^ final_col[i], we do:
    #   1) fan out work_col[k] to out[k] for all k
    #   2) apply CX out[i] -> out[j] in forward topological order!
    # To guarantee acyclic topological order: build a minimum spanning forest (Prim/Kruskal on Hamming distance!)
    if use_hub_compression:
        # Compute Hamming weights and pairwise Hamming distances on the 23 non-constant rows
        weights = C_work.sum(axis=0)
        # Build MST over {ROOT (0-vector)} U {0..O-1}
        in_tree = [False] * O
        parent = [-1] * O
        best_cost = [int(weights[o]) for o in range(O)]
        order = []
        for _ in range(O):
            # pick unvisited o with min best_cost
            u = min((o for o in range(O) if not in_tree[o]), key=lambda o: best_cost[o])
            in_tree[u] = True
            order.append(u)
            for v in range(O):
                if not in_tree[v]:
                    dist = int(np.bitwise_xor(C_work[:, u], C_work[:, v]).sum()) + 1  # +1 for the CX u->v
                    if dist < best_cost[v]:
                        best_cost[v] = dist
                        parent[v] = u
        # Now C_delta[:, u] = C_work[:, u] ^ C_work[:, parent[u]] (if parent[u] != -1)
        C_delta = C_work.copy()
        for u in order:
            if parent[u] != -1:
                C_delta[:, u] = np.bitwise_xor(C_work[:, u], C_work[:, parent[u]])
                post_cx.append((parent[u], u))
        C_emit = C_delta
    else:
        C_emit = C_work

    # 1) Low basis fan-out (rows 0..2 of C_emit)
    for i, mq in enumerate(m_qs):
        for o in range(O):
            if C_emit[i, o]:
                emit(f"CX q{mq} q{out_base + o}")

    # 2) High basis fan-out (rows 3..7 of C_emit)
    for j, Mq in enumerate(M_qs):
        for o in range(O):
            if C_emit[3 + j, o]:
                emit(f"CX q{Mq} q{out_base + o}")

    # 3) 15 Mixed bilinear products m_i & M_j (rows 8..22 of C_emit), reusing 1 ancilla p via zero-CCX HMR!
    for i, mq in enumerate(m_qs):
        for j, Mq in enumerate(M_qs):
            row_idx = 8 + i * 5 + j
            targets = [o for o in range(O) if C_emit[row_idx, o]]
            if not targets:
                continue
            emit(f"CCX q{mq} q{Mq} q{p}")
            for o in targets:
                emit(f"CX q{p} q{out_base + o}")
            hmr_uncompute(p, mq, Mq)

    # 4) Uncompute low/high caches via zero-CCX HMR!
    hmr_uncompute(c_h24, a2, a4)
    hmr_uncompute(c_h23, a2, a3)
    hmr_uncompute(c_lo, a0, a1)

    # 5) Apply MST hub CXs in topological order!
    for src_o, dst_o in post_cx:
        emit(f"CX q{out_base + src_o} q{out_base + dst_o}")

    # 6) Constant row (row 0) applied AFTER hub CXs so constants don't bleed across hubs!
    for o in range(O):
        if coeffs_24_O[0, o]:
            emit(f"X q{out_base + o}")

    return ops


def verify_qrom_exhaustive(ops, table_24_O):
    """Exhaustively simulate all 24 valid segments s=0..23 and verify all 125 output bits, clean ancillas, zero HMR debt."""
    O = table_24_O.shape[1]
    out_base = 9
    for s in range(24):
        state = s  # q0..q4 = s, all other qubits = 0
        m_debt = 0
        for line in ops:
            toks = line.split()
            cmd = toks[0]
            if cmd == "X":
                q = int(toks[1][1:])
                state ^= (1 << q)
            elif cmd == "CX":
                c, t = int(toks[1][1:]), int(toks[2][1:])
                if (state >> c) & 1:
                    state ^= (1 << t)
            elif cmd == "CCX":
                c1, c2, t = int(toks[1][1:]), int(toks[2][1:]), int(toks[3][1:])
                if ((state >> c1) & 1) and ((state >> c2) & 1):
                    state ^= (1 << t)
            elif cmd == "HMR":
                q, b = int(toks[1][1:]), int(toks[2][1:])
                if (state >> q) & 1:
                    m_debt ^= (1 << b)
                    state ^= (1 << q)
            elif cmd == "CZ" and toks[3] == "if":
                q1, q2, b = int(toks[1][1:]), int(toks[2][1:]), int(toks[4][1:])
                if ((state >> q1) & 1) and ((state >> q2) & 1):
                    m_debt ^= (1 << b)
        assert (state & 0x1F) == s, f"Address mutated at s={s}"
        assert ((state >> 5) & 0xF) == 0, f"Ancillas not clean at s={s}: {bin((state >> 5) & 0xF)}"
        assert m_debt == 0, f"HMR phase debt non-zero at s={s}: {bin(m_debt)}"
        for o in range(O):
            got = (state >> (out_base + o)) & 1
            exp = int(table_24_O[s, o])
            assert got == exp, f"Output mismatch at s={s}, bit {o}: got {got}, exp {exp}"
    return True


def main():
    table, col_widths = build_c0c4_table()
    coeffs = solve_gf2_basis_coeffs(table)

    results = {}
    for label, use_hub in [("raw", False), ("mst_hub_compressed", True)]:
        ops = emit_bilinear_qrom_kmb(coeffs, use_hub_compression=use_hub)
        ok = verify_qrom_exhaustive(ops, table)
        out_path = Path(rf"c:\Users\81808\.openclaw\gvqcc_v2832\v67_bilinear_qrom_c0c4_125b_{label}.kmb")
        circ = km.Circuit("\n".join(ops) + "\n")
        circ.to_file(str(out_path), format="kmb")
        reloaded = km.Circuit.from_file(str(out_path))
        st = reloaded.operation_statistics()
        sha = hashlib.sha256(out_path.read_bytes()).hexdigest()
        ccx = sum(1 for o in ops if o.startswith("CCX "))
        hmr = sum(1 for o in ops if o.startswith("HMR "))
        cx = sum(1 for o in ops if o.startswith("CX "))
        results[label] = {
            "pass_24_of_24": ok,
            "ccx": ccx,
            "hmr": hmr,
            "cx": cx,
            "total_ops": st.num_instructions,
            "sha256": sha,
            "path": str(out_path),
        }
        print(
            f"  [{label:18s}] 24/24 x 125b PASS={ok} | CCX={ccx:2d}, HMR={hmr:2d}, CX={cx:4d}, "
            f"total_ops={st.num_instructions:4d} | SHA={sha[:16]}..."
        )

    ops_drop = results["raw"]["total_ops"] - results["mst_hub_compressed"]["total_ops"]
    print(
        f"  >>> MST-HUB CX COMPRESSION: ops {results['raw']['total_ops']} -> {results['mst_hub_compressed']['total_ops']} "
        f"(-{ops_drop} / -{100*ops_drop/results['raw']['total_ops']:.2f}%!!), CCX=18 (4 ancillas, 0 HMR debt!)"
    )

    rec_path = Path(r"c:\Users\81808\.openclaw\gvqcc_v2832\v67_bilinear_qrom_receipt.json")
    with open(rec_path, "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
