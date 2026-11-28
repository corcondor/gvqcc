#!/usr/bin/env python3
"""Exact shared quadratic XAG synthesis and exhaustive Boolean certification.

Independent implementation inspired by Griffith's differentiable LUT approach.
This backend is *not* a generic optimal quantum compiler. It handles output
polynomials of degree <=2 on four Boolean input variables.
"""
from __future__ import annotations
from itertools import combinations
from dataclasses import dataclass, asdict
import argparse
import json


def parity(v):
    return v.bit_count() & 1


def anf(table, n=4):
    c=[(table >> i) & 1 for i in range(1 << n)]
    for i in range(n):
        for x in range(1 << n):
            if x & (1 << i): c[x] ^= c[x ^ (1 << i)]
    qindex={(1 << i) | (1 << j): k for k,(i,j) in enumerate(combinations(range(n),2))}
    linear=q=high=0
    for monomial,value in enumerate(c):
        if not value or not monomial: continue
        degree=monomial.bit_count()
        if degree==1: linear |= monomial
        elif degree==2: q |= 1 << qindex[monomial]
        else: high |= 1 << monomial
    return c[0],linear,q,high


def quadratic_of_product(l,r,n=4):
    q=0
    for k,(i,j) in enumerate(combinations(range(n),2)):
        if ((l>>i&1)&(r>>j&1))^((l>>j&1)&(r>>i&1)):
            q |= 1 << k
    return q


def truth_parity(mask,n=4):
    return sum(parity(mask & x) << x for x in range(1 << n))


def truth_product(l,r,n=4):
    return truth_parity(l,n) & truth_parity(r,n)


def basis(xs):
    piv={}
    for v in xs:
        while v:
            p=v.bit_length()-1
            if p in piv: v ^= piv[p]
            else:
                piv[p]=v
                break
    return piv


def span(xs):
    result=[0]
    for b in basis(xs).values():
        result += [v ^ b for v in result]
    return frozenset(result)


def coords(target,xs):
    p={}
    for i,x in enumerate(xs):
        s=1<<i
        for j in sorted(p,reverse=True):
            if x>>j&1:
                x ^= p[j][0];s ^= p[j][1]
        if x:p[x.bit_length()-1]=(x,s)
    value=target;ret=0
    for j in sorted(p,reverse=True):
        if value>>j&1:
            value ^= p[j][0];ret ^= p[j][1]
    return ret if value==0 else None


def rank2_pool(n=4):
    p={}
    for l in range(1,1<<n):
        for r in range(l+1,1<<n):
            q=quadratic_of_product(l,r,n)
            if q and q not in p:p[q]=(l,r)
    return p


def minimum_quadratic_basis(quad_outputs,n=4):
    """Shortest shared rank-2 basis, by BFS over finite subspaces of GF(2)^6."""
    assert n==4,"this exhaustive basis solver is limited to four input bits"
    pool=rank2_pool(n); candidates=sorted(pool)
    initial=span(quad_outputs)
    queue=[initial];seen={initial}
    for s in queue:
        r=(len(s)).bit_length()-1
        good=[x for x in candidates if x in s]
        if len(basis(good))==r:
            chosen=[]
            for q in good:
                if len(basis(chosen+[q]))>len(chosen):chosen.append(q)
            assert len(chosen)==r
            return chosen,pool,len(seen)
        for q in candidates:
            if q in s:continue
            t=span([*s,q])
            if t not in seen:
                seen.add(t);queue.append(t)
    raise AssertionError("ambient space spans all quadratics; search must terminate")


@dataclass
class Solution:
    n:int
    products:list
    output_products:list
    output_affine:list
    truth_tables:list
    visited_spaces:int

    def evaluate(self,x):
        prod=[parity(l&x)&parity(r&x) for l,r in self.products]
        out=[]
        for code,af in zip(self.output_products,self.output_affine):
            y=parity(x&(af&((1<<self.n)-1)))^((af>>self.n)&1)
            for i,p in enumerate(prod):
                if code>>i&1:y^=p
            out.append(y)
        return out

    def verify(self):
        return all(
            self.evaluate(x)==[((table>>x)&1) for table in self.truth_tables]
            for x in range(1<<self.n)
        )

    def cost(self):
        qmons=set()
        for t in self.truth_tables:
            _,_,q,_=anf(t,self.n)
            qmons.update(i for i in range(self.n*(self.n-1)//2) if q>>i&1)
        return {"naive_shared_ANF_AND":len(qmons),
                "qdln_AND":len(self.products),
                "clean_oracle_CCX":2*len(self.products),
                "peak_qubits":self.n+len(self.truth_tables)+len(self.products),
                "verified":self.verify()}


def synthesize(tables,n=4):
    tables=list(map(int,tables))
    if any(anf(t,n)[3] for t in tables):
        raise ValueError("high-degree targets are outside this exact quadratic backend")
    quads=[anf(t,n)[2] for t in tables]
    selected,pool,visited=minimum_quadratic_basis(quads,n)
    products=[pool[q] for q in selected]
    op=[];aff=[]
    for target,q in zip(tables,quads):
        coeff=coords(q,selected)
        assert coeff is not None
        pred=0
        for i,(l,r) in enumerate(products):
            if coeff>>i&1:pred ^= truth_product(l,r,n)
        c,a,quadratic,higher=anf(target^pred,n)
        assert quadratic==higher==0
        op.append(coeff)
        aff.append(a|(c<<n))
    sol=Solution(n,products,op,aff,tables,visited)
    assert sol.verify()
    return sol


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--truths",required=True,help="JSON list of 16-bit output truth tables")
    args=p.parse_args()
    sol=synthesize(json.loads(args.truths))
    print(json.dumps({"solution":asdict(sol),"cost":sol.cost()},indent=2))


if __name__=="__main__": main()
