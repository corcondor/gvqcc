"""V12 research core: exact affine/permutation plus phase word synthesis.
The runnable native scanner, multi-cut potential search, BDD verifier, and
receipts are in the companion archive. This is not a submission compiler.
"""
from functools import lru_cache

def ident(n):
    return tuple(sum(1 << v for v in range(1 << n) if v >> i & 1)
                 for i in range(n)) + (0,)

@lru_cache(None)
def moves(n):
    return tuple([(17,(i,)) for i in range(n)]
        + [(33,(i,j)) for i in range(n) for j in range(n) if i != j]
        + [(34,(i,j)) for i in range(n) for j in range(i+1,n)]
        + [(16,(i,)) for i in range(n)]
        + [(32,(i,j)) for i in range(n) for j in range(i+1,n)])

def act(s,o,n):
    g,w=o; a=list(s); x=w[0]; y=w[-1]
    if g==17: a[x]^=(1<<(1<<n))-1
    elif g==33: a[y]^=a[x]
    elif g==34: a[x],a[y]=a[y],a[x]
    elif g==16: a[-1]^=a[x]
    elif g==32: a[-1]^=a[x]&a[y]
    return tuple(a)

@lru_cache(None)
def base(n):
    s=ident(n); B={s:()}; front=[s]; M=moves(n)
    for _ in range(4 if n<=3 else 3):
        q=[]
        for a in front:
            for j,o in enumerate(M):
                b=act(a,o,n)
                if b not in B: B[b]=B[a]+(j,); q.append(b)
        front=q
    return B

@lru_cache(maxsize=200000)
def find(n,target,bound):
    B=base(n); M=moves(n); maxd=4 if n<=3 else 3
    if target in B: return B[target] if len(B[target])<bound else None
    if bound<=maxd+1: return None
    seen={target:()}; front=[target]; best=None
    for d in range(1,min(3,bound-1-maxd)+1):
        nex=[]
        for a in front:
            for j,o in enumerate(M):
                b=act(a,o,n)
                if b in seen: continue
                t=seen[a]+(j,); seen[b]=t
                if b in B:
                    p=B[b]+t[::-1]
                    if len(p)<bound and (best is None or len(p)<len(best)): best=p
                nex.append(b)
        if best is not None: return best
        front=nex
    return None

def phase_span(columns,target):
    """One GF(2) decomposition; bitsets are exact pulled-back ANF columns.
    The caller chooses column order and separately verifies the native splice.
    """
    B={}
    for j,v in enumerate(columns):
        c=1<<j
        while v:
            k=v.bit_length()-1
            if k not in B: B[k]=(v,c); break
            x,y=B[k]; v^=x; c^=y
    v=target; c=0
    while v:
        k=v.bit_length()-1
        if k not in B: return None
        x,y=B[k]; v^=x; c^=y
    return [i for i in range(len(columns)) if c>>i&1]
