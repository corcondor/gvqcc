"""Core extracted from V8 global_frame; Op is a dataclass with raw,wires,measurement,condition.
Use full reproduction archive for donor transfer, chart boundaries and all-domain replay."""
from dataclasses import replace
from collections import defaultdict

def permute_epoch(ops, width, Op):
    p=list(range(width)); stack=[]; out=[]
    def flush(target):
        for q in range(width):
            if p[q]!=target[q]:
                r=p.index(target[q])
                out.append(Op(34,(p[q],p[r])))
                p[q],p[r]=p[r],p[q]
        assert p==target
    for o in ops:
        if o.raw==129: stack.append(p.copy()); out.append(o)
        elif o.raw==1: flush(stack.pop()); out.append(o)
        elif o.raw==34:
            a,b=o.wires; p[a],p[b]=p[b],p[a]
        else: out.append(replace(o,wires=tuple(p[q] for q in o.wires)))
    assert not stack
    flush(list(range(width)))
    return out

XORS={17,33,49}; PHASE={0,16,32,48}; CANCEL=XORS|PHASE|{34,50}
def rw(o):
    g=o.raw&127; w=o.wires
    if g in XORS: return set(w[:-1]),set(w[-1:]),True
    if g in (34,50): return set(w),set(w[-2:]),False
    if g==80: return set(w),set(w),False
    return set(w),set(),False

def commute(a,b):
    ra,wa,xa=rw(a); rb,wb,xb=rw(b)
    return not(wa&rb or wb&ra or (wa&wb and not(xa and xb)))

def canonical(o):
    g=o.raw&127; w=o.wires
    if g in PHASE or g==34: w=tuple(sorted(w))
    if g==49: w=tuple(sorted(w[:2]))+w[2:]
    if g==50: w=w[:1]+tuple(sorted(w[1:]))
    return g,w

def causal(ops):
    ver=defaultdict(int);scope=[];removed=set();pairs=[];seen=defaultdict(list)
    for i,o in enumerate(ops):
        g=o.raw&127
        if o.raw==129:scope.append((o.condition,ver[o.condition]));continue
        if o.raw==1:scope.pop();continue
        key=(canonical(o),tuple(sorted(set(scope+([(o.condition,ver[o.condition])]if o.raw&128 else []))))) if g in CANCEL else None
        if g in(64,65,66,80):ver[o.measurement]+=1
        if key is None:continue
        L=seen[key]
        while L and L[-1] in removed:L.pop()
        if L:
            j=L[-1]
            if all(k in removed or ops[k].raw in(1,129) or commute(o,ops[k]) for k in range(j+1,i)):
                removed.update((j,i));pairs.append((j,i,g));L.pop();continue
        L.append(i)
    assert not scope
    return [o for i,o in enumerate(ops) if i not in removed],pairs
