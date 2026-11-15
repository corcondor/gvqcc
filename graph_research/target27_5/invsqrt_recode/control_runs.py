"""Audit the normalization-selector support and union graphs."""
from collections import Counter,defaultdict
from itertools import combinations
import json
from pathlib import Path
import sys

import kickmix as km
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'highest_inv_next'))
from quadratic_phase import MAX_X, SOURCE_SHA, gate, trace

CUT=7630
RUNS=((7631,7643),(7644,7656),(7659,7667))
QS=[23,24,25]
def degree(m):
    return sorted(Counter(x for row in m for x in row).items())

def union(a,b):
    link=defaultdict(set)
    edges=[]
    for name,run in zip('ab',(a,b)):
        for x,y in run:
            link[x].add(y);link[y].add(x);edges.append((x,y,name))
    visited=set()
    comps=[]
    for q in sorted(link):
        todo=[q]; seen=set()
        while todo:
            x=todo.pop()
            if x in seen:continue
            seen.add(x);todo.extend(link[x]-seen)
        if sorted(seen) in [r['vertices'] for r in comps]:continue
        comps.append({'vertices':sorted(seen),'edges':[e for e in edges if e[0] in seen]})
    return comps

def main():
    c=km.Circuit.from_file('invsqrt_new/rebuilt_source.kmb',format='kmb')
    lines=str(c).splitlines()
    ops=list(map(gate,lines))
    w,mask=trace(ops,np.arange(1,MAX_X+1,dtype=np.uint32),{CUT, *(a for a,b in RUNS)})
    v=w[CUT]
    selectors=[mask^v[24], v[25], mask^v[23]^v[24]^v[25]]
    distribution={}
    for c in range(8):
        z=mask
        for i,x in enumerate(selectors):
            z &= x if c>>i&1 else mask^x
        distribution[str(c)]=z.bit_count()
    rs=[[ops[i][1][1:] for i in range(a,b)] for a,b in RUNS]
    result=dict(source=SOURCE_SHA,selectors=distribution,comparisons={})
    for i,j in combinations(range(3),2):
        g=union(rs[i],rs[j])
        cyc=[r for r in g if len(r['vertices'])<=len(r['edges'])]
        result['comparisons'][f'{i}-{j}']={'components':g,'cyclic':len(cyc)}
    Path('score20_inv_recoding/controls.json').write_text(json.dumps(result,indent=2)+'\n')
    print(distribution)
    print([(k,x['cyclic'],[(len(q['vertices']),len(q['edges'])) for q in x['components']]) for k,x in result['comparisons'].items()])

if __name__=='__main__':
    main()
