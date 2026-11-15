"""Exact operator identities and barrier-safe two-CCX meeting rewrite.
All CCX candidates are 3 distinct quantum wires and without classical controls.
"""
from collections import defaultdict
from dataclasses import dataclass
from typing import Sequence
from kmb_v2 import Gate

CCX=0x31;CX=0x21

@dataclass(frozen=True)
class Move:
    left:int
    right:int
    split:int
    rule:str
    saved:int

def commutes_ccx(a:Gate,b:Gate)->bool:
    """Conservative sufficient condition, never rely on sampled inputs."""
    if a.name!='CCX' or a.cond:return False
    x,y,z=a.q
    q=b.q
    if b.cond:return False
    if b.name=='X':return q[0] not in (x,y)
    if b.name=='CX':return q[1] not in (x,y) and z!=q[0]
    if b.name=='CCX':return q[2] not in (x,y) and z not in q[:2]
    if b.name in ('Z','Z_POW'):return z not in q
    if b.name in ('CZ','CCZ'):return z not in q
    if b.name in ('SWAP','CSWAP'):return set(a.q).isdisjoint(q)
    if b.name=='NEG':return True
    return False

def rewrite_rules(a:Gate,b:Gate)->list[tuple[str, list[Gate],int]]:
    if a.name!='CCX' or b.name!='CCX' or a.cond or b.cond:return []
    x,y,t=a.q;u,v,s=b.q
    if len(set(a.q))!=3 or len(set(b.q))!=3:return []
    if {x,y}=={u,v}:
        if t==s:return [('cancel',[],2)]
        if t not in (u,v) and s not in (x,y):
            return [('fanout',[Gate(CX,(t,s)),a,Gate(CX,(t,s))],1)]
    if t==s and len({x,y,u,v})==3 and t not in {x,y,u,v}:
        common=({x,y}&{u,v}).pop()
        other1=({x,y}-{common}).pop();other2=({u,v}-{common}).pop()
        if len({common,other1,other2,t})==4:
            return [('input-factor',[Gate(CX,(other1,other2)),b,Gate(CX,(other1,other2))],1)]
    return []

def candidate_moves(gates:Sequence[Gate],window:int=256,limit:int=100000)->list[Move]:
    """Discover rewrites involving 2 CCXs and an exact commute split."""
    history=defaultdict(list);candidates=[]
    for j,g in enumerate(gates):
        if g.name!='CCX' or g.cond:continue
        a,b,t=g.q
        signatures=[('both',tuple(sorted((a,b)))),('left',a,t),('left',b,t)]
        predecessors=set()
        for key in signatures:
            for i in reversed(history[key]):
                if j-i>window:break
                predecessors.add(i)
        for i in sorted(predecessors,reverse=True):
            f=gates[i]
            pairs=rewrite_rules(f,g)
            if not pairs:continue
            # Earliest meeting point where left is freely moved right; right can move left.
            # Evaluate prefix/suffix validity exactly for the current gate interval.
            intermediates=gates[i+1:j]
            prefix=[True]
            for between in intermediates:prefix.append(prefix[-1] and commutes_ccx(f,between))
            suffix=[False]*(len(intermediates)+1);suffix[-1]=True
            for m in range(len(intermediates)-1,-1,-1):suffix[m]=suffix[m+1] and commutes_ccx(g,intermediates[m])
            split=next((m for m in range(len(prefix)) if prefix[m] and suffix[m]),None)
            if split is None:continue
            for name,replacement,saving in pairs:
                candidates.append(Move(i,j,split,name,saving))
                if len(candidates)>=limit:return candidates
        for key in signatures:history[key].append(j)
        # no need pruning small windows, history list bounded by gate counts
    return candidates

def apply_move(gates:Sequence[Gate],move:Move)->list[Gate]:
    i,j,k=move.left,move.right,move.split
    a,b=gates[i],gates[j]
    rules={name:(replacement,saved) for name,replacement,saved in rewrite_rules(a,b)}
    if move.rule not in rules:raise ValueError('invalid rule')
    replacement,saved=rules[move.rule]
    # g_i commutes past intermediate[:k]; g_j commutes left past intermediate[k:]
    # Then replace the now-neighboring CCXs by a proven exact identity.
    return list(gates[:i])+list(gates[i+1:i+1+k])+replacement+list(gates[i+1+k:j])+list(gates[j+1:])
