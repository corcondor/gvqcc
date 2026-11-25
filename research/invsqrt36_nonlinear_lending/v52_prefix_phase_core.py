"""Exact integer prefix/phase expansion core (V52, not a full emitter).
Input is the V51 quantized80 plan; full native emitter/verifier in companion ZIP.
"""
from collections import defaultdict
W = 22
MOD = 1 << 64

def expand(plan):
    G = defaultdict(lambda: defaultdict(int))
    C = 0
    scale = MOD // int(plan["scale"])
    assert scale * plan["scale"] == MOD
    for row in plan["blocks"]:
        k = int(row["k"]); start = int(row["start"]); d = W-k; p = start >> k
        for s,c in zip(row["indices"],row["coeff"]):
            s=int(s); c=int(c)*scale
            if c % MOD == 0:
                continue
            if s == 0:
                assert c % (1 << d) == 0
                C += c >> d
                for j in range(1,d+1):
                    bit=W-j; pref=p >> (d-j+1); sign=1-2*((start>>bit)&1)
                    G[(j-1,pref)][1<<bit] += sign*(c >> (d-j+1))
            elif d <= 20:
                G[(d,p)][s] += c
            else:
                assert d == 21 and c % 2 == 0
                G[(20,p>>1)][s] += c//2
                G[(20,p>>1)][s^(1<<k)] += (1-2*(p&1))*c//2
    return C%MOD, {g:{s:a%MOD for s,a in vals.items() if a%MOD} for g,vals in G.items()}
