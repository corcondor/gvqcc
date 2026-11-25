"""Portable exact integer core of V57. Native emitters and all-domain receipts
are in the companion archive; this file is not a complete oracle compiler."""
from itertools import product, combinations
from functools import lru_cache

def shared_weights(intervals):
    # Zero is preferred. Greedy stabbing of remaining closed integer intervals
    # minimizes the distinct nonzero values with all other atoms fixed.
    a=[0]*len(intervals)
    r={i for i,(l,u) in enumerate(intervals) if not l<=0<=u}
    while r:
        j=min(r,key=lambda i:intervals[i][1])
        u=intervals[j][1]
        g=[i for i in r if intervals[i][0]<=u<=intervals[i][1]]
        l=max(intervals[i][0] for i in g)
        h=min(intervals[i][1] for i in g)
        for k in reversed(range(63)):
            d=1<<k
            v=-(-l//d)*d
            if v<=h:break
        assert l<=v<=h and v!=0
        for i in g:a[i]=v
        r.difference_update(g)
    assert all(l<=v<=u for (l,u),v in zip(intervals,a))
    return a

def exchange(a,b,I,J,K):
    # I,J,K are allowable changes on i-only,j-only,intersection respectively.
    # One atom is deleted when possible; jointly choose the other atom values.
    na=[]; bounds=[]
    for x,y,(il,iu),(jl,ju),(kl,ku) in zip(a,b,I,J,K):
        d=-x
        l=max(jl,kl-d);u=min(ju,ku-d)
        if not(il<=d<=iu and l<=u):
            d=0;l=max(jl,kl);u=min(ju,ku)
        assert l<=u
        na.append(x+d);bounds.append((y+l,y+u))
    nb=shared_weights(bounds)
    return na,nb

def two_stage_terms(C,g,L=17):
    """C is the 24-by-5 signed coefficient table in integer units."""
    for k in (2,3,4):
        for i in range(max(abs(row[k]) for row in C).bit_length()):
            if not any((abs(row[k])>>i)&1 for row in C):continue
            if k==2:yield k,i,0,i+g
            elif k==3:
                for j in range(L):
                    w=i+j-L+g
                    if w>=0:yield k,i,1<<j,w
            else:
                for j in range(L):
                    for z in range(j,L):
                        w=i+j+z-2*L+int(j!=z)+g
                        if w>=0:yield k,i,(1<<j)|(1<<z),w

def evaluate_stream(C,a,t,g,L=17):
    s=0
    for k,i,m,w in two_stage_terms(C,g,L):
        if t&m==m and (abs(C[a][k])>>i)&1:
            s+=(-1 if k==3 else 1)*(1<<w)
    return s

def exclusive_partition(masks,columns,cap):
    @lru_cache(None)
    def independent(s):
        a=0
        for j,m in enumerate(masks):
            if (s>>j)&1:
                if a&m:return False
                a|=m
        return True
    @lru_cache(None)
    def color(s):
        if not s:return 0,()
        if independent(s):return 1,(s,)
        b=s&-s;u=s;best=(10**9,())
        while u:
            if u&b and independent(u):
                n,gs=color(s^u);best=min(best,(1+n,(u,)+gs))
            u=(u-1)&s
        return best
    @lru_cache(None)
    def cost(s):return sum(color(s&c)[0] for c in columns)
    @lru_cache(None)
    def dp(s):
        if not s:return 0,()
        b=s&-s;u=s;best=(10**9,())
        while u:
            if u&b and u.bit_count()<=cap:
                n,gs=dp(s^u);best=min(best,(n+cost(u),(u,)+gs))
            u=(u-1)&s
        return best
    return dp((1<<len(masks))-1)

if __name__=="__main__":
    assert shared_weights([(-1,2),(3,4),(4,7)])==[0,4,4]
    assert exclusive_partition([1,2,4],[7],3)[0]==1
    for a,b,c in product(range(2),repeat=3):
        assert a+b+c==(a^b^c)+2*(a^((a^b)&(a^c)))
    C=[[0,0,4,-8,16]]
    assert evaluate_stream(C,0,3,0,2)==7
    print("PASS: finite algebra and shared interval core")
