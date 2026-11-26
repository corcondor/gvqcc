"""Special rows (x=7,14) for a newly designed loader: Gamma (eps + 3), class systems with own-batch erasures,
budget, export for cs2/cs3.  Uses our dc/oracle/pass4 machinery (read-only)."""
import json, random, sys
from pathlib import Path
from assemble import *

HERE = Path(__file__).resolve().parent


def restrict_spec_for_neighbor(k):
    """special-row erasures of batch k also enter bank k+1: keep only flips that preserve bank k+1's
    cache-linear combos (its bit-1 relations can differ from bank k's)."""
    if k >= 14:
        return
    from tgt import BLK
    Znext = BLK[str(k + 1)]["Z"]
    spec = sp4lib.load_spec_free()
    for e in spec[str(k)]:
        vecs = list(e["basis35"])
        rows = [sum((bin(v & g).count("1") & 1) << i for i, v in enumerate(vecs)) for g in Znext]
        from lib import nullspace
        new = []
        for sol in nullspace(rows, len(vecs)):
            v = 0
            for i, vv in enumerate(vecs):
                if sol >> i & 1:
                    v ^= vv
            new.append(v)
        e["basis35"] = new
    sp4lib._SPEC_INDEX.clear()


def make_builder(pub, gamma, words):
    p4build.Pub4 = lambda bank, w=None: pub       # Builder() asks for Pub4(bank, words): hand it our loader
    restrict_spec_for_neighbor(pub.k)
    return p4build.Builder(pub.k, gamma, erase=True, words=words, donor=False)


def eps_of(pub, sp):
    eps = 0
    n = sp.n_main
    for w in range(25):
        r = pub.delta[w]
        for o in range(n):
            if pub.fan[o][w]:
                r ^= sp.l0[o] & sp.m0[o]
        c = sp.cel.coords(r & ORD_MASK)
        assert c is not None
        if (c >> (len(sp.cord) - 1)) & 1:
            eps |= 1 << w
    return eps


def pick_gamma(pub, eps, s, seed):
    U = span_basis(pub.fan_int[:pub.n_main])
    rng = random.Random(seed)
    gamma = [eps] if eps else []
    while len(gamma) < s:
        v = 0
        for u in U:
            if rng.random() < 0.5:
                v ^= u
        if v and len(span_basis(gamma + [v])) == len(gamma) + 1:
            gamma.append(v)
    return gamma


def export(B, tag, outdir, s):
    cs = B.cs
    n = cs.n
    cap = 2 * n + 25 - s - 2
    meta = dict(s=s, nunk=cs.nunk, cap=cap, weights={}, gamma=B.gamma)
    for row in (7, 14):
        fn = outdir / f"cs_{tag}_row{row}.txt"
        wts = []
        with open(fn, "w") as fh:
            fh.write(f"76 {cs.nunk}\n")
            for p in range(76):
                rows = cs.rows[row][p]
                w = len(span_basis([v >> 1 for v in rows])) - 2
                wts.append(w)
                fh.write(f"{len(rows)} {w}\n")
                for v in rows:
                    ws = [(v >> (64 * i)) & ((1 << 64) - 1) for i in range(5)]
                    fh.write(" ".join(map(str, ws)) + "\n")
        meta["weights"][row] = wts
        from collections import Counter
        print(f"row {row}: total weight {sum(wts)}, 5 x capacity {5*cap}, luck {sum(wts) - 5*cap} (weights {sorted(Counter(wts).items())})")
    json.dump(meta, open(outdir / f"cs_{tag}_meta.json", "w"))
    return meta


if __name__ == "__main__":
    tag = sys.argv[1]
    s = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    gseed = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    pub, F, d, prods, words = build_pub(tag, n_closers=s)
    sp = SpecialSystem4(pub)
    eps = eps_of(pub, sp)
    gamma = pick_gamma(pub, eps, s, gseed)
    print("eps weight", bin(eps).count("1"), "gamma weights", [bin(g).count("1") for g in gamma])
    B = make_builder(pub, gamma, words)
    outdir = HERE / "designs" / tag
    export(B, f"{tag}_s{s}g{gseed}", outdir, s)
    erased = sum(len(v) for v in B.cs.erase.values())
    print("erasure dimensions used (rows 7+14):", erased)
