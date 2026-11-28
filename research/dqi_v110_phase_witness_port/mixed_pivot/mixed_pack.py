"""Lossless four-word mixed Schur pivot reference in GF(4096)."""
import collections, json, random
from pathlib import Path
import crt882 as F

def sc(p,x):return F.trim([F.m(u,x) for u in p])
def e(g,x):return tuple(F.evalp(p,x) for p in g)
def det(a,b):return F.m(a[0],b[1])^F.m(a[1],b[0])
def diff(p):return F.trim([p[i] if i%2 else 0 for i in range(1,len(p))])
def gcd(a,b):
    while b:a,b=b,F.div(a,b)[1]
    return a
def der_at(g,x):return tuple(F.evalp(diff(p),x) for p in g)
def bracket(g,v):
    return F.add(sc(g[0],v[1]),sc(g[1],v[0]))
def exact(p,t):
    q,r=F.div(p,[t,1]);assert not r;return q

def forward(g,t,s):
    g0,g1=e(g,t),e(g,s)
    delta=t^s
    assert delta and not det(g0,der_at(g,t))
    c=F.m(det(g0,g1),F.inv(delta))
    d=det(g1,der_at(g,s))
    ci=F.inv(c)
    rho=F.m(d,ci)
    wt,ws=exact(bracket(g,g0),t),exact(bracket(g,g1),s)
    u0=sc(F.add(sc(wt,rho),ws),ci);u1=sc(wt,ci)
    r=tuple(exact(exact(F.add(F.add(p,sc(u0,a)),sc(u1,b)),t),s)
            for p,a,b in zip(g,g0,g1,strict=True))
    tau=F.m(F.m(delta,ci),det(g1,e(r,s)))
    return r,(g0[0],g0[1],rho,tau),(d,c)

def inverse(r,packed,t,s):
    a,b,rho,tau=packed
    g0=(a,b)
    delta=t^s;d2=F.m(delta,delta)
    rs=e(r,s)
    g1=tuple(F.m(d2,u)^F.m(tau,v) for u,v in zip(rs,g0,strict=True))
    det_e=det(g0,g1)
    assert det_e
    mu=sc(bracket(r,g0),F.inv(det_e))
    t2=F.mul([t,1],[t,1]);s2=F.mul([s,1],[s,1]);ss=[s,1]
    # G = (X+s)^2 R + delta^2 mu g1 + delta rho (X+s) mu g0.
    return tuple(F.add(F.add(F.mul(s2,p),sc(mu,F.m(d2,v))),
                           sc(F.mul(ss,mu),F.m(F.m(delta,rho),u)))
                 for p,u,v in zip(r,g0,g1,strict=True))

def bez(g,x,y):
    a,b=e(g,x),e(g,y)
    return (det(a,der_at(g,x)) if x==y else F.m(det(a,b),F.inv(x^y)))

def check_schur(g,r,t,s,d,c,nodes):
    # Test a direct mixed pivot against the source Bezoutian, independently
    # of the normalized reconstruction identities.
    def ratio(x):return F.m(x^t,x^s)
    ci=F.inv(c)
    checked=0
    for x in nodes:
        for y in nodes:
            a,b=bez(g,x,t),bez(g,x,s)
            u,v=bez(g,t,y),bez(g,s,y)
            z=F.m(ci,u)
            zz=F.m(ci,v^F.m(d,z))
            assert bez(g,x,y)^F.m(a,zz)^F.m(b,z)==F.m(F.m(ratio(x),ratio(y)),bez(r,x,y))
            checked+=1
    return checked

def dot(a,b):
    z=0
    for x,y in zip(a,b,strict=True):z^=F.m(x,y)
    return z

def rhs_check(g,reconstructed,t,s,d,c,nodes,rng):
    ts=[t,s]+nodes
    K=[[bez(g,x,y) for y in ts] for x in ts]
    L=[[bez(reconstructed,x,y) for y in ts] for x in ts]
    # Leave the two pivot RHS words in their slots; compute reduced
    # right-hand side using the direct solve, then reverse using only
    # the compact-record reconstruction of the source.
    for _ in range(2):
        v=[rng.randrange(4096) for _ in ts]
        rhs=[dot(row,v) for row in K]
        j=F.inv(c)
        def solve(a,b):
            z=F.m(j,a)
            return [F.m(j,b^F.m(d,z)),z]
        cut=[y^dot(row[:2],solve(*rhs[:2])) for y,row in zip(rhs[2:],K[2:],strict=True)]
        restored=[y^dot(row[:2],solve(*rhs[:2])) for y,row in zip(cut,L[2:],strict=True)]
        assert restored==rhs[2:]
        head=solve(*[rhs[i]^dot(L[i][2:],v[2:]) for i in (0,1)])
        assert head+v[2:]==v

