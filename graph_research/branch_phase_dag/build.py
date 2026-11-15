#!/usr/bin/env python3
"""Outcome-adaptive phase erasure with dependency-closed monomial DAGs.
Replaces one pinned invsqrt cleanup block. Never changes the verifier.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

BASE = [45, 8, 34, 10, 42, 21]
GARBAGE = [29, 28, 37, 41, 32]
WORK = [9, 29, 35, 28, 33, 37, 31, 41]
FUNCTIONS = [0x0003fe01f81e1c73, 0x0f0f18cf8266d8a4, 0x326d2a52b23c7b58,
             0xffffffc001fe0787, 0x00ff07c18e224a09]
ONE = (1 << 64) - 1
SOURCE_SHA = 'd431f212c7da02418429c2883dcdf4e3a90c9124ab2409c999efe0a5c7c037a8'
CANDIDATE_SHA = 'e7776e39fb567a750cbaf9b24665ed6b487419468f944b6bdb5256ee9c5c6248'
START, STOP = 22172, 22402

def bits(j: int) -> int:
    return sum(((x >> j) & 1) << x for x in range(64))

def solve(columns: list[int], target: int) -> int:
    basis = {}
    for i, value in enumerate(columns):
        mask = 1 << i
        while value:
            pivot = value.bit_length() - 1
            if pivot in basis:
                old, expr = basis[pivot]; value ^= old; mask ^= expr
            else:
                basis[pivot] = value, mask; break
    answer = 0
    while target:
        pivot = target.bit_length() - 1
        if pivot not in basis:
            raise ValueError('Target phase not in generated quadratic span')
        old, expr = basis[pivot]; target ^= old; answer ^= expr
    return answer

def basis_network(forms: list[int]) -> tuple[list[str], list[str]]:
    rows = forms.copy(); reduce = []
    if len(rows) != 6 or any(not 0 < r < 64 for r in rows):
        raise ValueError('Expected six nonzero six-bit linear forms')
    for k in range(6):
        pivot = next((j for j in range(k, 6) if rows[j] >> k & 1), None)
        if pivot is None:
            raise ValueError('Singular change of basis')
        if pivot != k:
            rows[k], rows[pivot] = rows[pivot], rows[k]
            reduce.append(f'SWAP q{BASE[pivot]} q{BASE[k]}')
        for j in range(6):
            if j != k and rows[j] >> k & 1:
                rows[j] ^= rows[k]; reduce.append(f'CX q{BASE[k]} q{BASE[j]}')
    assert rows == [1 << j for j in range(6)]
    return reduce[::-1], reduce

def branch(target: int, forms: list[int], mask: int) -> list[str]:
    if not 0 <= mask < 256 or (mask & 8 and not mask & 7) or (mask & 128 and not mask & 112):
        raise ValueError('Selected bank must be dependency-closed')
    forward, reverse = basis_network(forms)
    linear = []
    for row in forms:
        value = 0
        for j in range(6):
            if row >> j & 1: value ^= bits(j)
        linear.append(value)
    monomials = []
    for offset in (0, 3):
        a, b, c = linear[offset:offset+3]
        monomials += [a & b, a & c, b & c, a & b & c]
    out = forward.copy(); nodes = []; wires = BASE.copy(); values = linear.copy()
    for j in range(8):
        if not mask >> j & 1: continue
        side, kind = divmod(j, 4); group = BASE[3*side:3*side+3]
        if kind < 3:
            a, b = [(0, 1), (0, 2), (1, 2)][kind]; u, v = group[a], group[b]
        else:
            pair = next(p for p in range(3) if mask >> (4*side+p) & 1)
            u, v = WORK[4*side+pair], group[[2, 1, 0][pair]]
        q = WORK[j]
        assert len({u, v, q}) == 3
        nodes.append((u, v, q)); out.append(f'CCX q{u} q{v} q{q}')
        wires.append(q); values.append(monomials[j])
    columns = [ONE]; labels = ['NEG']
    for i, (q, value) in enumerate(zip(wires, values)):
        columns.append(value); labels.append(f'Z q{q}')
        for r, other in zip(wires[:i], values[:i]):
            columns.append(value & other); labels.append(f'CZ q{r} q{q}')
    expression = solve(columns, target)
    out += [label for j, label in enumerate(labels) if expression >> j & 1]
    for u, v, q in reversed(nodes):
        out += [f'HMR q{q} b406', f'CZ q{u} q{v} if b406']
    return out + reverse

def verify_branch(lines: list[str], target: int) -> None:
    """All 64 quantum assignments and all formal inner measurement outcomes."""
    state = [0]*46
    for j, q in enumerate(BASE): state[q] = bits(j)
    phase = target; debt = 0
    for line in lines:
        p = line.split(); op = p[0]; q = [int(s[1:]) for s in p if s.startswith('q')]
        if op == 'CX': state[q[1]] ^= state[q[0]]
        elif op == 'CCX': state[q[2]] ^= state[q[0]] & state[q[1]]
        elif op == 'SWAP': state[q[0]], state[q[1]] = state[q[1]], state[q[0]]
        elif op == 'HMR':
            assert debt == 0; debt = state[q[0]]; state[q[0]] = 0
        elif op in ('NEG', 'Z', 'CZ'):
            value = ONE
            for a in q: value &= state[a]
            if 'if' in p: debt ^= value
            else: phase ^= value
        else: raise ValueError(op)
    assert debt == phase == 0
    for q in range(46):
        assert state[q] == (bits(BASE.index(q)) if q in BASE else 0)

def compile_block(plans: dict) -> tuple[list[str], list[int]]:
    out = [f'HMR q{q} b{401+j}' for j, q in enumerate(GARBAGE)]
    for j in range(5): out += [f'BIT_STORE1 b{407+j}', f'BIT_INVERT b{407+j} if b{401+j}']
    costs = [0]
    for outcome in range(1, 32):
        plan = plans[str(outcome)]; target = 0
        for j, f in enumerate(FUNCTIONS):
            if outcome >> j & 1: target ^= f
        lines = branch(target, plan['forms'], plan['mask'])
        verify_branch(lines, target)
        cost = sum(line.startswith('CCX ') for line in lines)
        assert cost == plan['cost']; costs.append(cost)
        out += [f'PUSH_CONDITION if b{401+j if outcome >> j & 1 else 407+j}' for j in range(5)]
        out += lines + ['POP_CONDITION']*5
    out.append('HMR q32 b49')
    return out, costs

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--plans', type=Path, default=Path(__file__).with_name('plans.json'))
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--native', action='store_true')
    a = p.parse_args()
    raw = a.source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA: raise ValueError('Source hash mismatch')
    lines = raw.decode().splitlines(); metadata = lines[:23]; body = lines[23:]
    assert len(body) == 23881 and body[START] == 'CCX q8 q34 q9'
    assert body[STOP] == 'CX q12 q40'
    block, costs = compile_block(json.loads(a.plans.read_text())['plans'])
    assembled = '\n'.join(metadata + body[:START] + block + body[STOP:]) + '\n'
    kmx = a.out.with_suffix('.kmx')
    if kmx.exists(): raise FileExistsError(kmx)
    kmx.parent.mkdir(parents=True, exist_ok=True); kmx.write_text(assembled)
    receipt = {'source_kmx_sha256':SOURCE_SHA, 'block_mean_ccx':sum(costs)/32,
               'old_score20_block_mean_ccx':6.453125, 'additional_expected_ccx_saved':6.453125-sum(costs)/32,
               'full_expected_ccx':1478.75-8+sum(costs)/32, 'branch_ccx':costs,
               'qubits':46, 'formal_branch_phase_proof':'PASS', 'official_verifier_run':False}
    if a.native:
        import kickmix as km
        circuit = km.Circuit.from_file(kmx, format='kmx')
        kmb = a.out.with_suffix('.kmb')
        if kmb.exists(): raise FileExistsError(kmb)
        circuit.to_file(kmb, format='kmb')
        digest = hashlib.sha256(kmb.read_bytes()).hexdigest()
        assert digest == CANDIDATE_SHA, digest
        assert circuit.num_qubits == 46
        receipt.update(candidate_sha256=digest, num_ops=len(circuit), static_toffoli=circuit.operation_statistics().num_toffoli_like)
    a.out.with_suffix('.build.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt, indent=2))

if __name__ == '__main__': main()
