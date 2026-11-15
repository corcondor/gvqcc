#!/usr/bin/env python3
"""Bounded rank-43 feasibility refit of the actual recovered v27 angle table.

The public v27 stored angle_words are not the circuit words.  This driver
requires the recovered-word SHA, exported W, and accepted H2-only patch.
No circuit, source coefficient file, verifier, or scoring seed is changed.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import resource
import time
import zlib

import numpy as np
from scipy.linalg import solve_triangular
from scipy.optimize import minimize

from inverse_v2_chemistry_refit import FixedAngles
from dfthcsos.scoreinfra.dfthc_math import evaluate_dfthc_angle_words, reconstruct_u_vectors
from dfthcsos.scoreinfra.reference import UPPER_ENERGY
from dfthcsos.scoreinfra.costs_prepare import SpinFreeData_V1

BASE = Path(__file__).resolve().parent
WORD_SHA = '8caf7416de79102103757e3ab7ab4b6bbebfad9b1bf1ecd564c20eb948dbfcea'
W_SHA = 'a5bd72e36df3e810a08d55b8520bb68f07434d0f83a9df58411c9b8d8b34e395'
H2_SHA = 'c999197f880fc14864ea295f0015821b1b6cf692f520a07bc2051f45c1626b38'
BASE_COST = 294887987.4337159


def raw_sha(array):
    return hashlib.sha256(array.tobytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seconds', type=float, default=30.)
    parser.add_argument('--iterations', type=int, default=5000)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    args.out.mkdir(parents=True)
    begin = time.monotonic()
    data = dict(np.load(BASE.parent/'dqi_inputs/chemistry_4033/submission_asterios_full.npz', allow_pickle=False))
    exported = dict(np.load(BASE/'outcome_v27_public_weights.npz', allow_pickle=False))
    words = np.load(BASE/'outcome_v27_actual_words_uint8.npy', allow_pickle=False)
    assert words.shape == (1220,75) and words.dtype == np.uint8 and raw_sha(words) == WORD_SHA
    assert raw_sha(exported['W']) == W_SHA
    patch = json.loads((BASE/'outcome_v27_chem_h2_patch.json').read_text())['replacement']
    raw = zlib.decompress(base64.b64decode(patch['zlib_base64']))
    assert hashlib.sha256(raw).hexdigest() == H2_SHA == patch['raw_sha256']
    data['W'] = exported['W'].copy()
    data['H2_I'] = np.frombuffer(raw,dtype=patch['dtype']).copy().reshape(patch['shape'])
    data['angle_words'] = words.astype(np.int64)
    decoded = reconstruct_u_vectors(words.astype(float)/128, data['tree_edges'])
    decoded /= np.linalg.norm(decoded,axis=1)[:,None]
    data['U'] = decoded[76:].reshape(8,143,76)
    np.savez_compressed(args.out/'baseline_actual.npz', **data)
    model = FixedAngles(data)

    def official(candidate):
        return evaluate_dfthc_angle_words(candidate['angle_words'],candidate['W'],
            candidate['H2_I']-candidate['W'].sum(1),model.S,model.beta,model.ref,
            brot=8,tree_edges=candidate['tree_edges'],energy_upper=UPPER_ENERGY)

    baseline = official(data)
    assert baseline['error_1'] <= .02 and baseline['error_2'] <= .02 and baseline['E_gap'] > 3.914898
    assert abs(baseline['lambda_eff']*14722*427-BASE_COST) < .002
    r,b,old_c = data['W'].shape
    c = old_c-1
    ls = np.array([np.linalg.cholesky(model.G4[i,i]) for i in range(r)])
    qs = np.array([solve_triangular(ls[i],model.V[i*b:(i+1)*b],lower=True) for i in range(r)])
    orth = max(float(np.max(np.abs(q@q.T-np.eye(b)))) for q in qs)
    assert orth < 1e-7
    cross = np.array([[qs[i]@qs[j].T for j in range(r)] for i in range(r)])
    aa = []
    for i in range(r):
        first = solve_triangular(ls[i],model.A[i],lower=True)
        aa.append(solve_triangular(ls[i],first.T,lower=True).T)
    aa = np.array(aa)
    full_y = ls.transpose(0,2,1)@data['W']
    p0 = full_y@full_y.transpose(0,2,1)
    reduced_y, rotations, spectra = [], [], []
    for i in range(r):
        u,s,vh = np.linalg.svd(full_y[i],full_matrices=False)
        reduced_y.append(u[:,:c]*s[:c])
        rotations.append(vh[:c].T)
        spectra.append(s.tolist())
    reduced_y = np.array(reduced_y)
    rotations = np.array(rotations)
    d0 = np.einsum('ri,rij->rj',data['H2_I']-data['W'].sum(1),rotations)
    scale = .02**2
    calls = 0
    start = time.monotonic()
    best = reduced_y.ravel().copy()
    best_f = float('inf')
    trace = []

    class Budget(Exception): pass
    class Feasible(Exception): pass

    def objective(flat,budget=True):
        nonlocal calls,best,best_f
        if budget and time.monotonic()-start > args.seconds: raise Budget()
        calls += 1
        y = flat.reshape(r,b,c)
        dp = y@y.transpose(0,2,1)-p0
        kd = np.zeros_like(aa)
        for i in range(r):
            for j in range(r):
                g = cross[i,j]
                kd[i] += g@dp[j]@g.T
        f = float(model.e20+2*np.einsum('rij,rij->',aa,dp)+np.einsum('rij,rij->',kd,dp))/scale
        grad = 4*(aa+kd)@y/scale
        if f < best_f: best_f,best = f,flat.copy()
        return f,grad.ravel()

    def data_at(flat):
        dd = dict(data)
        y = flat.reshape(r,b,c)
        dd['W'] = np.array([solve_triangular(ls[i].T,y[i],lower=False) for i in range(r)])
        dd['H2_I'] = d0+dd['W'].sum(1)
        return dd

    initial_flat = best.copy()
    initial = objective(initial_flat,False)
    direction = np.sin(np.arange(len(best))+1.)
    direction /= np.linalg.norm(direction)
    eps = 1e-6
    fd = (objective(initial_flat+eps*direction,False)[0]-objective(initial_flat-eps*direction,False)[0])/(2*eps)
    analytic = float(initial[1]@direction)
    derivative_error = abs(fd-analytic)/max(1.,abs(fd))
    assert derivative_error < 1e-5
    best,best_f = initial_flat.copy(),initial[0]
    start = time.monotonic()
    print(json.dumps(dict(event='initial',baseline=baseline,C=c,
        reduced_error2=float(np.sqrt(initial[0]*scale)),orthogonality_error=orth,
        gradient_relative_error=derivative_error,preparation_seconds=start-begin)),flush=True)

    def callback(flat):
        elapsed = time.monotonic()-start
        if not trace or elapsed-trace[-1]['seconds'] >= 10:
            row = dict(calls=calls,best_error2=float(np.sqrt(max(best_f,0)*scale)),seconds=elapsed)
            trace.append(row)
            np.savez_compressed(args.out/'checkpoint.npz',**data_at(best))
            (args.out/'progress.json').write_text(json.dumps(trace,indent=2)+'\n')
            print(json.dumps(row),flush=True)
        if best_f*scale < .0199999**2: raise Feasible()

    try:
        opt = minimize(objective,initial_flat,jac=True,method='L-BFGS-B',callback=callback,
            options=dict(maxiter=args.iterations,maxcor=20,ftol=1e-14,gtol=1e-9,maxls=30))
        termination = str(opt.message)
    except Budget: termination = 'W refit time budget reached'
    except Feasible: termination = 'error2 reserve reached; H2 restoration still required'
    elapsed = time.monotonic()-start
    candidate = data_at(best)
    metrics = official(candidate)
    assert abs(metrics['error_2']-np.sqrt(max(best_f,0)*scale)) < 1e-9
    assert np.array_equal(candidate['angle_words'],data['angle_words'])
    candidate_path = args.out/'candidate.npz'
    np.savez_compressed(candidate_path,**candidate)
    resource_model = SpinFreeData_V1(R=r,B=b,C=c,N=76,chi=10,beta=8)
    outer = resource_model.outer_state_prep_qubit_cost()
    inner = resource_model.inner_state_prep_qubit_cost()
    total_t = 8060+resource_model.outer_state_prep()+resource_model.inner_state_prep()+resource_model.givens_rotations()
    total_q = 40+outer['persistent']+inner['persistent']+max(outer['temporary'],inner['temporary'])
    report = dict(status='C43_TWO_BODY_FEASIBLE_NEEDS_H2_RESTORE' if metrics['error_2'] <= .02 else 'C43_FIXED_V27_WORDS_BOUNDED_REFIT_NOT_FEASIBLE',
        source_actual_word_sha256=WORD_SHA,source_W_raw_sha256=W_SHA,source_H2_raw_sha256=H2_SHA,
        latest_accepted_baseline_cost=BASE_COST,baseline_official_numeric_metrics=baseline,
        C=c,word_changes=0,loader_changes=0,public_loader_reuse_expected=True,
        conditional_resources=dict(T=total_t,Q=total_q,loader_toffoli_per_pass=4030),
        conditional_lambda_break_even=BASE_COST/(total_t*total_q),
        gradient_check=dict(finite_difference=fd,analytic=analytic,scaled_error=derivative_error),
        orthogonality_error=orth,initial_reduced_error2=float(np.sqrt(initial[0]*scale)),
        group_whitened_singular_values=spectra,official_numeric_metrics=metrics,
        candidate_path=str(candidate_path),candidate_sha256=hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
        calls=calls,refit_seconds=elapsed,total_seconds=time.monotonic()-begin,termination=termination,
        trace=trace,full_official_verification_run=False,optimality_claimed=False,
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
    (args.out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in {'group_whitened_singular_values','trace'}}),flush=True)


if __name__ == '__main__': main()
