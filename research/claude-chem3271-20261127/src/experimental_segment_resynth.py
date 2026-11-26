"""Re-synthesise every maximal run of unconditional CX/X/SWAP (same affine map, same boundaries) and keep the shorter.

usage: python segsyn.py IN.kmb OUT.kmb
Nothing else changes: CCX/HMR/phase/conditional/bit ops keep their order and wires.
Synthesis: greedy two-sided reduction of M to I (row ops = later CNOTs, column ops = earlier CNOTs), minimising the
Hamming distance of M and of M^-1 to I, with a Gauss-Jordan fallback; X constants are pushed to the end of the run.
"""
import sys

import numpy as np
import kickmix as km

src, dst = sys.argv[1], sys.argv[2]
TRIES = int(sys.argv[3]) if len(sys.argv) > 3 else 2
text = str(km.Circuit.from_file(src)).split("\n")
header = [l for l in text if l.startswith(("REGISTER", "APPEND_TO_REGISTER"))]
body = [l for l in text if l and not l.startswith(("REGISTER", "APPEND_TO_REGISTER", "#"))]


def parse(line):
    p = line.split()
    if len(p) >= 2 and p[-2] == "if":
        return p[0], p[1:-2], p[-1]
    return p[0], p[1:], None


def linear(line):
    op, args, cond = parse(line)
    return cond is None and op in ("CX", "X", "SWAP")


def run_map(lines):
    """affine map of the run on its wires: new = M.old + c."""
    wires = sorted({int(a[1:]) for l in lines for a in parse(l)[1]})
    idx = {w: i for i, w in enumerate(wires)}
    n = len(wires)
    M = np.eye(n, dtype=np.uint8)
    c = np.zeros(n, np.uint8)
    for l in lines:
        op, args, _ = parse(l)
        q = [idx[int(a[1:])] for a in args]
        if op == "X":
            c[q[0]] ^= 1
        elif op == "CX":
            M[q[1]] ^= M[q[0]]
            c[q[1]] ^= c[q[0]]
        else:
            M[[q[0], q[1]]] = M[[q[1], q[0]]]
            c[[q[0], q[1]]] = c[[q[1], q[0]]]
    return wires, M, c


def inverse(M):
    n = len(M)
    A = M.copy()
    I = np.eye(n, dtype=np.uint8)
    for col in range(n):
        piv = col + int(np.argmax(A[col:, col]))
        assert A[piv, col]
        if piv != col:
            A[[col, piv]] = A[[piv, col]]
            I[[col, piv]] = I[[piv, col]]
        rows = np.nonzero(A[:, col])[0]
        rows = rows[rows != col]
        A[rows] ^= A[col]
        I[rows] ^= I[col]
    return I


def greedy(M):
    """list of CNOTs (control, target) whose composition is M."""
    n = len(M)
    A = M.astype(np.float32).copy()
    B = inverse(M).astype(np.float32)
    E = np.eye(n, dtype=np.float32)
    left, right = [], []          # left: row ops applied (A <- R A); right: column ops (A <- A R)
    steps = 0
    while not np.array_equal(A, E):
        best = (0.0, None)
        for side in ("row", "col"):
            X, Y = (A, B) if side == "row" else (A.T, B.T)
            # row op on X: X[t] ^= X[s]; the inverse Y gets column op Y[:, s] ^= Y[:, t]
            D = np.abs(X - E)
            gain_x = X.sum(1)[None, :] - 2.0 * (D @ X.T)                 # [t, s]
            D2 = np.abs(Y - E).T
            Yc = Y.T
            gain_y = (Yc.sum(1)[:, None] - 2.0 * (Yc @ D2.T))           # [t, s]: column t of Y added to column s
            G = gain_x + gain_y
            np.fill_diagonal(G, 1e9)
            k = int(np.argmin(G))
            t, s = divmod(k, n)
            if G[t, s] < best[0]:
                best = (G[t, s], (side, t, s))
        if best[1] is None:
            # fallback: one Gauss-Jordan row step on the first column that is not unit
            col = next(c for c in range(n) if not np.array_equal(A[:, c], E[:, c]))
            if A[col, col] == 0:
                s = int(np.nonzero(A[:, col])[0][0])
                op = ("row", col, s)
            else:
                t = int(np.nonzero(A[:, col])[0][0]) if A[:, col].sum() > 1 else col
                rows = [r for r in np.nonzero(A[:, col])[0] if r != col]
                op = ("row", int(rows[0]), col)
        else:
            op = best[1]
        side, t, s = op
        if side == "row":                       # A[t] ^= A[s]
            A[t] = np.abs(A[t] - A[s])
            B[:, s] = np.abs(B[:, s] - B[:, t])
            left.append((s, t))
        else:                                   # A[:, t] ^= A[:, s]  (A.T row op)
            A[:, t] = np.abs(A[:, t] - A[:, s])
            B[s] = np.abs(B[s] - B[t])
            right.append((t, s))
        steps += 1
        if steps > 40 * n + 400:
            return None
    # A = L_k..L_1 M R_1..R_j = I  =>  M = L_1..L_k R_j..R_1 (each op self-inverse); circuit order is first factor last
    return [(c, t) for c, t in right] + [(c, t) for c, t in reversed(left)]


