"""V60 diagonal partition planner. Call with the native compiler's exact option-cost function."""
from functools import lru_cache

def plan(k, M, weight, option):
    M = tuple(sorted(M, key=lambda v: (v.bit_count(), v)))
    @lru_cache(None)
    def go(i):
        if i == len(M):
            return 0, 0, ()
        opts = []
        for j in range(i+1, len(M)+1):
            m = M[i:j]
            for kind in (["small", "stream"] if len(m) in (2,3) else ["stream"]):
                cc, rr, groups = option(k, m, kind)
                a, b, tail = go(j)
                opts.append((cc+a, rr+b, ((m,kind,groups),)+tail))
        return min(opts, key=lambda v: (v[0]+weight*v[1],v[0],v[1],len(v[2])))
    return go(0)
