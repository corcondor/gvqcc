"""Independent replay of the exact source and replacement gates on all 2^9 inputs."""
import json
from pathlib import Path
d = json.loads(Path(__file__).with_name("V6_ENDPOINT_RECEIPT.json").read_text())
old, new = d["old_gates"], d["new_gates"]
wires = sorted({q for g in old + new for q in g[1:]})
assert len(wires) == 9 and max(wires) == 35
def run(s, gs):
    for op, *q in gs:
        if op == 33:
            a,b = q
            s ^= ((s >> a) & 1) << b
        elif op == 49:
            a,b,t = q
            s ^= (((s >> a) & (s >> b)) & 1) << t
        elif op == 34:
            a,b = q
            k = ((s >> a) ^ (s >> b)) & 1
            s ^= (k << a) | (k << b)
        else:
            raise ValueError(op)
    return s
for i in range(1 << len(wires)):
    s = sum(((i >> j) & 1) << q for j,q in enumerate(wires))
    assert run(s, old) == run(s, new), i
assert (len(old),len(new)) == (30,11)
assert [sum(g[0] == 49 for g in gs) for gs in (old,new)] == [2,0]
print("PASS: 512 arbitrary assignments, 30 -> 11 gates, 2 -> 0 CCX")
