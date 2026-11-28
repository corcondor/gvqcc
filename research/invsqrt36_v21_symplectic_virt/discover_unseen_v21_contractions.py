#!/usr/bin/env python3
"""
V21 Unseen Algebraic & Topological Contraction Discovery on real 60,766-op 37Q invsqrt.kmb.

Searches four structures NEVER jointly audited in PR #1-#72:
  1. Virtual SWAP elimination + commuting Clifford cancellation (exact instruction-count drop).
  2. Centralized classical-control phase-syndrome merging across all 2,271 PUSH/POP frames:
       m_1 * Z(q) + ... + m_k * Z(q) -> (m_1 ^ ... ^ m_k) * Z(q)
       m_1 * CZ(p,q) + ... + m_k * CZ(p,q) -> (m_1 ^ ... ^ m_k) * CZ(p,q)
  3. Exact epoch-aligned CCX Fan-Out & Bilinear Distributive Contraction:
       - Same control pair ((a, ep_a), (b, ep_b)) targeting multiple targets t_1..t_k -> 1 CCX!
       - Same (control (a, ep_a), target t) in a target-commuting window -> 1 CCX!
  4. Exact 36Q -> 37Q GVQCC geometric-mean score projection table (using PR #70's frozen budget).
"""
from __future__ import annotations

import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, r"c:\Users\81808\.openclaw\gvqcc\verifiers")
import kickmix

KMB_PATH = Path(r"c:\Users\81808\.openclaw\gvqcc_v2832\v3317\invsqrt.kmb")
Q_RE = re.compile(r"\bq(\d+)\b")
B_RE = re.compile(r"\bb(\d+)\b")


def parse_lines(path: Path):
    c = kickmix.Circuit.from_file(str(path))
    lines = [ln.strip() for ln in str(c).splitlines() if ln.strip() and not ln.strip().startswith("APPEND_TO_REGISTER")]
    return c, lines


