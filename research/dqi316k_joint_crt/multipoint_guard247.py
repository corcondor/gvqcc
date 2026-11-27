"""Additive-subspace evaluation points (#251) for stable truncated
Frobenius convolution inside the exact #253 syndrome guard. In-place
source and target frames use no additional field words.
"""
from functools import lru_cache
import random
import crt882 as C
import joint_phase as J
import grouped_guard247 as G
import fft_plan247 as P
import invariant247 as Base

BETA=(1,70,1971,2939,2,140,3942,1701,4,280,3743,3402)
@lru_cache(None)
def points(n):
    a=tuple(C.xor_word(v for k,v in enumerate(BETA) if j>>k&1) for j in range(n))
    assert len(set(a))==n
    return a
@lru_cache(None)
def coeffs(n):
    xs=points(n);result=[]
    for x in xs:
        f=[1];den=1
        for y in xs:
            if x!=y:
                f=C.mul(f,[y,1]);den=C.m(den,x^y)
        col=tuple(C.m(v,C.inv(den)) for v in f)
        assert len(col)==n
        result.append(col)
    return tuple(result)
@lru_cache(None)
def powers(x,n):
    v=[1]
    for _ in range(n-1):v.append(C.m(v[-1],x))
    return tuple(v)
@lru_cache(None)
def cols(c,d=1):
    return tuple(C.gf_pow(C.m(c,1<<i),d,12,C.MOD) for i in range(12))
def addlin(b,x,y,c):
    if c==0:return
    assert x!=y
    if c==1:
        for u,v in zip(x,y):b.cx(u,v)
    else:
        for i,k in enumerate(cols(c)):
            for j in C.bits(k):b.cx(x[i],y[j])
def frame(b,x,c,rev=False,d=1):
    if c==1 and d==1:return
    J.frame(b,x,cols(c,d),rev)
def form(b,a,u,v):
    """Make U in p and V in q, or V=cU if dependent. Return inverse tape."""
    u={k:z for k,z in u.items() if z};v={k:z for k,z in v.items() if z}
    if not u or not v:return None
    p=min(u);ops=[(0,p,u[p])]
    for k,z in u.items():
        if k!=p:ops.append((1,k,p,z))
    c=C.m(v.get(p,0),C.inv(u[p]))
    v1=dict(v);v1[p]=c
    for k,z in u.items():
        if k!=p:v1[k]=v1.get(k,0)^C.m(c,z)
    v1={k:z for k,z in v1.items() if z}
    q=next((k for k in sorted(v1) if k!=p),None)
    if q is None:
        if not c:return None
        q=p;f=c
    else:
        ops.append((0,q,v1[q]))
        for k,z in v1.items():
            if k!=q:ops.append((1,k,q,z))
        f=1
    for g,*z in ops:
        if g==0:frame(b,a[z[0]],z[1])
        else:addlin(b,a[z[0]],a[z[1]],z[2])
    return p,q,f,ops
def unform(b,a,ops):
    for g,*z in reversed(ops):
        if g==0:frame(b,a[z[0]],z[1],True)
        else:addlin(b,a[z[0]],a[z[1]],z[2])
def masked_copy(b,a,flag,tmp,j,f,d,clear=False):
    frame(b,a[j],f,d=d)
    for x,y in zip(a[j],tmp):
        if clear:b.del_and(flag,x,y)
        else:b.ccx(flag,x,y)
    frame(b,a[j],f,True,d=d)
def add_product(self,a,active,tmp,u,v,w,d):
    b=self.b
    w={k:z for k,z in w.items() if z}
    if not w:return
    f=form(b,a,u,v)
    if f is None:return
    p,q,c,ops=f
    t=min(w);assert p not in w and q not in w
    # A linear output shear transports a single product to every target.
    frame(b,a[t],C.inv(w[t]))
    for k,z in w.items():
        if k!=t:addlin(b,a[t],a[k],z)
    masked_copy(b,a,active,tmp,q,c,d)
    self.mul(a[p],tmp,a[t])
    masked_copy(b,a,active,tmp,q,c,d,True)
    for k,z in reversed(list(w.items())):
        if k!=t:addlin(b,a[t],a[k],z)
    frame(b,a[t],w[t])
    unform(b,a,ops)

