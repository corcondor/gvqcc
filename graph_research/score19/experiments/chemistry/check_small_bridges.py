#!/usr/bin/env python3
"""Exhaust low-rank bridge supports around the actual short output dependencies."""
import argparse
from itertools import combinations, chain
import hashlib
import json
from pathlib import Path
import time

from minrank_bridge import closure_components, load_segments, rank


def four_dependencies(directions):
    pairs = {}
    discovered = set()
    for i, j in combinations(range(len(directions)), 2):
        value = directions[i] ^ directions[j]
        for old in pairs.get(value, []):
            if i not in old and j not in old:
                discovered.add(tuple(sorted((*old, i, j))))
        pairs.setdefault(value, []).append((i, j))
    return sorted(discovered)


def check_neighbor_support(matrices, components, neighbors):
    all_vertices = [i for i in range(len(matrices)) if any(g >> i & 1 for g in components)]
    row_sum = [0] * 76
    prev = 0
    support = 0
    checked = 0
    results = []
    for i in range(1, 1 << len(all_vertices)):
        gray = i ^ (i >> 1)
        flip = (prev ^ gray).bit_length() - 1
        prev = gray
        vertex = all_vertices[flip]
        support ^= 1 << vertex
        row_sum = [x ^ y for x, y in zip(row_sum, matrices[vertex])]
        if sum(bool(g & support) for g in components) < 2:
            continue
        if neighbors and all(not (g & support) for g in neighbors):
            continue   # Supports contained in base already checked once.
        checked += 1
        intro = {}
        for value in row_sum:
            while value:
                key = value.bit_length()
                if key not in intro:
                    intro[key] = value
                    break
                value ^= intro[key]
            if len(intro) > 2:
                break
        else:
            results.append(dict(support=[v for v in all_vertices if support >> v & 1], rank=len(intro)))
    return checked, results


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--segments', type=Path, required=True)
    p.add_argument('--metadata', type=Path, required=True)
    p.add_argument('--loaders', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    reports = []
    started = time.monotonic()
    for matrices, row in load_segments(a.segments, a.metadata):
        path = a.loaders / f"angle_k_{row['batch']}.kmb"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row['source_sha256']
        dependencies = four_dependencies(row['directions'])
        if not dependencies:
            continue
        closure_size, components = closure_components(matrices)
        for dependency in dependencies:
            depmask = sum(1 << i for i in dependency)
            base = [g for g in components if g & depmask]
            extras = [g for g in components if not g & depmask]
            assert rank([row['directions'][i] for i in dependency]) == 3
            total = 0
            hits = []
            for addition in chain([[]], ([g] for g in extras)):
                count, result = check_neighbor_support(matrices, base + addition, addition)
                total += count
                hits.extend(result)
            report = dict(batch=row['batch'], source_sha256=row['source_sha256'],
                          output_dependency=dependency,
                          closure_size=closure_size,
                          base_component_sizes=[g.bit_count() for g in base],
                          additional_components_tested=len(extras),
                          checked_cross_component_supports=total, hits=hits)
            reports.append(report)
            print(json.dumps(report), flush=True)
    a.out.write_text(json.dumps(dict(reports=reports, seconds=time.monotonic() - started), indent=2) + '\n')


if __name__ == '__main__':
    main()
