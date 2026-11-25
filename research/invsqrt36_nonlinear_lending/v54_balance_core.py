"""Exact integer 34-bit target, balanced-control witness; no native score claim.
The complete native spectral emitter, certificate tables and complement
fragment are distributed in the companion reproduction archive.
"""
import math
import numpy as np

W=22
N=1<<W
M=3133452
S=1<<34

def target():
    a=np.empty(M,dtype=np.uint64)
    lo=(S-(S>>24))**2
    hi=(S+(S>>24))**2
    for i,x in enumerate(range(1,M+1)):
        v=math.isqrt(S*S//x)
        if x*(2*v+1)**2 <= 4*S*S:
            v+=1
        assert lo<=x*v*v<=hi
        a[i]=v%S
    return a

def masks(a):
    x=np.arange(N,dtype=np.uint32)
    legal=np.zeros(N,bool);legal[1:M+1]=1
    ill=np.flatnonzero(~legal)
    pivots=[((x>>j)&1).astype(bool) for j in range(W)]
    def direct(j,f):
        c=int(f.sum())
        assert M-N//2<=c<=N//2
        need=N//2-c
        q=min(range(W),key=lambda q:int(np.count_nonzero(pivots[q][1:M+1]^f))+abs(int(pivots[q][ill].sum())-need))
        g=pivots[q].copy();g[1:M+1]=f
        gi=g[ill].copy();n=int(gi.sum())
        if n>need:gi[np.flatnonzero(gi)[:n-need]]=0
        elif n<need:gi[np.flatnonzero(~gi)[:need-n]]=1
        g[ill]=gi
        yield j,1,q,g
    for j in range(34):
        f=((a>>np.uint64(j))&1).astype(bool)
        c=int(f.sum())
        if M-N//2<=c<=N//2:
            yield from direct(j,f)
        elif c<M-N//2:
            q=21;h=pivots[q]
            assert not np.any(h[1:M+1]&f) and c<=int(h[ill].sum())
            g=h.copy();g[1:M+1]^=f
            g[ill[np.flatnonzero(h[ill])[:c]]]^=True
            yield j,1,q,g
            yield j,-1,q,h.copy()
        else:
            ids=np.flatnonzero(f);u=np.zeros_like(f)
            u[ids[:c//2]]=True
            yield from direct(j,u)
            yield from direct(j,f^u)

def audit():
    a=target();z=np.zeros(M,dtype=np.uint64)
    x=np.arange(N,dtype=np.uint32)
    pos=[];neg=0;swaps=0;nc=0
    for j,sgn,p,g in masks(a):
        b=((x>>p)&1).astype(bool)
        assert int(g.sum())==N//2
        l=np.flatnonzero(g&~b);r=np.flatnonzero(~g&b)
        assert len(l)==len(r)
        if len(l)%2:
            good=np.flatnonzero((g==b)&~b)[:2]
            assert len(good)==2
            l=np.append(l,good[0]);r=np.append(r,good[1])
        assert len(l)%2==0 and len(np.unique(np.concatenate([l,r])))==2*len(l)
        y=b.copy();y[l]=b[r];y[r]=b[l]
        assert np.array_equal(y,g)
        swaps+=len(l);nc+=1
        v=g[1:M+1].astype(np.uint64)<<np.uint64(j)
        if sgn>0:
            pos.append(1<<j);z+=v
        else:
            assert p==21 and np.array_equal(g,b)
            neg-=1<<j;z-=v
    assert np.array_equal(z%S,a)
    angles=pos+[neg%S]
    assert len(angles)==36 and sum(t%(S//8)!=0 for t in angles)==33
    assert swaps==18944216 and nc==45
    print("exact integer tolerance + balanced even-permutation phase words: PASS")
    print("22Q abstract constructive route; 36 rotations / 33 generic; 18944216 swaps; no full native emission")

if __name__=="__main__":
    audit()
