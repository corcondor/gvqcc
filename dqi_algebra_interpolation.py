"""Exact GF24 identification and cross-evaluation binary-product dictionary.

This is a bounded alternative to the existing tensor flip search.  All 17
points of P1(GF16) contribute every nonzero binary linear form, rather than
finishing a nine-product GF16 multiplication independently at eleven points.
The search may change each AND's 24-bit output direction while preserving the
complete multiplication tensor.  No production KMB is read or modified.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import time

from inverse_v2_actual_block_audit import LEFT, RIGHT, FIELD_ORDER, mul24
from inverse_v2_optimize import mul, inverse_matrix

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'official_sources/Syed_v12/source/dqi_source/src/controller_work/night_root/extension24_tensor.py'


def extension_source():
    spec = importlib.util.spec_from_file_location('dqi_algebra_source_extension', SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def bits(value):
    while value:
        b = value & -value
        yield b.bit_length() - 1
        value ^= b


def outer(form, right=None):
    right = form if right is None else right
    return sum(right << (24 * i) for i in bits(form))


def tensor_value(terms, a, b):
    value = 0
    for left, right, weight in terms:
        if (left & a).bit_count() & 1 and (right & b).bit_count() & 1:
            value ^= weight
    return value


def certify(terms, conjugated=False):
    for i in range(24):
        for j in range(24):
            left = 1 << i
            if conjugated:
                left ^= left >> 12
            assert tensor_value(terms, 1 << i, 1 << j) == mul24(left, 1 << j), (i, j)
    return 576


def identify():
    path = Path(__file__).with_name('inverse_v2_actual_tensor99.json')
    terms = json.loads(path.read_text())
    certify(terms, conjugated=True)
    assert all(a ^ ((a & 4095) << 12) == b for a, b, _ in terms)
    delta, trace = 2048, 0
    for _ in range(12):
        trace ^= delta
        delta = mul(delta, delta, 12)
    roots = [x for x in range(4096) if mul(x, x, 12) ^ x ^ 2048 == 0]
    assert trace == 1 and not roots
    # A nonzero nilpotent would exist in the alternative jet algebra.
    assert mul24(1 << 12, 1 << 12) == ((1 << 12) | 2048)
    return dict(status='EXACT_GF_2_24_FIELD_IDENTIFICATION', basis_pairs=576,
                base_modulus='0x1053', extension_relation='t^2 + t + 2048 = 0',
                trace_delta=trace, roots_in_GF4096=len(roots),
                operation='target XOR conjugate(left) * right',
                conjugate='(x0,x1) -> (x0 XOR x1,x1)',
                not_the_length_two_jet_algebra=True,
                tensor_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                generator_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest())


def dictionary(ext):
    beta, theta, sub, rows = ext.basis()
    evaluations = []
    forms = []
    for point in range(17):
        ev = [0] * 4
        for j in range(24):
            tower = ext.apply(rows, 1 << j)
            value = 0
            if point == 16:
                value = tower >> 20
            else:
                for i in range(6):
                    value ^= ext.small_mul((tower >> (4 * i)) & 15, ext.small_power(point, i))
            for k in range(4):
                ev[k] |= ((value >> k) & 1) << j
        evaluations.append(ev)
        forms.extend(ext.compose(mask, ev) for mask in range(1, 16))
    assert len(set(forms)) == 255
    return forms, evaluations, beta, theta, sub


def decomposition(ext, points, evaluations, theta, sub):
    matrix = [[ext.small_power(p, k) for k in range(11)] if p < 16
              else [int(k == 10) for k in range(11)] for p in points]
    interpolation = inverse_matrix(matrix, 4)

    def embed(value):
        result = 0
        for i in bits(value):
            result ^= sub[i]
        return result

    terms = []
    for column, point in enumerate(points):
        weight = 0
        for k in range(11):
            weight ^= ext.mul(embed(interpolation[k][column]), ext.power(theta, k))
        for a, b, c in ext.small_tensor():
            terms.append((ext.compose(a, evaluations[point]), ext.compose(b, evaluations[point]),
                          ext.mul(weight, embed(c))))
    assert len(terms) == 99
    certify(terms)
    return terms


def coordinates(forms, terms, rng):
    location = {form: i for i, form in enumerate(forms)}
    selected = [location[a] for a, b, w in terms]
    assert all(a == b for a, b, _ in terms) and len(set(selected)) == 99
    extras = [i for i in range(len(forms)) if i not in selected]
    rng.shuffle(extras)
    pivots = {}
    basis = []
    for index in selected + extras:
        value, coeff = outer(forms[index]), 1 << len(basis)
        while value:
            p = value.bit_length() - 1
            if p not in pivots:
                pivots[p] = value, coeff
                basis.append(index)
                break
            row, combination = pivots[p]
            value ^= row
            coeff ^= combination
    reps = []
    for form in forms:
        value, coeff = outer(form), 0
        while value:
            p = value.bit_length() - 1
            row, combination = pivots[p]
            value ^= row
            coeff ^= combination
        reps.append(coeff)
    assert len(basis) == 142
    weights = [w for _, _, w in terms] + [0] * (len(basis) - 99)
    assert all(reps[index] == 1 << i for i, index in enumerate(basis))
    return basis, weights, reps


def prepare(output, starts=24):
    started = time.monotonic()
    ext = extension_source()
    forms, ev, beta, theta, sub = dictionary(ext)
    rng = random.Random(202611142004)
    states = []
    for iteration in range(starts):
        points = list(range(11)) if iteration == 0 else sorted(rng.sample(range(17), 11))
        terms = decomposition(ext, points, ev, theta, sub)
        basis, weights, reps = coordinates(forms, terms, rng)
        states.append((points, basis, weights, reps))
    words = 3
    lines = [f'{len(forms)} 142 {len(states)}']
    lines.append(' '.join(map(str, forms)))
    for points, basis, weights, reps in states:
        lines.append(' '.join(map(str, basis)))
        lines.append(' '.join(map(str, weights)))
        lines.extend(' '.join(str((v >> (64 * k)) & ((1 << 64) - 1)) for k in range(words)) for v in reps)
    output.write_text('\n'.join(lines) + '\n')
    report = identify()
    report.update(dictionary_size=len(forms), dictionary_rank=142, linear_dependencies=113,
                  evaluation_points='all 16 GF16 points plus infinity',
                  allowed_ANDs='phi_p,m(left) AND phi_p,m(right), all 15 nonzero masks at each point',
                  variable_output_directions=True, gf16_beta=beta, tower_theta=theta,
                  initial_states=len(states), all_initial_tensors_certified=True,
                  initial_rank=99, preparation_seconds=time.monotonic() - started,
                  input_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                  search_scope='fixed 255-form symmetric dictionary only; not a global tensor-rank lower bound')
    output.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


def prepare_nonsymmetric(output, starts=8, cross_points=False):
    started = time.monotonic()
    ext = extension_source()
    forms, ev, beta, theta, sub = dictionary(ext)
    pairs = ([(a, b) for a in forms for b in forms] if cross_points else
             [(a, b) for p in range(17)
              for a in forms[p * 15:(p + 1) * 15]
              for b in forms[p * 15:(p + 1) * 15]])
    dimension = 576 if cross_points else 240
    assert len(pairs) == len(set(pairs)) == (65025 if cross_points else 3825)
    location = {pair: i for i, pair in enumerate(pairs)}
    vectors = [outer(a, b) for a, b in pairs]
    rng = random.Random(202611142009)
    lines = [f'{len(pairs)} {dimension} {starts}',
             ' '.join(str(a) for a, b in pairs), ' '.join(str(b) for a, b in pairs)]
    for iteration in range(starts):
        points = list(range(11)) if iteration == 0 else sorted(rng.sample(range(17), 11))
        terms = decomposition(ext, points, ev, theta, sub)
        selected = [location[a, b] for a, b, w in terms]
        extras = [i for i in range(len(pairs)) if i not in selected]
        rng.shuffle(extras)
        basis, pivots = [], {}
        for index in selected + extras:
            value, coeff = vectors[index], 1 << len(basis)
            while value:
                p = value.bit_length() - 1
                if p not in pivots:
                    pivots[p] = value, coeff
                    basis.append(index)
                    break
                row, combination = pivots[p]
                value ^= row
                coeff ^= combination
        assert len(basis) == dimension
        reps = []
        for value in vectors:
            coeff = 0
            while value:
                p = value.bit_length() - 1
                row, combination = pivots[p]
                value ^= row
                coeff ^= combination
            reps.append(coeff)
        weights = [w for a, b, w in terms] + [0] * (dimension - 99)
        assert all(reps[index] == 1 << i for i, index in enumerate(basis))
        lines.append(' '.join(map(str, basis)))
        lines.append(' '.join(map(str, weights)))
        lines.extend(' '.join(str((v >> (64 * k)) & ((1 << 64) - 1)) for k in range((dimension+63)//64)) for v in reps)
    output.write_text('\n'.join(lines) + '\n')
    report = identify()
    report.update(dictionary_size=len(pairs), dictionary_rank=dimension, linear_dependencies=len(pairs)-dimension,
                  evaluation_points='all 16 GF16 points plus infinity',
                  allowed_ANDs=('phi_p,a(left) AND phi_q,b(right), all 255 by 255 evaluation forms' if cross_points else
                                'phi_p,a(left) AND phi_p,b(right), all 15 by 15 nonzero masks per point'),
                  different_evaluation_points_allowed=cross_points,
                  symmetric_control_forms_required=False, variable_output_directions=True,
                  initial_states=starts, all_initial_tensors_certified=True, initial_rank=99,
                  preparation_seconds=time.monotonic() - started,
                  input_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                  search_scope='fixed evaluation-form dictionary only; not a global tensor-rank lower bound')
    output.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


def verify_candidate(path):
    result = json.loads(path.read_text())
    terms = result['terms']
    certify(terms)
    converted = [(a ^ ((a & 4095) << 12), b, c) for a, b, c in terms]
    certify(converted, conjugated=True)
    assert len(converted) < 99
    from full_inverse_verify import vector_product
    gates = []
    for a, b, c in converted:
        u = sum(1 << LEFT[i] for i in bits(a))
        v = sum(1 << RIGHT[i] for i in bits(b))
        gates.extend(vector_product(u, v, c, FIELD_ORDER))
    target = path.with_suffix('.kmx')
    target.write_text('\n'.join(' '.join([g[0]] + [f'q{q}' for q in g[1:]]) for g in gates) + '\n')
    # Each vector_product is a conjugated CCX with exact input/target frames.
    # It is an arbitrary-target XOR, has no measurement or extra scratch.
    result.update(basis_pairs_certified=576, all_controls_restored=True,
                  arbitrary_target_xor=True, extra_scratch=0, phase_exact=True,
                  ccx=len(terms), cx=len(gates) - len(terms), kmx_path=str(target),
                  quantum_native_verification=False)
    path.with_name('dqi_algebra_candidate_certificate.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path(__file__).with_name('dqi_algebra_dictionary.txt'))
    parser.add_argument('--verify-candidate', type=Path)
    parser.add_argument('--starts', type=int, default=24)
    parser.add_argument('--nonsymmetric', action='store_true')
    parser.add_argument('--cross-points', action='store_true')
    args = parser.parse_args()
    if args.verify_candidate:
        verify_candidate(args.verify_candidate)
    elif args.nonsymmetric or args.cross_points:
        prepare_nonsymmetric(args.output, args.starts, cross_points=args.cross_points)
    else:
        prepare(args.output, args.starts)
