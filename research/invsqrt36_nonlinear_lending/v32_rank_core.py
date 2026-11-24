"""Multi-rank endpoint repair. Companion archive provides V31 dependencies.
Discovery on packed samples only. Every emitted candidate must independently
pass the full-domain BDD verifier. No additional measurement or quantum wire.
"""
from v31_joint import *

def dist(s,t,one):
    L=basis([one,*s]); T=basis([one,*t])
    return (len(basis([normal(T,x) for x in s])),
            len(basis([normal(L,x) for x in t])))

def isolate(s,T,order):
    y=list(s); g=[]; B={}; piv=[]
    for j in order:
        r,m=reduce(B,normal(T,y[j]))
        for k,p in enumerate(piv):
            if m>>k&1:
                y[j]^=y[p]; g.append(Op(33,(p,j)))
        assert normal(T,y[j])==r
        if r:
            B[r.bit_length()-1]=(r,1<<len(piv)); piv.append(j)
    return y,g,piv

def moves(y,t,one,R,sparse=False,limit=8):
    T=basis([one,*t]); d0=dist(y,t,one); n=len(y); out=[]; seen=set()
    for order in [list(range(n)),list(reversed(range(n)))]:
        z,pre,piv=isolate(y,T,order)
        ids=[j for j in range(n) if z[j] not in (0,one)]
        fs=[(z[j],(j,)) for j in ids]
        if sparse:
            fs += [(z[a]^z[b],(a,b)) for a,b in itertools.combinations(ids,2)
                   if a not in piv and b not in piv and z[a]^z[b] not in (0,one)]
        uniq={}
        for v,ix in fs: uniq.setdefault(v,(v,ix))
        fs=list(uniq.values()); targets={normal(T,z[j]):j for j in piv}
        W={(a,b):normal(T,z[a]&z[b]) for a,b in itertools.combinations(ids,2)} if sparse else None
        for k,(va,ia) in enumerate(fs):
            for vb,ib in fs[:k]:
                R['rank_product_probes']+=1
                h=va&vb
                r=xorv(W[min(a,b),max(a,b)] for a in ia for b in ib if a!=b) if sparse else normal(T,h)
                p=targets.get(r)
                if p is None or p in ia or p in ib: continue
                ua=next((i for i in ia if i not in ib),None)
                ub=next((i for i in ib if i not in ia),None)
                if ua is None or ub is None: continue
                zz=z[:]; zz[p]^=h; d=dist(zz,t,one)
                if d[0]>=d0[0] or d[1]>d0[1]: continue
                key=tuple(sorted(v[0] for v in basis([one,*zz]).values()))
                if key in seen: continue
                seen.add(key)
                cg=[Op(33,(i,ua)) for i in ia if i!=ua]+[Op(33,(i,ub)) for i in ib if i!=ub]
                g=pre+cg+[Op(49,(ua,ub,p))]+cg[::-1]
                out.append((d,len(g),zz,g)); R['rank_transitions']+=1
                if len(out)>=limit: return sorted(out,key=lambda x:x[:2])
    return sorted(out,key=lambda x:x[:2])

def repair_rank(s,t,one,R,maxpaid,sparse=False):
    start=dist(s,t,one); R['initial_rank_'+str(start)]+=1
    if max(start)>maxpaid or max(start)<2: return None
    frontier=[(s,[])]; seen=set()
    for step in range(maxpaid):
        nxt=[]
        for y,g in frontier:
            for d,_,z,h in moves(y,t,one,R,sparse):
                if max(d)>maxpaid-step-1: continue
                rep=fix(z,t,one)
                if rep is None and max(d)<=1 and maxpaid-step-1>=1:
                    rep=repair_one(z,t,one,R,sparse=False)
                if rep is not None:
                    ans=optimize(g+h+rep)
                    assert simulate(ans,s,{},one,[])[0]==t
                    R['multi_rank_fits']+=1
                    return ans
                key=tuple(sorted(v[0] for v in basis([one,*z]).values()))
                if key not in seen:
                    seen.add(key); nxt.append((z,g+h))
        frontier=sorted(nxt,key=lambda x:(max(dist(x[0],t,one)),len(x[1])))[:8]
        if not frontier: break
    return None
