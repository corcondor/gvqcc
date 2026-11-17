#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Independent zero-safe polynomial extraction oracle for DQI over GF(4096).

Diagnostic/reference only; NOT a quantum circuit optimization or Kickmix repair.
A public *set* of distinct irreducible quadratics is required.  If a current
numerator residue is zero at the next public quadratic, use a different
remaining public quadratic rather than taking an inverse of zero.  The exact
pivot order is recorded and replayed backwards, including non-final zeros.

Inputs are coefficient lists in increasing degree (x^0, x^1, ...).
Coefficient field: GF(2)[z]/(z^12+z^6+z^4+z+1).
Public quadratics: x^2+x+kappa for kappa with absolute trace 1.
"""
from dataclasses import dataclass
from typing import Sequence

P = 0x1053
MASK = 0xFFF


def gmul(a: int, b: int) -> int:
    assert 0 <= a <= MASK and 0 <= b <= MASK
    v = 0
    for _ in range(12):
        if b & 1: v ^= a
        b >>= 1
        a <<= 1
        if a & (1 << 12): a ^= P
    return v & MASK


def gpow(a: int, n: int) -> int:
    r = 1
    while n:
        if n & 1: r = gmul(r, a)
        a = gmul(a, a)
        n >>= 1
    return r


def ginv(a: int) -> int:
    if not a: raise ZeroDivisionError('GF(4096): inverse of zero')
    return gpow(a, 4094)


def absolute_trace(a: int) -> int:
    out = 0
    for _ in range(12):
        out ^= a
        a = gmul(a, a)
    assert out in (0, 1)
    return out


def norm_inv_quadratic(uv: Sequence[int], k: int) -> tuple[int, int]:
    """Inverse of u+vx modulo x^2+x+k (assuming absolute trace(k)=1)."""
    u, v = (list(uv) + [0, 0])[:2]
    norm = gmul(u, u) ^ gmul(u, v) ^ gmul(k, gmul(v, v))
    z = ginv(norm)
    return gmul(u ^ v, z), gmul(v, z)


def qmul(a: Sequence[int], b: Sequence[int], k: int) -> tuple[int, int]:
    a0, a1 = (list(a) + [0, 0])[:2]
    b0, b1 = (list(b) + [0, 0])[:2]
    vv = gmul(a1, b1)
    return gmul(a0, b0) ^ gmul(k, vv), gmul(a0, b1) ^ gmul(a1, b0) ^ vv


def trim(p: Sequence[int]) -> list[int]:
    p = list(p)
    while p and p[-1] == 0: p.pop()
    return p


def add(a: Sequence[int], b: Sequence[int]) -> list[int]:
    p = [0] * max(len(a), len(b))
    for i, v in enumerate(a): p[i] ^= v
    for i, v in enumerate(b): p[i] ^= v
    return trim(p)


def pmul(a: Sequence[int], b: Sequence[int]) -> list[int]:
    if not a or not b: return []
    out = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b): out[i + j] ^= gmul(x, y)
    return trim(out)


def divrem(p: Sequence[int], divisor: Sequence[int]) -> tuple[list[int], list[int]]:
    p, divisor = trim(p), trim(divisor)
    if not divisor: raise ZeroDivisionError('Zero divisor polynomial')
    quotient = [0] * max(0, len(p) - len(divisor) + 1)
    denom_inv = ginv(divisor[-1])
    while len(p) >= len(divisor):
        shift = len(p) - len(divisor)
        factor = gmul(p[-1], denom_inv)
        quotient[shift] = factor
        for i, v in enumerate(divisor): p[i + shift] ^= gmul(factor, v)
        p = trim(p)
    return trim(quotient), p


def qrem(p: Sequence[int], k: int) -> tuple[int, int]:
    rem = divrem(p, [k, 1, 1])[1]
    return (rem + [0, 0])[:2][0], (rem + [0, 0])[:2][1]


@dataclass(frozen=True)
class Step:
    index: int                  # index in original *public* list of quadratics
    kappa: int
    head: tuple[int, int]      # inverse-reconstruction head


@dataclass
class Extraction:
    numerator: list[int]
    denominator: list[int]
    steps: list[Step]
    remaining_indices: list[int]
    skipped_initial_zeros: int

    def reverse(self) -> tuple[list[int], list[int]]:
        n, d = self.numerator[:], self.denominator[:]
        for step in reversed(self.steps):
            n, d = d, add(pmul([step.kappa, 1, 1], n), pmul(step.head, d))
        return n, d


def step(n: Sequence[int], d: Sequence[int], k: int) -> tuple[list[int], list[int], tuple[int, int]]:
    rn, rd = qrem(n, k), qrem(d, k)
    if rn == (0, 0):
        raise ZeroDivisionError('Non-terminal zero numerator residue')
    h = qmul(rd, norm_inv_quadratic(rn, k), k)
    nn, remainder = divrem(add(d, pmul(h, n)), [k, 1, 1])
    assert not remainder, 'Polynomial-division invariant failed'
    return nn, trim(n), h


def extract_zero_safe(n: Sequence[int], d: Sequence[int], kappas: Sequence[int]) -> Extraction:
    """Exact reference algorithm, choosing first valid *remaining* public pivot.

    This is intentionally NOT a proposed efficient quantum implementation:
    dynamic pivot routing may be prohibitively expensive in a 889-Q design.
    """
    n, d = trim(n), trim(d)
    kappas = list(kappas)
    if len(set(kappas)) != len(kappas):
        raise ValueError('Repeated public quadratic: distinctness proof unavailable')
    if any(absolute_trace(k) != 1 for k in kappas):
        raise ValueError('Some public quadratic is reducible over GF(4096)')
    if len(n) > len(kappas) or len(d) > len(kappas) + 1:
        raise ValueError('Input polynomial degree violates extraction bound')
    original_n, original_d = n[:], d[:]
    available = list(range(len(kappas)))
    record: list[Step] = []
    skipped = 0
    while available:
        if not n:
            if len(d) != 1 or d[0] == 0:
                raise ValueError('Premature zero with nonconstant denominator')
            break    # valid early terminal; no need to consume irrelevant pivots
        chosen = next((i for i in available if qrem(n, kappas[i]) != (0, 0)), None)
        if chosen is None:
            raise ValueError('No nonzero pivot: violated degree/distinctness invariant')
        if chosen != available[0]: skipped += 1
        k = kappas[chosen]
        n, d, head = step(n, d, k)
        record.append(Step(chosen, k, head))
        available.remove(chosen)
        m = len(available)
        assert len(n) <= m and len(d) <= m + 1, 'Degree bound failed'
    assert n == [] and len(d) == 1 and d[0], 'Nonterminal remainder'
    result = Extraction(n, d, record, available, skipped)
    assert result.reverse() == (original_n, original_d), 'Inverse recovery failed'
    return result