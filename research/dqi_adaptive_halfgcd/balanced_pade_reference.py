"""Standalone GF(4096) balanced projective Padé reference; classical, not KMB.
The kernel uses a complete block of v+2 reciprocal coefficients rather than
a constant term, and retires precisely 2*(v+1) words of precision.
"""
from random import Random
MOD=0x1053
EXP=[]
LOG=[-1]*4096
x=1
for i in range(4095):
    assert LOG[x]==-1
    LOG[x]=i
    EXP.append(x)
    x<<=1
    if x&4096: x^=MOD
assert x==1
EXP*=2
def mul(a,b): return EXP[LOG[a]+LOG[b]] if a and b else 0
def inv(a):
    assert a
    return EXP[4095-LOG[a]]
def trim(a):
    a=list(a)
    while a and a[-1]==0: a.pop()
    return a
def add(a,b):
    c=[0]*max(len(a),len(b))
    for i,x in enumerate(a): c[i]^=x
    for i,x in enumerate(b): c[i]^=x
    return trim(c)
def pmul(a,b):
    if not a or not b: return []
    c=[0]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b): c[i+j]^=mul(x,y)
    return trim(c)
def reciprocal_unit(a):
    assert a and a[0]==1
    b=[1]
    for i in range(1,len(a)):
        z=0
        for j in range(1,i+1): z^=mul(a[j],b[i-j])
        b.append(z)
    return b
def extract(s):
    s=list(s)
    assert len(s)%2==0
    q=len(s)//2
    history=[]
    while q and any(s):
        assert len(s)==2*q
        v=next(i for i,a in enumerate(s) if a)
        assert v<q
        a=s[v]
        ai=inv(a)
        u=[mul(ai,z) for z in s[v:]]
        g=reciprocal_unit(u)
        H=g[:v+2]
        assert H[0]==1
        history.append((v,a,H))
        s=g[v+2:]
        q-=v+1
        assert len(s)==2*q
    N,D=[],[1]
    for v,a,H in reversed(history):
        N,D=[0]*v+[mul(a,z) for z in D],add(pmul(H,D),[0]*(v+2)+N if N else [])
    return trim(N),trim(D),history
def moments(xs,amps,n=70):
    s=[0]*n
    for x,e in zip(xs,amps):
        p=x
        for i in range(n):
            s[i]^=mul(e,p)
            p=mul(p,x)
    return s
def selftest():
    rng=Random(303)
    count=0
    for w in range(36):
        for _ in range(4):
            xs=rng.sample(range(1,4096),w)
            s=moments(xs,[rng.randrange(1,4096) for _ in xs])
            N,D,h=extract(s)
            assert len(D)==w+1 and D[0]==1
            assert len(N)<len(D)
            assert trim(pmul(D,s)[:70])==N
            assert sum(2*(v+1) for v,_,_ in h)==2*w
            count+=1
    print("synthetic rational reconstruction cases:",count)
if __name__=="__main__": selftest()
