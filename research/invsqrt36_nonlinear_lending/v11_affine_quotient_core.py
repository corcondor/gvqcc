"""Core of the tested V11 nonlinear affine-quotient path search.
The companion reproducibility archive supplies transport.py, native_kmb.py,
the full scanner and exact BDD chain replayer. This module is the search core.
"""
from transport import anf, affine_gates, matrix_basis, coord, ONE, emit
from native_kmb import Op

def basis(xs):
    b={}
    for x in xs:
        while x:
            k=x.bit_length()-1
            if k in b: x^=b[k]
            else: b[k]=x; break
    return list(b.values())

def reduce_by(b,x):
    for y in sorted(b,reverse=True):
        if x>>(y.bit_length()-1)&1: x^=y
    return x

def intersection(a,b):
    piv={}; ans=[]
    for v in a:
        x=reduce_by(b,v); u=v
        while x:
            k=x.bit_length()-1
            if k not in piv: piv[k]=(x,u); break
            y,w=piv[k]; x^=y; u^=w
        if not x: ans.append(u)
    return basis(ans)

def extend(H,S): return next(x for x in S if reduce_by(H,x))

def combo(bs,c):
    v=0
    while c:
        i=(c&-c).bit_length()-1; v^=bs[i]; c&=c-1
    return v

def hcoords(H,one):
    z=[one]
    for h in H:
        if reduce_by(basis(z),h): z.append(h)
    return z[1:]

def perm_basis(n):
    return [sum(1<<x for x in range(1<<n) if x>>i&1) for i in range(n)]

def apply(g,w):
    n=len(w); s=perm_basis(n); one=(1<<(1<<n))-1; I={q:i for i,q in enumerate(w)}
    for o in g:
        v=[I[q] for q in o.wires]
        if o.raw==17: s[v[0]]^=one
        elif o.raw==33: s[v[1]]^=s[v[0]]
        elif o.raw==34: s[v[0]],s[v[1]]=s[v[1]],s[v[0]]
        elif o.raw==49: s[v[2]]^=s[v[0]]&s[v[1]]
        else: raise ValueError(o)
    return s

def lin(froms,tos,w,one):
    B=matrix_basis(froms+[one]); rows=[1<<i for i in range(37)]; n=len(w)
    for i,f in enumerate(tos):
        c=coord(B,f); assert c is not None
        rows[w[i]]=sum(1<<w[j] for j in range(n) if c>>j&1)^(ONE if c>>n&1 else 0)
    return affine_gates(rows)

def edge(S,T,H,w,one,raw=False):
    H=basis(H); n=len(w); h=hcoords(H,one); assert len(h)==n-1
    s=extend(H,S); t=extend(H,T); f=s^t
    tab=[0]*(1<<(n-1)); seen=[False]*len(tab)
    for x in range(1<<n):
        k=sum(((z>>x)&1)<<j for j,z in enumerate(h)); v=(f>>x)&1
        if seen[k] and tab[k]!=v: return None
        tab[k]=v; seen[k]=True
    if not all(seen): return None
    for i in range(n-1):
        for j in range(len(tab)):
            if j>>i&1: tab[j]^=tab[j^(1<<i)]
    if any(v and j.bit_count()>2 for j,v in enumerate(tab)): return None
    pairs=[j for j,v in enumerate(tab) if v and j.bit_count()==2]
    if not pairs: return None
    rows=[0]*(n-1)
    for p in pairs:
        a=(p&-p).bit_length()-1; b=(p^(1<<a)).bit_length()-1
        rows[a]^=1<<b; rows[b]^=1<<a
    i,j=((pairs[0]&-pairs[0]).bit_length()-1,(pairs[0]^(pairs[0]&-pairs[0])).bit_length()-1)
    a,b=rows[i],rows[j]
    if any(rows[k]!=((b if a>>k&1 else 0)^(a if b>>k&1 else 0)) for k in range(n-1)): return None
    A,B=combo(h,a),combo(h,b)
    bas=matrix_basis(S+[one]); hc=[coord(bas,x) for x in h]
    direction=next(v for v in range(1,1<<n) if all((v&x).bit_count()%2==0 for x in hc))
    vv=sum(1<<w[i] for i in range(n) if direction>>i&1)
    ans=[]
    for U,V in [(A,B),(A,A^B),(B,A^B)]:
        aa,bb=coord(bas,U),coord(bas,V); assert aa is not None and bb is not None
        A0=combo(S,aa&((1<<n)-1)); B0=combo(S,bb&((1<<n)-1))
        ar=sum(1<<w[i] for i in range(n) if aa>>i&1); br=sum(1<<w[i] for i in range(n) if bb>>i&1)
        after=[x^(A0&B0) if direction>>i&1 else x for i,x in enumerate(S)]
        assert len(basis(after+[one]+T))==n+1
        g=emit(vv,ar,br); ans.append((g,after))
    if raw: return ans
    return min((g+lin(after,T,w,one) for g,after in ans),key=len)

def hyperplanes(S,I,one):
    B=matrix_basis(S+[one]); n=len(S); ix=[coord(B,x) for x in I]; assert None not in ix
    for a in range(1,1<<n):
        if any((a&x).bit_count()%2 for x in ix): continue
        p=(a&-a).bit_length()-1
        h=[S[j]^(S[p] if a>>j&1 else 0) for j in range(n) if j!=p]
        yield h+[one],S[p]

def solve(g,w,k,stats,max_two=True):
    n=len(w); one=(1<<(1<<n))-1; S=perm_basis(n); T=apply(g,w)
    SB=basis(S+[one]); TB=basis(T+[one]); I=intersection(SB,TB); d=n+1-len(I)
    stats['deficit'+str(d)]+=1
    if d==0: return lin(S,T,w,one)
    if d==1: return edge(S,T,I,w,one)
    if k<3 or d!=2 or not max_two: return None
    best=None
    for H,s in hyperplanes(S,I,one):
        hs=hcoords(H,one); v=[combo(hs,i) for i in range(1<<len(hs))]
        for a in range(1,len(v)):
            for b in range(a+1,len(v)):
                if b>=a^b: continue
                stats['two_moves']+=1; f=v[a]&v[b]; u=s^f; M=hs+[u]
                MB=basis(M+[one]); J=intersection(MB,TB)
                if len(J)!=n: continue
                stats['two_intersection_hits']+=1
                g2=edge(M,T,J,w,one)
                if g2 is None: continue
                g1s=edge(S,M,H,w,one,raw=True); assert g1s is not None
                for g1,inter in g1s:
                    g2=edge(inter,T,J,w,one); assert g2 is not None
                    cand=g1+g2
                    if best is None or len(cand)<len(best): best=cand
    return best
