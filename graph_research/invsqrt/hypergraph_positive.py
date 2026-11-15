#!/usr/bin/env python3
"""Exact four-variable positive control requiring two insertion cuts."""
import json
from pathlib import Path
from temporal_phase_graph import make_edges,solve,product


def main():
    mask=(1<<16)-1
    raw=[sum(((i>>j)&1)<<i for i in range(16)) for j in range(4)]
    x,y,z,w=raw
    states={0:raw,1:[x,y,z,w^(x&y)]}
    goal=x&y&z
    individual=[]
    for t, state in states.items():
        basis,_,_=make_edges({t:state},mask,t,1)
        individual.append(solve(basis,goal) is not None)
    basis,edges,_=make_edges(states,mask,0,2)
    chosen=solve(basis,goal)
    assert not any(individual) and chosen is not None
    selected=[edge for j,edge in enumerate(edges) if chosen>>j&1]
    observed=0
    for t,qs in selected: observed^=product(states[t],qs,mask)
    assert observed==goal
    data=dict(scope='synthetic exact 4-bit control, not a benchmark candidate',
              single_cut_found=individual,union_found=True,selected=selected,
              agrees_on_all_assignments=True,assignments=16)
    Path(__file__).with_name('hypergraph_positive.json').write_text(json.dumps(data,indent=2)+'\n')
    print(data)

if __name__=='__main__':main()
