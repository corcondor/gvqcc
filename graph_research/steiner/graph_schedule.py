#!/usr/bin/env python3
"""Graph-ordered exact ANGLE parity/fanout schedules."""
import argparse
from collections import Counter
from hashlib import sha256
import itertools
import json
from pathlib import Path
import random
import shutil
import sys

import kickmix as km

STATS=[]
BATCH=0


def mst(vertices):
    """Prim on an implicit Hamming-metric complete graph, rooted at node 0."""
    n=len(vertices)
    todo=set(range(1,n))
    weight=[(x^vertices[0]).bit_count() for x in vertices]
    parents=[0]*n
    total=0
    while todo:
        i=min(todo,key=lambda j:(weight[j],j))
        todo.remove(i)
        total+=weight[i]
        for j in todo:
            d=(vertices[i]^vertices[j]).bit_count()
            if d<weight[j]:
                weight[j],parents[j]=d,i
    return total,parents


def steiner_tree(vertices):
    nodes=list(vertices)
    base,parents=mst(nodes)
    cost=base
    # Add only bitwise 3-medians that reduce the metric spanning cost.
    # Trees through them are candidates, not an exact Steiner optimum.
    rng=random.Random(8713+len(nodes))
    for _ in range(3):
        adjacency=[[] for _ in nodes]
        for j,i in enumerate(parents[1:],1):
            adjacency[i].append(j)
            adjacency[j].append(i)
        triples=set()
        for i,neighbor in enumerate(adjacency):
            for j,k in itertools.combinations(sorted(neighbor)[:8],2):
                triples.add(tuple(sorted((i,j,k))))
        if len(nodes)>=3:
            for _ in range(16):
                triples.add(tuple(sorted(rng.sample(range(len(nodes)),3))))
        options=set()
        for i,j,k in triples:
            x,y,z=nodes[i],nodes[j],nodes[k]
            options.add((x&y)|(x&z)|(y&z))
        options.difference_update(nodes)
        best=None
        for value in sorted(options):
            score,tree=mst(nodes+[value])
            if score<cost and (best is None or score<best[0]):
                best=score,tree,value
        if best is None:break
        cost,parents,value=best
        nodes.append(value)
    return nodes,parents,base,cost


def preorder(vertices,parents,term_count,reverse):
    sons=[[] for _ in vertices]
    for j,i in enumerate(parents[1:],1):
        sons[i].append(j)
    order=[]
    pending=[0]
    while pending:
        i=pending.pop()
        if 1<=i<term_count:
            order.append(i-1)
        pending.extend(sorted(sons[i],key=lambda j:((vertices[i]^vertices[j]).bit_count(),j),
                              reverse=not reverse))
    return order


def canonical(a,b,pivots,S):
    ka,kb=S.selector_pair(a,b,*pivots)
    m={ka:a,kb:b,ka^kb:a^b}
    return m[1],m[2]


def costs(terms,entry,exit_,pivots,fan,S):
    forms=[[(a,b),(b,a)] for a,b,_ in terms]
    def ctl(a,b):
        return S.distance(S.parity_transition(a,b,pivots))
    start=[[ctl(entry,state)+(w^fan).bit_count() for state in options]
           for (_,_,w),options in zip(terms,forms,strict=True)]
    stop=[[(ctl(state,exit_) if exit_ is not None else 0)+(w^fan).bit_count()
           for state in options] for (_,_,w),options in zip(terms,forms,strict=True)]
    edges=[]
    for i,a in enumerate(forms):
        row=[]
        for j,b in enumerate(forms):
            f=(terms[i][2]^terms[j][2]).bit_count()
            row.append(tuple(ctl(u,v)+f for u in a for v in b))
        edges.append(row)
    return forms,start,stop,edges


def price(order,start,stop,edges,trace=False):
    d0,d1=start[order[0]]
    decisions=[]
    for i,j in zip(order,order[1:]):
        c00,c01,c10,c11=edges[i][j]
        a0,a1=d0+c00,d1+c10
        b0,b1=d0+c01,d1+c11
        if trace:decisions.append((int(a1<a0),int(b1<b0)))
        d0,d1=min(a0,a1),min(b0,b1)
    x,y=stop[order[-1]]
    d0+=x
    d1+=y
    result=min(d0,d1)
    if not trace:return result
    a=int(d1<d0)
    states=[a]
    for ds in reversed(decisions):
        a=ds[a]
        states.append(a)
    return result,states[::-1]


def greedy_order(start,edges):
    n=len(start)
    i=min(range(n),key=lambda j:min(start[j]))
    state=int(start[i][1]<start[i][0])
    remaining=set(range(n))-{i}
    order=[i]
    while remaining:
        j=min(remaining,key=lambda k:min(edges[i][k][2*state:2*state+2]))
        a,b=edges[i][j][2*state:2*state+2]
        state=int(b<a)
        remaining.remove(j)
        order.append(j)
        i=j
    return order


def refine(order,start,stop,edges):
    best=price(order,start,stop,edges)
    for _ in range(2):
        selected=None
        for i,j in itertools.combinations(range(len(order)),2):
            cand=order[:i]+order[i:j+1][::-1]+order[j+1:]
            c=price(cand,start,stop,edges)
            if c<best and (selected is None or c<selected[0]):
                selected=c,cand
        if selected is None:break
        best,order=selected
    return order


