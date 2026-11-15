#!/usr/bin/env python3
"""Bounded new search: whole phase = quadratic + three affine parities.

Extends score8's two raw controls. A negative result is not a lower bound.
Searches sparse first two parities and an unrestricted third parity.
Only reports a candidate after full-domain symbolic phase comparison.
"""
import argparse
import itertools
import json
from pathlib import Path
import random
import time
import score8_invsqrt_phase_oneccz as P
import score_invsqrt_retire as R


def search(values, target, one, seconds, seed):
    rng = random.Random(seed)
    wires = [q for q,v in enumerate(values) if v not in (0,one)]
    columns = [one]+[values[q] for q in wires]+[values[a]&values[b] for a,b in itertools.combinations(wires,2)]
    basis = R.affine_basis(columns)
    pivots = sorted(basis, reverse=True)
    def reduce(v):
        for p in pivots:
            if v>>p&1: v ^= basis[p][0]
        return v
    residual = reduce(target)
    cache = {}
    started = time.monotonic()
    queries = 0
    while time.monotonic()-started < seconds:
        aa = tuple(sorted(rng.sample(wires,rng.choice((2,2,3,4)))))
        bb = tuple(sorted(rng.sample(wires,rng.choice((1,2,3,4)))))
        if aa == bb: continue
        reduced = []
        for c in wires:
            v = 0
            for a in aa:
                for b in bb:
                    if len({a,b,c})<3: continue  # belongs to the free quadratic span
                    key = tuple(sorted((a,b,c)))
                    if key not in cache: cache[key]=reduce(values[a]&values[b]&values[c])
                    v ^= cache[key]
            reduced.append(v)
        coeff = R.solve(R.affine_basis(reduced),residual)
        queries += 1
        if coeff is not None:
            cc = [q for i,q in enumerate(wires) if coeff>>i&1]
            prod = one
            for form in (aa,bb,cc):
                val = 0
                for q in form: val ^= values[q]
                prod &= val
            quad,_ = P.quadratic(values,target^prod,one)
            assert quad is not None
            return dict(status='SAMPLE_HIT',factors=[list(aa),list(bb),cc],quadratic=quad,queries=queries)
    return dict(status='NO_HIT_WITHIN_TIME_BUDGET',queries=queries,cubic_cache=len(cache))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--seconds-per-block',type=float,default=5)
    args=ap.parse_args(); args.out.mkdir(parents=True,exist_ok=True)
    source=Path(__file__).with_name('score3_invsqrt_cache.kmx')
    assert P.sha(source)==P.PIN
    lines,ops=R.instructions(source)
    blocks,depth,uses=P.shape(lines,ops)
    items=[]
    for x in blocks:
        if x['paid']<=1: continue
        sym,_=P.symbols(lines,ops,x,depth,uses)
        if sym is not None: items.append({**x,'symbolic':sym})
    rng=random.Random(2026111518)
    xs=sorted(set(list(range(1,129))+[rng.randrange(1,R.MAX_X+1) for _ in range(4096)]))
    one,values=P.sample_values(xs)
    data=P.extract(lines,ops,items,one,values)
    rows=[]
    for item,values,key,target in data:
        model=search(values,target,one,args.seconds_per_block,2026111500+item['start'])
        row=dict(start=item['start'],end=item['end'],original_paid=item['paid'],condition=key,model=model)
        rows.append(row)
        print(json.dumps(row),flush=True)
    hits={r['start']:r for r in rows if r['model']['status']=='SAMPLE_HIT'}
    if hits:
        one,values=R.initial_values()
        for item,values,key,target in P.extract(lines,ops,[x for x in items if x['start'] in hits],one,values):
            m=hits[item['start']]['model']; prod=one
            for form in m['factors']:
                v=0
                for q in form:v^=values[q]
                prod&=v
            actual=prod
            for term in m['quadratic']:
                v=one
                for q in term:v&=values[q]
                actual^=v
            m['full_domain_equal']=actual==target
    result=dict(source_sha256=P.PIN,inputs=len(xs),blocks=rows,
                scope='First parity weight 2-4; second weight 1-4; arbitrary third parity; arbitrary quadratic correction. Fixed wall-clock budget; no general lower bound.',
                full_domain_hits=sum(r['model'].get('full_domain_equal',False) for r in rows),
                candidate_emitted=False,full_official_verification=False)
    (args.out/'result.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__': main()
