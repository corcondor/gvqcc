"""How many equal-product Toffoli pairs could a DQI circuit cache on w extra always-free qubits?

Input: tab/space separated link list with columns i1 i2 dist a1 b1 t1 a2 b2 t2 depth guardOK ... (op indices of two
Toffolis computing the same product).  Greedy interval scheduling by right end, w wires.
One extra qubit costs about 710 Toffolis of score (cost ~ Q^2 * T with Q = 900), one cached link saves 1.

usage: python -I dqi_link_packing.py links.tsv
"""
import sys

rows = []
with open(sys.argv[1]) as fh:
    for line in fh:
        if line.startswith("#"):
            continue
        p = line.split()
        if int(p[10]):                       # same scope and guard
            rows.append((int(p[0]), int(p[1])))


def pack(w):
    ends, k = [0] * w, 0
    for i1, i2 in sorted(rows, key=lambda r: r[1]):
        best = -1
        for j in range(w):
            if ends[j] <= i1 and (best < 0 or ends[j] > ends[best]):
                best = j
        if best >= 0:
            ends[best] = i2
            k += 1
    return k


print("guard-compatible links:", len(rows))
for w in (1, 2, 3, 4, 6, 8, 12, 16, 24, 32):
    k = pack(w)
    print(f"extra wires {w:3d}: cacheable links {k:5d}  per wire {k / w:7.1f}  net T = {k - w * 710:+d}")
