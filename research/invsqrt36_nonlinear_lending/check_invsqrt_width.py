"""Fail-closed width acceptance gate for invsqrt KMB v2 research candidates.

Pass means width only: it does not establish phase accuracy or score.
Default maximum 36; use --max-width 22 for the strict 22Q track.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

MAGIC = bytes.fromhex('d750c7d5c329d326e3cc9f6834f2b8bf')
HEADER = struct.Struct('<4I9Q')
SECTION = struct.Struct('<QQ')
WIRE_COLS = {0: (), 1: (7,), 2: (5, 6), 3: (2, 3, 4)}


def check(path, cap=36):
    if not 22 <= cap <= 36:
        raise ValueError('invsqrt acceptance cap must be 22..36')
    data = Path(path).read_bytes()
    if len(data) < 16 + HEADER.size or data[:16] != MAGIC:
        raise ValueError('invalid KMB v2 prefix or truncated header')
    h = HEADER.unpack_from(data, 16)
    if h[0] != 2 or not 22 <= h[1] <= cap:
        raise ValueError(f'unsupported version or declared width {h[1]} exceeds cap {cap} or is below 22')
    off = 16 + HEADER.size
    cols = {}
    while off < len(data):
        if off + SECTION.size > len(data):
            raise ValueError('truncated section header')
        kind, size = SECTION.unpack_from(data, off)
        off += SECTION.size
        if size > len(data) - off:
            raise ValueError('truncated section body')
        if 1 <= kind <= 9:
            if kind in cols or (kind != 1 and size % 4):
                raise ValueError('duplicate or malformed operation column')
            cols[kind] = memoryview(data)[off:off+size]
        off += size
    if set(cols) != set(range(1, 10)) or len(cols[1]) != h[4]:
        raise ValueError('missing operation columns or incorrect instruction count')
    pos = dict.fromkeys(range(2, 10), 0)
    wires = set()
    def take(c):
        i = pos[c]
        pos[c] += 4
        if pos[c] > len(cols[c]):
            raise ValueError('truncated operation column')
        return struct.unpack_from('<I', cols[c], i)[0]
    for op in cols[1]:
        for c in WIRE_COLS[(op >> 4) & 3]:
            q = take(c)
            if q >= h[1]:
                raise ValueError(f'wire q{q} outside declared width {h[1]}')
            wires.add(q)
        if op & 64:
            take(8)
        if op & 128:
            take(9)
    if any(pos[c] != len(cols[c]) for c in pos):
        raise ValueError('unconsumed operation entries')
    return {'width_gate': 'PASS', 'declared_width': h[1], 'max_wire_index': max(wires, default=-1), 'distinct_wires': len(wires), 'instructions': h[4], 'cap': cap, 'sha256': hashlib.sha256(data).hexdigest()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kmb')
    parser.add_argument('--max-width', type=int, choices=range(22, 37), default=36)
    args = parser.parse_args()
    try:
        print(json.dumps(check(args.kmb, args.max_width)))
    except (ValueError, OSError, struct.error) as exc:
        parser.exit(1, f'WIDTH REJECT: {exc}\n')
