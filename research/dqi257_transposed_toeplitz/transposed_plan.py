"""Exact transposed Lagrange middle-product rank plan for #271 / #277.
Import alongside the archived #271 or #277 coefficient modules.
"""
from functools import lru_cache
from packed_shared import m,inv,mul,pad
import toeplitz as old

def powseq(x,n):
    v=[1]
    for _ in range(n-1):v.append(m(v[-1],x))
    return tuple(v)

@lru_cache(None)
def plan(l,r):
    k=l+r-1
    if k>=l*r:return None
    xs=list(range(k));terms=[]
    for x in xs:
        poly=[1];d=1
        for y in xs:
            if y!=x:poly=mul(poly,[y,1]);d=m(d,x^y)
        terms.append((tuple(m(z,inv(d)) for z in pad(poly,k)),
                      tuple(reversed(powseq(x,r))),powseq(x,l)))
    for a in range(k):
        for b in range(r):
            for i in range(l):
                v=0
                for x,y,z in terms:v^=m(m(x[a],y[b]),z[i])
                assert v==int(a+b==r-1+i)
    A,P,T=old.Frame(k),old.Frame(r),old.Frame(l);out=[]
    while terms:
        def cost(t):
            x,y,z=t
            return sum(bool(v) for v in A.coords(x))+2*sum(bool(v) for v in P.coords(y))+2*sum(bool(v) for v in T.vector(z))
        idx=min(range(len(terms)),key=lambda i:(cost(terms[i]),i));x,y,z=terms.pop(idx)
        starts=[len(f.ops) for f in (A,P,T)];a=A.form(x);p=P.form(y);q,c=T.direction(z)
        for f,tag,s in zip((A,P,T),('B','P','T'),starts):old.emit_frame(out,f,tag,s)
        out.append(('mul',q,a,p,c))
    for f,tag in zip((A,P,T),('B','P','T')):old.undo_frame(out,f,tag)
    assert sum(g[0]=='mul' for g in out)==k
    return tuple(out)