def legal_cases():
    rng=random.Random(286217)
    pool=F.ks
    hits=collections.Counter()
    eligible=attempts=entries=0
    for w in range(36):
        for _ in range(4):
            attempts+=1
            X=rng.sample(range(1,4096),w)
            D=[1]
            for a in X:D=F.mul(D,[a,1])
            if w%2==0:D=F.mul(D,[0,1])
            for c in rng.sample(pool,(35-w)//2):D=F.mul(D,[c,1,1])
            g=tuple(F.trim([F.gf_pow(a,2048,12,F.MOD) for a in D[k::2]]) for k in (0,1))
            assert len(gcd(*g))==1
            cand=[x for x in range(4096) if not bez(g,x,x)]
            cand2=[x for x in range(4096) if bez(g,x,x)]
            rng.shuffle(cand)
            for t in cand:
                s=next((x for x in cand2 if det(e(g,t),e(g,x))),None)
                if s is None:continue
                r,p,(d,c)=forward(g,t,s)
                q=inverse(r,p,t,s)
                assert q==g and d
                slots=rng.sample([x for x in range(12) if x not in (t,s)],3)
                entries+=check_schur(g,r,t,s,d,c,slots)
                rhs_check(g,q,t,s,d,c,slots,rng)
                hits[w]+=1;eligible+=1
                break
    return dict(padded_squarefree_locators=attempts,adaptive_mixed_found=eligible,checked_schur_entries=entries,
                rhs_roundtrips=2*eligible,hits_by_weight=dict(hits))

def family():
    old,new=collections.Counter(),set()
    for d in range(4096):
        g=(F.trim([1,d,1^d]),[0,0,0,1])
        r,p,k=forward(g,0,1)
        assert k==(d,1) and r==([1],[0,1])
        old[(e(g,0),e(g,1),tuple(map(tuple,r)))]+=1
        assert inverse(r,p,0,1)==g
        assert p==(1,0,d,1)
        new.add(p)
    assert len(old)==1 and len(new)==4096
    return {'naive_records':len(old),'four_word_records':len(new),'roundtrips':4096}

def random_cases():
    rng=random.Random(2862048)
    n=checks=0
    degs=collections.Counter()
    def rnd():return rng.randrange(4096)
    while n<1024:
        t,s=rng.sample(range(4096),2);dt=t^s;di=F.inv(dt);rho=rnd()
        x2,y2=F.mul([t,1],[t,1]),F.mul([s,1],[s,1])
        d2i=F.m(di,di)
        deg=2+n%16
        a,b=[rnd() for _ in range(deg-1)],[rnd() for _ in range(deg-1)]
        b[0]^=F.evalp(b,s)^d2i
        a[0]^=F.evalp(a,t)^d2i^F.m(rho,F.evalp(b,t))
        lam=F.add(F.mul(y2,a),sc(F.mul([s,1],b),F.m(dt,rho)))
        mu=F.mul(x2,b)
        E=((rnd(),rnd()),(rnd(),rnd()))
        if not det(*E):continue
        g=tuple(F.add(sc(lam,i),sc(mu,j)) for i,j in zip(*E,strict=True))
        if len(gcd(*g))!=1:continue
        r,p,(d,c)=forward(g,t,s)
        assert inverse(r,p,t,s)==g
        assert r==tuple(F.add(sc(a,i),sc(b,j)) for i,j in zip(*E,strict=True))
        assert p[-2]==rho and bool(d)==bool(rho)
        nodes=rng.sample([x for x in range(4096) if x not in (t,s)],3)
        checks+=check_schur(g,r,t,s,d,c,nodes)
        rhs_check(g,inverse(r,p,t,s),t,s,d,c,nodes,rng)
        n+=1;degs[max(map(len,g))-1]+=1
    return dict(coprime_roundtrips=n,checked_schur_entries=checks,rhs_roundtrips=2*n,degree_counts=dict(degs))

if __name__=='__main__':
    d=dict(collision=family(),random=random_cases(),synthetic_half_locator=legal_cases())
    Path('mixed_word_receipt.json').write_text(json.dumps(d,indent=2)+'\n')
    print(d)
