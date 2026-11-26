"""Lazy affine synthesis for loader circuits: same CCX/HMR/phase gates, far fewer CX/X.

Invariant: orig = T.phys + c over GF(2) (T invertible, U = T^-1 kept alongside).  Unconditional X/CX/SWAP only update
(T, c).  Before each CCX(a,b,t) the controls are materialised on single wires (rows a, b of T become unit vectors) and
the target flip onto a single wire (column t of U becomes a unit vector); CNOTs there are the only ones emitted.  HMR
and R additionally require that no other value depends on the measured wire.  Phase gates (Z, CZ, NEG, also
conditioned) are expanded over T or materialised, whichever is cheaper.  At the end T is returned to the identity.

usage: python lazy.py IN.kmb OUT.kmb [--pivot MODE] [--seed N]
"""
import argparse
import random
import sys

import kickmix as km

ap = argparse.ArgumentParser()
ap.add_argument("src")
ap.add_argument("dst")
ap.add_argument("--pivot", default="look", choices=["light", "self", "random", "look", "greedy"])
ap.add_argument("--k", type=int, default=12)
ap.add_argument("--decay", type=float, default=0.75)
ap.add_argument("--min-gain", type=float, default=1.0)
ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--quiet", action="store_true")
A = ap.parse_args()
rng = random.Random(A.seed)

text = str(km.Circuit.from_file(A.src)).split("\n")
header = [l for l in text if l.startswith(("REGISTER", "APPEND_TO_REGISTER"))]
body = [l for l in text if l and not l.startswith(("REGISTER", "APPEND_TO_REGISTER", "#"))]


def parse(line):
    p = line.split()
    cond = None
    if len(p) >= 2 and p[-2] == "if":
        cond = p[-1]
        p = p[:-2]
    return p[0], p[1:], cond


N = 1 + max(int(a[1:]) for l in body for a in parse(l)[1] if a.startswith("q"))
T = [1 << i for i in range(N)]   # row w: which physical wires make orig w
U = [1 << i for i in range(N)]   # row p: which orig values make phys p  (U = T^-1)
C = [0] * N
out = []


def bits(x):
    while x:
        b = x & -x
        yield b.bit_length() - 1
        x ^= b


def emit_cx(ctl, tgt, cond=None):
    """physical CNOT: phys[tgt] ^= phys[ctl].  T column ctl ^= column tgt; U row tgt ^= row ctl."""
    assert ctl != tgt
    out.append(f"CX q{ctl} q{tgt}")
    mc, mt = 1 << ctl, 1 << tgt
    for w in range(N):
        if T[w] & mt:
            T[w] ^= mc
    U[tgt] ^= U[ctl]


def orig_cx(a, b):
    """absorbed orig[b] ^= orig[a]: T row b ^= row a; U column a ^= column b."""
    T[b] ^= T[a]
    C[b] ^= C[a]
    ma, mb = 1 << a, 1 << b
    for p in range(N):
        if U[p] & mb:
            U[p] ^= ma


def column_of_U(a):
    m = 1 << a
    x = 0
    for p in range(N):
        if U[p] & m:
            x |= 1 << p
    return x


def col_weight_T(k):
    m = 1 << k
    return sum(1 for w in range(N) if T[w] & m)


FUT = []   # per body index: upcoming (kind, orig index) needs
NEXT = 0


def look_score(kind, pivot, others):
    """cost of future rows/columns after fanning `others` into column `pivot` (row mode) or out of it (col mode)."""
    mask = 0
    for k in others:
        mask |= 1 << k
    mp = 1 << pivot
    s, w = 0.0, 1.0
    for fk, fi in FUT[NEXT:NEXT + A.k]:
        if kind == "row":   # column ops: column k ^= column pivot for k in others
            if fk == "row":
                v = T[fi]
                if v & mp:
                    v ^= mask
                s += w * bin(v).count("1")
            else:           # U rows: U[pivot] ^= U[k]
                x = 0
                for q_ in range(N):
                    u = U[q_]
                    if q_ == pivot:
                        for k in others:
                            u ^= U[k]
                    if u >> fi & 1:
                        x += 1
                s += w * x
        else:               # column t=pivot ^= column l for l in others; U rows U[l] ^= U[t]
            if fk == "row":
                v = T[fi]
                if bin(v & mask).count("1") & 1:
                    v ^= mp
                s += w * bin(v).count("1")
            else:
                x = 0
                ut = U[pivot] >> fi & 1
                for q_ in range(N):
                    b_ = U[q_] >> fi & 1
                    if (mask >> q_ & 1):
                        b_ ^= ut
                    x += b_
                s += w * x
        w *= A.decay
    return s