def choose_tour(terms,entry,exit_,pivots,fan,S):
    forms,start,stop,edges=costs(terms,entry,exit_,pivots,fan,S)
    n=len(terms)
    bitwidth=max(x.bit_length() for a,b,_ in terms for x in (a,b,*entry))
    def point(a,b,w):
        x,y=canonical(a,b,pivots,S)
        return x|(y<<bitwidth)|(w<<(2*bitwidth))
    vertices=[point(*entry,fan)]+[point(a,b,w) for a,b,w in terms]
    tree_cost,tree=mst(vertices)
    vs,sh,_,steiner_cost=steiner_tree(vertices)
    orders=[('greedy',greedy_order(start,edges))]
    for flip in (False,True):
        orders.append(('mst',preorder(vertices,tree,n+1,flip)))
        orders.append(('steiner' if len(vs)>len(vertices) else 'mst',
                       preorder(vs,sh,n+1,flip)))
    best_by_method={}
    for label,order in orders:
        assert len(order)==n and len(set(order))==n
        alt=refine(order,start,stop,edges) if n<=65 else order
        score=price(alt,start,stop,edges)
        if label not in best_by_method or score<best_by_method[label][0]:
            best_by_method[label]=score,alt
    label=min(best_by_method,key=lambda k:best_by_method[k][0])
    score,order=best_by_method[label]
    _,orient=price(order,start,stop,edges,trace=True)
    STATS.append(dict(batch=BATCH,size=n,mst_cost=tree_cost,steiner_cost=steiner_cost,
                      hubs=len(vs)-len(vertices),
                      pivot_state_changes=sum(int(S.selector_pair(a,b,*pivots)!=(1,2))
                                              for a,b,_ in terms),
                      mean_weight=sum(w.bit_count() for _,_,w in terms)/n,
                      costs={k:v[0] for k,v in best_by_method.items()},
                      selected=label,chosen_cost=score))
    return [(forms[j][s],terms[j][2]) for j,s in zip(order,orient,strict=True)]


def graph_schedule(terms,pool,data,S):
    lines=[]
    for pivots,group in S.choose_groups(terms,pool):
        orig=tuple(1<<(q+1) for q in pivots)
        ctrl=orig
        while group:
            t=max(range(len(data)),key=lambda i:sum((w>>i)&1 for _,_,w in group))
            fan=1<<t
            bucket=[term for term in group if term[2]&fan]
            group=[term for term in group if not term[2]&fan]
            tour=choose_tour(bucket,ctrl,orig if not group else None,pivots,fan,S)
            last=fan
            for target,w in tour:
                lines.extend(S.emit_transition(S.parity_transition(ctrl,target,pivots),pivots))
                lines.extend(S.cnot(data[t],data[j]) for j in S.bit_positions(last^w))
                lines.append(f'CCX q{pivots[0]} q{pivots[1]} q{data[t]}')
                ctrl,last=target,w
            lines.extend(S.cnot(data[t],data[j]) for j in S.bit_positions(last^fan))
        lines.extend(S.emit_transition(S.parity_transition(ctrl,orig,pivots),pivots))
    return lines


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('repo','implementation','source','previous','out'):
        p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args()
    sys.path[:0]=[str(a.repo),str(a.implementation)]
    import schedule_angle as S
    from chemistry_affine_span_resynthesis import parse_line
    from chemistry_joint_product_resynthesis import DATA

    orig=S.schedule_products
    def best(terms,pool,data):
        return min(orig(terms,pool,data),graph_schedule(terms,pool,data,S),key=len)
    S.schedule_products=best
    a.out.mkdir(parents=True,exist_ok=False)
    receipts=[]
    for k in range(15):
        global BATCH
        BATCH=k
        name=f'angle_k_{k}.kmb'
        c=km.Circuit.from_file(a.source/name)
        prior=km.Circuit.from_file(a.previous/name)
        graph,checks=S.rewrite(c,parse_line,DATA)
        assert graph.num_qubits==c.num_qubits==prior.num_qubits
        assert graph.operation_statistics().num_toffoli_like==prior.operation_statistics().num_toffoli_like
        assert len(graph)<=len(prior), (k,len(graph),len(prior))
        out=a.out/name
        graph.to_file(out,format='kmb')
        assert str(km.Circuit.from_file(out))==str(graph)
        row=dict(batch=k,source_ops=len(c),baseline_ops=len(prior),new_ops=len(graph),
                 peak_q=graph.num_qubits,ccx=graph.operation_statistics().num_toffoli_like,
                 sha256=sha256(out.read_bytes()).hexdigest(),checked_blocks=checks)
        receipts.append(row)
        print(k,len(prior),len(graph),flush=True)
    shutil.copyfile(a.source/'submission.npz',a.out/'submission.npz')
    result=dict(batches=receipts,previous_total=sum(x['baseline_ops'] for x in receipts),
                new_total=sum(x['new_ops'] for x in receipts),
                toffoli_per_pass=sum(x['ccx'] for x in receipts),
                route_counts=Counter(v['selected'] for v in STATS),
                steiner_hubs=sum(x['hubs'] for x in STATS),route_cases=STATS)
    (a.out/'build_receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    print({k:v for k,v in result.items() if k not in ('batches','route_cases')},flush=True)

if __name__=='__main__':
    main()
