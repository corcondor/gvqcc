"""Predicated-liveness ("code sinking" / lazy evaluation) census for a measurement-based circuit.

For every AND gadget (a CCX written into a clean wire, later released by HMR/R) collect the intersection of
the classical conditions under which its value is READ.  If every read happens under extra conditions that the
compute does not have, the compute can be moved inside those conditions (call-by-need), and its expected
Toffoli cost drops from P(compute guard) to P(use guard).

usage: python -I -X utf8 pred_sink.py ops.txt [n_input_qubits]
ops.txt: first line = op count, then "opcode a b c cond angle" (conv.py format).
"""
import sys
from collections import Counter, defaultdict

NAMES = ["X", "CX", "CCX", "CCZ", "CSWAP", "SWAP", "Z", "CZ", "HMR", "Z_POW", "NEG", "BIT_INVERT",
         "BIT_STORE0", "BIT_STORE1", "PUSH_CONDITION", "POP_CONDITION"]


def main():
    lines = open(sys.argv[1]).read().split("\n")
    n = int(lines[0])
    ops = [tuple(int(x) for x in line.split()) for line in lines[1:n + 1]]
    n_in = int(sys.argv[2]) if len(sys.argv) > 2 else 22

    ver, wpos, kind = defaultdict(int), {}, {}
    stack = []
    clean = defaultdict(lambda: True)
    dirty = {}
    for q in range(n_in):
        clean[q] = False
        dirty[q] = frozenset()
    gad = {}
    opnd = defaultdict(list)
    done = []
    n_ccx = n_gad = 0

    def read(q, g, i):
        d = gad.get(q)
        if d is None:
            return
        d["ug"] = g if d["ug"] is None else d["ug"] & g
        d["nr"] += 1
        d["first"] = d["first"] if d["first"] is not None else i
        d["last"] = i

    def write(q, g, i):
        for d in opnd[q]:
            if d["opw"] is None and i > d["i"]:
                d["opw"] = i
        if q in gad:
            gad[q]["impure"] = True
        if clean[q]:
            clean[q] = False
            dirty[q] = g
        else:
            dirty[q] = dirty[q] & g

    def finalize(d, i, how):
        d["end"], d["how"] = i, how
        done.append(d)
        for w in (d["a"], d["b"]):
            if d in opnd[w]:
                opnd[w].remove(d)

    def reset(q, g, i):
        d = gad.pop(q, None)
        if d is not None:
            if not (g <= (dirty.get(q) or frozenset())) and g:
                d["impure"] = True
            d["hg"] = g
            finalize(d, i, "reset")
        if not clean[q] and g <= dirty[q]:
            clean[q] = True

    for i, (op, a, b, c, cd, ang) in enumerate(ops):
        name = NAMES[op]
        if name == "PUSH_CONDITION":
            stack.append((cd, ver[cd]))
            continue
        if name == "POP_CONDITION":
            stack.pop()
            continue
        g = frozenset(stack) | (frozenset([(cd, ver[cd])]) if cd >= 0 else frozenset())
        if name == "X":
            write(a, g, i)
        elif name == "CX":
            read(a, g, i)
            write(b, g, i)
        elif name == "CCX":
            n_ccx += 1
            read(a, g, i)
            read(b, g, i)
            fresh = clean[c] and c not in gad
            write(c, g, i)
            if fresh:
                n_gad += 1
                d = {"i": i, "a": a, "b": b, "t": c, "cg": g, "ug": None, "impure": False,
                     "first": None, "last": None, "opw": None, "nr": 0, "hg": None}
                gad[c] = d
                opnd[a].append(d)
                opnd[b].append(d)
        elif name in ("CCZ",):
            for q in (a, b, c):
                read(q, g, i)
        elif name == "CSWAP":
            for q in (a, b, c):
                read(q, g, i)
            write(b, g, i)
            write(c, g, i)
        elif name == "SWAP":
            if not g:
                ga, gb = gad.pop(a, None), gad.pop(b, None)
                if ga is not None:
                    ga["t"] = b
                    gad[b] = ga
                if gb is not None:
                    gb["t"] = a
                    gad[a] = gb
                for w in (a, b):
                    for d in opnd[w]:
                        if d["opw"] is None and i > d["i"]:
                            d["opw"] = i
                ca, cb = clean[a], clean[b]
                da, db = dirty.get(a, frozenset()), dirty.get(b, frozenset())
                clean[a], clean[b] = cb, ca
                dirty[a], dirty[b] = db, da
            else:
                for q in (a, b):
                    read(q, g, i)
                    write(q, g, i)
        elif name in ("Z", "Z_POW"):
            read(a, g, i)
        elif name == "CZ":
            read(a, g, i)
            read(b, g, i)
        elif name == "HMR":
            ver[b] += 1
            wpos[(b, ver[b])] = i
            kind[b] = "H"
            reset(a, g, i)
        elif name == "NEG":
            pass
        elif name in ("BIT_INVERT", "BIT_STORE0", "BIT_STORE1"):
            ver[a] += 1
            wpos[(a, ver[a])] = i
            kind[a] = "S"
        else:
            raise ValueError(name)
        # "R" does not exist in this text format (all releases are HMR)
    for d in list(gad.values()):
        finalize(d, len(ops), "output")

    pure = [d for d in done if not d["impure"] and d["how"] == "reset"]
    dead = [d for d in pure if d["ug"] is None]
    cand = [d for d in pure if d["ug"] is not None and d["ug"] - d["cg"]]
    print(f"CCX {n_ccx}  AND gadgets into clean wires {n_gad}  pure released gadgets {len(pure)}"
          f"  never read {len(dead)}  read only under extra conditions {len(cand)}")
    stats = Counter()
    saving = 0.0
    for d in cand:
        extra = d["ug"] - d["cg"]
        kinds = "".join(sorted(kind.get(bit, "?") for bit, _ in extra))
        # a legal new position must come after every extra bit is written and before the first use / operand change
        lo = max([d["i"]] + [wpos.get((bit, v), -1) + 1 for bit, v in extra])
        hi = min(d["first"], d["opw"] if d["opw"] is not None else d["first"])
        movable = lo <= hi
        coin = sum(1 for bit, _ in extra if kind.get(bit) == "H")
        pc = 0.5 ** sum(1 for bit, _ in d["cg"] if kind.get(bit) == "H")
        pu = pc * 0.5 ** coin
        stats[(kinds, movable)] += 1
        if movable:
            saving += pc - pu
    for key, v in sorted(stats.items()):
        print(f"  extra condition bit kinds {key[0] or '-':6s} movable={key[1]}  gadgets {v}")
    print(f"estimated mean Toffoli saved (coin bits only, movable): {saving:.3f}")
    for d in cand[:40]:
        print(f"    ccx op {d['i']} ({d['a']},{d['b']}->{d['t']}) first_use {d['first']} end {d['end']}"
              f" reads {d['nr']} extra {sorted(d['ug'] - d['cg'])} operand_rewrite {d['opw']}")


if __name__ == "__main__":
    main()