import numpy as np


def bitrow(v):
    return np.frombuffer(v.to_bytes(N // 8 + 1, "little"), np.uint8)


def to_vec(v):
    return np.unpackbits(bitrow(v), bitorder="little")[:N].astype(np.float32)


def greedy_reduce():
    """apply physical CNOTs while they shrink the weighted size of the next A.k needed rows/columns by > min_gain."""
    window = FUT[NEXT:NEXT + A.k]
    if not window:
        return
    while True:
        R, wr, X, wx = [], [], [], []
        w = 1.0
        for fk, fi in window:
            if fk == "row":
                R.append(to_vec(T[fi])); wr.append(w)
            else:
                X.append(to_vec(column_of_U(fi))); wx.append(w)
            w *= A.decay
        D = np.zeros((N, N), np.float32)   # D[k, l]: weighted change if col k of T ^= col l  (emit_cx(k, l))
        if R:
            Rm, wm = np.stack(R), np.asarray(wr, np.float32)
            D += (wm @ Rm)[None, :] - 2.0 * ((Rm * wm[:, None]).T @ Rm)
        if X:
            Xm, wm = np.stack(X), np.asarray(wx, np.float32)
            D += (wm @ Xm)[:, None] - 2.0 * ((Xm * wm[:, None]).T @ Xm)
        np.fill_diagonal(D, 1e9)
        k, l = np.unravel_index(int(np.argmin(D)), D.shape)
        if D[k, l] > -A.min_gain - 1e-6:
            return
        emit_cx(int(k), int(l))


def choose(cands, prefer, kind="row", sup=()):
    cands = list(cands)
    if A.pivot == "greedy":
        return prefer if prefer in cands else min(cands, key=col_weight_T)
    if A.pivot == "look":
        scored = [(look_score(kind, k, [s for s in sup if s != k]), 0 if k == prefer else 1, rng.random(), k) for k in cands]
        return min(scored)[3]
    if A.pivot == "self" and prefer in cands:
        return prefer
    if A.pivot == "random":
        return rng.choice(cands)
    best = min(col_weight_T(k) for k in cands)
    pool = [k for k in cands if col_weight_T(k) == best]
    return prefer if prefer in pool else rng.choice(pool)


def materialise_row(a, avoid=()):
    """make T row a a unit vector; returns the wire holding orig a (up to constant C[a])."""
    sup = list(bits(T[a]))
    i = choose([k for k in sup if k not in avoid], a, "row", sup)
    for k in sup:
        if k != i:
            emit_cx(k, i)
    assert T[a] == 1 << i
    return i


def make_column_unit(c, forced=None):
    """make U column c a unit vector e_t, so flipping phys t flips exactly orig c."""
    x = column_of_U(c)
    sup = list(bits(x))
    t = forced if forced is not None else choose(sup, c, "col", sup)
    assert x >> t & 1
    for l in sup:
        if l != t:
            emit_cx(t, l)
    assert column_of_U(c) == 1 << t
    return t


def phase_linear(a, cond):
    """Z on orig a = product of Z over its wires, times -1 if the constant is set."""
    for k in bits(T[a]):
        out.append(f"Z q{k}" + (f" if {cond}" if cond else ""))
    if C[a]:
        out.append("NEG" + (f" if {cond}" if cond else ""))


def phase_cz(a, b, cond):
    suf = f" if {cond}" if cond else ""
    wa, wb = bin(T[a]).count("1"), bin(T[b]).count("1")
    if wa * wb > wa + wb:  # materialise the denser rows first (cheaper than expanding)
        i = materialise_row(a)
        if bin(T[b]).count("1") > 2:
            materialise_row(b, avoid=(i,))
    al, bl = list(bits(T[a])), list(bits(T[b]))
    parity = {}
    for k in al:
        for l in bl:
            key = (k,) if k == l else tuple(sorted((k, l)))
            parity[key] = parity.get(key, 0) ^ 1
    for k in al:  # c_b * Z(alpha)
        if C[b]:
            parity[(k,)] = parity.get((k,), 0) ^ 1
    for l in bl:
        if C[a]:
            parity[(l,)] = parity.get((l,), 0) ^ 1
    for key, v in parity.items():
        if v:
            out.append((f"Z q{key[0]}" if len(key) == 1 else f"CZ q{key[0]} q{key[1]}") + suf)
    if C[a] and C[b]:
        out.append("NEG" + suf)


POS = []
for line in body:
    op, args, cond = parse(line)
    q = [int(a[1:]) for a in args if a.startswith("q")]
    POS.append(len(FUT))
    if op == "CCX":
        FUT += [("row", q[0]), ("row", q[1]), ("col", q[2])]
    elif op in ("HMR", "R"):
        FUT += [("row", q[0])]

for line_no, line in enumerate(body):
    op, args, cond = parse(line)
    NEXT = POS[line_no]
    if A.pivot == "greedy" and op in ("CCX", "HMR", "R"):
        greedy_reduce()
    NEXT = POS[line_no] + (3 if op == "CCX" else 1 if op in ("HMR", "R") else 0)
    q = [int(a[1:]) for a in args if a.startswith("q")]
    if op == "X" and cond is None:
        C[q[0]] ^= 1
    elif op == "CX" and cond is None:
        orig_cx(q[0], q[1])
    elif op == "SWAP" and cond is None:
        x, y = q
        orig_cx(x, y); orig_cx(y, x); orig_cx(x, y)
    elif op == "CCX" and cond is None:
        a, b, c = q
        i = materialise_row(a)
        j = materialise_row(b, avoid=(i,))
        assert T[a] == 1 << i, "row a disturbed"
        t = make_column_unit(c)
        assert t not in (i, j) and T[a] == 1 << i and T[b] == 1 << j
        out.append(f"CCX q{i} q{j} q{t}")
        ca, cb = C[a], C[b]
        if cb:
            orig_cx(a, c)
        if ca:
            orig_cx(b, c)
        if ca and cb:
            C[c] ^= 1
    elif op in ("HMR", "R") and cond is None:
        a = q[0]
        i = materialise_row(a)
        make_column_unit(a, forced=i)
        assert T[a] == 1 << i and column_of_U(a) == 1 << i
        if C[a]:
            out.append(f"X q{i}")
            C[a] = 0
        out.append(f"HMR q{i} {args[1]}" if op == "HMR" else f"R q{i}")
        # orig a is now 0 = phys i (reset)
    elif op == "Z":
        phase_linear(q[0], cond)
    elif op == "CZ":
        if q[0] == q[1]:
            phase_linear(q[0], cond)
        else:
            phase_cz(q[0], q[1], cond)
    elif op == "NEG":
        out.append(line)
    elif op.startswith("BIT_"):
        out.append(line)
    else:
        raise SystemExit("unsupported op: " + line)

# flush: return T to the identity (column operations), then constants
for r in range(N):
    if not T[r] >> r & 1:
        k = next(k for k in bits(T[r]) if k > r)
        emit_cx(r, k)
    for k in list(bits(T[r])):
        if k != r:
            emit_cx(k, r)
    assert T[r] == 1 << r
for r in range(N):
    assert T[r] == 1 << r
    if C[r]:
        out.append(f"X q{r}")

circ = km.Circuit("\n".join(header + out) + "\n")
circ.to_file(A.dst, format="kmb")
if not A.quiet:
    st = circ.operation_statistics()
    print(f"ops {len(body)} -> {len(circ)}  toffoli-like {st.num_toffoli_like}")
