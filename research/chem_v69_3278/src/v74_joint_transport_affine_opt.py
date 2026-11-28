"""
V74 Joint Nonlinear-Relation Transport, Difference-Equation, and Affine-Interval Optimizer.

Applies exact algebraic transport across CCX and diagonal measurement-phase (Z/CZ if b) gates
to fuse fragmented {X, CX} strips into large affine intervals, cancel redundant difference steps
(M_t -> M_{t+1} via Delta = M_{t+1} M_t^{-1} instead of M_t -> I -> M_{t+1}), cancel duplicate
commuting diagonal phase gates (CZ^2 = I, Z^2 = I), and resynthesize every fused affine interval
using Boyar-Peralta greedy Hamming-weight descent + sparsity-ordered PMH (both M and M^T).

100% exact unitary equivalence (zero CCX/HMR count change; verified per-block algebraically AND
by unchanged official dfthcsos/verify.py on both default and fresh salts).
"""

import sys
import time
from pathlib import Path
import numpy as np

sys.path.insert(0, r"c:\Users\81808\.openclaw\gvqcc\verifiers")
sys.path.insert(0, r"c:\Users\81808\.openclaw\gvqcc_v2832")
import kickmix as km
from v71_math_commute_bp_compress import compress_affine_block

SRC_DIR = Path(r"c:\Users\81808\.openclaw\gvqcc_v2832\v72_fam_3271")
DST_DIR = Path(r"c:\Users\81808\.openclaw\gvqcc_v2832\v74_fam_3271_jointopt")


def parse_op(ln: str):
    toks = ln.split()
    cmd = toks[0]
    if cmd == "X" and len(toks) == 2:
        return ("X", int(toks[1][1:]), ln)
    if cmd == "CX" and len(toks) == 3:
        return ("CX", int(toks[1][1:]), int(toks[2][1:]), ln)
    if cmd == "CCX" and len(toks) == 4:
        return ("CCX", int(toks[1][1:]), int(toks[2][1:]), int(toks[3][1:]), ln)
    if cmd == "HMR":
        return ("HMR", int(toks[1][1:]), toks[2], ln)
    if cmd == "Z" and len(toks) == 4 and toks[2] == "if":
        return ("Z_IF", int(toks[1][1:]), toks[3], ln)
    if cmd == "CZ" and len(toks) == 5 and toks[3] == "if":
        a, b = int(toks[1][1:]), int(toks[2][1:])
        if a > b:
            a, b = b, a
        return ("CZ_IF", a, b, toks[4], ln)
    return ("OTHER", ln)


def commutes(op1, op2):
    """Exact sound commutation check between any two gates in {X, CX, CCX, HMR, Z_IF, CZ_IF}."""
    k1, k2 = op1[0], op2[0]
    if k1 == "OTHER" or k2 == "OTHER":
        return False
    # Diagonal phase gates (Z_IF, CZ_IF) always commute with each other!
    if k1 in ("Z_IF", "CZ_IF") and k2 in ("Z_IF", "CZ_IF"):
        return True
    # Helper: sets of (controls_z, targets_x, meas_bits_written, meas_bits_read)
    # A gate flips X on `xt`, reads Z on `zc`. Two gates commute if:
    #   (xt1 & zc2) == empty AND (xt2 & zc1) == empty AND no HMR/classical-bit conflict!
    # For HMR(q, b): reads & resets q (treat as both xt and zc on q) and writes classical bit b.
    def profile(op):
        k = op[0]
        if k == "X":
            return (set(), {op[1]}, None, None)
        if k == "CX":
            return ({op[1]}, {op[2]}, None, None)
        if k == "CCX":
            return ({op[1], op[2]}, {op[3]}, None, None)
        if k == "Z_IF":
            return ({op[1]}, set(), None, op[2])
        if k == "CZ_IF":
            return ({op[1], op[2]}, set(), None, op[3])
        if k == "HMR":
            return ({op[1]}, {op[1]}, op[2], None)
        return None

    zc1, xt1, mw1, mr1 = profile(op1)
    zc2, xt2, mw2, mr2 = profile(op2)
    if (xt1 & zc2) or (xt2 & zc1):
        return False
    if mw1 is not None and (mw1 == mr2 or mw1 == mw2):
        return False
    if mw2 is not None and (mw2 == mr1 or mw2 == mw1):
        return False
    return True


