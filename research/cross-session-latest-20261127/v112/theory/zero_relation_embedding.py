#!/usr/bin/env python3
"""Find simultaneous hidden-bit embeddings in quadratic zero relations.

Input: n variables, relations as ANF monomial bit masks, and optional linear
constraints on permitted translation directions. The caller must separately
prove that every relation vanishes at the actual circuit boundary.

For relations r_i and directions v_j, the checker proves the polynomial laws
    r_i(y + sum_j v_j f_j) = r_i(y) + f_i.
Thus, when r_i(y)=0, all f_i can be measured out after their CNOT translations,
with phase correction sum_i m_i r_i(y'). This is only an encoding law;
transport and decoding at later circuit boundaries remain separate obligations.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

def parity(x): return x.bit_count() & 1

def evaluate(p,x):
    return sum((x&m)==m for m in p)&1

def polar_rows(p,n):
    rows=[0]*n
    for m in p:
        assert m.bit_count()<=2 and m>>n==0
        if m.bit_count()==2:
            a=m&-m;b=m^a
            rows[a.bit_length()-1]^=b;rows[b.bit_length()-1]^=a
    return rows

def solve(equations,rhs,n):
    piv={}
    for row,b in zip(equations,rhs):
        while row:
            k=row.bit_length()-1
            if k not in piv:
                piv[k]=(row,b);break
            a,c=piv[k];row^=a;b^=c
        if not row and b: return None
    x=0
    for k,(row,b) in sorted(piv.items()):
        if parity(row&x)^b: x|=1<<k
    assert all(parity(row&x)==b for row,b in zip(equations,rhs))
    return x

def nullspace(rows,n):
    piv={}
    for row in rows:
        while row:
            k=row.bit_length()-1
            if k not in piv:piv[k]=row;break
            row^=piv[k]
    basis=[]
    for free in range(n):
        if free in piv:continue
        x=1<<free
        for k,row in sorted(piv.items()):
            if parity(row&x):x^=1<<k
        assert all(parity(row&x)==0 for row in rows)
        basis.append(x)
    return basis

def derivative_check(polynomials,directions,n):
    for i,p in enumerate(polynomials):
        rows=polar_rows(p,n)
        for j,v in enumerate(directions):
            assert all(parity(row&v)==0 for row in rows)
            assert evaluate(p,v)^evaluate(p,0)==int(i==j)
    # Each direction is in every polar radical; hence all cross terms also
    # vanish, and the first derivatives compose for arbitrary hidden bits.
    return True

def discover(n,polynomials,constraints=()):
    polynomials=[set(p) for p in polynomials]
    rows=list(constraints)
    for p in polynomials:rows+=polar_rows(p,n)
    radical=nullspace(rows,n);d=len(radical)
    linear=[]
    for p in polynomials:
        linear.append(sum((evaluate(p,v)^evaluate(p,0))<<i for i,v in enumerate(radical)))
    directions=[]
    for j in range(len(polynomials)):
        coefficients=solve(linear,[int(i==j) for i in range(len(polynomials))],d)
        if coefficients is None:
            return dict(status='NO_SIMULTANEOUS_EMBEDDING_IN_THIS_COMMON_RADICAL',
                        variables=n,relations=len(polynomials),radical_dimension=d)
        v=0
        for i,b in enumerate(radical):
            if coefficients>>i&1:v^=b
        directions.append(v)
    assert derivative_check(polynomials,directions,n)
    return dict(status='EXACT_QUADRATIC_TRANSLATION_LAW_PASS',variables=n,
                relations=len(polynomials),radical_dimension=d,
                directions=directions,direction_wires=[[i for i in range(n) if v>>i&1] for v in directions],
                scope='Symbolic derivative law only. Boundary zero identities, endpoint decoders, measurement lifetimes, and global width are not supplied by this check.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input',type=Path);p.add_argument('--out',type=Path)
    a=p.parse_args();d=json.loads(a.input.read_text());r=discover(d['variables'],d['relations'],d.get('direction_constraints',[]))
    if a.out:a.out.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps(r))