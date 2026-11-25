"""Exact Boolean phase pullback used in the V49 native compiler.

This is the dependency-free algebraic core. The full native emitter,
BDD engine, selected splices and independent replay are in the companion
archive. This module does not certify physical width or the full oracle.
"""
from collections import defaultdict

DATA = {17, 33, 34, 49, 50}
PHASE = {0, 16, 32, 48}


class Cap(Exception):
    pass


def mul(a, b):
    """Boolean quotient product: monomials are bit masks, x*x=x."""
    if len(a) * len(b) > 5000:
        raise Cap
    s = set()
    for u in a:
        for v in b:
            w = u | v
            if w in s:
                s.remove(w)
            else:
                s.add(w)
    if len(s) > 500:
        raise Cap
    return s


def update(f, raw, w):
    """All supported data operations are involutions."""
    g = raw & 127
    if g == 17:
        f[w[0]] ^= {0}
    elif g == 33:
        f[w[1]] ^= f[w[0]]
    elif g == 34:
        f[w[0]], f[w[1]] = f[w[1]], f[w[0]]
    elif g == 49:
        f[w[2]] ^= mul(f[w[0]], f[w[1]])
    elif g == 50:
        a, u, v = w
        p = mul(f[a], f[u] ^ f[v])
        f[u] ^= p
        f[v] ^= p
    else:
        raise ValueError(raw)
    if any(len(f[j]) > 500 for j in w):
        raise Cap


def collect(ops, anchor, width=37):
    """ops = (raw, wires, classical_condition) triples.

    Preconditions: unconditional data operations, no HMR, scope, rotation,
    or classical writes. The same classical conditions hold at the anchor.
    Returned phase polynomials are exact in the Boolean quotient.
    """
    if not 0 <= anchor <= len(ops):
        raise ValueError("anchor")
    result = defaultdict(set)
    def walk(seq):
        f = [{1 << i} for i in range(width)]
        for raw, wires, condition in seq:
            g = raw & 127
            if g in DATA:
                if raw != g or condition is not None:
                    raise ValueError("guarded data not supported")
                update(f, raw, wires)
            elif g in PHASE:
                p = {0}
                for j in wires:
                    p = mul(p, f[j])
                result[condition] ^= p
                if len(result[condition]) > 1000:
                    raise Cap
            else:
                raise ValueError("barrier")
    walk(ops[anchor:])
    walk(reversed(ops[:anchor]))
    return {c: p for c, p in result.items() if p}


def evaluate(poly, row):
    return sum((row & m) == m for m in poly) % 2


def regression():
    import random
    rng = random.Random(49)
    for _ in range(128):
        # Use the actual pullback, and compare to independently replayed bits.
        ops = []
        for _ in range(18):
            raw = rng.choice([17, 33, 34, 49, 50, 16, 32, 48])
            n = {17:1,33:2,34:2,49:3,50:3,16:1,32:2,48:3}[raw]
            ops.append((raw, tuple(rng.sample(range(5), n)), None))
        anchor = rng.randrange(len(ops)+1)
        P = collect(ops, anchor, 5)
        for x in range(32):
            bits = [(x >> q) & 1 for q in range(5)]
            phase = 0
            def step(raw, w):
                nonlocal phase
                if raw == 17:
                    bits[w[0]] ^= 1
                elif raw == 33:
                    bits[w[1]] ^= bits[w[0]]
                elif raw == 34:
                    bits[w[0]], bits[w[1]] = bits[w[1]], bits[w[0]]
                elif raw == 49:
                    bits[w[2]] ^= bits[w[0]] & bits[w[1]]
                elif raw == 50:
                    if bits[w[0]]:
                        bits[w[1]], bits[w[2]] = bits[w[2]], bits[w[1]]
                else:
                    phase ^= int(all(bits[j] for j in w))
            for raw,w,_ in ops[anchor:]:
                step(raw,w)
            bits[:] = [(x >> q) & 1 for q in range(5)]
            for raw,w,_ in reversed(ops[:anchor]):
                step(raw,w)
            assert phase == evaluate(P.get(None,set()), x)
    print("V49 Boolean transport regression PASS")


if __name__ == "__main__":
    regression()
