#!/usr/bin/env python3
"""Dense one-Toffoli synthesis of coherent windows with one new affine direction."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from collections import Counter

import numpy as np
import kickmix as km

from quadratic_phase import MAX_X, SOURCE_SHA, advance, coefficients, gate, solve_coset, trace
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'quick_inv_score'))
from rankone import select, intersection, affine_basis, solve, encode_common

def combination(v, data):
    value = 0
    for j, bits in enumerate(data):
        if v >> j & 1:
            value ^= bits
    return value

def synthesize(before, after, mask, limit, sat_ms):
    old = select([mask, *before])
    new = select([mask, *after])
    bases = affine_basis(old), affine_basis(new)
    common = select([mask, *[v for v in before if solve(bases[1],v) is not None], *intersection(old, new)])
    extra = [x for x in new if solve(bases[0], x) is None]
    if len(new) != len(common) + 1 or len(old) not in (len(common), len(common)+1):
        return 'incompatible_intersection', None, {}
    retained = common[1:]
    t = next((x for x in old if solve(bases[1], x) is None), 0)
    if not t and len(old) == len(before)+1:
        return 'no_target_coordinate', None, {}
    target = extra[0] ^ t
    wires, edges, kernel, polynomial = coefficients(retained, mask, [target])
    report = dict(common_dimension=len(retained), nullity=len(kernel))
    p = polynomial[0]
    if p is None:
        return 'outside_quadratic_span', None, report
    fact, exhausted, report['star_rank'] = solve_coset(p, kernel, edges, len(wires), limit)
    if fact is None and not exhausted and sat_ms:
        from complete_tripartite import find_by_sat
        fact, exhausted = find_by_sat(len(wires), edges, kernel, p, sat_ms)
        report['sat'] = 'SAT' if fact is not None else ('UNSAT' if exhausted else 'UNKNOWN')
    if fact is None:
        return ('rank_two_excluded'  if exhausted else 'projection_above_limit'), None, report
    if not all(fact):
        return 'affine_relation', None, report
    x,y = (combination(v, [retained[q] for q in wires]) for v in fact)
    others = select([mask, x, y, t, *old])[3+(t!=0):]
    layout = [x, y, t, *others]
    assert len(layout) <= len(before)
    layout += [0]*(len(before)-len(layout))
    assert len(affine_basis([mask, *layout])) == len(old)
    result = layout[:]
    result[2] ^= x & y
    result_basis = affine_basis([mask, *result])
    assert len(result_basis) == len(new) and all(solve(result_basis, v) is not None for v in new)
    code = (encode_common([mask, *layout], [mask, *before], None)
            + ['CCX q0 q1 q2']
            + encode_common([mask, *after], [mask, *result], None))
    actual = before[:]
    for op, qs in map(gate, code):
        advance(op, qs, actual, mask)
    assert actual == after
    return 'candidate', code, report

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--windows', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--projection-limit', type=int, default=17)
    p.add_argument('--sat-ms', type=int, default=0)
    args = p.parse_args()
    assert hashlib.sha256(args.source.read_bytes()).hexdigest() == SOURCE_SHA
    lines = str(km.Circuit.from_file(args.source,format='kmb')).splitlines()
    ops = list(map(gate, lines))
    windows = [w for w in json.loads(args.windows.read_text())['hits'] if w['rank']==1]
    rng = np.random.default_rng(46322)
    xs = np.unique(np.r_[np.arange(1,900), rng.integers(1, MAX_X+1, 10200), MAX_X]).astype(np.uint32)
    states, mask = trace(ops, xs, {w[k]+(k=='end') for w in windows for k in ('start','end')})
    certificates = []
    matches = []
    for w in windows:
        a,b = w['start'],w['end']+1
        assert all(op in {'X','CX','CCX','SWAP','CSWAP'} for op, _ in ops[a:b])
        status, code, detail = synthesize(states[a], states[b], mask, args.projection_limit, args.sat_ms)
        row = dict(**w, status=status, **detail)
        if code:
            row['code']=code
            matches.append(row)
        print(row, flush=True)
        certificates.append(row)
    if matches:
        all_x = np.arange(1,MAX_X+1,dtype=np.uint32)
        states, domain = trace(ops, all_x, {w[k]+(k=='end') for w in matches for k in ('start','end')})
        for index, w in enumerate(matches):
            a,b = w['start'],w['end']+1
            actual = states[a][:]
            for op, qs in map(gate, w['code']):
                advance(op, qs, actual, domain)
            w['full_domain'] = states[b]==actual
            if w['full_domain']:
                text = '\n'.join(lines[:a]+w['code']+lines[b:])+'\n'
                target = args.out.with_name(args.out.stem + f'_{index}.kmb')
                km.Circuit(text).to_file(target, format='kmb')
                w['kmb_sha'] = hashlib.sha256(target.read_bytes()).hexdigest()
    args.out.write_text(json.dumps(dict(source=SOURCE_SHA, samples=len(xs),
                                        outcomes=Counter(r['status'] for r in certificates),
                                        certificate=certificates),indent=2)+'\n')

if __name__=='__main__':main()
