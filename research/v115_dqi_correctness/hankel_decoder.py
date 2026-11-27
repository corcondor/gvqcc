"""Independent syndrome-only Hankel decoder and rational chart codec.

The rank of H35 is the number of nonzero errors on distinct nonzero
evaluation points. The leading w-by-w block is invertible even if its
leading entries/minors vanish. Pivot search, never inv(0), is mandatory.
This is a classical reference, not a quantum implementation.
"""
from field_reference import mul,div,trim,add,prod,divrem,evalp
from checked_decoder import recover,syndromes,N,W,M

def eliminate(rows,ncols):
    a=[list(r) for r in rows]
    if any(len(r)<ncols for r in a):raise ValueError("short matrix row")
    rank=0
    for col in range(ncols):
        pivot=next((j for j in range(rank,len(a)) if a[j][col]),None)
        if pivot is None:continue
        a[rank],a[pivot]=a[pivot],a[rank]
        r=a[rank];scale=div(1,r[col])
        for j in range(col,len(r)):r[j]=mul(r[j],scale)
        for i,t in enumerate(a):
            if i==rank or not t[col]:continue
            scale=t[col]
            for j in range(col,len(t)):t[j]^=mul(scale,r[j])
        rank+=1
        if rank==len(a):break
    return rank,a

def locator(s):
    s=list(s)
    if len(s)!=N or any(not isinstance(x,int) or not 0<=x<=M for x in s):
        raise ValueError("invalid syndrome")
    w,_=eliminate([s[i:i+W] for i in range(W)],W)
    if not w:
        if any(s):raise ValueError("zero Hankel rank but nonzero syndrome")
        return [1]
    rank,a=eliminate([s[i:i+w]+[s[i+w]] for i in range(w)],w)
    if rank!=w:raise ValueError("singular leading Hankel block")
    d=[r[-1] for r in a]+[1]
    if not d[0]:raise ValueError("zero evaluation point")
    for i in range(N-w):
        v=s[i+w]
        for j,c in enumerate(d[:-1]):v^=mul(c,s[i+j])
        if v:raise ValueError("moment recurrence failure")
    return d[::-1]

def decode_hankel(s):
    s=list(s)
    return recover(s,locator(s))

def invmod(a,b):
    # GF(4096)[X] extended Euclid. Return inverse modulo b, or reject.
    r0,r1=trim(b),divrem(a,b)[1];t0,t1=[],[1]
    while r1:
        q,r=divrem(r0,r1)
        r0,r1=r1,r
        t0,t1=t1,add(t0,prod(q,t1))
    if len(r0)!=1:raise ValueError("nonunit modulo denominator")
    return divrem([div(x,r0[0]) for x in t0],b)[1]

def rational_from_syndrome(s,U):
    # D(X)=X^w Lambda(1/X); N0(X)=X^(w-1) Omega(1/X).
    # N = U*N0 mod D. No error positions or magnitudes enter this function.
    lam=locator(s);w=len(lam)-1
    d=lam[::-1]
    if not w:return [],d
    omega=trim(prod(list(s),lam)[:N])
    if len(omega)>w:raise ValueError("key equation degree")
    n0=trim((omega+[0]*(w-len(omega)))[::-1])
    n=divrem(prod(U,n0),d)[1]
    return n,d

def syndrome_from_rational(n,d,U):
    d=trim(d);n=trim(n)
    if not d or d[-1]!=1:raise ValueError("nonmonic denominator")
    w=len(d)-1
    if not w:
        if n:raise ValueError("nonzero numerator for degree zero")
        return [0]*N
    if len(n)>w or not d[0]:raise ValueError("invalid rational pair")
    n0=divrem(prod(n,invmod(U,d)),d)[1]
    omega=(n0+[0]*(w-len(n0)))[::-1]
    lam=d[::-1]
    s=[]
    for j in range(N):
        v=omega[j] if j<len(omega) else 0
        for k in range(1,min(w,j)+1):v^=mul(lam[k],s[j-k])
        s.append(v)
    return s
