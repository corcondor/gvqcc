"""Joint schedule for the #253 invariant rank guard.
Uses the original #247 physical tape, #253 wrapper, and #237 GF12 rank-42
multiplication. No externally selected input branches. All scheduling is static.
"""
from functools import lru_cache
from collections import defaultdict
import crt882 as C
import joint_phase as J
import invariant247 as Base

@lru_cache(None)
def one_block(lo,hi,d):
    singles=[]
    groups=defaultdict(list)
    for i in range(hi,lo-1,-1):
        for j in range(1,i//d+1):
            t=i-d*j
            if not t or max(t,j)>=lo:singles.append((i,j,t))
            else:groups[j].append((i,t))
    return singles,groups

@lru_cache(None)
def optimal(n,d):
    # Minimum number of masked words among all contiguous descending partitions.
    dp={d-1:(0,())}
    for hi in range(d,n):
        vals=[]
        for lo in range(d,hi+1):
            s,g=one_block(lo,hi,d)
            cost,blocks=dp[lo-1]
            vals.append((cost+sum(t!=0 for i,j,t in s)+len(g),((lo,hi),)+blocks))
        dp[hi]=min(vals)
    return dp[n-1][1] if n>d else ()

def unit_power(self,a,active,tmp,d):
    b=self.b
    frame=tuple(C.gf_pow(1<<i,d,12,C.MOD) for i in range(12))
    def copy(j):
        J.frame(b,a[j],frame)
        for u,v in zip(a[j],tmp):b.ccx(active,u,v)
        J.frame(b,a[j],frame,True)
    def clear(j):
        J.frame(b,a[j],frame)
        for u,v in zip(a[j],tmp):b.del_and(active,u,v)
        J.frame(b,a[j],frame,True)
    for lo,hi in optimal(len(a),d):
        singles,groups=one_block(lo,hi,d)
        # All reads inside the current block must happen before their source
        # index is written. Keep descending target order for these terms.
        for i,j,t in singles:
            if t==0:
                J.frame(b,a[j],frame)
                for u,v in zip(a[j],a[i]):b.ccx(active,u,v)
                J.frame(b,a[j],frame,True)
            else:
                copy(j);self.mul(a[t],tmp,a[i]);clear(j)
        # Every source index is strictly below lo, hence unchanged. A single
        # active*Frob(a[j]) word is used for all targets in its group.
        for j,items in groups.items():
            copy(j)
            for i,t in items:self.mul(a[t],tmp,a[i])
            clear(j)

def reciprocal(self,p,active):
    b=self.b;a=self.w[p:self.n]
    f=self.alloc(12);g=self.alloc(12)
    b.x(f[0]);b.cx(active,f[0])
    for u,v in zip(a[0],f):b.ccx(active,u,v)
    self.invxor(f,g);tmp=self.alloc(12)
    for x in a[1:]:self.scale(x,g,f,tmp)
    for d in (2,4,16):
        if d<len(a):unit_power(self,a,active,tmp,d)
    for x in a[1:]:self.scale(x,g,f,tmp)
    self.free(tmp)
    for u,v,z in zip(f,g,a[0]):b.cx(u,z);b.cx(v,z)
    for u,v in zip(f,g):b.swap(u,v)
    self.invxor(f,g);self.free(g)
    for u,v in zip(a[0],f):b.ccx(active,u,v)
    b.cx(active,f[0]);b.x(f[0]);self.free(f)

def verify_plan():
    import random
    rng=random.Random(253254)
    def evalold(a,d):
        a=list(a)
        for i in range(len(a)-1,d-1,-1):
            for j in range(1,i//d+1):
                t=i-d*j
                a[i]^=C.m(a[t],C.gf_pow(a[j],d,12,C.MOD))
        return a
    def evalnew(a,d):
        a=list(a)
        for lo,hi in optimal(len(a),d):
            s,g=one_block(lo,hi,d)
            for i,j,t in s:a[i]^=C.m(a[t],C.gf_pow(a[j],d,12,C.MOD))
            for j,items in g.items():
                v=C.gf_pow(a[j],d,12,C.MOD)
                for i,t in items:a[i]^=C.m(a[t],v)
        return a
    k=0;old=new=0
    for n in range(20,53):
        for d in (2,4,16):
            for _ in range(16):
                a=[1]+[rng.randrange(4096) for _ in range(n-1)]
                assert evalold(a,d)==evalnew(a,d)
                k+=1
            old+=sum(max(0,i//d-int(i%d==0)) for i in range(d,n))
            for lo,hi in optimal(n,d):
                s,g=one_block(lo,hi,d)
                new+=sum(t!=0 for i,j,t in s)+len(g)
    print('schedule_reference_cases',k,'old_mask_words',old,'new_mask_words',new,'full_expected_paid_reduction',48*(old-new),flush=True)
    return old,new
if __name__=='__main__':
    verify_plan()
    Base.Guard.reciprocal=reciprocal
    Base.main()
