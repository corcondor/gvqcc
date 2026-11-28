#!/usr/bin/env python3
"""Reproducible GF(2^12) degree-drop analysis for saved DQI failure fixtures.

Only tests the independent classical syndrome/key-equation model.
Does NOT simulate a KickMix native circuit or identify a physical gate.
For input NPZ keys: syndromes, error_positions, error_values; optional actual_syndromes.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np

MOD = 0x1053
FIELD_ORDER = 4095
N_SYNDROMES = 70
T = N_SYNDROMES // 2


def slowmul(a: int, b: int) -> int:
    c = 0
    while b:
        if b & 1:
            c ^= a
        b >>= 1
        a <<= 1
        if a & (1 << 12):
            a ^= MOD
    return c


EXP = []
LOG = [-1] * 4096
x = 1
for k in range(FIELD_ORDER):
    if LOG[x] != -1:
        raise AssertionError('primitive generator failed')
    EXP.append(x)
    LOG[x] = k
    x = slowmul(x, 2)
assert x == 1 and len(EXP) == len(set(EXP)) == FIELD_ORDER
EXP *= 2


def mul(a: int, b: int) -> int:
    return EXP[LOG[a] + LOG[b]] if a and b else 0


def div(a: int, b: int) -> int:
    if not b:
        raise ZeroDivisionError('GF division by zero')
    return EXP[(LOG[a] - LOG[b]) % FIELD_ORDER] if a else 0


def trim(p):
    p = list(p)
    while p and not p[-1]:
        p.pop()
    return p


def add(a, b):
    r = [0] * max(len(a), len(b))
    for i, x in enumerate(a):
        r[i] ^= x
    for i, x in enumerate(b):
        r[i] ^= x
    return trim(r)


def prod(a, b):
    if not a or not b:
        return []
    r = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        if x:
            for j, y in enumerate(b):
                if y:
                    r[i + j] ^= mul(x, y)
    return trim(r)


def scale(a, k):
    return trim([mul(x, k) for x in a])


def divrem(a, b):
    a, b = trim(a), trim(b)
    if not b:
        raise ZeroDivisionError('zero polynomial divisor')
    q = [0] * max(0, len(a) - len(b) + 1)
    while len(a) >= len(b):
        offset = len(a) - len(b)
        factor = div(a[-1], b[-1])
        q[offset] ^= factor
        for j, val in enumerate(b):
            a[offset + j] ^= mul(factor, val)
        a = trim(a)
    return trim(q), a


def evalp(a, x):
    y = 0
    for c in reversed(a):
        y = mul(y, x) ^ c
    return y


def eea_trace(s):
    # Berlekamp key equation: S(X)*Lambda(X) = Omega(X) mod X^70.
    # Track coefficient t of S in r = a*X^70 + t*S.
    rprev, r = [0] * N_SYNDROMES + [1], trim(s)
    tprev, t = [], [1]
    trace = []
    while r and len(r) - 1 >= T:
        dp, dc = len(rprev) - 1, len(r) - 1
        q, rem = divrem(rprev, r)
        tn = add(tprev, prod(q, t))
        trace.append({
            'iteration': len(trace),
            'dividend_degree': dp,
            'divisor_degree': dc,
            'quotient_degree': len(q)-1,
            'quotient': q,
            'next_remainder_degree': len(rem)-1,
            'degree_drop_divisor_to_remainder': dc-(len(rem)-1),
            'crosses_stop_threshold': dc >= T and len(rem)-1 < T,
            'remainder_leading_coefficient': rem[-1] if rem else 0,
            'remainder_hash': hashlib.sha256(json.dumps(rem).encode()).hexdigest(),
            'key_coefficient_degree': len(tn)-1,
        })
        rprev, r = r, rem
        tprev, t = t, tn
    return trace, trim(t), trim(r)



# Exact 70-dimensional confluent-coordinate analysis from the V110 certificate.
# The coordinate rows form a basis in GF(4096); a residual confined to one
# kappa block indicates corruption of four coordinates, not necessarily an
# EEA or physical-gate origin at that location.
NODES = (3134, 3169, 3257, 3302, 3384, 3431, 3519, 3552,
         3592, 3633, 3671, 3727, 3792, 3854, 3921, 3977, 4054)


def quotient(a, b):
    q, r = divrem(a, b)
    if r:
        raise ValueError('not divisible by nodal polynomial')
    return q


def dot(a,b):
    z=0
    for x,y in zip(a,b):
        z ^= mul(x,y)
    return z


def field_modulus():
    out=[1]
    for c in NODES:
        q=[c,1,1]
        out=prod(out,prod(q,q))
    assert len(out)==69
    return out


def jet_rows(P,c):
    qc=[c,1,1]
    p1=quotient(P,qc)
    p2=quotient(p1,qc)
    polys=[prod([0,1],prod(p1,[1,1])),
           prod([0,1],p1),
           prod([0,1],prod(p2,[1^c,0,1])),
           prod([0,1],p2)]
    return [(a[1:]+[0]*70)[:70] for a in polys]


def classify_syndrome_residual(expected, actual):
    if actual is None:
        return None
    P=field_modulus()
    nodes=[]
    for c in NODES:
        rows=jet_rows(P,c)
        a=[dot(r,expected) for r in rows]
        b=[dot(r,actual) for r in rows]
        if a!=b:
            nodes.append({'kappa':c,'input':a,'output':b,'delta':[x^y for x,y in zip(a,b)]})
    inf_rows=[(P+[0])[:70],[0]+P]
    infinity_equal=all(dot(r,expected)==dot(r,actual) for r in inf_rows)
    delta=[x^y for x,y in zip(expected,actual)]
    minimal_c=[]
    for c in NODES:
        factor=mul(c,c)
        if all(delta[j]==delta[j-2]^mul(factor,delta[j-4]) for j in range(4,70)):
            minimal_c.append(c)
    return {'changed_blocks':nodes,
            'changed_block_count':len(nodes),
            'infinity_coordinates_equal':infinity_equal,
            'delta_double_node_recurrence_matches':minimal_c}


def analyze_fixture(path: Path):
    source = path.read_bytes()
    with np.load(path, allow_pickle=False) as f:
        positions = list(map(int, f['error_positions']))
        values = list(map(int, f['error_values']))
        synd = list(map(int, f['syndromes']))
        actual = list(map(int, f['actual_syndromes'])) if 'actual_syndromes' in f else None
    assert len(synd) == N_SYNDROMES and len(positions) == len(values)
    assert len(set(positions)) == len(positions) and len(positions) <= 35
    assert all(0 <= p < 4095 for p in positions)
    assert all(0 < v < 4096 for v in values)
    a = [EXP[p] for p in positions]
    re_synd = [0] * 70
    for j in range(N_SYNDROMES):
        re_synd[j] = 0
        for x, e in zip(a, values):
            re_synd[j] ^= mul(e, EXP[(LOG[x]*(j+1)) % FIELD_ORDER])
    assert synd == re_synd, 'input syndromes do not match independent reference'
    lam_expected = [1]
    for root in a:
        lam_expected = prod(lam_expected, [1, root])
    omega_expected = []
    for x, e in zip(a, values):
        q, rem = divrem(lam_expected, [1, x])
        assert not rem
        omega_expected = add(omega_expected, scale(q, mul(x, e)))
    assert len(omega_expected)-1 < len(positions)
    key_lhs = trim(prod(synd, lam_expected)[:N_SYNDROMES])
    assert key_lhs == omega_expected, 'key equation check failed'
    trace, t, r = eea_trace(synd)
    assert t and t[0] != 0, 'unexpected EEA normalization failure'
    factor = div(1, t[0])
    lam = scale(t, factor)
    omega = scale(r, factor)
    assert lam == lam_expected, 'EEA locator differs from constructed locator'
    assert omega == omega_expected, 'EEA evaluator differs from constructed evaluator'
    # Independently decode the *positions and magnitudes* from (lambda,omega).
    recovered = [p for p in range(FIELD_ORDER) if evalp(lam, EXP[(FIELD_ORDER-p)%FIELD_ORDER]) == 0]
    assert recovered == sorted(positions), 'independent locator root scan failed'
    derivative = trim([lam[j] if j % 2 else 0 for j in range(1,len(lam))])
    magnitudes = {}
    for p in recovered:
        inv_x = EXP[(FIELD_ORDER-p) % FIELD_ORDER]
        denom = evalp(derivative, inv_x)
        assert denom != 0, 'repeated root in locator'
        magnitudes[p] = div(evalp(omega, inv_x), denom)
    assert magnitudes == dict(zip(positions, values)), 'independent Forney magnitudes differ'
    high_jumps = [x for x in trace if x['degree_drop_divisor_to_remainder']>=3]
    return {
        'source': path.name,
        'fixture_sha256': hashlib.sha256(source).hexdigest(),
        'field_poly': hex(MOD),
        'error_weight': len(positions),
        'syndrome_words': len(synd),
        'syndrome_wrong_bits': sum((x^y).bit_count() for x,y in zip(synd,actual)) if actual is not None else None,
        'wrong_words': sum(x!=y for x,y in zip(synd,actual)) if actual is not None else None,
        'reference_syndrome_match': True,
        'independent_position_recovery': True,
        'independent_magnitude_recovery': True,
        'locator_degree': len(lam)-1,
        'evaluator_degree': len(omega)-1,
        'eea_iterations': len(trace),
        'stop_degree': len(r)-1,
        'last_transition': trace[-1],
        'degree_jumps_ge_3': high_jumps,
        'confluent_residual': classify_syndrome_residual(synd, actual),
        'trace': trace,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument('fixtures', nargs='+', type=Path)
    p.add_argument('--out', type=Path)
    p.add_argument('--corpus', type=Path, help='optional saved 64-shot legal-input corpus')
    args=p.parse_args()
    results=[]
    for f in args.fixtures:
        r=analyze_fixture(f)
        results.append(r)
        print(json.dumps({k:v for k,v in r.items() if k!='trace'}, ensure_ascii=False))
    controls = None
    if args.corpus is not None:
        with np.load(args.corpus, allow_pickle=False) as z:
            weights = list(map(int, z['weights']))
            syndromes = z['syndromes']
        counts={}
        details=[]
        for i,(weight,synd) in enumerate(zip(weights,syndromes)):
            trace,loc,om=eea_trace(list(map(int,synd)))
            assert len(loc)-1 == weight
            last=trace[-1]
            drop=last['degree_drop_divisor_to_remainder']
            counts[str(weight)]=counts.get(str(weight),0)+1
            details.append({'index':i,'weight':weight,'last_degree_from':last['divisor_degree'],
                            'last_degree_to':last['next_remainder_degree'],
                            'last_degree_drop':drop,'matches_71_minus_2w':drop==71-2*weight})
        controls={'corpus_sha256':hashlib.sha256(args.corpus.read_bytes()).hexdigest(),
                  'samples':len(details), 'weight_counts':counts,
                  'degree_formula_matched':sum(x['matches_71_minus_2w'] for x in details),
                  'weight33_same_37_to_32_indices':[x['index'] for x in details if x['weight']==33 and x['last_degree_from']==37 and x['last_degree_to']==32],
                  'degree_jumps_ge_3':sum(x['last_degree_drop']>=3 for x in details),
                  'details':details}
        print(json.dumps({'controls_summary':{k:v for k,v in controls.items() if k!='details'}}, ensure_ascii=False))
    if args.out:
        args.out.write_text(json.dumps({'results':results,'controls':controls,'status':'INDEPENDENT_CLASSICAL_REFERENCE_ONLY','native_first_divergence_identified':False}, indent=2, ensure_ascii=False)+'\n')

if __name__=='__main__':
    main()
