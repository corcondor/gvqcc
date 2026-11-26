"""
V71 Mathematical Circuit Compressor:
  1. Commutation-Driven Affine Block Merging:
     - Moves CX(c,t) and X(q) across commuting diagonal gates (Z if b, CZ if b) and commuting CCX(a,b,d)
       whenever the standard Pauli/Clifford commutation rules hold:
         * X(q) commutes with CCX(a,b,d) iff q not in {a, b} (wait: X on target d commutes with CCX!)
         * X(q) commutes with Z(a) / CZ(a,b) iff q not in {a, b}
         * CX(c,t) commutes with Z(a) iff t != a; commutes with CZ(a,b) iff t not in {a, b}
         * CX(c,t) commutes with CCX(a,b,d) iff t not in {a, b} and c != d
     - This fuses fragmented {X, CX} strips separated by CZ-phase-fixes / CCX into large GF(2) affine blocks!
  2. Multi-Strategy Exact GF(2) Linear Synthesis on each fused affine block (M, v):
     - Strategy A: Greedy Minimum-Weight Cancellation / Boyar-Peralta-inspired row/col reduction
       (repeatedly pick the pair (i, j) maximizing Hamming-weight drop in M, then finish with Gaussian elim).
     - Strategy B: Sparsity-Ordered PMH (permute rows/cols by ascending Hamming weight, run PMH widths 1..6,
       both on M and M^T).
     - Strategy C: Bidirectional Peephole CX/X cancellation inside the block.
     - Strictly replaces a block ONLY when gate count strictly drops AND exact algebraic equality (M'==M, v'==v) holds!
"""

import sys
import time
from pathlib import Path
import numpy as np

sys.path.insert(0, r"c:\Users\81808\.openclaw\gvqcc\verifiers")
import kickmix as km

SRC_DIR = Path(r"c:\Users\81808\.openclaw\gvqcc_v2832\v70_fam_3275_ultra")
DST_DIR = Path(r"c:\Users\81808\.openclaw\gvqcc_v2832\v71_fam_3275_mathopt")


def eval_affine(ops, qmap):
    k = len(qmap)
    M = np.eye(k, dtype=np.uint8)
    v = np.zeros(k, dtype=np.uint8)
    for op in ops:
        if op[0] == "X":
            v[qmap[op[1]]] ^= 1
        else:
            c, t = qmap[op[1]], qmap[op[2]]
            M[t] ^= M[c]
            v[t] ^= v[c]
    return M, v


def pmh_lower(M_in, m):
    k = M_in.shape[0]
    A = M_in.copy()
    ops = []
    n_sec = (k + m - 1) // m
    for sec in range(n_sec):
        c0 = sec * m
        c1 = min(k, c0 + m)
        seen = {}
        for r in range(c0, k):
            pat = 0
            for c in range(c0, c1):
                if A[r, c]:
                    pat |= 1 << (c - c0)
            if pat == 0:
                continue
            if pat in seen:
                src = seen[pat]
                A[r] ^= A[src]
                ops.append((src, r))
            else:
                seen[pat] = r
        for c in range(c0, c1):
            if A[c, c] == 0:
                piv = next(r for r in range(c + 1, k) if A[r, c])
                A[c] ^= A[piv]
                ops.append((piv, c))
            for r in range(c + 1, k):
                if A[r, c]:
                    A[r] ^= A[c]
                    ops.append((c, r))
    return A, ops


def synth_pmh_perm(M_target, m, perm=None):
    """Run PMH on P M P^T and unpermute."""
    k = M_target.shape[0]
    if perm is not None:
        P = np.array(perm, dtype=np.int32)
        Mp = M_target[np.ix_(P, P)]
    else:
        Mp = M_target
    U, ops_lo = pmh_lower(Mp, m)
    U_rev = U[::-1, ::-1].copy()
    _, ops_up_rev = pmh_lower(U_rev, m)
    ops_up = [(k - 1 - c, k - 1 - t) for (c, t) in ops_up_rev]
    all_ops = ops_lo + ops_up
    all_ops.reverse()
    if perm is not None:
        all_ops = [(int(perm[c]), int(perm[t])) for (c, t) in all_ops]
    return all_ops


