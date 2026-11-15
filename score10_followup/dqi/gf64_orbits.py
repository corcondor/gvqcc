#!/usr/bin/env python3
"""Use GF64 multiplication and Frobenius to classify inverse scaffolds."""
import argparse
from collections import Counter
from itertools import combinations
import json
from pathlib import Path

from gf64_probe import bases, mix, probe, table, solve
from gf64_quad_spaces import rem_basis, reduce_against, quadratic_anf

def orbit_scan(source, data):
    current, targets, _, _=probe(source)
    import kickmix as km
    field=km.GF2Field(6)
    adjugate=[table(lambda x:(field.pow(x,20)>>i)&1) for i in range(6)]
    adj_basis=rem_basis([quadratic_anf(t) for t in adjugate])
    coordinates=list(combinations(range(6),2))
    actions=[]
    for scalar in range(1,64):
        for power in range(6):
            transform=[field.mul(scalar,field.pow(x,1<<power)) for x in range(64)]
            bits=[table(lambda x:(transform[x]>>i)&1) for i in range(6)]
            actions.append([reduce_against(quadratic_anf(bits[i]&bits[j]),adj_basis)
                            for i,j in coordinates])
    sources={tuple(sorted(x['plane'])):x for x in data['rank8_bases']}
    remaining=set(sources)
    orbits=[]
    while remaining:
        u,v=min(remaining)
        orbit=set()
        for action in actions:
            moved_u,moved_v=mix(action,u),mix(action,v)
            assert moved_u and moved_v and moved_u!=moved_v
            orbit.add(tuple(sorted((moved_u,moved_v,moved_u^moved_v))[:2]))
        assert orbit<=remaining
        remaining-=orbit
        orbits.append((sources[(u,v)],len(orbit)))
    assert sum(count for _,count in orbits)==len(sources)
    print('Orbit sizes:', [count for _,count in orbits],flush=True)
    summary=[]
    for row,count in orbits:
        bits=current[1:7]
        terms=[mix(bits,a)&mix(bits,b) for a,b in row['terms']]
        live=current[:7]+terms
        remainder=rem_basis(live)
        basis= bases(live)[0]
        norm_classes=[reduce_against(mix(current[-2:],mask),remainder) for mask in (1,2,3)]
        assert len(bases(norm_classes)[0])==2
        candidates=[None]*3
        checked=0
        for left in range(1,1<<14):
            left_table=mix(live[1:],left)
            right_space,_=bases([reduce_against(left_table&word,remainder)
                                 for word in live[1:]])
            checked+=1
            for i,target in enumerate(norm_classes):
                if candidates[i] is None:
                    right=solve(target,right_space)
                    if right is not None:
                        norm=mix(current[-2:],i+1)
                        correction=solve((left_table&mix(live[1:],right))^norm,basis)
                        assert correction is not None
                        candidates[i]=dict(left=left,right=right,correction=correction)
            if sum(x is not None for x in candidates)>=2:
                break
        summary.append(dict(orbit_size=count,checked_left_forms=checked,**row,
                            single_and_norm_directions=candidates))
        print(row['plane'],count,candidates,flush=True)
    return dict(status='COMPLETE',orbit_count=len(orbits),
                winning_orbit_count=sum(sum(x is not None for x in r['single_and_norm_directions'])>=2 for r in summary),
                records=summary)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--source',required=True)
    p.add_argument('--scaffolds',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    ans=orbit_scan(args.source,json.loads(args.scaffolds.read_text()))
    args.output.write_text(json.dumps(ans,indent=2)+'\n')
