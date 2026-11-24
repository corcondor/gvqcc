"""Virtual physical-wire frame for native GVQCC chart bodies.
Standalone pass. Caller must provide closed, scope-balanced chart boundaries
and verify native semantics against the original circuit. No added qubit.
The full BDD and rankhub integration are included in the V8 research archive.
"""
from dataclasses import replace

def perm_frame(ops, width=37):
    p = list(range(width))
    depth, skipped = 0, 0
    out = []
    for o in ops:
        if o.raw == 129: depth += 1
        if o.raw == 1: depth -= 1
        assert depth >= 0
        if o.raw == 34 and depth == 0:
            a,b = o.wires
            p[a],p[b] = p[b],p[a]
            skipped += 1
            continue
        out.append(replace(o, wires=tuple(p[q] for q in o.wires)))
    assert depth == 0
    tail = []
    for i in range(width):
        if p[i] != i:
            j = p.index(i)
            tail.append(type(ops[0])(34,(p[i],i)))
            p[i],p[j] = p[j],p[i]
    assert p == list(range(width))
    return out+tail, skipped, len(tail)

def dependency_depth(ops,width=37):
    """Scope-fenced operand dependency depth, not hardware time."""
    t=[0]*width; c={}; fence=0
    for o in ops:
        if o.raw in (129,1):
            fence=max([fence]+t+list(c.values()))+1
            continue
        w=o.wires
        cl=[c.get(o.condition,0)] if o.condition is not None else []
        if o.measurement is not None: cl.append(c.get(o.measurement,0))
        v=max([fence]+[t[q] for q in w]+cl)+1
        if not w and o.measurement is None: fence=v
        for q in w: t[q]=v
        if o.measurement is not None: c[o.measurement]=v
    return max([fence]+t+list(c.values()))