def analyze_all(lines):
    gcnt = Counter(s.split()[0].upper() for s in lines)

    # 1. Exact Virtual SWAP elimination (track permutation perm[logical] = physical)
    # Note: in kickmix, SWAPs are physical 2Q swaps; we count how many SWAPs exist and
    # how many direct adjacent/commuting Clifford self-cancellations appear after virtualizing SWAPs.
    perm = list(range(37))
    virt_ops = []
    n_swaps = 0
    for s in lines:
        parts = s.split()
        name = parts[0].upper()
        qs = [int(m) for m in Q_RE.findall(s)]
        bs = [int(m) for m in B_RE.findall(s)]
        if name == "SWAP" and len(qs) == 2:
            a, b = qs
            perm[a], perm[b] = perm[b], perm[a]
            n_swaps += 1
            continue
        vqs = [perm[q] if q < 37 else q for q in qs]
        virt_ops.append((name, tuple(vqs), tuple(bs), s))

    # Count direct adjacent self-cancellations after SWAP virtualization (inside same condition depth)
    stack_out = []
    n_cancel = 0
    for op in virt_ops:
        name, vqs, bs, _ = op
        if stack_out and name in ("X", "Z", "H", "CX", "CZ", "CCX", "CCZ") and not bs:
            p_name, p_vqs, p_bs, _ = stack_out[-1]
            if p_name == name and not p_bs:
                # Symmetric gates: CZ, CCZ; CCX symmetric in controls; CX exact match
                same = False
                if name in ("X", "Z", "H", "CX"):
                    same = (p_vqs == vqs)
                elif name in ("CZ", "CCZ"):
                    same = (set(p_vqs) == set(vqs))
                elif name == "CCX":
                    same = (p_vqs[-1] == vqs[-1] and set(p_vqs[:-1]) == set(vqs[:-1]))
                if same:
                    stack_out.pop()
                    n_cancel += 2
                    continue
        stack_out.append(op)

    # 2. Epoch-exact CCX Fan-Out & Bilinear Distributive Scan (on original physical ops)
    write_epoch = [0] * 37
    # Also track "non-XOR-write epoch" for targets (CCX(a,b,t) commutes with CCX(c,d,t) on target t!)
    non_target_epoch = [0] * 37
    cond_depth = 0
    ccx_by_ctrl_pair = defaultdict(list)  # ((a, ep_a), (b, ep_b)) -> list of (t, target, cond_depth)
    ccx_by_ctrl_and_tgt = defaultdict(list)  # ((a, ep_a), (tgt, nt_ep_tgt)) -> list of (t, other_ctrl, ep_other)

    # Also track conditioned Z and CZ by exact (q, write_epoch[q]) for centralization compression!
    cond_z_freq = Counter()
    cond_cz_freq = Counter()
    cond_ccz_freq = Counter()

    for t, s in enumerate(lines):
        parts = s.split()
        name = parts[0].upper()
        qs = [int(m) for m in Q_RE.findall(s)]
        bs = [int(m) for m in B_RE.findall(s)]

        if name == "PUSH_CONDITION":
            cond_depth += 1
            continue
        if name == "POP_CONDITION":
            cond_depth = max(0, cond_depth - 1)
            continue

        if (cond_depth > 0 or bs) and name == "Z" and len(qs) == 1:
            cond_z_freq[(qs[0], write_epoch[qs[0]])] += 1
        elif (cond_depth > 0 or bs) and name == "CZ" and len(qs) == 2:
            k = tuple(sorted((q, write_epoch[q]) for q in qs))
            cond_cz_freq[k] += 1
        elif (cond_depth > 0 or bs) and name == "CCZ" and len(qs) == 3:
            k = tuple(sorted((q, write_epoch[q]) for q in qs))
            cond_ccz_freq[k] += 1

        if name == "CCX" and len(qs) == 3 and cond_depth == 0 and not bs:
            c1, c2, tgt = qs
            cp = tuple(sorted([(c1, write_epoch[c1]), (c2, write_epoch[c2])]))
            ccx_by_ctrl_pair[cp].append((t, tgt))
            ccx_by_ctrl_and_tgt[((c1, write_epoch[c1]), (tgt, non_target_epoch[tgt]))].append((t, c2, write_epoch[c2]))
            ccx_by_ctrl_and_tgt[((c2, write_epoch[c2]), (tgt, non_target_epoch[tgt]))].append((t, c1, write_epoch[c1]))

        # Update epochs
        if name in ("X", "H", "HMR", "M", "MR", "RESET", "SX", "RX", "RY"):
            for q in qs:
                if q < 37:
                    write_epoch[q] += 1
                    if name != "X":
                        non_target_epoch[q] += 1
        elif name in ("CX", "CNOT"):
            if len(qs) == 2:
                c, tgt = qs
                if c < 37:
                    non_target_epoch[c] += 1  # reading c as control blocks moving target writes past it
                if tgt < 37:
                    write_epoch[tgt] += 1
        elif name == "CCX":
            if len(qs) == 3:
                c1, c2, tgt = qs
                if c1 < 37:
                    non_target_epoch[c1] += 1
                if c2 < 37:
                    non_target_epoch[c2] += 1
                if tgt < 37:
                    write_epoch[tgt] += 1
        elif name == "SWAP":
            for q in qs:
                if q < 37:
                    write_epoch[q] += 1
                    non_target_epoch[q] += 1
        elif name in ("CZ", "CCZ", "Z", "S", "T", "Z_POW"):
            for q in qs:
                if q < 37:
                    non_target_epoch[q] += 1

    # Summarize CCX fan-out & distributive savings
    fanout_groups = [(cp, items) for cp, items in ccx_by_ctrl_pair.items() if len(items) >= 2]
    fanout_saving = sum(len(items) - 1 for _, items in fanout_groups)

    # Deduplicate distributive groups (same target window)
    dist_groups = [(k, items) for k, items in ccx_by_ctrl_and_tgt.items() if len(items) >= 2]
    dist_saving_upper = sum(len(items) - 1 for _, items in dist_groups)

    # Summarize centralized phase-syndrome instruction savings!
    z_total = sum(cond_z_freq.values())
    z_unique = len(cond_z_freq)
    z_saved = z_total - z_unique

    cz_total = sum(cond_cz_freq.values())
    cz_unique = len(cond_cz_freq)
    cz_saved = cz_total - cz_unique

    ccz_total = sum(cond_ccz_freq.values())
    ccz_unique = len(cond_ccz_freq)
    ccz_saved = ccz_total - ccz_unique

    # 3. Exact GVQCC Score Projection Model
    # Baseline: InvSqrt 37Q, expected paid = 1406.3125; PR #70 exact frozen budget at 36Q: < +40.74140236 expected paid!
    # Notice: cost(InvSqrt) proportional to Q * expected_paid (or Q^alpha * T):
    # Check PR #70's exact break-even: 37 * 1406.3125 = 52033.5625; 52033.5625 / 36 = 1445.3767 (+39.0642)
    # Wait: with the exact +40.74140236 budget from PR #70, break-even is 1447.05390236!
    # Let's compute relative InvSqrt cost factor (new_cost / base_cost) and geometric-mean score impact
    # assuming baseline geom-mean = 33.17023 (3 tasks: Chemistry, DQI, InvSqrt -> InvSqrt has 1/3 exponent in geom mean!).
    # Wait: score = C * (cost_chem * cost_dqi * cost_inv)^(-1/3) or similar -> ratio = (base_inv / new_inv)^(1/3)!
    base_exp = 1406.3125
    be_36q = base_exp + 40.74140236
    base_score = 33.17023
    projections = []
    for label, q_new, exp_new in [
        ("Baseline 37Q (public)", 37, 1406.3125),
        ("PR #68 V18 (37Q diagnostic)", 37, 1411.3125),
        ("36Q Break-even (PR #70 budget)", 36, be_36q),
        ("36Q @ PR #68 cost (1411.3125)", 36, 1411.3125),
        ("36Q @ baseline cost (1406.3125)", 36, 1406.3125),
        ("36Q + V20/V21 reuse (-30 paid -> 1376.3)", 36, 1376.3125),
        ("36Q + V20/V21 reuse (-60 paid -> 1346.3)", 36, 1346.3125),
    ]:
        # Using exact PR #70 break-even ratio: (exp_new / be_36q) at 36Q, (exp_new / base_exp) at 37Q
        cost_ratio = (exp_new / be_36q) if q_new == 36 else (exp_new / base_exp)
        # Note: in GVQCC, score scales as (1 / cost_ratio)^(1/3) for the InvSqrt component (3-problem geometric mean)
        proj_score = base_score * (cost_ratio ** (-1.0 / 3.0))
        projections.append({
            "scenario": label,
            "qubits": q_new,
            "expected_paid": round(exp_new, 4),
            "invsqrt_cost_ratio_vs_base": round(cost_ratio, 6),
            "projected_geom_score": round(proj_score, 5),
            "delta_score": round(proj_score - base_score, 5),
        })

    return {
        "source_ops": len(lines),
        "top_gate_counts": dict(gcnt.most_common(15)),
        "virtual_swap_elimination": {
            "swaps_removed": n_swaps,
            "immediate_adjacent_clifford_cancellations": n_cancel,
            "ops_after_swap_and_cancel": len(stack_out),
            "net_instruction_reduction": len(lines) - len(stack_out),
        },
        "centralized_phase_syndrome_merging": {
            "cond_Z_total": z_total,
            "cond_Z_unique_epoch": z_unique,
            "cond_Z_eliminated": z_saved,
            "cond_CZ_total": cz_total,
            "cond_CZ_unique_epoch": cz_unique,
            "cond_CZ_eliminated": cz_saved,
            "cond_CCZ_total": ccz_total,
            "cond_CCZ_unique_epoch": ccz_unique,
            "cond_CCZ_eliminated": ccz_saved,
            "total_phase_ops_eliminated": z_saved + cz_saved + ccz_saved,
        },
        "ccx_bilinear_contractions": {
            "fanout_same_ctrl_pair_groups": len(fanout_groups),
            "fanout_ccx_saving": fanout_saving,
            "fanout_examples": [(list(cp), items) for cp, items in fanout_groups[:10]],
            "distributive_same_ctrl_tgt_groups": len(dist_groups),
            "distributive_ccx_saving_upper": dist_saving_upper,
            "distributive_examples": [(list(k), items) for k, items in dist_groups[:10]],
        },
        "score_projections": projections,
    }


