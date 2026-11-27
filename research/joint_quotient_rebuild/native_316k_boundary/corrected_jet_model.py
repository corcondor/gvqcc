"""Corrected exact model for the recovered first 16 heads of the original 316k tape.
Uses the historical direct_codec.py from GVQCC_316K_Native_Root_Diagnosis.zip.
No native replacement claim. The physical mapping must be independently certified.
"""
import direct_codec as D

ORDER = [3169,3169,3257,3257,3134,3134,3302,3302,
         3727,3727,3671,3671,3792,3792,3592,3592]
def add(a,b): return a[0]^b[0], a[1]^b[1]
def scale(q,a): return D.mul(q,a[0]), D.mul(q,a[1])
def prod(x,y,k):
    a,b=x; c,d=y; t=D.mul(b,d)
    return D.mul(a,c)^D.mul(k,t), D.mul(a,d)^D.mul(b,c)^t
def inv0(x,k):
    a,b=x
    n=D.mul(a,a)^D.mul(a,b)^D.mul(k,D.mul(b,b))
    return (D.div(a^b,n),D.div(b,n)) if n else (0,0)
def jet(u,v,k):
    i=inv0(u,k); t=i if u!=(0,0) else (1,0)
    return i,prod(v,prod(t,t,k),k)
def forward(u,v,h,k,q):
    a,b=jet(add(u,h),add(v,(h[1],0)),k)
    return scale(q,a),add(a,scale(q,b))
def reverse(u,v,h,k,q):
    qi=D.inv(q); a=scale(qi,u); b=scale(qi,add(v,a))
    a,b=jet(a,b,k)
    return add(a,h),add(b,(h[1],0))
def inverse_head(n,d,k):
    nr,dr=D.rem(n,k),D.rem(d,k)
    if not nr:
        q,r=D.divrem(n,D.g(k)); assert not r
        return (0,0),(q,d)
    a,b=(nr+[0,0])[:2]
    h=prod(tuple((dr+[0,0])[:2]),inv0((a,b),k),k)
    q,r=D.divrem(D.add(d,D.pmul(h,n)),D.g(k)); assert not r
    assert D.add(D.pmul(D.g(k),q),D.pmul(h,n))==d
    return h,(q,n)
def ev(p,k): return tuple((D.rem(p,k)+[0,0])[:2])
def deriv(p): return [p[i] if i%2 else 0 for i in range(1,len(p))]
def initial_jet(n,d,k):
    N,T=ev(n,k),ev(d,k); I=inv0(T,k)
    a=prod(N,I,k)
    b=prod(add(prod(ev(deriv(n),k),T,k),prod(N,ev(deriv(d),k),k)),prod(I,I,k),k)
    return jet(a,b,k)
def model(errors):
    n,d=D.rational(errors)
    bank={k:initial_jet(n,d,k) for k in D.NODES}
    heads=[];prev=None
    for k in ORDER:
        h,v=bank[k]
        if k==prev: h=inv0(v,k)
        heads+=list(h)
        for l in bank:
            if l!=k: bank[l]=forward(*bank[l],h,l,k^l)
        if k!=prev:bank[k]=(h,add(v,(h[1],0)))
        prev=k
    return heads,bank

def test(mixed_json):
    import random,json
    rng=random.Random(316240)
    for i in range(4096):
        k=rng.choice(D.NODES);q=rng.randrange(1,4096)
        u=(0,0) if i%4==0 else (rng.randrange(4096),rng.randrange(4096))
        v=(rng.randrange(4096),rng.randrange(4096))
        h=(rng.randrange(4096),rng.randrange(4096))
        assert reverse(*forward(u,v,h,k,q),h,k,q)==(u,v)
        assert jet(*jet(u,v,k),k)==(u,v)
    rng=random.Random(164839)
    es=[{x:rng.randrange(1,4096)for x in rng.sample(range(1,4096),35)}for _ in range(64)]
    es += [{int(x):v for x,v in e.items()}for e in json.load(open(mixed_json))]
    for e in es:
        n,d=D.rational(e);r=[]
        for k in ORDER:
            h,(n,d)=inverse_head(n,d,k);r+=h
        assert model(e)[0]==r
    for k in D.NODES:
        for v in range(4096):assert jet((0,0),(v,0),k)==((0,0),(v,0))
    print(dict(transport_cases=4096,head_cases=len(es),zero_fiber_cases=17*4096))
if __name__=="__main__":
    import sys
    test(sys.argv[1])
