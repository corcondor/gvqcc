"""Phase-safe Clifford simplifier; never crosses an HMR/reset or a condition."""
from dataclasses import dataclass
from kmb_v2 import Gate,Circuit
from rewrite import candidate_moves,apply_move,commutes_ccx

FREE={'X','CX'}

def commute_free(a:Gate,b:Gate)->bool:
    if a.cond or a.bit or a.name not in FREE:return False
    q=a.q
    if b.name in ('R','HMR','PUSH_CONDITION','POP_CONDITION','INFO_TAG'):return False
    if b.cond and b.name!='CZ_IF':return False
    if a.name=='X':
        x=q[0]
        if b.name=='X':return True
        if b.name=='CX':return x!=b.q[0]
        if b.name=='CCX':return x not in b.q[:2]
        if b.name in ('CZ','CZ_IF','CCZ','Z','Z_POW'):return x not in b.q
        return False
    # a is CX(x,y): commutation when both gates' reads remain invariant
    x,y=q
    if b.name=='X':return x!=b.q[0]
    if b.name=='CX':return y!=b.q[0] and b.q[1]!=x
    if b.name=='CCX':return y not in b.q[:2] and b.q[2]!=x
    if b.name in ('Z','Z_POW','CZ','CZ_IF','CCZ'):
        return y not in b.q
    return False

def simplify_free(gates:list[Gate],window=96,max_passes=2):
    """Bounded linear-pass cancellation under exact commutation conditions.

    Pairs are non-overlapping; removing earlier proved pairs cannot invalidate
    the commutation proof of a later pair. Never crosses R/HMR/classical state.
    """
    seq=list(gates);removed=0
    for _ in range(max_passes):
        keep=[True]*len(seq);latest={};changes=0
        for j,g in enumerate(seq):
            if g.name not in FREE or g.cond:continue
            key=(g.op,g.q)
            if key in latest:
                i=latest[key]
                if j-i<=window and all(commute_free(g,seq[k]) for k in range(i+1,j) if keep[k]):
                    keep[i]=False;keep[j]=False;changes+=2
                    latest.pop(key,None)
                    continue
            latest[key]=j
        if not changes:break
        seq=[g for g,k in zip(seq,keep) if k]
        removed+=changes
    return seq,removed

def optimize(circuits,window=300,ccx_window=4096):
    out=[];stats=[]
    for c in circuits:
        ops,free_deleted=simplify_free(c.ops,window=window)
        moves=candidate_moves(ops,window=ccx_window)
        saved=0
        if moves:
            best=max(moves,key=lambda m:m.saved)
            ops=apply_move(ops,best)
            saved=best.saved
        out.append(Circuit(c.magic,c.version,c.nqubits,c.nbits,c.registers,ops,c.tags))
        stats.append(dict(free_deleted=free_deleted,toffoli_saved=saved))
    return out,stats
