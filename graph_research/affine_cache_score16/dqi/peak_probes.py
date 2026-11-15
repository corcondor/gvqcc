"""Select the start and midpoint of each maximum-width interval span."""
import csv
from collections import Counter
from pathlib import Path
import sys

events = Counter()
with Path(sys.argv[1]).open() as source:
    for row in csv.DictReader(source, delimiter="\t"):
        events[int(row["first"])] += 1
        events[int(row["last"]) + 1] -= 1

ends = sorted(events)
width = max_width = 0
spans = []
for start, stop in zip(ends, ends[1:]):
    width += events[start]
    if width > max_width:
        max_width = width
        spans.clear()
    if width != max_width:
        continue
    spans.append((start, stop))
points = {point for a, b in spans for point in (a, (a + b) // 2)}
Path(sys.argv[2]).write_text("".join(f"{p}\n" for p in sorted(points)))
