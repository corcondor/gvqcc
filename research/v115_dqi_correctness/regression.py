"""Degree-safe rational extraction, reference only; full polynomial pair assumed.
All 34 head slots are used, with explicit finite/infinity/terminal records.
"""
from field_reference import mul,div,prod,trim,add,evalp,divrem,LOG,EXP,NODES
from checked_decoder import syndromes,decode,decode_eea
import random,json
ORDER=[3169,3257]+[k for k in NODES if k not in [3169,3257]]
SLOTS=[k for k in ORDER for _ in range(2)]
def g(k):return [k,1,1]
def rem(p,k):return divrem(p,g(k))[1]
def exact(a,b):
    q,r=divrem(a,b)
    if r:raise ValueError('inexact quotient')
    return q
def inverse_quad(p,k):
    a,b=(p+[0,0])[:2]
    norm=mul(a,a)^mul(a,b)^mul(k,mul(b,b))
    if not norm:raise ValueError('zero chart inverse')
    inv=trim([div(a^b,norm),div(b,norm)])
    assert rem(prod(p,inv),k)==[1]
    return inv
def product(ps):
    p=[1]
    for q in ps:p=prod(p,q)
    return p
U=product(g(k) for k in SLOTS)
def physical(roots,values):
    d=product([x,1] for x in roots);n=[]
    for x,e in zip(roots,values):n=add(n,prod(exact(d,[x,1]),[mul(mul(e,x),evalp(U,x))]))
    return n,d
def degree(p):return len(p)-1
def pack(n,d,slots=SLOTS):
    n,d=trim(n),trim(d);remaining=list(slots);hist=[]
    assert d and degree(n)<=len(remaining) and degree(d)<=len(remaining)+1
    while remaining:
        m=len(remaining)
        if not n:
            assert len(d)==1 and d[0]
            hist.append(('STOP',remaining.pop(0),[]))
        else:
            j=next((j for j,k in enumerate(remaining) if rem(n,k)),None)
            if j is not None:
                k=remaining.pop(j);h=rem(prod(rem(d,k),inverse_quad(rem(n,k),k)),k)
                n,d=exact(add(d,prod(h,n)),g(k)),n
                hist.append(('FINITE',k,h))
            else:
                assert degree(n)==m
                q,r=divrem(d,n);assert degree(q)<=1
                n,d=r,n
                hist.append(('INFINITY',remaining.pop(0),q))
        assert d and degree(n)<=m-1 and degree(d)<=m
    return n,d,hist
def unpack(n,d,hist):
    for kind,k,h in reversed(hist):
        if kind=='FINITE':n,d=d,add(prod(g(k),n),prod(h,d))
        elif kind=='INFINITY':n,d=d,add(n,prod(h,d))
        elif kind=='STOP':assert not n and len(d)==1
        else:raise ValueError(kind)
    return n,d
def fixed_zero(n,d):
    for k in SLOTS:
        if not rem(n,k):n=exact(n,g(k))
        else:
            h=rem(prod(rem(d,k),inverse_quad(rem(n,k),k)),k)
            n,d=exact(add(d,prod(h,n)),g(k)),n
    return degree(n),degree(d)
def forced_one(w,seed):
    rng=random.Random(seed)
    while True:
        xs=rng.sample(range(1,4096),w);es=[rng.randrange(1,4096) for _ in range(w-2)]
        d=product([x,1] for x in xs);vv=[]
        for x in xs:
            r=rem(prod(exact(d,[x,1]),[mul(x,evalp(U,x))]),SLOTS[0]);vv.append((r+[0,0])[:2])
        a,b=vv[-2:];det=mul(a[0],b[1])^mul(a[1],b[0]);assert det
        u=v=0
        for e,(x,y) in zip(es,vv):u^=mul(e,x);v^=mul(e,y)
        es.extend([div(mul(u,b[1])^mul(v,b[0]),det),div(mul(a[0],v)^mul(a[1],u),det)])
        if all(es):return xs,es
def forced_all(seed):
    rng=random.Random(seed);xs=rng.sample(range(1,4096),35)
    target=product(g(k) for k in ORDER);d=product([x,1] for x in xs)
    es=[div(evalp(target,x),mul(mul(x,evalp(U,x)),evalp(exact(d,[x,1]),x))) for x in xs]
    assert all(es) and physical(xs,es)==(target,d)
    assert all(not rem(target,k) for k in ORDER)
    return xs,es
def regression():
    assert len(set(ORDER))==17
    assert all(evalp(g(k),x) for k in ORDER for x in range(4096))
    cases=[]
    for w in [29,32,33,34,35]:
        for seed in range(5):cases.append(('forced_one',*forced_one(w,seed)))
    for seed in range(20):cases.append(('forced_all',*forced_all(seed)))
    rng=random.Random(20261127)
    for w in range(36):
        for _ in range(10):cases.append(('stratified',rng.sample(range(1,4096),w),[rng.randrange(1,4096) for _ in range(w)]))
    stats={};bad_fixed=[];tails={};inf_cases=0;inf_steps=0
    for kind,xs,es in cases:
        n,d=physical(xs,es);p,q,hist=pack(n,d)
        assert unpack(p,q,hist)==(n,d)
        assert len(hist)==34 and degree(p)<=0 and degree(q)<=1
        errs=dict(zip((LOG[x] for x in xs),es));s=syndromes(errs)
        assert decode(s)==decode_eea(s)==errs
        old=fixed_zero(n,d)
        if old[0]>0 or old[1]>1:bad_fixed.append({'kind':kind,'w':len(xs),'tail':old})
        num=sum(t[0]=='INFINITY' for t in hist);inf_cases+=bool(num);inf_steps+=num
        if kind=='forced_all':assert hist[0][0]=='INFINITY'
        stats[kind]=stats.get(kind,0)+1
        key=str((degree(p),degree(q)));tails[key]=tails.get(key,0)+1
    assert len(bad_fixed)==25
    return {'classical_cases':len(cases),'breakdown':stats,'adaptive_exact':len(cases),'bm_and_eea_exact':len(cases),'all_tail_degree_valid':len(cases),'tail_distribution':tails,'fixed_scheme_tail_overflow':len(bad_fixed),'infinity_cases':inf_cases,'infinity_steps':inf_steps,'native_repair':False}
if __name__=='__main__':print(json.dumps(regression(),indent=2))
