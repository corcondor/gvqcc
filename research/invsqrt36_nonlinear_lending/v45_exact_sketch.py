"""Exact pivot witness rows and nullspace refinement for reachable Boolean XAGs.

All truth masks index legal inputs in a fixed common order. The pivot rows
of a complete echelon basis are an injective restriction on the entire
linear span, including constants. No sampled equality is accepted here.
"""
from itertools import combinations

def bit_indices(v):
    while v:
        t = v & -v
        yield t.bit_length() - 1
        v ^= t

def xor_selected(vs, mask):
    v = 0
    for k in bit_indices(mask):
        v ^= vs[k]
    return v

def echelon(cols):
    b = {}
    for i, v in enumerate(cols):
        tag = 1 << i
        while v:
            j = v.bit_length()-1
            if j not in b:
                b[j] = (v, tag)
                break
            w, t = b[j]
            v ^= w
            tag ^= t
    return b

def exact_affine_witness_rows(full_atom_masks):
    return sorted(echelon(full_atom_masks), reverse=True)

def nullspace(cols):
    b = {}
    rels = []
    for i, v in enumerate(cols):
        tag = 1 << i
        while v:
            j = v.bit_length()-1
            if j not in b:
                b[j] = (v, tag)
                break
            w, t = b[j]
            v ^= w
            tag ^= t
        if not v:
            rels.append(tag)
    return rels

def polynomial_columns(values, terms, one):
    out = []
    for term in terms:
        v = one
        for i in term:
            v &= values[i]
        out.append(v)
    return out

def exact_quadratic_kernel(full_values, legal_count, sample_values, sample_count):
    n = len(full_values)
    terms = [()] + [(i,) for i in range(n)] + list(combinations(range(n), 2))
    sample_cols = polynomial_columns(sample_values, terms, (1 << sample_count)-1)
    ker = nullspace(sample_cols)
    cursor = 0
    while ker and cursor < legal_count:
        size = min(65536 if cursor < 196608 else legal_count-cursor,
                   legal_count-cursor)
        one = (1 << size)-1
        vv = [(x >> cursor) & one for x in full_values]
        cols = polynomial_columns(vv, terms, one)
        residuals = [xor_selected(cols, k) for k in ker]
        ker = [xor_selected(ker, k) for k in nullspace(residuals)]
        cursor += size
    return terms, ker

def test():
    n = 16
    values = [sum(((x >> i) & 1) << x for x in range(n)) for i in range(4)]
    values += [values[0] & values[1], values[2] ^ values[3], (1 << n)-1]
    rows = exact_affine_witness_rows(values)
    for mask in range(1 << len(values)):
        f = xor_selected(values, mask)
        assert (f == 0) == all(not (f >> row & 1) for row in rows)
    terms, ker = exact_quadratic_kernel(values, n, values, n)
    cols = polynomial_columns(values, terms, (1 << n)-1)
    assert all(not xor_selected(cols, k) for k in ker)
    print("exact affine sketch and quadratic kernel regression PASS")

if __name__ == "__main__":
    test()
