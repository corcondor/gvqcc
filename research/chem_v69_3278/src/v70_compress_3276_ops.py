"""
V70 Exact Linear/Affine Block Resynthesis Compressor on the 3,276 (<248M) Chemistry Family.

Method (100% exact unitary equivalence, zero CCX/HMR/CZ changes):
  1. Partition each .kmb into maximal contiguous {X, CX} affine blocks (leaving CCX, HMR, Z, CZ untouched).
  2. For each block touching k active qubits, compute its exact GF(2) affine map (M, v) where y = M x ^ v.
  3. Re-synthesize M using multi-width Patel-Markov-Hayes (PMH) block Gaussian elimination (widths 1..5)
     on both M and M^T (reversed) and greedy pivot selection, keeping the strictly shortest CX+X sequence.
  4. Verify algebraic identity (M_new == M and v_new == v) on every single replaced block!
  5. Reload every output .kmb via kickmix.Circuit.from_file and report exact ops & CCX reductions.
"""

import hashlib
import json
import sys
import time
from pathlib import Path
import numpy as np

sys.path.insert(0, r"c:\Users\81808\.openclaw\gvqcc\verifiers")
import kickmix as km

SRC_DIR = Path(r"c:\Users\81808\.openclaw\gvqcc_v2832\v70_fam_3276_base")
DST_DIR = Path(r"c:\Users\81808\.openclaw\gvqcc_v2832\v70_fam_3276_opt")


def eval_affine_block(ops, qmap):
    """Return (M, v) over GF(2) for a list of ('X', q) / ('CX', c, t) ops on local qubits 0..k-1."""
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
    """
    Patel-Markov-Hayes (2008) lower-triangularization of invertible GF(2) matrix M_in with section width m.
    Returns list of (ctrl, tgt) row ops (row[tgt] ^= row[ctrl]) that reduce M_in to upper triangular,
    so applying them in REVERSE builds M_in from upper triangular.
    """
    k = M_in.shape[0]
    A = M_in.copy()
    ops = []
    n_sec = (k + m - 1) // m
    for sec in range(n_sec):
        c0 = sec * m
        c1 = min(k, c0 + m)
        # Step 1: eliminate duplicate non-zero sub-rows in columns [c0:c1] among rows [c0:k]
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
        # Step 2: standard elimination in columns [c0:c1]
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


def synth_pmh(M_target, m):
    """Full PMH synthesis of invertible GF(2) matrix M_target with block width m."""
    # Reduce M -> U via lower ops, then U^T -> I via lower ops (which are upper ops on U)
    U, ops_lo = pmh_lower(M_target, m)
    # Now reverse row order to reduce U to I using pmh_lower!
    U_rev = U[::-1, ::-1].copy()
    I_chk, ops_up_rev = pmh_lower(U_rev, m)
    k = M_target.shape[0]
    ops_up = [(k - 1 - c, k - 1 - t) for (c, t) in ops_up_rev]
    # ops_lo followed by ops_up turns M_target into I; so applying (ops_lo + ops_up) in REVERSE turns I into M_target!
    all_ops = ops_lo + ops_up
    all_ops.reverse()
    return all_ops


def compress_affine_block(block_ops):
    """Try PMH with widths 1..5 on M and M^T (dual), return shortest exact [('X', q) | ('CX', c, t)] list."""
    if len(block_ops) <= 2:
        return block_ops
    qs = sorted({q for op in block_ops for q in op[1:]})
    k = len(qs)
    qmap = {q: i for i, q in enumerate(qs)}
    M, v = eval_affine_block(block_ops, qmap)

    best_ops = block_ops
    best_len = len(block_ops)
    n_x = int(v.sum())

    # Try PMH on M with m in 1..min(6, k)
    for m in range(1, min(6, k) + 1):
        cx_local = synth_pmh(M, m)
        if len(cx_local) + n_x < best_len:
            cand = [("CX", qs[c], qs[t]) for (c, t) in cx_local]
            for i in range(k):
                if v[i]:
                    cand.append(("X", qs[i]))
            # Verify exactness!
            Mc, vc = eval_affine_block(cand, qmap)
            if np.array_equal(Mc, M) and np.array_equal(vc, v):
                best_ops = cand
                best_len = len(cand)

    # Also try synthesizing M^{-1} (transpose/inverse dual):
    # Note: for a linear circuit implementing M, reversing the circuit gives M^{-1},
    # and transposing every CX(c,t) -> CX(t,c) + reversing gives M^T!
    # So synthesizing M^T gives ops for M by reversing and swapping (c,t) -> (t,c)!
    MT = M.T.copy()
    for m in range(1, min(6, k) + 1):
        cx_mt = synth_pmh(MT, m)
        if len(cx_mt) + n_x < best_len:
            # Reverse and swap (c, t) -> (t, c)
            cx_local = [(t, c) for (c, t) in reversed(cx_mt)]
            cand = [("CX", qs[c], qs[t]) for (c, t) in cx_local]
            for i in range(k):
                if v[i]:
                    cand.append(("X", qs[i]))
            Mc, vc = eval_affine_block(cand, qmap)
            if np.array_equal(Mc, M) and np.array_equal(vc, v):
                best_ops = cand
                best_len = len(cand)

    return best_ops


def compress_kmb(src_path: Path, dst_path: Path):
    circ = km.Circuit.from_file(str(src_path))
    lines = [ln.strip() for ln in str(circ).splitlines() if ln.strip()]
    in_ops = len(lines)
    in_ccx = sum(1 for ln in lines if ln.startswith("CCX "))

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

    for ln in lines:
        toks = ln.split()
        cmd = toks[0]
        if cmd == "X" and len(toks) == 2:
            buf.append(("X", int(toks[1][1:])))
        elif cmd == "CX" and len(toks) == 3:
            buf.append(("CX", int(toks[1][1:]), int(toks[2][1:])))
        else:
            flush()
            out_lines.append(ln)
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
    # Copy submission.npz byte-identical
    (DST_DIR / "submission.npz").write_bytes((SRC_DIR / "submission.npz").read_bytes())

    tot_in = tot_out = tot_ccx = 0
    for k in range(15):
        src = SRC_DIR / f"angle_k_{k}.kmb"
        dst = DST_DIR / f"angle_k_{k}.kmb"
        io, oo, ccx = compress_kmb(src, dst)
        tot_in += io
        tot_out += oo
        tot_ccx += ccx
        print(f"k={k:2d}: CCX={ccx:3d} | ops {io:6d} -> {oo:6d} ({oo - io:+7d} / {100*(oo-io)/io:+6.2f}%)")
    print(f"TOTAL: CCX={tot_ccx} | ops {tot_in} -> {tot_out} ({tot_out - tot_in:+d} / {100*(tot_out-tot_in)/tot_in:+.2f}%) in {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
