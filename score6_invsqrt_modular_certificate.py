#!/usr/bin/env python3
"""An exact, finite certificate for the fixed invsqrt phase feature lattice.

If every unchanged feature is assigned a new real angle, equivalence modulo
one turn forces each angle change to be an integer turn.  The certificate
does not cover new Boolean features or approximate fitting.
"""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import time

import sympy as S
import score_invsqrt_retire as R
from score6_invsqrt_joint_phase import PIN


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def replay_small(lines, xs):
    """Independent truth-table replay on just the published witness inputs."""
    rows = []
    for x in xs:
        q = [(x >> j) & 1 for j in range(22)] + [0]*24
        saved, row = [], [1]
        for line in lines:
            op = line.split()[0]
            wires = tuple(map(int, re.findall(r'\bq(\d+)\b', line)))
            if ' if ' in line:
                assert op in ('PUSH_CONDITION', 'CZ', 'BIT_INVERT', 'NEG')
            if op == 'Z_POW':
                assert not saved
                row.append(q[wires[0]])
            elif op == 'X':
                q[wires[0]] ^= 1
            elif op == 'CX':
                a, t = wires; q[t] ^= q[a]
            elif op == 'CCX':
                a, b, t = wires; q[t] ^= q[a] & q[b]
            elif op == 'CSWAP':
                c, a, b = wires
                if q[c]:
                    q[a], q[b] = q[b], q[a]
            elif op == 'SWAP':
                a, b = wires; q[a], q[b] = q[b], q[a]
            elif op == 'HMR':
                q[wires[0]] = 0
            elif op == 'PUSH_CONDITION':
                saved.append(q[:])
            elif op == 'POP_CONDITION':
                before = saved.pop()
                assert before == q
                q = before
        assert not saved
        assert q[:22] == [(x >> j) & 1 for j in range(22)]
        assert not any(q[22:])
        rows.append(row)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    began = time.monotonic()
    source = Path(__file__).parent/'score3_invsqrt_cache.kmx'
    assert sha(source) == PIN
    lines, ops = R.instructions(source)
    domain, values = R.initial_values()
    stack, columns, features = [], [domain], []
    conditional_blocks = 0
    for i, ((op, qs), line) in enumerate(zip(ops, lines)):
        if ' if ' in line:
            assert op in ('PUSH_CONDITION', 'CZ', 'BIT_INVERT', 'NEG')
        if op == 'Z_POW':
            assert not stack and ' if ' not in line
            angle = Fraction(line.split()[2])
            kind = ('clifford' if angle % Fraction(1, 2) == 0 else
                    't' if angle % Fraction(1, 4) == 0 else 'rotation')
            columns.append(values[qs[0]])
            features.append(dict(line=i+1, qubit=qs[0], half_turns=str(angle),
                                 kind=kind, support=values[qs[0]].bit_count()))
        if op == 'PUSH_CONDITION':
            stack.append(values[:]); conditional_blocks += 1
        elif op == 'POP_CONDITION':
            before = stack.pop()
            # Therefore either branch leaves all later Z_POW predicates
            # unchanged, on every legal input, independent of HMR bits.
            assert before == values
            values = before
        else:
            R.advance(op, qs, values, domain)
    assert not stack and len(columns) == 39
    xs = sorted(R.affine_basis(columns))
    assert len(xs) == 39 and all(1 <= x <= R.MAX_X for x in xs)
    rows = [[(f >> x) & 1 for f in columns] for x in xs]
    M = S.Matrix(rows)
    det = int(M.det())
    assert det == -3
    extra_x, replace_row = 2, 33
    assert extra_x not in xs
    extra = [(f >> extra_x) & 1 for f in columns]
    second_rows = [r[:] for r in rows]
    second_rows[replace_row] = extra
    N = S.Matrix(second_rows)
    det2 = int(N.det())
    assert det2 == -2
    all_xs, all_rows = xs + [extra_x], rows + [extra]
    assert replay_small(lines, all_xs) == all_rows
    adj_m = M.inv()*det
    adj_n = N.inv()*det2
    assert all(v.q == 1 for v in adj_m) and all(v.q == 1 for v in adj_n)
    # (-1)*(-3) + (1)*(-2) = 1.  Embed both adjugates into the
    # same 40-row evaluation table to give an explicit integer left inverse.
    B = S.zeros(39, 40)
    for i in range(39):
        for j in range(39):
            B[i, j] -= adj_m[i, j]
            B[i, 39 if j == replace_row else j] += adj_n[i, j]
    assert B*S.Matrix(all_rows) == S.eye(39)
    report = dict(
        status='PASS_EXACT_FIXED_FEATURE_MODULAR_CERTIFICATE',
        source_path=str(source), source_sha256=PIN,
        script_sha256=sha(__file__), legal_inputs=R.MAX_X,
        phase_unit='turn (2*pi radians)', coefficient_unit='turn',
        fixed_feature_count=38, includes_constant=True,
        classes=dict(Counter(f['kind'] for f in features)), features=features,
        conditional_quantum_identity_blocks_checked_full_domain=conditional_blocks,
        witness_input_count=len(all_xs), witness_xs=all_xs,
        evaluation_rows=all_rows, first_minor_rows=list(range(39)),
        second_minor_rows=[39 if j == replace_row else j for j in range(39)],
        determinants=[det, det2], bezout_coefficients=[-1, 1],
        integer_left_inverse=[[int(B[i, j]) for j in range(40)] for i in range(39)],
        left_inverse_times_evaluation='identity_39',
        independent_scalar_replay='PASS',
        theorem='For every real delta in R^39, if the fixed-feature phase '
                'difference is integer turns on every legal input, then delta '
                'is an integer vector. The 40 witness rows alone suffice.',
        proof='For witness evaluation A and published integer B, BA=I. '
              'If A*delta is integer, delta=B*(A*delta) is integer.',
        scope='Only coefficient changes on these same 38 Boolean Z_POW '
              'features plus a constant phase. No lower bound for circuits '
              'using new features, changed arithmetic, or allowed approximation.',
        benchmark_candidate_created=False, elapsed_seconds=time.monotonic()-began)
    args.out.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: report[k] for k in ('status', 'witness_input_count',
        'determinants', 'classes', 'independent_scalar_replay', 'elapsed_seconds')}, indent=2))


if __name__ == '__main__':
    main()
