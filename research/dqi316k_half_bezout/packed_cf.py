"""Fixed word-level full raw syndrome codec, not an emitted native KMB.
Uses the exact GF and phase-coordinate reference of PR246.
630 fixed controlled blocks; 35 history bits; Python if interprets controls.
"""
import collections, json, random
from pathlib import Path
from verify_half import F,m,trim,prod,divrem,decode,make_squarefree,half,fixtures,moments,K,add

BLOCKS=tuple((i,k) for i in range(35) for k in range(1,36-i))
assert len(BLOCKS)==630
def perm(p,order):
    cur=list(range(len(order)));pos=cur[:]
    for j,v in enumerate(order):
        k=pos[v]
        if j!=k:
            yield ('swap',p+j,p+k)
            u=cur[j];cur[j],cur[k]=cur[k],cur[j];pos[u],pos[v]=k,j

def recip(p,n):
    for j in range(1,n):yield ('scale',p+j,p,1)
    for d in (2,4,16):
        if d>=n:continue
        for i in range(n-1,d-1,-1):
            for j in range(1,i//d+1):
                if i==d*j:yield ('frobxor',p+i,p+j,d)
                else:yield ('frobmulxor',p+i,p+i-d*j,p+j,d)
    yield ('inv',p)
    for j in range(1,n):yield ('scale',p+j,p,0)

def pack(p,k,r):
    order=list(range(2*k,2*k+r))+list(range(2*k+r,2*k+2*r))+list(range(2*k-1,k-2,-1))+list(range(k-1))
    yield from perm(p,order)
    base=p+r;q=base+r;lead=q+k
    for j in range(k+1):
        for i in range(r):yield ('mulxor',base+j+i,q+j,p+i)
    for i in range(r):yield ('scale',p+i,lead,1)
    for i in range(r+k):yield ('scale',base+i,lead,1)
    yield ('inv',lead)
    yield from perm(p,list(range(r,r+r+k))+list(range(r))+[2*r+k]+list(range(2*r+k+1,2*(r+k))))

def apply(a,ops,reverse=False,c=None):
    if reverse:ops=reversed(list(ops))
    for tag,*p in ops:
        if c is not None:c[tag]+=1
        if tag=='scale':
            t,i,e=p;assert t!=i;a[t]=m(a[t],F.inv(a[i]) if e^reverse else a[i])
        elif tag=='mulxor':
            t,i,j=p;assert t not in (i,j);a[t]^=m(a[i],a[j])
        elif tag=='frobxor':
            t,i,d=p;assert t!=i;a[t]^=F.power(a[i],d) if a[i] else 0
        elif tag=='frobmulxor':
            t,i,j,d=p;assert t not in (i,j);a[t]^=m(a[i],F.power(a[j],d)) if a[j] else 0
        elif tag=='inv':
            i,=p;assert a[i];a[i]=F.inv(a[i])
        elif tag=='swap':
            i,j=p;a[i],a[j]=a[j],a[i]
        else:raise ValueError(tag)

def active(h,i):return i==0 or h[i-1]
def first(h,a,i,k):return active(h,i) and not any(a[2*i:2*i+k-1]) and a[2*i+k-1]!=0
def adjacent(h,i,k):return active(h,i) and active(h,i+k) and not any(h[i:i+k-1])
def terminal(h,i):return active(h,i) and not any(h[i:])
def pad_at(a,i):
    P=[0,1] if (35-i)%2 else [1]
    for k in K[:(35-i)//2]:P=prod(P,[k,1,1])
    assert len(P)==36-i and P[-1]==1
    for j,v in enumerate(P[:-1]):a[2*i+j]^=v

def forward(S):
    a=list(S);h=[0]*35;c=collections.Counter()
    for i,k in BLOCKS:
        if first(h,a,i,k):
            apply(a,recip(2*i+k-1,71-2*i-k),c=c);h[i+k-1]^=1
    for i in range(36):
        if terminal(h,i):pad_at(a,i)
    for i,k in reversed(BLOCKS):
        if adjacent(h,i,k):apply(a,pack(2*i,k,35-i-k),c=c)
    return a,h,c

def reverse(DN,h):
    a=list(DN);h=list(h)
    for i,k in BLOCKS:
        if adjacent(h,i,k):apply(a,pack(2*i,k,35-i-k),reverse=True)
    for i in reversed(range(36)):
        if terminal(h,i):pad_at(a,i)
    for i,k in reversed(BLOCKS):
        if first(h,a,i,k):
            h[i+k-1]^=1;apply(a,recip(2*i+k-1,71-2*i-k),reverse=True)
    assert not any(h)
    return a

def inverse_half(D,H):
    A=trim([F.power(c,2048) if c else 0 for c in D[::2]])
    B=trim([F.power(c,2048) if c else 0 for c in D[1::2]])
    P0=add(divrem(prod(A,H[18:35]),B)[1],[m(H[0],b) for b in B])
    P1=divrem(prod(A,H[1:18]),B)[1]
    N=[0]*35
    for i,c in enumerate(P0):N[2*i]=m(c,c)
    for i,c in enumerate(P1):N[2*i+1]=m(c,c)
    return trim(N)

def main():
    cases=0;groups=collections.Counter();mx=collections.Counter();rng=random.Random(316250)
    for label,w,e in fixtures():
        S=moments(e);D,N,w0=decode(S);assert w0==w
        D,N=make_squarefree(D,N,w)
        DN,h,c=forward(S)
        assert DN[:35]+[1]==D and trim(DN[35:])==trim(N)
        H,V=half(D,N);N2=inverse_half(D,H);assert N2==trim(N)
        decoded={}
        for j in range(4095):
            x=F.EXP[j]
            if F.evalpoly(D,x)==0:
                v=m(F.evalpoly(V,x),F.inv(x));assert v;decoded[j]=v
        assert decoded==e
        mask=[rng.randrange(4096) for _ in range(4095)]
        phase=lambda err:sum((mask[j]&v).bit_count() for j,v in err.items())&1
        assert phase(decoded)==phase(e)
        assert reverse(D[:-1]+N2+[0]*(35-len(N2)),h)==S
        groups[label]+=1;cases+=1
        for k,v in c.items():mx[k]=max(mx[k],v)
    static=collections.Counter()
    for i,k in BLOCKS:
        static.update(op[0] for op in recip(2*i+k-1,71-2*i-k))
        static.update(op[0] for op in pack(2*i,k,35-i-k))
    result=dict(scope="fixed controlled WORD reference only; no KMB, no physical width or score",cases=cases,groups=groups,errors=0,history_bits=35,static_forward_word_ops=static,max_active_forward_word_ops=mx)
    print(json.dumps(result,indent=2))
    Path("packed_cf_receipt.json").write_text(json.dumps(result,indent=2)+"\n")
if __name__=="__main__":main()