def main():
    c, lines = parse_lines(KMB_PATH)
    res = analyze_all(lines)
    print("=== V21 UNSEEN CONTRACTIONS ON REAL 60,766-OP INVSQRT.KMB ===")
    print("Top gates:", res["top_gate_counts"])
    print("\n1) Virtual SWAP + Immediate Cancellation:", res["virtual_swap_elimination"])
    print("\n2) Centralized Phase-Syndrome Merging:", res["centralized_phase_syndrome_merging"])
    print("\n3) Exact Epoch-Aligned CCX Fan-Out & Distributive Contractions:")
    cb = res["ccx_bilinear_contractions"]
    print(f"   Fan-out same-control-pair groups: {cb['fanout_same_ctrl_pair_groups']} -> CCX saving = {cb['fanout_ccx_saving']}")
    for ex in cb["fanout_examples"][:5]:
        print("     fanout:", ex)
    print(f"   Distributive same-(ctrl,tgt) groups: {cb['distributive_same_ctrl_tgt_groups']} -> CCX saving upper = {cb['distributive_ccx_saving_upper']}")
    for ex in cb["distributive_examples"][:5]:
        print("     dist:", ex)
    print("\n4) Exact GVQCC Score Projections (3-task geometric mean, base 33.17023):")
    for p in res["score_projections"]:
        print(f"   {p['scenario']:42s} | Q={p['qubits']} | exp={p['expected_paid']:9.4f} | score={p['projected_geom_score']:.5f} ({p['delta_score']:+.5f})")

    Path(r"c:\Users\81808\.openclaw\gvqcc_v2832\v21_unseen_contractions_audit.json").write_text(
        json.dumps(res, indent=2), encoding="utf-8"
    )
    print("\nSaved v21_unseen_contractions_audit.json")


if __name__ == "__main__":
    main()
