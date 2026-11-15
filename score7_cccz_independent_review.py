#!/usr/bin/env python3
"""Independent dense-matrix/TeX review of the exact CCCZ implementation.

Circuit instructions and feedback controls are parsed directly from the three
Qcircuit environments in primary-source Fig. 1. No paper content is emitted.
Dense complex matrices use normalised Hadamards, unlike the integer simulator.
This corroborates, but does not replace, the exact cyclotomic proof.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import tarfile
from typing import Sequence

import kickmix as km
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def parse_paper(path):
    with tarfile.open(path) as archive:
        text = archive.extractfile('main.tex').read().decode()
    figure = text[text.index(r'\begin{figure}'):text.index(r'\end{figure}')]
    blocks = re.findall(r'\\Qcircuit[^\n]*\{\n(.*?)\n\}\}', figure, re.S)
    assert len(blocks) == 3
    circuits = {}
    for name, block in zip(('a', 'aprime', 'b'), blocks):
        rows = [row.strip().split('&') for row in block.split(r'\\')]
        assert len(rows) == 5 and len(set(map(len, rows))) == 1
        measurement = next(c for c, cell in enumerate(rows[4]) if r'\meter' in cell)
        gates = []
        for column in range(measurement):
            controls = []
            targets = []
            for q, row in enumerate(rows):
                cell = row[column]
                phases = {r'\gate{T}': 1, r'\gate{T^\dagger}': -1,
                          r'\gate{S}': 2, r'\gate{S^\dagger}': -2}
                if r'\gate{H}' in cell:
                    gates.append(('H', q))
                for token, power in phases.items():
                    if token in cell:
                        gates.append(('P', q, power))
                if r'\ctrl{' in cell:
                    controls.append(q)
                if r'\targ' in cell:
                    targets.append(q)
            if controls or targets:
                assert len(controls) == 1 and targets
                gates.extend(('CX', controls[0], q) for q in targets)
        feedback = []
        for column in range(measurement + 1, len(rows[0])):
            classical = rows[4][column]
            if r'\cctrl' not in classical:
                continue
            outcome = 0 if r'\cctrlo' in classical else 1
            terms = []
            for q in range(4):
                cell = rows[q][column]
                if r'\ctrl' in cell or r'\control' in cell:
                    open_control = r'\ctrlo' in cell or r'\controlo' in cell
                    terms.append((q, 0 if open_control else 1))
            assert len(terms) == 2
            feedback.append((outcome, terms))
        assert len(feedback) == 2
        circuits[name] = (gates, feedback)
    return circuits, hashlib.sha256(text.encode()).hexdigest()


def matrix(gates):
    result = np.eye(32, dtype=np.complex128)
    for gate in gates:
        kind, q = gate[:2]
        op = np.zeros((32, 32), dtype=np.complex128)
        for x in range(32):
            if kind == 'H':
                op[x & ~(1 << q), x] = 1 / np.sqrt(2)
                op[x | (1 << q), x] = (-1 if x >> q & 1 else 1) / np.sqrt(2)
            elif kind == 'P':
                op[x, x] = np.exp(1j * np.pi / 4 * gate[2]) if x >> q & 1 else 1
            elif kind == 'CX':
                op[x ^ ((1 << gate[2]) if x >> q & 1 else 0), x] = 1
            else:
                raise ValueError(gate)
        result = op @ result
    return result


def ring_review(module):
    rng = np.random.default_rng(761003)
    max_embedding_error = 0.0
    z = np.exp(1j*np.pi/4)
    def embed(a):
        return sum(value * z**i for i, value in enumerate(a))
    for _ in range(256):
        a, b = [tuple(map(int, rng.integers(-9, 10, 4))) for _ in range(2)]
        convolution = [0] * 7
        for i in range(4):
            for j in range(4):
                convolution[i+j] += a[i]*b[j]
        for exponent in range(6, 3, -1):
            convolution[exponent-4] -= convolution[exponent]
        assert module.mul(a, b) == tuple(convolution[:4])
        assert module.add(a, b) == tuple(a[i]+b[i] for i in range(4))
        assert module.neg(a) == tuple(-value for value in a)
        for power in range(-9, 10):
            error = abs(embed(module.shift(a, power)) - embed(a)*z**power)
            max_embedding_error = max(max_embedding_error, error)
        error = abs(embed(module.conjugate(a))-embed(a).conjugate())
        max_embedding_error = max(max_embedding_error, error)
    assert max_embedding_error < 1e-11
    return dict(integer_convolution_products=256, shift_powers_tested=list(range(-9,10)),
                complex_embedding_max_abs_error=max_embedding_error,
                relation='zeta^4=-1', integer_product_check='PASS')


def interface_review(official_root):
    parser = {}
    for instruction in ('H q0', 'T q0', 'Z_POW q0 0.25'):
        try:
            km.Circuit(instruction + '\n')
            parser[instruction] = {'accepted': True}
        except ValueError as error:
            parser[instruction] = {'accepted': False, 'error': str(error)}
    assert not parser['H q0']['accepted'] and not parser['T q0']['accepted']
    assert parser['Z_POW q0 0.25']['accepted']
    rotation = km.Circuit('Z_POW q0 0.25\n')
    dqi = official_root/'dqi/verify_submission_dqi.py'
    chem = official_root/'dfthcsos/scoreinfra/circuits.py'
    inv = official_root/'invsqrt/verify_submission_invsqrt.py'
    dqi_ast = ast.parse(dqi.read_text())
    verify = next(node for node in dqi_ast.body if isinstance(node, ast.FunctionDef) and node.name == 'verify')
    reject = next(node for node in verify.body if isinstance(node, ast.If) and 'Z_POW' in ast.unparse(node.test))
    dqi_check = ast.fix_missing_locations(ast.Module(body=[reject], type_ignores=[]))
    try:
        exec(compile(dqi_check, str(dqi), 'exec'), {'circuit_stats': rotation.operation_statistics()})
        raise AssertionError('DQI did not reject a T rotation')
    except ValueError as error:
        dqi_error = str(error)
    chem_ast = ast.parse(chem.read_text())
    function = next(node for node in chem_ast.body if isinstance(node, ast.FunctionDef) and node.name == '_reject_rotations')
    isolated = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
    namespace = {'Sequence': Sequence, 'km': km, 'InvalidCircuits': ValueError}
    exec(compile(isolated, str(chem), 'exec'), namespace)
    try:
        namespace['_reject_rotations']([rotation])
        raise AssertionError('Chemistry did not reject a T rotation')
    except ValueError as error:
        chem_error = str(error)
    return dict(parser=parser, dqi_rotation_rejection=dqi_error,
                chemistry_rotation_rejection=chem_error,
                official_guard_execution_scope='Only unchanged AST rejection guards, not full verifier execution',
                source_sha256={str(path):sha(path) for path in (dqi,chem,inv)},
                cost_audit={'dqi':'R * Q^2 * mean num_toffoli_like',
                            'chemistry':'lambda_eff * total_Toffoli_like * Q_total',
                            'invsqrt':'Q * (mean num_toffoli_like + synthesized_T_count / 4)'},
                t_count_not_identical_to_competition_toffoli_like=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--paper', type=Path, required=True)
    ap.add_argument('--exact', type=Path, required=True)
    ap.add_argument('--receipt', type=Path, required=True)
    ap.add_argument('--official-root', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    assert not args.output.exists()
    spec = importlib.util.spec_from_file_location('reviewed_exact_cccz', args.exact)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    receipt = json.loads(args.receipt.read_text())
    assert receipt['source_sha256'] == sha(args.exact)
    circuits, tex_sha = parse_paper(args.paper)
    ideal = np.eye(16, dtype=complex); ideal[15,15] = -1
    rng = np.random.default_rng(761004)
    random_states = rng.normal(size=(64,16,2))+1j*rng.normal(size=(64,16,2))
    random_states /= np.linalg.norm(random_states.reshape(64,-1),axis=1)[:,None,None]
    figures = {}
    expected = {'a':(6,[6,8]), 'aprime':(6,[7,7]), 'b':(2,[12,14])}
    for name, (gates, feedback) in circuits.items():
        whole = matrix(gates)
        root_whole = matrix(receipt['figures'][name]['gates'])
        assert np.max(np.abs(whole-root_whole)) < 1e-13
        assert sum(g[0] == 'H' for g in gates) == 2
        cnot = sum(g[0] == 'CX' for g in gates)
        t_count = sum(g[0] == 'P' and g[2] % 2 != 0 for g in gates)
        depths = [0]*5
        for gate in gates:
            if gate[0] == 'P' and gate[2] % 2:
                depths[gate[1]] += 1
            elif gate[0] == 'CX':
                depth = max(depths[gate[1]],depths[gate[2]])
                depths[gate[1]] = depths[gate[2]] = depth
        branch_rows = []; kraus = []
        for outcome in (0,1):
            k = whole[16*outcome:16*(outcome+1),:16].copy()
            for enabled, controls in feedback:
                if outcome == enabled:
                    for x in range(16):
                        if all((x>>q&1)==value for q,value in controls): k[x] *= -1
            scalar = np.trace(ideal.conj().T@k)/16
            residual = float(np.max(np.abs(k-scalar*ideal)))
            zeta = np.exp(1j*np.pi/4)
            exact_scalar = sum(v*zeta**i for i,v in enumerate(receipt['figures'][name]['branch_scalar_numerators_in_basis_1_zeta_zeta2_zeta3'][outcome]))/2
            entangled_error = max(float(np.max(np.abs(k@state-scalar*ideal@state))) for state in random_states)
            assert residual < 1e-13 and entangled_error < 1e-13
            assert abs(abs(scalar)**2-.5) < 1e-13 and abs(scalar-exact_scalar) < 1e-13
            kraus.append(k)
            branch_rows.append(dict(outcome=outcome,scalar=[float(scalar.real),float(scalar.imag)],
                                    matrix_max_abs_error=residual,probability=float(abs(scalar)**2),
                                    reference_entangled_states=64,reference_entangled_max_abs_error=entangled_error,
                                    cnot_equivalent=cnot+sum(outcome==enabled for enabled,_ in feedback)))
        completeness = float(np.max(np.abs(sum(k.conj().T@k for k in kraus)-np.eye(16))))
        assert completeness < 1e-13
        assert t_count == 6 and max(depths) == expected[name][0]
        assert [r['cnot_equivalent'] for r in branch_rows] == expected[name][1]
        figures[name] = dict(unitary_parsed_from_primary_tex=True,feedback_parsed_from_primary_tex=feedback,
                             phase_convention_matches_exact_proof=True,t_count=t_count,t_depth=max(depths),
                             branches=branch_rows,kraus_completeness_max_abs_error=completeness)
    coherent = matrix(receipt['coherent_15t']['gates'])
    target = np.zeros((32,16),dtype=complex); target[:16] = ideal
    coherent_error = float(np.max(np.abs(coherent[:,:16]-target)))
    assert coherent_error < 1e-13
    assert sum(g[0]=='H' for g in receipt['coherent_15t']['gates']) == 4
    result = dict(status='INDEPENDENT_REVIEW_PASS', reviewer_source_sha256=sha(__file__),
                  reviewed_source_sha256=sha(args.exact), reviewed_receipt_sha256=sha(args.receipt),
                  primary_source_archive_sha256=sha(args.paper),primary_source_main_tex_sha256=tex_sha,
                  figures=figures,ring_arithmetic=ring_review(module),
                  normalization_review={'six_T_figures':'2 unnormalised H gates -> amplitude denominator 2',
                                        'coherent_15T':'4 unnormalised H gates -> amplitude denominator 4'},
                  coherent_15t_independent_matrix_max_abs_error=coherent_error,
                  interface_audit=interface_review(args.official_root),
                  limitations=['Complex numerical checks corroborate the separate integer proof; they are not themselves an exact proof.',
                               'T-depth is the depth of the displayed constructions, not a newly established minimum.',
                               'No competition circuit, verifier receipt, score, or submission was changed.'])
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'figures':{k:{x:v[x] for x in ('t_count','t_depth')} for k,v in figures.items()},
                      'coherent_error':coherent_error,'reviewed_source_sha256':result['reviewed_source_sha256']}))


if __name__ == '__main__': main()