def check(wires, M, seq):
    n = len(wires)
    Z = np.eye(n, dtype=np.uint8)
    for c, t in seq:
        Z[t] ^= Z[c]
    return np.array_equal(Z, M)


rng = np.random.default_rng(1)


def lower(A, m):
    """PMH: row ops (ctrl, tgt) making invertible A upper triangular (in place)."""
    n = len(A)
    ops = []
    for c0 in range(0, n, m):
        c1 = min(n, c0 + m)
        seen = {}
        for r in range(c0, n):
            key = A[r, c0:c1].tobytes()
            if not A[r, c0:c1].any():
                continue
            if key in seen:
                A[r] ^= A[seen[key]]
                ops.append((seen[key], r))
            else:
                seen[key] = r
        for c in range(c0, c1):
            if not A[c, c]:
                s = c + 1 + int(np.argmax(A[c + 1:, c]))
                A[c] ^= A[s]
                ops.append((s, c))
            rows = c + 1 + np.nonzero(A[c + 1:, c])[0]
            if len(rows):
                A[rows] ^= A[c]
                ops += [(c, int(r)) for r in rows]
    return ops


def pmh(M, m):
    A = M.copy()
    ops_l = lower(A, m)
    B = A.T.copy()
    ops_u = lower(B, m)
    assert np.array_equal(B, np.eye(len(M), dtype=np.uint8))
    return [(t, s) for s, t in ops_u] + [o for o in reversed(ops_l)]


def best_pmh(M, tries):
    n = len(M)
    best = None
    for trial in range(tries):
        perm = np.arange(n) if trial == 0 else rng.permutation(n)
        Mp = M[np.ix_(perm, perm)]
        for m in (2, 3, 4, 5):
            for inv_ in (False, True):
                X = inverse(Mp) if inv_ else Mp
                seq = pmh(X, m)
                if inv_:
                    seq = list(reversed(seq))
                if best is None or len(seq) < len(best):
                    best = [(int(perm[a]), int(perm[b])) for a, b in seq]
    return best


def synth(lines):
    wires, M, c = run_map(lines)
    cands = []
    seq = greedy(M)
    if seq is not None and check(wires, M, seq):
        cands.append(seq)
    if len(lines) > 24:
        seq = best_pmh(M, TRIES)
        if check(wires, M, seq):
            cands.append(seq)
    if not cands:
        return lines
    seq = min(cands, key=len)
    new = [f"CX q{wires[a]} q{wires[b]}" for a, b in seq] + [f"X q{wires[i]}" for i in np.nonzero(c)[0]]
    return new if len(new) < len(lines) else lines


out, run = [], []
saved = 0
for l in body + [None]:
    if l is not None and linear(l):
        run.append(l)
        continue
    if run:
        new = synth(run) if len(run) > 2 else run
        saved += len(run) - len(new)
        out += new
        run = []
    if l is not None:
        out.append(l)
circ = km.Circuit("\n".join(header + out) + "\n")
circ.to_file(dst, format="kmb")
print(f"ops {len(body)} -> {len(circ)} (saved {saved})  toffoli-like {circ.operation_statistics().num_toffoli_like}")
