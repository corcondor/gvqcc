"""Finite integer identities and bounded reversible borrow-path search.
Full native generators and serialized replay are in the companion archive.
"""
import heapq
def rounded(m,t):
    return (2*m*t+m+8)//16
def absorbed(m,t):
    p=m*t+m//2
    return (p>>3)+((p>>2)&1)
def borrow(a,y,b):
    return ((1-a)&y)|((1-a)&b)|(y&b)
def plan(costs,k=4):
    n=len(costs); dist={0:0}; parent={}; queue=[(0,0)]
    while queue:
        cost,s=heapq.heappop(queue)
        if cost!=dist[s]:continue
        if s>>(n-1)&1:
            out=[]
            while s:
                s,j=parent[s];out.append(j)
            return out[::-1],cost
        for j,w in enumerate(costs):
            if j and not s>>(j-1)&1:continue
            if not s>>j&1 and s.bit_count()>=k:continue
            z=s^(1<<j);new=cost+w
            if new<dist.get(z,float("inf")):
                dist[z]=new;parent[z]=(s,j);heapq.heappush(queue,(new,z))
    raise ValueError("no schedule")
if __name__=="__main__":
    for m in range(16):
        for t in range(4096):assert rounded(m,t)==absorbed(m,t)
    for a in range(2):
        for y in range(2):
            for b in range(2):assert a-y-b==(a^y^b)-2*borrow(a,y,b)
    p,c=plan([1]*14,4)
    s=0
    for j in p+p[::-1]:
        assert not j or s>>(j-1)&1
        s^=1<<j
        assert s.bit_count()<=4
    assert s==0
    print("PASS: 65536 rounding cases, 8 borrow cases and reversible pebble schedule")
