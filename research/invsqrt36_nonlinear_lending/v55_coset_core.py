"""Finite signed affine-coset contraction (same algorithm as V55 coset_plan.py).
No quantum compiler dependencies; full native emitter and verifier in companion ZIP.
"""
from collections import defaultdict

def contract(co, beam=8):
    groups=defaultdict(dict)
    for s,c in co.items():
        if c: groups[abs(c)][s]=1 if c>0 else -1
    out=[]
    for a,z in groups.items():
        while z:
            if len(z)==1:
                s,sgn=z.popitem();out.append((s,[],[],sgn*a));break
            keys=sorted(z);best=None
            for s in keys[:min(len(keys),beam)]:
                for t in keys[:min(len(keys),beam)]:
                    if t==s: continue
                    Q={s:z[s],t:z[t]};V=[s^t];H=[z[s]*z[t]]
                    while True:
                        opts=[]
                        for u in keys:
                            if u in Q: continue
                            d=s^u;sgn=z[u]*z[s]
                            if all(z.get(x^d,0)==v*sgn for x,v in Q.items()):
                                opts.append((d.bit_count(),d,sgn))
                        if not opts: break
                        _,d,h=min(opts);Q.update({x^d:v*h for x,v in list(Q.items())});V.append(d);H.append(h)
                    key=(len(Q),-sum(v.bit_count() for v in V),-s.bit_count())
                    if best is None or key>best[0]:best=(key,s,V,H,Q)
                    if len(Q)==len(z):break
                if best and best[0][0]==len(z):break
            assert best
            _,s,V,H,Q=best
            out.append((s,V,H,z[s]*a*len(Q)))
            for x in Q:del z[x]
    return out

def expand(groups):
    out=defaultdict(int)
    for s,V,H,a in groups:
        assert a%(1<<len(V))==0
        q={s:a//(1<<len(V))}
        for d,h in zip(V,H):
            assert not set(q)&{x^d for x in q}
            q.update({x^d:c*h for x,c in list(q.items())})
        for x,c in q.items():out[x]+=c
    return {s:c for s,c in out.items() if c}

if __name__=="__main__":
    import random
    rng=random.Random(55)
    for _ in range(512):
        co={i:rng.randrange(-3,4) for i in range(64)}
        assert expand(contract(co))=={i:v for i,v in co.items() if v}
    print("signed coset exact expansion regression PASS")
