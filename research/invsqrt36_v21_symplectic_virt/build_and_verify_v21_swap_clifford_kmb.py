#!/usr/bin/env python3
"""
V21 Real-Circuit Compiler & Official Verifier Runner for GVQCC InvSqrt (60,766 ops -> reduced KMB).

Applies two 100%-exact, zero-paid-overhead passes directly to v3317/invsqrt.kmb:
  Pass 1: Exact Unconditional Virtual SWAP Elimination (S_37 permutation tracking,
          minimal cycle-decomposition restore at circuit end).
  Pass 2: Commuting-Window Self-Inverse Clifford Cancellation (X, Z, H, CX, CZ)
          within identical classical condition frames.
Then serializes a real binary .kmb, audits q36 lifetimes before vs after, and runs
the official verify_submission_invsqrt.py!
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, r"c:\Users\81808\.openclaw\gvqcc\verifiers")
import kickmix as km

SRC_KMB = Path(r"c:\Users\81808\.openclaw\gvqcc_v2832\v3317\invsqrt.kmb")
OUT_KMB = Path(r"c:\Users\81808\.openclaw\gvqcc_v2832\invsqrt_v21_virt_swap_clifford.kmb")
Q_RE = re.compile(r"\bq(\d+)\b")


def remap_qubits(line: str, perm: list[int]) -> str:
    """Replace every q<i> token with q<perm[i]>."""
    return Q_RE.sub(lambda m: f"q{perm[int(m.group(1))]}", line)


def cycle_restore_swaps(perm: list[int]) -> list[str]:
    """
    We maintained `perm[logical] = physical`, so logical qubit `i` currently sits
    on physical wire `perm[i]`. To restore logical `i` onto physical `i` for all i,
    emit minimal SWAPs on physical wires.
    """
    # cur_loc[logical] = physical
    cur_loc = list(perm)
    # who_at[physical] = logical
    who_at = [0] * len(perm)
    for log_q, phys_q in enumerate(cur_loc):
        who_at[phys_q] = log_q
    swaps = []
    for log_q in range(len(perm)):
        phys_now = cur_loc[log_q]
        if phys_now != log_q:
            other_log = who_at[log_q]
            swaps.append(f"SWAP q{log_q} q{phys_now}")
            # Update maps
            cur_loc[log_q] = log_q
            cur_loc[other_log] = phys_now
            who_at[log_q] = log_q
            who_at[phys_now] = other_log
    return swaps


def gates_commute(op1, op2) -> bool:
    """Conservative exact commutation check for unconditional Clifford/diagonal ops."""
    n1, q1, b1, _ = op1
    n2, q2, b2, _ = op2
    if b1 or b2:
        return False
    if n1 in ("PUSH_CONDITION", "POP_CONDITION", "HMR", "BIT_STORE0", "BIT_INVERT", "NEG"):
        return False
    if n2 in ("PUSH_CONDITION", "POP_CONDITION", "HMR", "BIT_STORE0", "BIT_INVERT", "NEG"):
        return False
    s1, s2 = set(q1), set(q2)
    if s1.isdisjoint(s2):
        return True
    # Diagonal ops commute with each other
    diag = {"Z", "CZ", "CCZ", "S", "SDAG", "T", "TDAG", "Z_POW"}
    if n1 in diag and n2 in diag:
        return True
    # X commutes with X and with CX/CCX targets
    if n1 == "X" and n2 == "X":
        return True
    if n1 == "CX" and n2 == "CX":
        c1, t1 = q1
        c2, t2 = q2
        return (c1 != t2) and (c2 != t1)
    if n1 == "X" and n2 == "CX":
        return q1[0] != q2[0]  # X on target commutes with CX
    if n2 == "X" and n1 == "CX":
        return q2[0] != q1[0]
    if n1 in diag and n2 == "CX":
        return q2[1] not in s1  # diagonal on control commutes with CX
    if n2 in diag and n1 == "CX":
        return q1[1] not in s2
    return False


def is_self_inverse_match(op1, op2) -> bool:
    n1, q1, b1, _ = op1
    n2, q2, b2, _ = op2
    if n1 != n2 or b1 or b2:
        return False
    if n1 in ("X", "Z", "H", "CX"):
        return q1 == q2
    if n1 in ("CZ", "CCZ", "SWAP"):
        return set(q1) == set(q2)
    return False


def count_q36_lifetimes(ops_lines: list[str]) -> tuple[int, int]:
    """Count maximal live lifetimes and total touches of physical wire q36."""
    touches = 0
    lifetimes = 0
    alive = False
    for s in ops_lines:
        name = s.split()[0].upper()
        qs = [int(m) for m in Q_RE.findall(s)]
        if 36 in qs:
            touches += 1
            if not alive:
                alive = True
                lifetimes += 1
            if name == "HMR" and qs[0] == 36:
                alive = False
    return lifetimes, touches


def compile_circuit(src: Path, out: Path):
    c_in = km.Circuit.from_file(str(src))
    raw_lines = [ln.strip() for ln in str(c_in).splitlines() if ln.strip()]
    header = [ln for ln in raw_lines if ln.startswith("APPEND_TO_REGISTER")]
    body = [ln for ln in raw_lines if not ln.startswith("APPEND_TO_REGISTER")]

    lt_before, tch_before = count_q36_lifetimes(body)

    # Pass 1: Exact Virtual SWAP elimination (unconditional SWAPs only; conditional SWAPs stay untouched)
    perm = list(range(37))
    cond_depth = 0
    pass1 = []
    swaps_virtualized = 0
    for ln in body:
        parts = ln.split()
        name = parts[0].upper()
        qs = [int(m) for m in Q_RE.findall(ln)]
        if name == "PUSH_CONDITION":
            cond_depth += 1
            pass1.append(ln)
            continue
        if name == "POP_CONDITION":
            cond_depth = max(0, cond_depth - 1)
            pass1.append(ln)
            continue
        if name == "SWAP" and len(qs) == 2 and cond_depth == 0:
            a, b = qs
            perm[a], perm[b] = perm[b], perm[a]
            swaps_virtualized += 1
            continue
        pass1.append(remap_qubits(ln, perm))

    restore_swaps = cycle_restore_swaps(perm)
    pass1.extend(restore_swaps)

    # Pass 2: Commuting-window self-inverse Clifford cancellation (window size 24)
    # Represent each op as (name, tuple(qs), has_b, line)
    B_RE = re.compile(r"\bb(\d+)\b")
    out_ops = []
    cancelled_ops = 0
    WIN = 24
    for ln in pass1:
        parts = ln.split()
        name = parts[0].upper()
        qs = tuple(int(m) for m in Q_RE.findall(ln))
        has_b = bool(B_RE.search(ln))
        cur = (name, qs, has_b, ln)

        # Try to cancel against an earlier op within window if all intervening ops commute
        matched_idx = -1
        if name in ("X", "Z", "H", "CX", "CZ") and not has_b:
            lo = max(0, len(out_ops) - WIN)
            for idx in range(len(out_ops) - 1, lo - 1, -1):
                if is_self_inverse_match(out_ops[idx], cur):
                    matched_idx = idx
                    break
                if not gates_commute(out_ops[idx], cur):
                    break
        if matched_idx >= 0:
            out_ops.pop(matched_idx)
            cancelled_ops += 2
        else:
            out_ops.append(cur)

    final_body = [op[3] for op in out_ops]
    lt_after, tch_after = count_q36_lifetimes(final_body)

    full_text = "\n".join(header + final_body) + "\n"
    c_out = km.Circuit(full_text)
    c_out.to_file(str(out), format="kmb")

    # Reload to verify binary round-trip
    c_chk = km.Circuit.from_file(str(out))
    st_in = c_in.operation_statistics()
    st_out = c_chk.operation_statistics()
    sha_out = hashlib.sha256(out.read_bytes()).hexdigest()

    summary = {
        "src_kmb": str(src),
        "out_kmb": str(out),
        "out_sha256": sha_out,
        "in_stats": str(st_in),
        "out_stats": str(st_out),
        "in_ops": len(body),
        "out_ops": len(final_body),
        "ops_removed": len(body) - len(final_body),
        "ops_reduction_pct": round(100.0 * (len(body) - len(final_body)) / len(body), 3),
        "swaps_virtualized": swaps_virtualized,
        "end_restore_swaps": len(restore_swaps),
        "clifford_ops_cancelled": cancelled_ops,
        "q36_lifetimes_before": lt_before,
        "q36_lifetimes_after": lt_after,
        "q36_touches_before": tch_before,
        "q36_touches_after": tch_after,
    }
    print("=== V21 Real KMB Compilation Summary ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    Path(r"c:\Users\81808\.openclaw\gvqcc_v2832\v21_real_kmb_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return summary


if __name__ == "__main__":
    t0 = time.time()
    compile_circuit(SRC_KMB, OUT_KMB)
    print(f"Compiled & serialized in {time.time()-t0:.2f}s. Running official verify_submission_invsqrt.py...", flush=True)
    res = subprocess.run(
        [sys.executable, "-u", r"c:\Users\81808\.openclaw\gvqcc\verifiers\invsqrt\verify_submission_invsqrt.py", str(OUT_KMB)],
        capture_output=True, text=True
    )
    print("VERIFIER EXIT CODE:", res.returncode)
    print(res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr)
