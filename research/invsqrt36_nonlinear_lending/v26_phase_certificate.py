"""Independent V26 global phase deletion receipt checker.
Place beside affine_reset.py in the V26 companion archive; Python stdlib.
Usage: python v26_phase_certificate.py parent.kmb result.kmb receipt.json
"""
from affine_reset import *
from collections import defaultdict
from fractions import Fraction
from functools import lru_cache
PH = {0, 16, 32, 48}
def check(parent, output, receipt):
    K, N = NativeKMB.read(parent), NativeKMB.read(output)
    r = json.load(open(receipt))
    assert hashlib.sha256(Path(parent).read_bytes()).hexdigest() == r["parent_sha"]
    assert hashlib.sha256(Path(output).read_bytes()).hexdigest() == r["sha256"]
    groups = [x["indices"] for x in r["chosen"]]
    used = {i for c in groups for i in c}
    assert sum(map(len, groups)) == len(used)
    assert N.ops == [o for i,o in enumerate(K.ops) if i not in used]
    assert [(k,v) for k,v in K.sections if k not in range(1,10)] == [(k,v) for k,v in N.sections if k not in range(1,10)]
    ev = defaultdict(list)
    for j,c in enumerate(groups):
        assert all(K.ops[i].raw & 127 in PH for i in c)
        for i in c: ev[i].append(j)
    B = BDD(NLEGAL)
    inp = [B.leaf(mask(i,NLEGAL)) for i in range(22)] + [B.zero]*15
    M = Machine(B, inp)
    pending = {}
    E = Fraction(0); saved = Fraction(0)
    @lru_cache(None)
    def prob(v):
        return Fraction(v.value.bit_count(), NLEGAL) if v.var < 0 else (prob(v.low)+prob(v.high))/2
    for i,o in enumerate(K.ops):
        if (o.raw & 127) in (48,49,50):
            w = prob(active(M,o)); prob.cache_clear(); E += w
            if i in used: saved += w
        if i in ev:
            v = active(M,o)
            for q in o.wires: v = B.and_(v,M.s[q])
            for j in ev[i]:
                pending[j] = B.xor(pending.get(j,B.zero),v)
                if i == groups[j][-1]: assert pending.pop(j) is B.zero
        M.p=B.zero; M.rot=[]
        M.step(o, B.variable() if (o.raw & 127)==80 else None)
    assert not pending and M.s == inp and not M.stack and B.nvar == r["hmr"]
    assert E == Fraction(r["expected_before"]) and E-saved == Fraction(r["expected_after"])
    print("PASS", len(groups), len(used), NLEGAL, B.nvar, str(E-saved))
if __name__=="__main__": check(*sys.argv[1:])
