"""Exact GF(2) variable projection certificates on packed legal-state bitsets.

This proves impossibility of deleting one *fixed* nonlinear factor when
output XOR wiring alone is retrained; it is not a global Toffoli lower bound.
"""
from __future__ import annotations

def extend_basis(piv, vector):
    x = int(vector)
    while x:
        i = x.bit_length()-1
        if i in piv:
            x ^= piv[i]
        else:
            piv[i] = x
            return True
    return False

def basis(vectors):
    p = {}
    for value in vectors:
        extend_basis(p, value)
    return p

def rank(vectors):
    return len(basis(vectors))

def contains(piv, vector):
    x = int(vector)
    while x:
        i = x.bit_length()-1
        if i not in piv:
            return False
        x ^= piv[i]
    return True

def certify(input_functions, hidden_products, output_functions):
    inputs = list(map(int, input_functions))
    hidden = list(map(int, hidden_products))
    outputs = list(map(int, output_functions))
    full = basis(inputs + hidden)
    if any(not contains(full, y) for y in outputs):
        raise ValueError('Parent output is not spanned by parent features')
    base = rank(inputs)
    dim = rank(inputs + hidden)
    out_dim = rank(inputs + outputs)
    deletions = []
    for i in range(len(hidden)):
        available = basis(inputs + hidden[:i] + hidden[i+1:])
        uncovered = sum(not contains(available, y) for y in outputs)
        deletions.append({
            'gate': i,
            'possible_by_output_refit_only': uncovered == 0,
            'unrepresented_output_bits': uncovered
        })
    return {
        'input_rank': base,
        'input_plus_products_rank': dim,
        'input_plus_outputs_rank': out_dim,
        'nonlinear_output_dimension': out_dim - base,
        'hidden_product_count': len(hidden),
        'fixed_factor_omissions_possible': [
            d['gate'] for d in deletions if d['possible_by_output_refit_only']
        ],
        'single_gate_deletion_certificates': deletions,
        'scope': 'unchanged hidden-factor truth tables on supplied legal support'
    }

def _smoke_test():
    n = 16
    xs = [sum(((i>>j)&1)<<i for i in range(n)) for j in range(4)]
    h1 = sum((((i>>0)&1)&((i>>1)&1))<<i for i in range(n))
    h2 = sum((((i>>2)&1)&((i>>3)&1))<<i for i in range(n))
    d = certify(xs + [(1<<n)-1], [h1,h2], [h1^h2,h1])
    assert d['fixed_factor_omissions_possible'] == []
    assert d['nonlinear_output_dimension'] == 2
    print('GF2_PROJECTED_CERTIFICATE_PASS', d['input_rank'], d['nonlinear_output_dimension'])

if __name__ == '__main__':
    _smoke_test()
