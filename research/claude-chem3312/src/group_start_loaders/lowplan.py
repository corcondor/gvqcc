# low-part product plans: functions of x = (x0,x1,x2) as 8-bit truth tables; each product is one AND of two
# affine combinations of earlier functions.  Find a plan whose first j products span (mod affine) a space that
# contains every U of a chosen chip set, followed by 4-j products completing all monomials.
import itertools

ONE, X0, X1, X2 = 0xFF, 0xAA, 0xCC, 0xF0


def reduce(piv, v):
    for h, r in piv:
        if v >> h & 1:
            v ^= r
    return v


def span_piv(vs):
    piv = []
    for v in vs:
        v = reduce(piv, v)
        if v:
            piv.append((v.bit_length() - 1, v))
    return piv


def span_all(basis):
    out = {0}
    for b in basis:
        out |= {v ^ b for v in out}
    return out


def contains(vs, targets):
    piv = span_piv(vs)
    return all(reduce(piv, t) == 0 for t in targets)


def plans(j, targets):
    """all ordered plans of j products (L, M) whose span with 1, x0, x1, x2 contains targets."""
    out = []
    base = [ONE, X0, X1, X2]

    def rec(basis, prods):
        if len(prods) == j:
            if contains(basis, targets):
                out.append(list(prods))
            return
        sp = sorted(span_all(basis))
        seen = set()
        for a, b in itertools.combinations([v for v in sp if v not in (0, ONE)], 2):
            if (a ^ b) == ONE:
                continue
            f = a & b
            r = reduce(span_piv(basis), f)
            if r == 0 or r in seen:
                continue
            seen.add(r)
            prods.append((a, b))
            rec(basis + [f], prods)
            prods.pop()
            if out:
                return
        return

    rec(base, [])
    return out


def full_plan(j, targets):
    """plan with j early products spanning targets, then 4 - j completing the 8-dim function space."""
    p = plans(j, targets)
    if not p:
        return None
    early = p[0]
    basis = [ONE, X0, X1, X2] + [a & b for a, b in early]
    late = []
    allf = [1 << i for i in range(8)]
    while not contains(basis, allf):
        sp = sorted(span_all(basis))
        for a, b in itertools.combinations([v for v in sp if v not in (0, ONE)], 2):
            if (a ^ b) == ONE:
                continue
            if reduce(span_piv(basis), a & b):
                late.append((a, b))
                basis.append(a & b)
                break
        else:
            return None
    return early, late


def express(basis_forms, target):
    """basis_forms: list of (truth table, linear form); returns the form of target or None."""
    piv = {}
    for v, f in basis_forms:
        while v:
            h = v.bit_length() - 1
            if h in piv:
                v ^= piv[h][0]
                f ^= piv[h][1]
            else:
                piv[h] = (v, f)
                break
    form = 0
    t = target
    while t:
        h = t.bit_length() - 1
        if h not in piv:
            return None
        t ^= piv[h][0]
        form ^= piv[h][1]
    return form