@lru_cache(None)
def eval_forms(d,r,h0,h1,j0,j1,u0,u1):
    n=j1-j0+u1-u0+1
    result=[]
    for x,col in zip(points(n),coeffs(n)):
        u={d*k+r:v for k,v in zip(range(u0,u1+1),powers(x,u1-u0+1))}
        v={k:C.gf_pow(z,4096//d,12,C.MOD) for k,z in zip(range(j0,j1+1),powers(x,j1-j0+1))}
        w={d*h+r:col[h-u0-j0] for h in range(h0,h1+1) if 0<=h-u0-j0<n}
        result.append((u,v,w))
    return tuple(result)

def unit_power(self,a,active,tmp,d):
    b=self.b
    def copy(j):masked_copy(b,a,active,tmp,j,1,d)
    def clear(j):masked_copy(b,a,active,tmp,j,1,d,True)
    def singles(s):
        for i,j,t in s:
            if t==0:
                frame(b,a[j],1,d=d)
                for x,y in zip(a[j],a[i]):b.ccx(active,x,y)
                frame(b,a[j],1,True,d=d)
            else:
                copy(j);self.mul(a[t],tmp,a[i]);clear(j)
    for lo,hi in P.plan(len(a),d)[1]:
        s,g=G.one_block(lo,hi,d)
        singles(s)
        _,rr=P.block_cost(lo,hi,d)
        if rr is None:
            for j,items in g.items():
                copy(j)
                for i,t in items:self.mul(a[t],tmp,a[i])
                clear(j)
        else:
            for ev,r,h0,h1,j0,j1,u0,u1 in rr:
                if ev:
                    for u,v,w in eval_forms(d,r,h0,h1,j0,j1,u0,u1):
                        add_product(self,a,active,tmp,u,v,w,d)
                else:
                    for j in range(j0,j1+1):
                        copy(j)
                        for h in range(max(h0,u0+j),min(h1,u1+j)+1):
                            self.mul(a[d*(h-j)+r],tmp,a[d*h+r])
                        clear(j)

def reference_check():
    rng=random.Random(251253)
    def dot(a,u):
        return C.xor_word(C.m(a[k],v) for k,v in u.items())
    for n in range(20,53):
        for d in (2,4,16):
            for _ in range(4):
                a=[1]+[rng.randrange(4096) for k in range(n-1)];z=a[:]
                for i in range(n-1,d-1,-1):
                    for j in range(1,i//d+1):
                        z[i]^=C.m(z[i-d*j],C.gf_pow(z[j],d,12,C.MOD))
                for lo,hi in P.plan(n,d)[1]:
                    s,g=G.one_block(lo,hi,d)
                    for i,j,t in s:a[i]^=C.m(a[t],C.gf_pow(a[j],d,12,C.MOD))
                    _,rr=P.block_cost(lo,hi,d)
                    if rr is None:
                        for j,items in g.items():
                            v=C.gf_pow(a[j],d,12,C.MOD)
                            for i,t in items:a[i]^=C.m(a[t],v)
                    else:
                        for ev,r,h0,h1,j0,j1,u0,u1 in rr:
                            if ev:
                                for u,v,w in eval_forms(d,r,h0,h1,j0,j1,u0,u1):
                                    z0=C.m(dot(a,u),C.gf_pow(dot(a,v),d,12,C.MOD))
                                    for i,t in w.items():a[i]^=C.m(z0,t)
                            else:
                                for j in range(j0,j1+1):
                                    for h in range(max(h0,u0+j),min(h1,u1+j)+1):
                                        a[d*h+r]^=C.m(a[d*(h-j)+r],C.gf_pow(a[j],d,12,C.MOD))
                assert a==z,(n,d)
    print('multipoint references 396/396 PASS',flush=True)

if __name__=='__main__':
    reference_check()
    G.unit_power=unit_power
    Base.Guard.reciprocal=G.reciprocal
    Base.main()
