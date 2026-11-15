#!/usr/bin/env python3
"""Check a five-edge kernel dependency with an independently predicted result."""
from pathlib import Path
from tempfile import TemporaryDirectory
import struct
import subprocess
import sys

width = 6
parts = [struct.pack("<I", width)]
for i in range(width):
    rows = [0] * 76
    rows[0] = (1 << i) ^ (1 << ((i + 1) % width))
    rows[i + 1] = 1 << 9
    parts.append(struct.pack("<76H", *rows))
with TemporaryDirectory() as tmp:
    src = Path(tmp) / "cycle.bin"
    src.write_bytes(b"".join(parts))
    command = [sys.argv[1], str(src), "graph"]
    process = subprocess.run(command, check=True, capture_output=True, text=True)
    hits = []
    for line in process.stdout.splitlines():
        _, a, b, *words = line.split()
        if (int(a), int(b)) == (512, 3):
            hits.append(sum(int(v, 16) << (64 * i) for i, v in enumerate(words)))
assert sorted(hits) == [1, 62], hits
print("graph kernel, plane (512,3):", hits)
