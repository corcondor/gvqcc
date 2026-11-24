#!/usr/bin/env python3
"""
Stack-Exact V7 Centralized Phase-Basis Compression Scanner on real 60,766-op invsqrt.kmb.

Tracks the exact PUSH_CONDITION / POP_CONDITION control stack and exact qubit write-epochs
across all 60,766 ops of v3317/invsqrt.kmb to extract every measurement-conditioned phase
polynomial P_k(x) and compute exact GF(2) rank compression:
    phi(x, m) = XOR_{k=1}^K m_k P_k(x) = XOR_{i=1}^r h_i(m) B_i(x)
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


def main():
    c = kickmix.Circuit.from_file(str(KMB_PATH))
    lines = [ln.strip() for ln in str(c).splitlines() if ln.strip() and not ln.strip().startswith("APPEND_TO_REGISTER")]

    write_epoch = [0] * 37
    cond_stack: list[tuple[str, ...]] = []
    # Map classical condition key (e.g. ('b0',)) -> Counter of (q, epoch) monomials mod 2
    # Split each classical bit b_k into distinct "measurement instances" (since kickmix reuses b0..bN)
    bit_gen = Counter()
    active_cond_id = {}

    cond_monomials = defaultdict(set)  # (cond_instance_key) -> set of monomials (XOR mod 2)
    cond_paid_ops = Counter()
    total_push = 0
    total_pop = 0
    diag_inside_cond = Counter()

    for t, s in enumerate(lines):
        parts = s.split()
        name = parts[0].upper()
        qs = [int(m) for m in Q_RE.findall(s)]
        bs = [int(m) for m in B_RE.findall(s)]

        if name == "HMR" and qs:
            if bs:
                bit_gen[bs[0]] += 1
                active_cond_id[bs[0]] = (bs[0], bit_gen[bs[0]])
            write_epoch[qs[0]] += 1
            continue

        if name == "PUSH_CONDITION":
            total_push += 1
            ckey = tuple(active_cond_id.get(b, (b, 0)) for b in bs)
            cond_stack.append(ckey)
            continue

        if name == "POP_CONDITION":
            total_pop += 1
            if cond_stack:
                cond_stack.pop()
            continue

        # Effective classical condition = union of stack + any inline b<k>
        eff_cond = tuple(x for frame in cond_stack for x in frame)
        if bs and name not in ("BIT_STORE0", "BIT_INVERT", "NEG"):
            eff_cond = eff_cond + tuple(active_cond_id.get(b, (b, 0)) for b in bs)

        if eff_cond and name in ("Z", "CZ", "CCZ", "S", "SDAG", "T", "TDAG", "Z_POW"):
            diag_inside_cond[name] += 1
            mon = tuple(sorted((q, write_epoch[q]) for q in qs))
            # Toggle mod 2 for Z/CZ/CCZ
            if name in ("Z", "CZ", "CCZ"):
                if mon in cond_monomials[eff_cond]:
                    cond_monomials[eff_cond].remove(mon)
                else:
                    cond_monomials[eff_cond].add(mon)
            if name in ("CCZ", "T", "TDAG", "Z_POW"):
                cond_paid_ops[eff_cond] += 1

        # Update write epochs for computational-basis writes
        if name in ("X", "H", "M", "MR", "RESET", "SX", "RX", "RY"):
            for q in qs:
                if q < 37:
                    write_epoch[q] += 1
        elif name in ("CX", "CNOT", "CY", "CCX", "TOFFOLI", "CCNOT"):
            if qs and qs[-1] < 37:
                write_epoch[qs[-1]] += 1
        elif name == "SWAP":
            for q in qs:
                if q < 37:
                    write_epoch[q] += 1

    # Compute exact GF(2) compression over ALL conditioned polynomials (deg >= 1 and deg >= 2)
    all_mons_d1 = sorted({m for ms in cond_monomials.values() for m in ms if len(m) >= 1})
    all_mons_d2 = sorted({m for ms in cond_monomials.values() for m in ms if len(m) >= 2})
    idx_d1 = {m: i for i, m in enumerate(all_mons_d1)}
    idx_d2 = {m: i for i, m in enumerate(all_mons_d2)}

    vecs_d1 = []
    vecs_d2 = []
    mon_freq_d2 = Counter()
    for ckey, ms in cond_monomials.items():
        v1 = 0
        v2 = 0
        for m in ms:
            if len(m) >= 1:
                v1 ^= (1 << idx_d1[m])
            if len(m) >= 2:
                v2 ^= (1 << idx_d2[m])
                mon_freq_d2[m] += 1
        if v1:
            vecs_d1.append(v1)
        if v2:
            vecs_d2.append(v2)

    rk1 = gf2_rank(vecs_d1)
    rk2 = gf2_rank(vecs_d2)
    shared_d2 = sum(1 for m, cnt in mon_freq_d2.items() if cnt >= 2)

    res = {
        "total_push_condition": total_push,
        "total_pop_condition": total_pop,
        "diag_ops_inside_conditions": dict(diag_inside_cond),
        "distinct_active_conditions": len(cond_monomials),
        "nonzero_phase_polys_deg1plus": len(vecs_d1),
        "gf2_rank_deg1plus": rk1,
        "compression_delta_deg1plus": len(vecs_d1) - rk1,
        "nonzero_phase_polys_deg2plus": len(vecs_d2),
        "gf2_rank_deg2plus": rk2,
        "compression_delta_deg2plus": len(vecs_d2) - rk2,
        "unique_deg2_monomials_epoch_exact": len(all_mons_d2),
        "shared_deg2_monomials_across_conditions": shared_d2,
        "max_monomial_reuse_count": max(mon_freq_d2.values()) if mon_freq_d2 else 0,
        "top5_reused_deg2_monomials": [(list(m), cnt) for m, cnt in mon_freq_d2.most_common(5)],
    }
    print("=== V7 Stack-Exact PUSH_CONDITION Centralized Phase-Basis Compression ===")
    for k, v in res.items():
        print(f"  {k}: {v}")
    Path(r"c:\Users\81808\.openclaw\gvqcc_v2832\v7_central_phase_basis_receipt.json").write_text(
        json.dumps(res, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