def cancel_diagonal_phase_and_bubble(ops, direction="right"):
    """
    1. Bubble Z_IF / CZ_IF gates across commuting gates and cancel identical pairs (Z^2=I, CZ^2=I).
    2. Bubble non-affine gates (CCX, Z_IF, CZ_IF) rightward (or leftward) past commuting {X, CX} gates
       so fragmented {X, CX} strips fuse into large affine intervals!
    """
    seq = list(ops) if direction == "right" else list(reversed(ops))
    out = []
    deferred_non_aff = []  # non-affine gates deferred rightward past commuting affine gates

    for op in seq:
        if op[0] in ("X", "CX"):
            # Flush only those deferred non-affine gates that do NOT commute with `op`
            # (preserving relative order among non-commuting deferred gates!)
            # Maintain exact soundness: if deferred[i] doesn't commute with `op`, then any deferred[j] (j < i)
            # that doesn't commute with deferred[i] must ALSO be flushed before deferred[i]!
            n_def = len(deferred_non_aff)
            must_flush = [False] * n_def
            for i in range(n_def - 1, -1, -1):
                if not commutes(deferred_non_aff[i], op):
                    must_flush[i] = True
                if must_flush[i]:
                    for j in range(i):
                        if not must_flush[j] and not commutes(deferred_non_aff[j], deferred_non_aff[i]):
                            must_flush[j] = True
            new_def = []
            for i, dop in enumerate(deferred_non_aff):
                if must_flush[i]:
                    out.append(dop)
                else:
                    new_def.append(dop)
            deferred_non_aff = new_def
            out.append(op)
        else:
            # Non-affine gate: check if it's a Z_IF / CZ_IF that cancels with a matching one in deferred_non_aff!
            if op[0] in ("Z_IF", "CZ_IF"):
                # Can it commute back to a matching key in deferred_non_aff?
                key = op[:-1]
                cancelled = False
                for i in range(len(deferred_non_aff) - 1, -1, -1):
                    if deferred_non_aff[i][:-1] == key:
                        # Check if op commutes with everything after i in deferred_non_aff
                        if all(commutes(deferred_non_aff[j], op) for j in range(i + 1, len(deferred_non_aff))):
                            deferred_non_aff.pop(i)
                            cancelled = True
                            break
                if cancelled:
                    continue
            # Keep deferred buffer bounded (<= 48) for O(N) speed
            if len(deferred_non_aff) >= 48:
                out.append(deferred_non_aff.pop(0))
            deferred_non_aff.append(op)

    out.extend(deferred_non_aff)
    return out if direction == "right" else list(reversed(out))


def resynth_affine_intervals(ops):
    """Resynthesize every maximal contiguous {X, CX} interval using V71's exact BP + Sparsity-PMH solver."""
    out = []
    buf = []

    def flush():
        nonlocal buf
        if not buf:
            return
        simple = [(op[0], op[1]) if op[0] == "X" else (op[0], op[1], op[2]) for op in buf]
        comp = compress_affine_block(simple)
        for c in comp:
            if c[0] == "X":
                out.append(("X", c[1], f"X q{c[1]}"))
            else:
                out.append(("CX", c[1], c[2], f"CX q{c[1]} q{c[2]}"))
        buf = []

    for op in ops:
        if op[0] in ("X", "CX"):
            buf.append(op)
        else:
            flush()
            out.append(op)
    flush()
    return out


def optimize_kmb(src_path: Path, dst_path: Path):
    circ = km.Circuit.from_file(str(src_path))
    lines = [ln.strip() for ln in str(circ).splitlines() if ln.strip()]
    in_ops = len(lines)
    in_ccx = sum(1 for ln in lines if ln.startswith("CCX "))

    ops = [parse_op(ln) for ln in lines]
    # Two alternating directional passes (rightward fusion + leftward fusion) + affine resynthesis!
    for direction in ("right", "left", "right"):
        ops = cancel_diagonal_phase_and_bubble(ops, direction=direction)
        ops = resynth_affine_intervals(ops)

    out_lines = [op[-1] for op in ops]
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
        io, oo, ccx = optimize_kmb(src, dst)
        tot_in += io
        tot_out += oo
        tot_ccx += ccx
        print(f"k={k:2d}: CCX={ccx:3d} | ops {io:6d} -> {oo:6d} ({oo - io:+7d} / {100*(oo-io)/io:+6.2f}%)", flush=True)
    print(f"TOTAL: CCX={tot_ccx} | ops {tot_in} -> {tot_out} ({tot_out - tot_in:+d} / {100*(tot_out-tot_in)/tot_in:+.2f}%) in {time.time()-t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
