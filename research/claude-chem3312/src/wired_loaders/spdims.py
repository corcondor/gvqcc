"""special-row erasure dimensions per pair of special columns (>2), per bank, per erase batch set"""
import sys, itertools
from specgen import erasure_items
from tgt import BLK
for k, bs in [(12, [12]), (10, [9]), (10, [9, 10]), (9, [8]), (9, [9]), (3, [3]), (3, [2]), (14, [14]), (13, [13]), (8, [8])]:
    col = {}
    for x in range(3, 16):
        col[x] = sum(len(erasure_items(k, x + 16 * p, bs)) for p in range(76))
    best = sorted(((col[a] + col[b], (a, b)) for a, b in itertools.combinations(range(3, 16), 2)), reverse=True)[:3]
    print(f"bank {k} erase {bs}: (7,14) -> {col[7]+col[14]} dims; best pairs {best}")
