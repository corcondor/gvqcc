"""#248 codec forward reciprocals ordered by physical pivot, with exact inverse.
Classical word schedule only. Conditional reads/writes, pack and phase not priced.
"""
import collections
from packed_cf import apply,recip,terminal,adjacent,pad_at,pack,BLOCKS

PIVOTS=tuple(range(69))
BY_P={p:tuple((i,k) for i,k in BLOCKS if 2*i+k-1==p) for p in PIVOTS}
assert sum(map(len,BY_P.values()))==630

def forward(s):
    a=list(s);h=[0]*35;i=0; used=[]
    for p in PIVOTS:
        k=p-2*i+1
        if 1<=k<=35-i and a[p]:
            # Earlier allowable pivots of the same continuation had zero value.
            assert not any(a[2*i:p])
            apply(a,recip(p,70-p))
            i+=k;h[i-1]=1;used.append(p)
    pad_at(a,i)
    for i,k in reversed(BLOCKS):
        if adjacent(h,i,k):apply(a,pack(2*i,k,35-i-k))
    return a,h,used

def reverse(dn, hist):
    a=list(dn);h=list(hist)
    for i,k in BLOCKS:
        if adjacent(h,i,k):apply(a,pack(2*i,k,35-i-k),reverse=True)
    i=max((i for i in range(36) if terminal(h,i)))
    pad_at(a,i)
    for p in reversed(PIVOTS):
        if not i:break
        prev=max((j+1 for j in range(i-1) if h[j]),default=0)
        if p!=prev+i-1:continue
        apply(a,recip(p,70-p),reverse=True)
        h[i-1]=0;i=prev
    assert i==0 and not any(h)
    return a

def costs():
    def count(pivots):
        return dict(collections.Counter(op[0] for p in pivots for op in recip(p,70-p)))
    return {'pivot_counts':[len(BLOCKS),len(PIVOTS)],'original_recip':count(2*i+k-1 for i,k in BLOCKS),'ordered_recip':count(PIVOTS)}
