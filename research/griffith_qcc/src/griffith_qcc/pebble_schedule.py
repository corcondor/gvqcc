"""Small exact reversible-pebble planner for ancilla-limited AND DAGs.

Clean ancilla only; input bits are negative refs (-1 is input 0).
Output taps XOR one computed node into one independent target each.
No HMR, dirty ancilla, phase operations, or opaque mutation is allowed.
Dijkstra search minimizes exact CCX count; suitable for small DAG cuts.
This is independent research code inspired by ETH Reqomp (MIT):
https://github.com/eth-sri/Reqomp and Meuli et al. arXiv:1904.02121.
"""
from dataclasses import dataclass
import heapq


@dataclass(frozen=True)
class Plan:
    n_inputs: int
    clean_budget: int
    nodes: tuple
    outputs: tuple
    steps: tuple
    gates: tuple
    ccx: int
    cx: int
    max_live: int


def plan_and_dag(n_inputs, nodes, outputs, clean_budget):
    """Emit unitary CX/CCX XOR oracle for a Boolean AND DAG, all ancillas clean.

    nodes[i]=(src,src) where src<0 means input -src-1 and src>=0
    means an earlier AND node. Taps identify which nodes are XORed into
    independent target bits, possibly initially dirty. Work must start 0.
    """
    nodes=tuple(tuple(pair) for pair in nodes)
    outputs=tuple(outputs)
    n,m=len(nodes),len(outputs)
    assert n_inputs>=1 and clean_budget>=1
    assert all(0<=j<n for j in outputs)
    for i,(a,b) in enumerate(nodes):
        assert a!=b
        assert all((0<=p<i) if p>=0 else (0<=-p-1<n_inputs)
                   for p in (a,b))
    start=(0,0)
    goal=(0,(1<<m)-1)
    dist={start:(0,0)}
    previous={}
    heap=[(0,0,0,start)]
    serial=0
    while heap:
        t,nop,_,state=heapq.heappop(heap)
        if dist[state]!=(t,nop):
            continue
        if state==goal:
            break
        live,done=state
        def present(src):
            return src<0 or bool(live & (1<<src))
        transitions=[]
        for j,(a,b) in enumerate(nodes):
            if not (present(a) and present(b)):
                continue
            bit=1<<j
            if live&bit:
                transitions.append(((live^bit,done),"uncompute",j,1))
            elif live.bit_count()<clean_budget:
                transitions.append(((live|bit,done),"compute",j,1))
        for o,node in enumerate(outputs):
            bit=1<<o
            if live&(1<<node) and not done&bit:
                transitions.append(((live,done|bit),"output",o,0))
        for nxt,action,index,extra_t in transitions:
            score=(t+extra_t,nop+1)
            if score<dist.get(nxt,(10**9,10**9)):
                dist[nxt]=score
                previous[nxt]=(state,action,index)
                serial+=1
                heapq.heappush(heap,(*score,serial,nxt))
    else:
        raise ValueError("no valid reversible schedule under this clean budget")
    steps=[]
    cur=goal
    while cur!=start:
        old,action,i=previous[cur]
        steps.append((action,i))
        cur=old
    steps.reverse()
    free=list(range(n_inputs,n_inputs+clean_budget))
    held={}
    gates=[]
    max_live=0
    def q(src):
        return -src-1 if src<0 else held[src]
    for action,i in steps:
        if action=="output":
            gates.append(("CX",held[outputs[i]],n_inputs+clean_budget+i))
        elif action=="compute":
            a,b=nodes[i]
            target=free.pop(0)
            gates.append(("CCX",q(a),q(b),target))
            held[i]=target
            max_live=max(max_live,len(held))
        else:
            a,b=nodes[i]
            target=held[i]
            gates.append(("CCX",q(a),q(b),target))
            del held[i]
            free.append(target)
            free.sort()
    assert not held
    ccx=sum(g[0]=="CCX" for g in gates)
    assert ccx==dist[goal][0]
    return Plan(n_inputs,clean_budget,nodes,outputs,tuple(steps),
                tuple(gates),ccx,m,max_live)
