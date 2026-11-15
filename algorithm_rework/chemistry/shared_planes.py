#!/usr/bin/env python3
"""Check shared affine-factor rank using all bases of each control plane."""
from argparse import ArgumentParser
from collections import defaultdict
from pathlib import Path
import json
import sys

import kickmix as km

from schedule_angle import bit_positions, get_frame

def factor_rank(matrices):
    rows = {}
    for row in matrices:
        while row:
            lead=row.bit_length()
            if lead not in rows:
                rows[lead]=row
                break
            row ^= rows[lead]
    return len(rows)

def sharing(terms,n_outputs):
    choices=defaultdict(list)
    for i,(a,b,w) in enumerate(terms):
        a &= ~1
        b &= ~1
        assert a and b and a!=b
        choices[a].append((i,b,w))
        choices[b].append((i,a,w))
        choices[a^b].append((i,a,w))
    results=[]
    max_group=0
    tested=0
    for c,items in choices.items():
        if len(items)<2: continue
        tested+=1
        max_group=max(max_group,len(items))
        matrices=[0]*n_outputs
        for _,b,w in items:
            for o in bit_positions(w): matrices[o]^=b
        rank=factor_rank(matrices)
        if rank<len(items):
            results.append({'factor':hex(c),'term_ids':[i for i,_,_ in items],
                            'rank':rank,'potential_and_reduction':len(items)-rank})
    return {'shared_factors':tested,'max_group':max_group,'rank_reductions':results}

def main():
    p=ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--loaders',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    a=p.parse_args()
    sys.path.insert(0,str(a.repo))
    from chemistry_affine_span_resynthesis import parse_line
    from chemistry_joint_product_resynthesis import DATA
    found=[]
    for k in range(15):
        circ=km.Circuit.from_file(a.loaders/f'angle_k_{k}.kmb')
        ops=list(map(parse_line,str(circ).splitlines()))
        pool=set(range(circ.num_qubits))-set(DATA)
        start=0
        for i,(g,w,c) in enumerate(ops+[('END',(),None)]):
            if c is None and (g=='X' or (g=='CX' and not (w[0] in DATA and w[1] in pool))
                or (g=='CCX' and w[2] in DATA and w[0] in pool and w[1] in pool)):
                continue
            if any(g=='CCX' for g,_,_ in ops[start:i]):
                _,terms=get_frame(ops[start:i],DATA,int(circ.num_qubits))
                found.append(dict(batch=k,start=start,end=i,terms=len(terms),**sharing(terms,len(DATA))))
            start=i+1
    a.report.write_text(json.dumps(found,indent=2)+'\n')
    print('blocks',len(found),'shared factors',sum(q['shared_factors'] for q in found),
          'reductions',sum(len(q['rank_reductions']) for q in found))
if __name__=='__main__':
    main()
