from functools import lru_cache

@lru_cache(None)
def plan(n,a):
    # Direct chain requires n-2 clean.
    best=(n-2,0) if n<=a+2 else (10**9,0)
    # Retain g group roots, reuse scratch after each measurement-based erase.
    for g in range(2,min(a,n//2)+1):
        # This implementation uses the same post-allocation scratch pool for every group.
        if n>g*(a-g+2): continue
        inner,_=plan(g,a-g)
        v=2*n-3*g+inner
        best=min(best,(v,g))
    return best
if __name__=='__main__':
    for n in (420,840): print(n,plan(n,60))
