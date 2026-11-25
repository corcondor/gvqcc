"""V54 portable algebra core. Full native emitter and all-domain receipts are in companion ZIP."""
from collections import defaultdict
def encode(q, d, A, m):
    assert d>0 and 0<=A<1<<m and -A<=q<(1<<m)-A
    z=q+A
    return [((z>>j)&1)^((A>>j)&1) for j in range(m)], [d*(1<<j)*(1-2*((A>>j)&1)) for j in range(m)]
def allowed_interval(r,tol,d,A,m):
    return max(-A,-(-(r-tol)//d)),min((1<<m)-1-A,(r+tol)//d)
def best_fiber_codes(rows):
    """rows=(feature, lower, upper); inclusive integer intervals.
    Return exact minimum number of violating rows, and an optimal code for each nonempty fiber.
    """
    buckets=defaultdict(list)
    for f,l,u in rows:buckets[f].append((l,u))
    codes={};bad=0
    for f,b in buckets.items():
        events=defaultdict(int)
        for l,u in b:
            if l<=u:events[l]+=1;events[u+1]-=1
        best=0;cur=0;code=0
        for z,delta in sorted(events.items()):
            cur+=delta
            if cur>best:best,code=cur,z
        codes[f]=code;bad+=len(b)-best
    return bad,codes
if __name__=='__main__':
    for m in range(1,8):
        for A in range(1<<m):
            for q in range(-A,(1<<m)-A):
                b,w=encode(q,13,A,m)
                assert sum(x*y for x,y in zip(b,w))==q*13
    assert best_fiber_codes([(0,0,1),(0,2,3),(0,1,2)])[0]==1
    print('PASS finite signed code and exact fiber optimizer')
