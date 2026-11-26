"""qsim op text <-> invsqrt .kmb (kickmix).  usage:
  python conv.py to_kmb ops.txt out.kmb       (header: q0..q21 = register x, as in the b806 export)
  python conv.py to_ops in.kmb out.ops.txt    (round trip for the full-input checker)
Op line: opcode a b c cond angle; angle in units of 2^-63 half-turns.
"""
import hashlib
import sys
from fractions import Fraction

import kickmix as km

NAMES = ["X", "CX", "CCX", "CCZ", "CSWAP", "SWAP", "Z", "CZ", "HMR", "Z_POW", "NEG", "BIT_INVERT", "BIT_STORE0",
         "BIT_STORE1", "PUSH_CONDITION", "POP_CONDITION"]
CODE = {n: i for i, n in enumerate(NAMES)}
NQUB = {"X": 1, "CX": 2, "CCX": 3, "CCZ": 3, "CSWAP": 3, "SWAP": 2, "Z": 1, "CZ": 2}


def dec(units):
    f = Fraction(units, 1 << 63) % 2
    k = f.denominator.bit_length() - 1
    assert f.denominator == 1 << k
    digits = str(f.numerator * 5 ** k).rjust(k + 1, "0")
    return digits[:-k] + "." + digits[-k:] if k else digits + ".0"


def to_kmb(src, out):
    lines = open(src).read().split("\n")
    n = int(lines[0])
    body = []
    for line in lines[1:n + 1]:
        g, a, b, c, cd, ang = (int(x) for x in line.split())
        name = NAMES[g]
        if name == "PUSH_CONDITION":
            body.append("PUSH_CONDITION if b%d" % cd)
            continue
        if name == "POP_CONDITION":
            body.append("POP_CONDITION")
            continue
        if name in NQUB:
            parts = [name] + ["q%d" % v for v in (a, b, c)[:NQUB[name]]]
        elif name == "HMR":
            parts = [name, "q%d" % a, "b%d" % b]
        elif name == "Z_POW":
            parts = [name, "q%d" % a, dec(ang)]
        elif name == "NEG":
            parts = [name]
        else:
            parts = [name, "b%d" % a]
        if cd >= 0:
            parts += ["if", "b%d" % cd]
        body.append(" ".join(parts))
    header = ["APPEND_TO_REGISTER q%d r0" % i for i in range(22)] + ['REGISTER r0 "x"']
    circ = km.Circuit("\n".join(header + body) + "\n")
    circ.to_file(out, format="kmb")
    back = km.Circuit.from_file(out)
    st = back.operation_statistics()
    print("qubits", back.num_qubits, "ops", len(back), "static toffoli-like", st.num_toffoli_like)
    print("sha256", hashlib.sha256(open(out, "rb").read()).hexdigest())


def to_ops(src, out):
    circ = km.Circuit.from_file(src)
    ops = []
    for line in str(circ).split("\n"):
        p = line.split()
        if not p or p[0] in ("REGISTER", "APPEND_TO_REGISTER", "#"):
            continue
        name = p[0]
        cond = -1
        if len(p) >= 2 and p[-2] == "if":
            cond = int(p[-1][1:])
            p = p[:-2]
        v = [-1, -1, -1]
        ang = 0
        if name in NQUB:
            for i in range(NQUB[name]):
                v[i] = int(p[1 + i][1:])
        elif name == "HMR":
            v[0], v[1] = int(p[1][1:]), int(p[2][1:])
        elif name == "Z_POW":
            v[0] = int(p[1][1:])
            x = Fraction(p[2]) % 2
            ang = int(x * (1 << 63))
            assert Fraction(ang, 1 << 63) == x
        elif name in ("BIT_INVERT", "BIT_STORE0", "BIT_STORE1"):
            v[0] = int(p[1][1:])
        elif name not in ("NEG", "PUSH_CONDITION", "POP_CONDITION"):
            raise SystemExit("unknown op " + line)
        ops.append("%d %d %d %d %d %d" % (CODE[name], v[0], v[1], v[2], cond, ang))
    with open(out, "w") as f:
        f.write("%d\n" % len(ops) + "\n".join(ops) + "\n")
    print("ops", len(ops))


if __name__ == "__main__":
    {"to_kmb": to_kmb, "to_ops": to_ops}[sys.argv[1]](sys.argv[2], sys.argv[3])