def synth_greedy_weight(M_target, limit_steps=2000):
    """
    Greedy Hamming-weight descent (Boyar-Peralta / Paar style) on GF(2) matrix M -> I:
    At each step, find (c, t) that maximizes weight reduction of row t (with bonus for making row t unit weight),
    then finish any remaining off-diagonal entries with PMH!
    """
    k = M_target.shape[0]
    # Pack rows into Python ints for ultra-fast popcount!
    rows = [0] * k
    for r in range(k):
        val = 0
        for c in range(k):
            if M_target[r, c]:
                val |= 1 << c
        rows[r] = val

    ops = []
    # Greedy reduction while strictly decreasing total Hamming weight (excluding diagonal bonus)
    for _ in range(limit_steps):
        # Compute weights
        wts = [r.bit_count() for r in rows]
        if sum(wts) == k:
            # Permutation matrix! Check if identity
            break
        best_gain = 0
        best_pair = None
        # Only consider rows with wt > 1 as targets (or any row if we want to create unit rows)
        for t in range(k):
            rt = rows[t]
            wt = wts[t]
            if wt <= 1:
                continue
            for c in range(k):
                if c == t:
                    continue
                nw = (rt ^ rows[c]).bit_count()
                gain = wt - nw
                if gain > best_gain:
                    best_gain = gain
                    best_pair = (c, t)
        if best_gain <= 0:
            break
        c, t = best_pair
        rows[t] ^= rows[c]
        ops.append((c, t))

    # Convert remaining rows back to numpy and finish with PMH(m=2)
    rem = np.zeros((k, k), dtype=np.uint8)
    for r in range(k):
        v = rows[r]
        for c in range(k):
            if (v >> c) & 1:
                rem[r, c] = 1
    tail_ops = synth_pmh_perm(rem, 2)
    # Note: `ops` turns M_target -> rem, and `tail_ops` builds rem from I.
    # So applying `tail_ops` then `reversed(ops)` builds M_target from I!
    return tail_ops + list(reversed(ops))


def compress_affine_block(block_ops):
    if len(block_ops) <= 2:
        return block_ops
    qs = sorted({q for op in block_ops for q in op[1:]})
    k = len(qs)
    qmap = {q: i for i, q in enumerate(qs)}
    M, v = eval_affine(block_ops, qmap)
    n_x = int(v.sum())

    best_ops = block_ops
    best_len = len(block_ops)

    def try_cx(cx_local):
        nonlocal best_ops, best_len
        if len(cx_local) + n_x >= best_len:
            return
        cand = [("CX", qs[c], qs[t]) for (c, t) in cx_local]
        for i in range(k):
            if v[i]:
                cand.append(("X", qs[i]))
        Mc, vc = eval_affine(cand, qmap)
        if np.array_equal(Mc, M) and np.array_equal(vc, v):
            best_ops = cand
            best_len = len(cand)

    # 1) Greedy Hamming-weight descent on M and M^T (fast for k <= 64)
    if k <= 70:
        try_cx(synth_greedy_weight(M))
        cx_mt = synth_greedy_weight(M.T.copy())
        try_cx([(t, c) for (c, t) in reversed(cx_mt)])

    # 2) Sparsity-ordered PMH on M and M^T
    # Order qubits by ascending row+col weight in M
    deg = M.sum(axis=0) + M.sum(axis=1)
    perm_asc = list(np.argsort(deg))
    perm_desc = list(np.argsort(-deg))
    for perm in (None, perm_asc, perm_desc):
        for m in range(1, min(6, k) + 1):
            try_cx(synth_pmh_perm(M, m, perm))
            cx_mt = synth_pmh_perm(M.T.copy(), m, perm)
            try_cx([(t, c) for (c, t) in reversed(cx_mt)])

    return best_ops


def can_commute_affine_past_barrier(aff_op, bar_toks):
    """Exact Clifford/Toffoli commutation check: can X/CX move past a non-affine gate?"""
    bcmd = bar_toks[0]
    if aff_op[0] == "X":
        q = aff_op[1]
        if bcmd == "Z":
            return q != int(bar_toks[1][1:])
        if bcmd == "CZ":
            return q != int(bar_toks[1][1:]) and q != int(bar_toks[2][1:])
        if bcmd == "CCX":
            # X on target commutes with CCX; X on either control does NOT
            return q != int(bar_toks[1][1:]) and q != int(bar_toks[2][1:])
        if bcmd == "HMR":
            return q != int(bar_toks[1][1:])
        return False
    else:  # ("CX", c, t)
        c, t = aff_op[1], aff_op[2]
        if bcmd == "Z":
            return t != int(bar_toks[1][1:])
        if bcmd == "CZ":
            return t != int(bar_toks[1][1:]) and t != int(bar_toks[2][1:])
        if bcmd == "CCX":
            a, b, d = int(bar_toks[1][1:]), int(bar_toks[2][1:]), int(bar_toks[3][1:])
            return (t != a) and (t != b) and (c != d)
        if bcmd == "HMR":
            q = int(bar_toks[1][1:])
            return (c != q) and (t != q)
        return False


