"""Check a rank-two alternating coset by recognizing a complete tripartite graph."""
from functools import reduce
from quadratic_phase import insert

def alternating_constraints(edges, kernel, particular):
    eliminate = {}
    for v in kernel:
        insert(eliminate, v)
    pivots = {i: row for i, (row, _) in eliminate.items()}
    witness = [0] * len(edges)
    for j in range(len(edges)):
        if j not in pivots:
            witness[j] = 1 << j
        else:
            v = pivots[j] ^ (1 << j)
            while v:
                i = (v & -v).bit_length()-1
                witness[j] ^= witness[i]
                v ^= 1 << i
    rows = {}
    rhs = 0
    for j, v in enumerate(witness):
        if particular >> j & 1:
            rhs ^= v
        while v:
            p = (v & -v).bit_length()-1
            rows.setdefault(p, []).append(j)
            v ^= 1 << p
    return [(row, bool(rhs >> j & 1)) for j, row in rows.items()]

def find_by_sat(n, edges, kernel, particular, timeout_ms=8000):
    import z3
    s = z3.SolverFor('QF_FD')
    s.set(timeout=timeout_ms)
    aa = [z3.Bool(f'a{i}') for i in range(n)]
    bb = [z3.Bool(f'b{i}') for i in range(n)]
    edge = [z3.Bool(f'e{i}_{j}') for i,j in edges]
    for w, (i,j) in zip(edge,edges):
        s.add(w == z3.Xor(z3.And(aa[i],bb[j]),z3.And(aa[j],bb[i])))
    for row,rhs in alternating_constraints(edges, kernel, particular):
        bit = reduce(z3.Xor, (edge[i] for i in row))
        s.add(bit if rhs else z3.Not(bit))
    # Rank-two coordinates are invariant under GL(2,2). Force the first
    # nonzero coordinate to be (1,0) and first distinct label to be (0,1).
    active = z3.BoolVal(False)
    distinct = z3.BoolVal(False)
    for a,b in zip(aa,bb):
        s.add(z3.Implies(z3.Not(active),z3.Not(b)))
        s.add(z3.Implies(z3.Not(distinct),z3.Not(z3.And(a,b))))
        active = z3.Or(active,a)
        distinct = z3.Or(distinct,b)
    ans = s.check()
    if ans == z3.unsat:
        return None, True
    if ans == z3.unknown:
        return None, False
    m = s.model()
    return tuple(sum(1<<j for j,x in enumerate(xs) if z3.is_true(m.eval(x,model_completion=True)))
                 for xs in (aa,bb)), True
