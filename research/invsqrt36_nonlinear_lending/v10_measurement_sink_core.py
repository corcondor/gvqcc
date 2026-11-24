"""V10 measurement-sink candidate generation (native KickMix Op compatible).

This is the static proposal stage. Use the companion archive's full-domain
BDD replay before admitting any emitted KMB. No official scoring here.
"""
from collections import Counter

def frames(ops):
    s, out = [], []
    for i, o in enumerate(ops):
        out.append(tuple(s))
        if o.raw == 129:
            s.append(i)
        if o.raw == 1:
            s.pop()
    assert not s
    return out

def phase_for(op, m):
    cls = type(op)
    phase = cls({17:0, 33:16, 49:32}[op.raw & 127] | 128,
                op.wires[:-1], condition=m)
    if op.raw & 128:
        return [cls(129, (), condition=op.condition), phase, cls(1, ())]
    return [phase]

def screen(ops, cuts):
    fs = frames(ops)
    options, hist = [], Counter()
    scanned = 0
    for z, h in enumerate(ops):
        if h.raw != 80:
            continue
        t, m, frame = h.wires[0], h.measurement, fs[z]
        writes, paid, seen, hmr, nested = set(), 0, -1, 0, 0
        for a in range(z-1, -1, -1):
            if a+1 in cuts or fs[a][:len(frame)] != frame:
                break
            o, g = ops[a], ops[a].raw & 127
            scanned += 1
            if m in (o.measurement, o.condition):
                break
            if t in o.wires:
                if g not in (17, 33, 49) or o.wires[-1] != t or t in o.wires[:-1]:
                    break
                writes.add(a)
                paid += g == 49
                hist[g] += 1
            if g == 80:
                hmr += 1
            if o.raw == 129:
                nested += 1
            if fs[a] != frame or len(writes) == seen or not paid:
                continue
            seen = len(writes)
            new = [h]
            for k in range(a, z):
                new.extend(phase_for(ops[k], m) if k in writes else [ops[k]])
            options.append((a, z+1, new, paid, len(writes), hmr, nested))
    return options, dict(hist), scanned

# This is the new phase-only virtualization in source [26344,26426).
# It is valid ONLY at the pinned parent coordinates with independently
# proven q36=0 and independence of the removed HMR outcome. In the actual
# serialized span, all downstream uses of that outcome are overwritten
# before the enclosing block returns. The proof is NOT inferred from the
# static pattern alone.
def virtual_accumulator_gates(Op):
    return [Op(33,(2,18)), Op(17,(18,)), Op(48,(27,28,18)),
            Op(32,(27,18)), Op(32,(25,18)), Op(17,(18,)),
            Op(33,(2,18)), Op(64,(),measurement=483)]