def commute_and_fuse_pass(lines):
    """
    Push affine ops (X, CX) leftward past commuting Z/CZ barriers (and pull rightward)
    to fuse adjacent affine blocks separated only by measurement-phase CZ/Z gates!
    """
    # Represent each instruction as (is_aff, data)
    seq = []
    for ln in lines:
        toks = ln.split()
        cmd = toks[0]
        if cmd == "X" and len(toks) == 2:
            seq.append((True, ("X", int(toks[1][1:]))))
        elif cmd == "CX" and len(toks) == 3:
            seq.append((True, ("CX", int(toks[1][1:]), int(toks[2][1:]))))
        else:
            seq.append((False, (ln, toks)))

    # Bubble Z / CZ barriers rightward past commuting affine ops so affine blocks merge!
    # Do a single linear sweep maintaining a small buffer of deferred Z/CZ gates.
    out = []
    deferred_diag = []  # list of (ln, toks) for Z / CZ only!
    for is_aff, data in seq:
        if not is_aff:
            ln, toks = data
            if toks[0] in ("Z", "CZ"):
                deferred_diag.append((ln, toks))
            else:
                # Flush all deferred_diag before CCX / HMR / etc.
                for dln, dtoks in deferred_diag:
                    out.append((False, (dln, dtoks)))
                deferred_diag.clear()
                out.append((False, data))
        else:
            # Check if aff_op commutes with ALL deferred_diag!
            # Only flush those deferred_diag that DO NOT commute with aff_op (keeping relative order among Z/CZ, which all commute with each other!).
            still_deferred = []
            for dln, dtoks in deferred_diag:
                if can_commute_affine_past_barrier(data, dtoks):
                    still_deferred.append((dln, dtoks))
                else:
                    out.append((False, (dln, dtoks)))
            deferred_diag = still_deferred
            out.append((True, data))
    for dln, dtoks in deferred_diag:
        out.append((False, (dln, dtoks)))
    return out


def compress_kmb(src_path: Path, dst_path: Path):
    circ = km.Circuit.from_file(str(src_path))
    lines = [ln.strip() for ln in str(circ).splitlines() if ln.strip()]
    in_ops = len(lines)
    in_ccx = sum(1 for ln in lines if ln.startswith("CCX "))

    # Pass 1: Commutation-fuse Z/CZ barriers out of affine blocks
    seq = commute_and_fuse_pass(lines)

    # Pass 2: Resynthesize every maximal affine block
    out_lines = []
    buf = []

    def flush():
        nonlocal buf
        if not buf:
            return
        comp = compress_affine_block(buf)
        for op in comp:
            if op[0] == "X":
                out_lines.append(f"X q{op[1]}")
            else:
                out_lines.append(f"CX q{op[1]} q{op[2]}")
        buf = []

    for is_aff, data in seq:
        if is_aff:
            buf.append(data)
        else:
            flush()
            out_lines.append(data[0])
    flush()

    out_circ = km.Circuit("\n".join(out_lines) + "\n")
    out_circ.to_file(str(dst_path), format="kmb")
    reloaded = km.Circuit.from_file(str(dst_path))
    out_ops = reloaded.operation_statistics().num_instructions
    out_ccx = sum(1 for ln in str(reloaded).splitlines() if ln.startswith("CCX "))
    assert out_ccx == in_ccx
    return in_ops, out_ops, in_ccx


def main():
    t0 = time.time()
    DST_DIR.mkdir(parents=True, exist_ok=True)
    (DST_DIR / "submission.npz").write_bytes((SRC_DIR / "submission.npz").read_bytes())

    tot_in = tot_out = tot_ccx = 0
    for k in range(15):
        src = SRC_DIR / f"angle_k_{k}.kmb"
        dst = DST_DIR / f"angle_k_{k}.kmb"
        io, oo, ccx = compress_kmb(src, dst)
        tot_in += io
        tot_out += oo
        tot_ccx += ccx
        print(f"k={k:2d}: CCX={ccx:3d} | ops {io:6d} -> {oo:6d} ({oo - io:+7d} / {100*(oo-io)/io:+6.2f}%)", flush=True)
    print(f"TOTAL: CCX={tot_ccx} | ops {tot_in} -> {tot_out} ({tot_out - tot_in:+d} / {100*(tot_out-tot_in)/tot_in:+.2f}%) in {time.time()-t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
