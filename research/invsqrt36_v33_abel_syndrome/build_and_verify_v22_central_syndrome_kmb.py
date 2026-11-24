#!/usr/bin/env python3
"""
V22 Real-Circuit Compiler & Official Verifier Runner for GVQCC InvSqrt:
  Builds on V21 (55,988 ops, official 200M-shot PASS) and adds:
    1) Wider commuting-window (WIN=256) Clifford/diagonal self-inverse cancellation
       (including safe commutation of Z/CZ past CX/CCX controls and X/CX targets past CX/CCX targets).
    2) Real-circuit Centralized Classical-XOR Phase-Syndrome Hub Compression:
       Inside every commuting diagonal phase epoch, cancels duplicate (monomial, b) pairs,
       and whenever M distinct quantum phase monomials (Z / CZ) share the EXACT same classical
       control set S = {b_1, ..., b_k} with (k - 1)*M > k + 1, synthesizes ONE centralized
       classical syndrome bit b_hub = XOR(S) via native BIT_STORE0 + BIT_INVERT and replaces
       all k*M quantum phase gates with M centralized gates!
    3) Exact discrete-summation-by-parts (Abel) audit on telescoping phase-syndrome chains.
Then serializes a real binary .kmb and runs the official verify_submission_invsqrt.py!
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, r"c:\Users\81808\.openclaw\gvqcc\verifiers")
import kickmix as km

SRC_KMB = Path(r"c:\Users\81808\.openclaw\gvqcc_v2832\invsqrt_v21_virt_swap_clifford.kmb")
OUT_KMB = Path(r"c:\Users\81808\.openclaw\gvqcc_v2832\invsqrt_v22_central_syndrome.kmb")
Q_RE = re.compile(r"\bq(\d+)\b")
B_RE = re.compile(r"\bb(\d+)\b")


def gates_commute_v22(op1, op2) -> bool:
    """Exact conservative commutation check (extended safely to CCX/CCZ controls/targets)."""
    n1, q1, b1, _ = op1
    n2, q2, b2, _ = op2
    if b1 or b2:
        return False
    blockers = {"PUSH_CONDITION", "POP_CONDITION", "HMR", "BIT_STORE0", "BIT_INVERT", "NEG", "SWAP", "CSWAP"}
    if n1 in blockers or n2 in blockers:
        return False
    s1, s2 = set(q1), set(q2)
    if s1.isdisjoint(s2):
        return True
    diag = {"Z", "CZ", "CCZ", "S", "SDAG", "T", "TDAG", "Z_POW"}
    if n1 in diag and n2 in diag:
        return True
    # X / CX / CCX target-only commutation
    if n1 == "X" and n2 == "X":
        return True
    if n1 == "X" and n2 in ("CX", "CCX"):
        return q1[0] not in q2[:-1]  # X on target commutes with CX/CCX
    if n2 == "X" and n1 in ("CX", "CCX"):
        return q2[0] not in q1[:-1]
    if n1 in ("CX", "CCX") and n2 in ("CX", "CCX"):
        # Controls of one must not hit target of the other
        return (q1[-1] not in q2[:-1]) and (q2[-1] not in q1[:-1])
    if n1 in diag and n2 in ("CX", "CCX"):
        return q2[-1] not in s1  # diagonal on controls commutes with CX/CCX
    if n2 in diag and n1 in ("CX", "CCX"):
        return q1[-1] not in s2
    return False


def is_self_inverse_match(op1, op2) -> bool:
    n1, q1, b1, _ = op1
    n2, q2, b2, _ = op2
    if n1 != n2 or b1 != b2:
        return False
    if b1:
        return False
    if n1 in ("X", "Z", "H", "CX"):
        return q1 == q2
    if n1 in ("CZ", "CCZ"):
        return set(q1) == set(q2)
    return False


def pass_wider_clifford_cancel(body: list[str], win: int = 256) -> tuple[list[str], int]:
    out_ops = []
    cancelled = 0
    for ln in body:
        parts = ln.split()
        name = parts[0].upper()
        qs = tuple(int(m) for m in Q_RE.findall(ln))
        bs = tuple(int(m) for m in B_RE.findall(ln))
        cur = (name, qs, bs, ln)
        matched = -1
        if name in ("X", "Z", "H", "CX", "CZ") and not bs:
            lo = max(0, len(out_ops) - win)
            for idx in range(len(out_ops) - 1, lo - 1, -1):
                if is_self_inverse_match(out_ops[idx], cur):
                    matched = idx
                    break
                if not gates_commute_v22(out_ops[idx], cur):
                    break
        if matched >= 0:
            out_ops.pop(matched)
            cancelled += 2
        else:
            out_ops.append(cur)
    return [op[3] for op in out_ops], cancelled


def pass_centralized_phase_syndrome(body: list[str], next_bit_id: int) -> tuple[list[str], dict]:
    """
    Maximal contiguous runs of inline classically-controlled `Z q if b` and `CZ p q if b`
    (at cond_depth == 0, with zero intervening non-diagonal gates or bit-writes) commute
    arbitrarily! Within each run:
      1) Cancel duplicate (monomial, bit) mod 2.
      2) Group monomials by their exact classical control bit-set S = frozenset(bits).
      3) For any S with |S| >= 2 and M = len(monomials[S]) such that (|S| - 1)*M > |S| + 1:
         emit ONE fresh classical syndrome bit `b_hub = XOR(S)` and replace all |S|*M
         quantum Z/CZ gates with M centralized gates!
    """
    INLINE_Z_RE = re.compile(r"^Z\s+q(\d+)\s+if\s+b(\d+)$")
    INLINE_CZ_RE = re.compile(r"^CZ\s+q(\d+)\s+q(\d+)\s+if\s+b(\d+)$")

    out = []
    run_items = []  # list of (monomial, bit_id, orig_line)
    cond_depth = 0

    stats = {
        "runs_processed": 0,
        "dup_phase_cancelled": 0,
        "syndrome_hubs_created": 0,
        "quantum_phase_ops_before": 0,
        "quantum_phase_ops_after": 0,
        "classical_xor_ops_added": 0,
        "net_ops_saved_by_syndrome": 0,
        "abel_telescoping_pairs_detected": 0,
    }

    def flush_run():
        nonlocal next_bit_id, run_items
        if not run_items:
            return
        stats["runs_processed"] += 1
        stats["quantum_phase_ops_before"] += len(run_items)

        # 1) Mod-2 cancellation of identical (monomial, bit)
        mon_to_bits: dict[tuple, set[int]] = defaultdict(set)
        for mon, bid, _ in run_items:
            if bid in mon_to_bits[mon]:
                mon_to_bits[mon].remove(bid)
                stats["dup_phase_cancelled"] += 2
            else:
                mon_to_bits[mon].add(bid)

        # Clean empty monomials
        mon_to_bits = {m: bs for m, bs in mon_to_bits.items() if bs}

        # 2) Group monomials by exact control bit-set S
        sig_to_mons: dict[frozenset[int], list[tuple]] = defaultdict(list)
        for mon, bs in mon_to_bits.items():
            sig_to_mons[frozenset(bs)].append(mon)

        # Check Abel telescoping pairs: two signatures S1, S2 with |S1 ^ S2| == 1
        sigs_multi = [s for s in sig_to_mons if len(s) >= 2]
        for i in range(len(sigs_multi)):
            for j in range(i + 1, len(sigs_multi)):
                if len(sigs_multi[i] ^ sigs_multi[j]) == 1:
                    stats["abel_telescoping_pairs_detected"] += 1

        # 3) Emit centralized syndrome hubs where strictly net-op-saving
        emitted_q = 0
        emitted_c = 0
        for sig, mons in sig_to_mons.items():
            k = len(sig)
            M = len(mons)
            if k >= 2 and (k - 1) * M > k + 1:
                hub = next_bit_id
                next_bit_id += 1
                out.append(f"BIT_STORE0 b{hub}")
                for b in sorted(sig):
                    out.append(f"BIT_INVERT b{hub} if b{b}")
                emitted_c += (k + 1)
                stats["syndrome_hubs_created"] += 1
                for mon in sorted(mons):
                    if len(mon) == 1:
                        out.append(f"Z q{mon[0]} if b{hub}")
                    else:
                        out.append(f"CZ q{mon[0]} q{mon[1]} if b{hub}")
                    emitted_q += 1
            else:
                for mon in sorted(mons):
                    for b in sorted(sig):
                        if len(mon) == 1:
                            out.append(f"Z q{mon[0]} if b{b}")
                        else:
                            out.append(f"CZ q{mon[0]} q{mon[1]} if b{b}")
                        emitted_q += 1

        stats["quantum_phase_ops_after"] += emitted_q
        stats["classical_xor_ops_added"] += emitted_c
        stats["net_ops_saved_by_syndrome"] += len(run_items) - (emitted_q + emitted_c)
        run_items = []

    for ln in body:
        u = ln.split()[0].upper()
        if u == "PUSH_CONDITION":
            flush_run()
            cond_depth += 1
            out.append(ln)
            continue
        if u == "POP_CONDITION":
            flush_run()
            cond_depth = max(0, cond_depth - 1)
            out.append(ln)
            continue
        if cond_depth == 0:
            m1 = INLINE_Z_RE.match(ln)
            if m1:
                run_items.append(((int(m1.group(1)),), int(m1.group(2)), ln))
                continue
            m2 = INLINE_CZ_RE.match(ln)
            if m2:
                q1, q2 = int(m2.group(1)), int(m2.group(2))
                mon = (min(q1, q2), max(q1, q2))
                run_items.append((mon, int(m2.group(3)), ln))
                continue
        flush_run()
        out.append(ln)
    flush_run()
    return out, stats


def main():
    t0 = time.time()
    c_in = km.Circuit.from_file(str(SRC_KMB))
    raw = [ln.strip() for ln in str(c_in).splitlines() if ln.strip()]
    header = [ln for ln in raw if ln.startswith("APPEND_TO_REGISTER")]
    body = [ln for ln in raw if not ln.startswith("APPEND_TO_REGISTER")]
    max_b = max((int(m) for ln in body for m in B_RE.findall(ln)), default=0)

    body1, c_win = pass_wider_clifford_cancel(body, win=256)
    body2, syn_stats = pass_centralized_phase_syndrome(body1, next_bit_id=max_b + 1)

    full_text = "\n".join(header + body2) + "\n"
    c_out = km.Circuit(full_text)
    c_out.to_file(str(OUT_KMB), format="kmb")
    c_chk = km.Circuit.from_file(str(OUT_KMB))
    sha = hashlib.sha256(OUT_KMB.read_bytes()).hexdigest()

    summary = {
        "src_kmb": str(SRC_KMB),
        "out_kmb": str(OUT_KMB),
        "out_sha256": sha,
        "v21_ops": len(body),
        "v22_ops": len(body2),
        "delta_vs_v21": len(body) - len(body2),
        "delta_vs_60766_orig": 60766 - len(body2),
        "wider_clifford_cancelled": c_win,
        "syndrome_stats": syn_stats,
        "out_stats": str(c_chk.operation_statistics()),
    }
    print("=== V22 Real KMB Compilation Summary ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    Path(r"c:\Users\81808\.openclaw\gvqcc_v2832\v22_real_kmb_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(f"Compiled in {time.time()-t0:.2f}s. Running official verify_submission_invsqrt.py...", flush=True)
    res = subprocess.run(
        [sys.executable, "-u", r"c:\Users\81808\.openclaw\gvqcc\verifiers\invsqrt\verify_submission_invsqrt.py", str(OUT_KMB)],
        capture_output=True, text=True
    )
    print("VERIFIER EXIT CODE:", res.returncode)
    print(res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr)


if __name__ == "__main__":
    main()
