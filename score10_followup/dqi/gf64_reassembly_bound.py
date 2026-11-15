#!/usr/bin/env python3
"""Rank certificate for norm-linear reassembly on each GF64 scaffold."""
import argparse
from collections import Counter
import json
from pathlib import Path

from gf64_probe import bases, mix, probe, solve
from gf64_quad_spaces import reduce_against, rem_basis

def check(source, scaffold_data):
    current, targets, _, _ = probe(source)
    valid = scaffold_data['rank8_bases']
    assert len(valid) == 1120
    ranks = Counter()
    nullities = Counter()
    for record in valid:
        gates = record['terms']
        quads = [mix(current[1:7], a) & mix(current[1:7], b) for a,b in gates]
        scaffold = current[:7]+quads+current[-2:]
        columns = scaffold + [norm & word for norm in scaffold[-2:]
                              for word in scaffold[1:15]]
        basis, null = bases(columns)
        target_coefficients = [solve(y,basis) for y in targets]
        assert None not in target_coefficients
        nullities[len(null)] += 1
        projections = (
            lambda v: (v >> 17) & 0x3fff,
            lambda v: (v >> 31) & 0x3fff,
            lambda v: ((v >> 17) ^ (v >> 31)) & 0x3fff,
        )
        projected_ranks = []
        for coefficients in projections:
            unrestricted = rem_basis([coefficients(n) for n in null])
            rows = [reduce_against(coefficients(v),unrestricted)
                    for v in target_coefficients]
            projected_ranks.append(len(bases(rows)[0]))
        assert projected_ranks == [6,6,6]
        ranks[tuple(projected_ranks)] += 1
    return dict(status='COMPLETE',scaffolds=len(valid),one_row_nullities=dict(nullities),
                projected_rank_histogram={str(k):v for k,v in ranks.items()},
                min_norm_linear_output_products=9)

if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--source',required=True)
    p.add_argument('--scaffolds',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    report=check(a.source,json.loads(a.scaffolds.read_text()))
    a.out.write_text(json.dumps(report,indent=2)+'\n')
    print(report)
