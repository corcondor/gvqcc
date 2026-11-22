"""Exact affine-XOR/AND networks and reversible KickMix oracle emission.

Original interoperability code inspired by the Griffith differentiable-logic
project, not a copy of the Griffith implementation. SPDX-License-Identifier:
Apache-2.0.

The target map is (x, z) -> (x, z XOR f(x)). Temporary products are removed
using HMR followed by conditional CZ, preserving phase for every measurement.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


def parity(x: int) -> int:
    return x.bit_count() & 1


@dataclass(frozen=True)
class Affine:
    mask: int
    constant: int = 0

    def eval(self, signals: Sequence[int]) -> int:
        out = self.constant & 1
        mask = self.mask
        while mask:
            j = (mask & -mask).bit_length() - 1
            out ^= int(signals[j])
            mask &= mask - 1
        return out

    def validate(self, n_signals: int) -> None:
        if self.mask < 0 or (self.mask >> n_signals) or self.constant not in (0, 1):
            raise ValueError(f"invalid affine mask {self} for {n_signals} signals")


@dataclass(frozen=True)
class AndProduct:
    left: Affine
    right: Affine


@dataclass(frozen=True)
class XAG:
    inputs: int
    products: tuple[AndProduct, ...]
    outputs: tuple[Affine, ...]

    def validate(self) -> None:
        if self.inputs < 1 or not self.outputs:
            raise ValueError('need >=1 inputs and outputs')
        for i, gate in enumerate(self.products):
            gate.left.validate(self.inputs + i)
            gate.right.validate(self.inputs + i)
        for out in self.outputs:
            out.validate(self.inputs + len(self.products))

    def eval(self, inputs: Sequence[int]) -> tuple[int, ...]:
        self.validate()
        if len(inputs) != self.inputs or any(a not in (0, 1) for a in inputs):
            raise ValueError('inputs must be bits matching input width')
        values = list(inputs)
        for g in self.products:
            values.append(g.left.eval(values) & g.right.eval(values))
        return tuple(out.eval(values) for out in self.outputs)

    def truth_tables(self) -> tuple[int, ...]:
        if self.inputs > 16:
            raise ValueError('explicit truth tables only for <=16 input bits')
        values = [0] * len(self.outputs)
        for a in range(1 << self.inputs):
            x = tuple((a >> i) & 1 for i in range(self.inputs))
            o = self.eval(x)
            for j, b in enumerate(o):
                values[j] |= b << a
        return tuple(values)

    def assert_exact(self, targets: Sequence[int], *, care_mask: int | None = None) -> dict:
        if len(targets) != len(self.outputs):
            raise ValueError('wrong number of targets')
        if care_mask is None:
            care_mask = (1 << (1 << self.inputs)) - 1
        actual = self.truth_tables()
        failures = [(j, ((a ^ b) & care_mask).bit_count()) for j, (a, b) in enumerate(zip(actual, targets)) if (a ^ b) & care_mask]
        if failures:
            raise AssertionError(f'Boolean output mismatch: {failures[:10]}')
        return {'num_inputs': self.inputs, 'num_outputs': len(self.outputs),
                'verified_input_patterns': care_mask.bit_count(),
                'nonlinear_products': len(self.products), 'mismatch': 0}

    def emit_kmx(self, *, hmr: bool = True) -> str:
        """Export a *new* clean-scratch oracle. Not an in-place KMB patch.

        q0..q(n-1) are untouched input bits; next m qubits are arbitrary XOR
        targets; next k are initially-zero product ancillas; two extra scratch
        qubits are initially zero. HMR outcomes are stored in classical b0.
        """
        self.validate()
        n, m, k = self.inputs, len(self.outputs), len(self.products)
        wires = [i for i in range(n)] + [n + m + i for i in range(k)]
        target = [n + i for i in range(m)]
        tmp = [n + m + k, n + m + k + 1]
        lines = []
        for i in range(n): lines.append(f'APPEND_TO_REGISTER q{i} r0')
        lines.append('REGISTER r0 "selection"')
        for q in target: lines.append(f'APPEND_TO_REGISTER q{q} r1')
        lines.append('REGISTER r1 "target"')
        for q in tmp:lines.append(f'R q{q}')
        for i in range(k):lines.append(f'R q{wires[n+i]}')

        def build_affine(a: Affine, dst: int) -> list[str]:
            result = [f'X q{dst}'] if a.constant else []
            mask = a.mask
            while mask:
                j = (mask & -mask).bit_length() - 1
                result.append(f'CX q{wires[j]} q{dst}')
                mask &= mask-1
            return result

        for i, p in enumerate(self.products):
            ops = build_affine(p.left,tmp[0]) + build_affine(p.right,tmp[1])
            # reverse the affine build to put scratch back to zero
            lines.extend(ops)
            lines.append(f'CCX q{tmp[0]} q{tmp[1]} q{wires[n+i]}')
            lines.extend(reversed(ops))
        for j, a in enumerate(self.outputs):
            lines.extend(build_affine(a, target[j]))
        for i in reversed(range(k)):
            p = self.products[i]
            ops = build_affine(p.left,tmp[0]) + build_affine(p.right,tmp[1])
            lines.extend(ops)
            if hmr:
                lines.append(f'HMR q{wires[n+i]} b0')
                lines.append(f'CZ q{tmp[0]} q{tmp[1]} if b0')
            else:
                lines.append(f'CCX q{tmp[0]} q{tmp[1]} q{wires[n+i]}')
            lines.extend(reversed(ops))
        return '\n'.join(lines) + '\n'

    def resources(self, *, hmr: bool = True) -> dict:
        return {'qubits': self.inputs + len(self.outputs) + len(self.products) + 2,
                'ccx_static': len(self.products) * (1 if hmr else 2),
                'hmr': len(self.products) if hmr else 0,
                'measurement_conditional_cz': len(self.products) if hmr else 0,
                'note': 'component-level only; not an official KickMix score'}


def affine_functions(n: int) -> dict[int, Affine]:
    """All distinct affine Boolean functions on n inputs as packed truth tables."""
    if not 1 <= n <= 6:
        raise ValueError('exhaustive affine basis intended for 1..6 inputs')
    packed = [sum(((a >> j) & 1) << a for a in range(1 << n)) for j in range(n)]
    all_ones = (1 << (1 << n)) - 1
    out = {}
    for mask in range(1 << n):
        val = 0
        for j, p in enumerate(packed):
            if (mask >> j) & 1:
                val ^= p
        out[val] = Affine(mask, 0)
        out[val ^ all_ones] = Affine(mask, 1)
    return out


def synthesize_shared_one_and(targets: Sequence[int], n: int) -> XAG | None:
    """Find an exact *shared* single AND with affine fan-in and affine outputs.

    For n<=6 enumeration is complete within the stated one-product model.
    Covers multiple outputs with a single product and free XOR readouts.
    """
    af = affine_functions(n)
    for ta in targets:
        if ta < 0 or ta >> (1 << n):
            raise ValueError('targets must be packed Boolean truth tables')
    if all(t in af for t in targets):
        return XAG(n, (), tuple(af[t] for t in targets))
    candidates = list(af.items())
    for a_bits, a in candidates:
        if not a_bits: continue
        for b_bits, b in candidates:
            if not b_bits: continue
            p = a_bits & b_bits
            if p in af: continue
            readout = []
            for t in targets:
                if t in af:
                    readout.append(af[t])
                elif (t ^ p) in af:
                    a0 = af[t ^ p]
                    readout.append(Affine(a0.mask | (1 << n), a0.constant))
                else:
                    break
            else:
                ir = XAG(n, (AndProduct(a,b),), tuple(readout))
                ir.assert_exact(targets)
                return ir
    return None


def anf_nonlinear_terms(table: int, n: int) -> int:
    """Number of nonlinear monomials in the unique ANF, not actual AND cost."""
    co = [(table >> i) & 1 for i in range(1 << n)]
    for bit in range(n):
        for m in range(1 << n):
            if m & (1 << bit):
                co[m] ^= co[m ^ (1 << bit)]
    return sum(co[i] for i in range(1 << n) if i.bit_count() >= 2)
