"""Width-aware reversible arithmetic building blocks for GVQCC research.

X/CX/CCX only: no hidden phase, no measurements, no nonzero initial scratch.
Includes a carry-save compressor, a Cuccaro-style reversible modulo adder,
a ternary modulo adder, and exact AND fanout/clean-cache variants.

Algorithmic references: Cuccaro et al. arXiv:quant-ph/0410184,
Google Qualtran https://github.com/quantumlib/Qualtran,
and ETH Reqomp https://github.com/eth-sri/Reqomp.
This module is independently written, not a copy of those libraries.
Not a claimed improvement to any production GVQCC circuit.
"""
from collections import Counter


def cx(a, b):
    assert a != b
    return ("CX", a, b)


def ccx(a, b, t):
    assert len({a, b, t}) == 3
    return ("CCX", a, b, t)


def maj(carry, b, a):
    """Ripple majority: move carry into a, temporarily changing b and carry."""
    return [cx(a, b), cx(a, carry), ccx(carry, b, a)]


def uma(carry, b, a):
    """Reverse majority and write the sum bit to b."""
    return [ccx(carry, b, a), cx(a, carry), cx(carry, b)]


def add_mod(n, a, b, carry):
    """(a,b,0) -> (a,(a+b) modulo 2**n,0); one clean carry qubit.

    2(n-1) CCX and 4n-2 CX for n>1. Inputs a and b are disjoint.
    """
    assert n >= 1 and len(a) == len(b) == n
    assert len(set(a + b + [carry])) == 2*n+1
    if n == 1:
        return [cx(a[0], b[0])]
    out = []
    for i in range(n-1):
        out += maj(carry if i == 0 else a[i-1], b[i], a[i])
    out += [cx(a[n-2], b[n-1]), cx(a[n-1], b[n-1])]
    for i in reversed(range(n-1)):
        out += uma(carry if i == 0 else a[i-1], b[i], a[i])
    return out


def add_three_mod(n):
    """Preserve A,B,C; write (A+B+C) modulo 2**n to clean S; return carry 0.

    Layout: A[0:n], B[0:n], C[0:n], S[0:n], carry at 4*n.
    Q=4n+1, CCX=4(n-1); unlike CSA the result is one binary word.
    """
    assert n >= 1
    regs = {name:list(range(j*n, (j+1)*n))
            for j,name in enumerate(("A","B","C","S"))}
    carry = 4*n
    out = [cx(regs["A"][i], regs["S"][i]) for i in range(n)]
    out += add_mod(n, regs["B"], regs["S"], carry)
    out += add_mod(n, regs["C"], regs["S"], carry)
    regs["carry"] = [carry]
    return out, regs


def csa_three(n):
    """3:2 bitwise compression: S+2*K=A+B+C, preserving all inputs.

    Layout: A,B,C,S,K, each n bits. S,K must start at zero.
    Q=5n, CCX=2n, CX=3n. NOT a completed carry-propagated sum.
    """
    assert n >= 1
    regs = {name:list(range(j*n, (j+1)*n))
            for j,name in enumerate(("A","B","C","S","K"))}
    ops=[]
    for i in range(n):
        a,b,c,s,k=(regs[name][i] for name in ("A","B","C","S","K"))
        ops += [cx(a,s),cx(b,s),ccx(a,b,k),ccx(s,c,k),cx(c,s)]
    return ops,regs


def and_fanout(a,b,targets):
    """XOR AND(a,b) into dirty targets, one CCX, no scratch; contiguous use."""
    assert targets and len(set([a,b]+targets)) == len(targets)+2
    one=[cx(targets[0],t) for t in targets[1:]]
    return one+[ccx(a,b,targets[0])]+list(reversed(one))


def and_clean_cache(a,b,clean,targets):
    """Hold product over later targets, using one clean ancilla, restored to 0."""
    assert len(set([a,b,clean]+targets)) == len(targets)+3
    return [ccx(a,b,clean)]+[cx(clean,t) for t in targets]+[ccx(a,b,clean)]


def simulate(ops,bits):
    """Exact classical permutation; CX/CCX have no phase for any basis input."""
    bits=list(bits)
    for op in ops:
        if op[0]=="CX":
            _,a,t=op
            bits[t] ^= bits[a]
        elif op[0]=="CCX":
            _,a,b,t=op
            bits[t] ^= bits[a] & bits[b]
        else:
            raise ValueError(op)
    return bits


def costs(ops,regs):
    c=Counter(op[0] for op in ops)
    return {"qubits":max(max(qs) for qs in regs.values())+1,
            "CCX":c["CCX"],"CX":c["CX"],"T_equivalent":c["CCX"]}


def kmx_text(ops):
    return "\n".join(" ".join([op[0],*(f"q{q}" for q in op[1:])])
                     for op in ops)+"\n"
