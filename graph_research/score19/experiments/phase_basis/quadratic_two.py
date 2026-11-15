"""Look for two paid sequential updates in rank-two coherent windows."""
import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
import kickmix as km
from quadratic_windows import MAX_X, SOURCE_SHA, advance, affine_basis, coefficients
from quadratic_windows import combination, encode_common, gate, intersection, select, solve, solve_coset, trace

def extra_directions(common, vectors):
    base = affine_basis(common)
    extra = []
    for v in vectors:
        if solve(base,v) is None:
            extra.append(v)
            base = affine_basis([*common,*extra])
    return extra

def extensions(vectors):
    if len(vectors) < 2:
        if not vectors:
            return [(0, 0)]
        v, = vectors
        return [(v, 0),(0, v),(v, v)]
    a,b = vectors
    return list(itertools.permutations((a,b,a^b),2))

def compile_gate(data, desired, a, b, old_t, new_t, mask):
    layout = [a, b, old_t]
    initial = select([mask,a,b,old_t])
    kept = select([*initial,*data])[len(initial):]
    layout.extend(kept)
    layout += [0]*(len(data)-len(layout))
    if len(layout) != len(data):
        return
    old = [mask,*data]
    now = layout[:]
    now[2] ^= a&b
    target = [mask,*desired]
    rank = affine_basis([mask,*now])
    if len(rank) != len(affine_basis(target)) or not all(solve(rank,v) is not None for v in target):
        return
    return (encode_common([mask,*layout],old,None) + ['CCX q0 q1 q2']
            + encode_common(target,[mask,*now],None))

def factor(retained, target, mask, limit):
    wires, edges, kernel, ps = coefficients(retained, mask, [target])
    if ps[0] is None:
        return None, True
    fact, exact, _ = solve_coset(ps[0], kernel, edges, len(wires), limit)
    if fact is None:
        return None, exact
    if not all(fact):
        return (0, 0), True
    return tuple(combination(f, [retained[q] for q in wires]) for f in fact), True

def synthesize(before, after, mask, limit):
    old = select([mask,*before])
    new = select([mask,*after])
    new_basis = affine_basis(new)
    common = select([mask,*[v for v in before if solve(new_basis,v) is not None],*intersection(old,new)])
    p = extra_directions(common,old)
    q = extra_directions(common,new)
    if len(q)!=2 or len(p)>2:
        return None, dict(reason='intersection_incompatible',p=len(p),q=len(q))
    checked = 0
    unresolved = 0
    cache = {}
    for (t0,t1),(u0,u1) in itertools.product(extensions(p),extensions(q)):
        def solve_stage(kept, target):
            key = tuple(kept),target
            if key not in cache:
                cache[key]=factor(kept,target,mask,limit)
            return cache[key]
        steps=[(common[1:]+([t1] if t1 else []),t0^u0),
               (common[1:]+[u0], t1^u1)]
        if t0 and t0==t1:
            continue
        solutions = []
        for retained,target in steps:
            f, exact = solve_stage(retained,target)
            if not exact:
                unresolved += 1
            if not f or not all(f):
                break
            solutions.append(f)
        checked += 1
        if len(solutions) != 2:
            continue
        middle = [*steps[0][0],u0]
        middle += [0]*(len(before)-len(middle))
        a0,b0 = solutions[0]
        a1,b1 = solutions[1]
        code0 = compile_gate(before,middle,a0,b0,t0,u0,mask)
        code1 = compile_gate(middle,after,a1,b1,t1,u1,mask)
        if code0 is None or code1 is None:
            continue
        return code0+code1,dict(reason='candidate',checked=checked,unresolved=unresolved)
    return None,dict(reason='no_candidate',checked=checked,unresolved=unresolved)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for x in ('source','windows','out'):
        p.add_argument('--'+x,type=Path,required=True)
    p.add_argument('--projection-limit',type=int,default=14)
    args=p.parse_args()
    assert hashlib.sha256(args.source.read_bytes()).hexdigest()==SOURCE_SHA
    lines=str(km.Circuit.from_file(args.source,format='kmb')).splitlines()
    ops=list(map(gate,lines))
    windows=[w for w in json.loads(args.windows.read_text())['hits'] if w['rank']==2]
    rng=np.random.default_rng(377433)
    xs=np.unique(np.r_[np.arange(1,900),rng.integers(1,MAX_X+1,10200),MAX_X]).astype(np.uint32)
    states,mask=trace(ops,xs,{w[k]+(k=='end') for w in windows for k in ('start','end')})
    hits=[]
    records=[]
    for w in windows:
        a,b=w['start'],w['end']+1
        assert all(op in {'X','CX','CCX','SWAP','CSWAP'} for op,_ in ops[a:b])
        code,details=synthesize(states[a],states[b],mask,args.projection_limit)
        row=dict(**w,**details)
        if code:
            row['code']=code
            hits.append(row)
        print({k:v for k,v in row.items() if k!='code'},flush=True)
        records.append(row)
    if hits:
        states,mask=trace(ops,np.arange(1,MAX_X+1,dtype=np.uint32),
                          {w[k]+(k=='end') for w in hits for k in ('start','end')})
        for i,row in enumerate(hits):
            a,b=row['start'],row['end']+1
            actual=states[a][:]
            for op,qs in map(gate,row['code']):
                advance(op,qs,actual,mask)
            row['full_domain']=actual==states[b]
            print('full domain',i,row['full_domain'],flush=True)
            if row['full_domain']:
                target=args.out.with_name(args.out.stem+f'_{i}.kmb')
                km.Circuit('\n'.join(lines[:a]+row['code']+lines[b:])+'\n').to_file(target,format='kmb')
                row['kmb_sha']=hashlib.sha256(target.read_bytes()).hexdigest()
    args.out.write_text(json.dumps(dict(source=SOURCE_SHA,samples=len(xs),records=records),indent=2)+'\n')

if __name__=='__main__':
    main()
