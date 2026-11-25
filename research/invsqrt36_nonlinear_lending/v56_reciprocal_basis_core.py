"""V56 finite GF(2) quotient batch planner used by the conditional basis emitter.
Native compiler, phase checker and data are in the reproducibility ZIP.
"""
import random
from collections import defaultdict

def pivot_basis(B):
    tab={}
    for j,v in enumerate(B):
        c=1<<j
        while v:
            p=v.bit_length()-1
            if p not in tab:tab[p]=(v,c);break
            a,b=tab[p];v^=a;c^=b
        assert v,'dependent basis'
    return tab

def reduce(v,tab):
    c=0;r=0
    while v:
        p=v.bit_length()-1
        if p in tab:a,b=tab[p];v^=a;c^=b
        else:r^=1<<p;v^=1<<p
    return r,c

def batches(keys,cap,seed,keep):
    rng=random.Random(seed);rem=set(v for v,h in keys);B=[];out=[];paid=0
    while rem:
        old=B[:];B=[]
        if keep and old:
            for _ in range(min(keep,len(old),cap)):
                T=pivot_basis(B);cand=[v for v in old if reduce(v,T)[0]]
                if not cand:break
                def merit(v):
                    q=reduce(v,T)[0];return sum(reduce(a,T)[0]==q for a in rem)
                B.append(max(cand,key=lambda v:(merit(v),-v.bit_count(),-v)))
        while len(B)<cap:
            T=pivot_basis(B);C=defaultdict(list)
            for v in sorted(rem):
                r,_=reduce(v,T)
                if r:C[r].append(v)
            if not C:break
            q=max(C,key=lambda r:(len(C[r]),-min(v.bit_count()for v in C[r]),rng.random()if seed else -r))
            cand=C[q]+[q];v=min(cand,key=lambda a:(a not in old,a.bit_count(),a));B.append(v)
        T=pivot_basis(B);sel=sorted(v for v in rem if reduce(v,T)[0]==0)
        if not sel:
            B=[min(rem)];T=pivot_basis(B);sel=[v for v in sorted(rem)if reduce(v,T)[0]==0]
        rem.difference_update(sel);paid+=sum(v not in old for v in B)
        out.append((B[:],[(v,h,reduce(v,T)[1])for v,h in keys if v in sel]))
    return paid,out

def verify_batch_plan(keys, cap, plan):
    done=set();old=set();cost=0
    for B,entries in plan:
        assert len(B)<=cap
        pivot_basis(B)
        cost+=len(set(B)-old);old=set(B)
        for v,h,c in entries:
            w=0
            for i,b in enumerate(B):
                if c>>i&1:w^=b
            assert w==v and (v,h) not in done
            done.add((v,h))
    assert done==set(keys)
    return cost

if __name__=='__main__':
    keys=[(i,1) for i in range(1,32)]
    paid,plan=batches(keys,3,0,1)
    assert paid==verify_batch_plan(keys,3,plan)
    print('GF(2) quotient batch reconstruction PASS',paid)
