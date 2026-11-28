#!/usr/bin/env python3
"""Reversible X/CX/CCX oracle lowerer for exact quadratic XAG networks.

Inputs may be temporarily changed by invertible CX basis transforms but are
restored after each AND. Scratch is uncomputed by reversing the AND compute.
Every gate is phase-free on the computational basis, so all branches have
exactly zero introduced phase. This is NOT a KickMix .kmb encoder.
"""
from __future__ import annotations
from dataclasses import dataclass
from solver import parity,basis


@dataclass(frozen=True)
class Gate:
    op:str
    args:tuple[int,...]


class CleanOracle:
    def __init__(self, n, m, k, gates):
        self.n,self.m,self.k,self.gates=n,m,k,gates

    @property
    def width(self):return self.n+self.m+self.k

    def evaluate(self, x, y=0):
        wires=[(x>>i)&1 for i in range(self.n)]
        wires += [(y>>i)&1 for i in range(self.m)]
        wires += [0]*self.k
        for gate in self.gates:
            if gate.op=="X":
                wires[gate.args[0]]^=1
            elif gate.op=="CX":
                a,b=gate.args
                wires[b]^=wires[a]
            elif gate.op=="CCX":
                a,b,c=gate.args
                wires[c]^=wires[a]&wires[b]
            else:raise ValueError(gate.op)
        rx=sum(v<<i for i,v in enumerate(wires[:self.n]))
        ry=sum(v<<i for i,v in enumerate(wires[self.n:self.n+self.m]))
        dirty=sum(v<<i for i,v in enumerate(wires[self.n+self.m:]))
        return rx,ry,dirty

    def resource_count(self):
        from collections import Counter
        c=Counter(g.op for g in self.gates)
        return dict(c,logical_qubits=self.width,total_ops=len(self.gates),
                    paid_Toffolis=c["CCX"])


def full_basis(l,r,n):
    assert l and r and l!=r
    xs=[l,r]
    for i in range(n):
        if len(basis(xs+[1<<i]))>len(xs):xs.append(1<<i)
        if len(xs)==n:break
    assert len(xs)==n
    return xs


def linear_map_ops(matrix):
    """Create a CNOT circuit for the invertible row map x -> matrix*x."""
    A=matrix.copy()
    n=len(A)
    reduction=[]
    for col in range(n):
        pivot=next(i for i in range(col,n) if (A[i]>>col)&1)
        if pivot!=col:
            A[col]^=A[pivot];reduction.append(Gate("CX",(pivot,col)))
            A[pivot]^=A[col];reduction.append(Gate("CX",(col,pivot)))
            A[col]^=A[pivot];reduction.append(Gate("CX",(pivot,col)))
        for row in range(n):
            if row!=col and ((A[row]>>col)&1):
                A[row]^=A[col]
                reduction.append(Gate("CX",(col,row)))
    assert A==[1<<i for i in range(n)]
    return list(reversed(reduction))


def compile_oracle(solution):
    n=solution.n
    m=len(solution.truth_tables)
    k=len(solution.products)
    gates=[];transformations=[]
    for i,(left,right) in enumerate(solution.products):
        ops=linear_map_ops(full_basis(left,right,n))
        gates.extend(ops)
        gates.append(Gate("CCX",(0,1,n+m+i)))
        gates.extend(reversed(ops))
        transformations.append(ops)
    for o,(code,affine) in enumerate(zip(solution.output_products,solution.output_affine)):
        target=n+o
        if (affine>>n)&1:gates.append(Gate("X",(target,)))
        for i in range(n):
            if (affine>>i)&1:gates.append(Gate("CX",(i,target)))
        for j in range(k):
            if (code>>j)&1:gates.append(Gate("CX",(n+m+j,target)))
    for i in reversed(range(k)):
        ops=transformations[i]
        gates.extend(ops)
        gates.append(Gate("CCX",(0,1,n+m+i)))
        gates.extend(reversed(ops))
    return CleanOracle(n,m,k,gates)


def verify_clean_xor(solution,all_y=True):
    oracle=compile_oracle(solution)
    for x in range(1<<solution.n):
        desired=sum(v<<i for i,v in enumerate(solution.evaluate(x)))
        ys=range(1<<len(solution.truth_tables)) if all_y else (0,)
        for y in ys:
            rx,ry,dirty=oracle.evaluate(x,y)
            if (rx,ry,dirty)!=(x,y^desired,0):
                return False
    return True
