"""Independent GF(4096) algebraic certificate of packed Padé continuants.

This is a host-side proof witness / test oracle, not a coherent gate emitter.
Native generators, dependencies and per-chunk hashes are in the companion archive.
"""
import random
Q=4096
E=[1]
for _ in range(4094):
    a=2*E[-1]; E.append(a^(0x1053 if a>=Q else 0))
assert len(set(E))==4095
L=[0]*Q
for i,a in enumerate(E): L[a]=i
E*=2
def mul(a,b): return E[L[a]+L[b]] if a and b else 0
def inv(a): assert a; return E[4095-L[a]]
def trim(p):
    while p and p[-1]==0:p.pop()
    return p
def add(a,b):
    r=[0]*max(len(a),len(b))
    for p in (a,b):
        for i,x in enumerate(p):r[i]^=x
    return trim(r)
def prod(a,b):
    if not a or not b:return []
    r=[0]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):r[i+j]^=mul(x,y)
    return trim(r)
def ev(a,x):
    v=0
    for c in reversed(a):v=mul(v,x)^c
    return v
def locator(xs):
    p=[1]
    for x in xs:p=prod(p,[1,x])
    return p
def extract(s):
    q=len(s)//2; h=0; hist=[]
    while h<q:
        t=s[2*h:];v=next((i for i,a in enumerate(t) if a),len(t))
        if v==len(t):break
        assert v<q-h
        a=t[v]; u=[mul(x,inv(a)) for x in t[v:]]
        g=[1]+[0]*(len(u)-1)
        for k in range(1,len(g)):
            for j in range(1,k+1):g[k]^=mul(u[j],g[k-j])
        assert prod(u,g)[:len(u)]==[1] if len(u)==1 else (prod(u,g)[:len(u)]+[0]*len(u))[:len(u)]==[1]+[0]*(len(u)-1)
        s[2*h:]=[0]*v+[a]+g[1:]
        hist.append((v,a,g[:v+2]));h+=v+1
    return h,hist
def reconstruct(hist):
    N,D=[],[1]
    for v,a,H in reversed(hist):
        N,D=[0]*v+[mul(a,x) for x in D],add(prod(H,D),[0]*(v+2)+N if N else [])
    return trim(N),trim(D)
def moments(xs,es,n):
    s=[0]*n
    for x,e in zip(xs,es):
        p=x
        for j in range(n):s[j]^=mul(e,p);p=mul(p,x)
    return s
def high_valuation(xs):
    # barycentric weights give v = w-1, including all large degree gaps.
    out=[]
    for x in xs:
        t=x
        for y in xs:
            if x!=y:t=mul(t,x^y)
        out.append(inv(t))
    return out
def main():
    rng=random.Random(341340);num=0
    for w in range(36):
        for j in range(8):
            xs=rng.sample(range(1,4096),w)
            es=high_valuation(xs) if j%4==0 else [rng.randrange(1,Q) for x in xs]
            s=moments(xs,es,70);k,hist=extract(s[:]);N,D=reconstruct(hist)
            assert k==w and D==locator(xs)
            assert trim((prod(D,s)+[0]*70)[:70])==N
            deriv=[a if j%2==0 else 0 for j,a in enumerate(D[1:])]
            for x,e in zip(xs,es):
                z=inv(x);assert ev(D,z)==0 and ev(deriv,z)!=0
                assert mul(ev(N,z),inv(ev(deriv,z)))==e
            num+=1
    print("reference: %d rank, packed continuant, residue cases PASS"%num)
if __name__=="__main__":main()
