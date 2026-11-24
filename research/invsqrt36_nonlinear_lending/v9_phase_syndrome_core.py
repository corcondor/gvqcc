"""Core V9 global phase-syndrome search used in v9_syndrome.py.
The full native KMB pipeline and exact BDD checker are in the companion archive.
Input columns are sparse dictionaries: transcript monomial -> bit-packed
input truth vector. Sampled reductions only propose deletions, never authorize
a rewrite without full-domain coefficient cancellation.
"""
def vadd(a, b):
    for k, v in b.items():
        a[k] = a.get(k, 0) ^ v
        if not a[k]:
            a.pop(k)

def reduce_vec(B, v, w=0):
    v = dict(v)
    while v:
        k = max(v)
        p = (k, v[k].bit_length()-1)
        if p not in B:
            break
        u, j = B[p]
        vadd(v, u)
        w ^= j
    return v, w

def propose_subset(items, is_paid):
    """Return proposed removable native indices; exact verification required.

    items: (native_index, coefficient_dictionary), same sampled support.
    is_paid: predicate used to prefer free basis columns.
    """
    B, total, ix = {}, {}, []
    for i, v in sorted(items, key=lambda a: (is_paid(a[0]), a[0])):
        vadd(total, v)
        r, w = reduce_vec(B, v)
        if r:
            k = max(r)
            p = (k, r[k].bit_length()-1)
            w ^= 1 << len(ix)
            ix.append(i)
            B[p] = (r, w)
    v, w = reduce_vec(B, total)
    assert not v
    keep = {i for j, i in enumerate(ix) if w >> j & 1}
    return [i for i, _ in items if i not in keep], len(B)

def verify_deletion_exact(removed_coefficients):
    """Full-domain coefficients, independent HMR variables, no sampling."""
    ledger = {}
    for coeff in removed_coefficients:
        vadd(ledger, coeff)
    return not ledger
