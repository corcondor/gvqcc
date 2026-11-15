#!/usr/bin/env python3
"""Refit W for an actual integer-word chemistry candidate in whitened coordinates.

Every reference quantity is built from the supplied candidate's decoded words.
For V_r=L_r Q_r and Y_r=L_r.T W_r, the exact residual objective is
e20 + 2<A, dP> + <K dP, dP>, where dP=YY.T-Y0Y0.T.
This changes neither the integer words nor the factor count.  H2_I initially
tracks sum(W) to preserve natural d; if error_2 is feasible, a separate small
H2_I-only constrained optimization restores error_1 and the strict gap floor.
The final receipt uses the unchanged official numerical evaluator.  Loader
costs are estimates until a separate full loader proof and official run pass.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import resource
import time

import numpy as np
from scipy.linalg import solve_triangular
from scipy.optimize import minimize

from inverse_v2_chemistry_refit import FixedAngles
from inverse_v2_chemistry_screen import ROOT
from score_chemistry_identity_polish import FixedW
from score2_angle_sparse_patch import estimate_family
from score3_chemistry_b_prefix import resource_row
from dfthcsos.scoreinfra.dfthc_math import evaluate_dfthc_angle_words
from dfthcsos.scoreinfra.reference import UPPER_ENERGY


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def numeric_pass(metrics):
    return bool(metrics['error_1'] <= .02 and metrics['error_2'] <= .02
                and metrics['Lambda'] > 49 and metrics['E_gap'] > 3.914898
                and metrics['gap_in_domain'] and np.isfinite(metrics['lambda_eff']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seconds', type=float, default=90.)
    parser.add_argument('--iterations', type=int, default=4000)
    parser.add_argument('--stop-at', type=float, default=.01999)
    parser.add_argument('--identity-seconds', type=float, default=45.)
    parser.add_argument('--method', choices=('lbfgs','block'), default='lbfgs',
                        help='block uses the exact rank-C PSD minimizer for each group')
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    args.out.mkdir(parents=True)
    begin = time.monotonic()
    data = dict(np.load(args.source, allow_pickle=False))
    original = dict(np.load(ROOT/'dqi_inputs/chemistry_4033/submission_asterios_full.npz', allow_pickle=False))
    assert np.array_equal(data['tree_edges'], original['tree_edges'])
    assert data['angle_words'].shape == original['angle_words'].shape
    assert np.issubdtype(data['angle_words'].dtype, np.integer)
    assert np.all((data['angle_words'] >= 0) & (data['angle_words'] < 256))
    initial_words = data['angle_words'].copy()
    r, b, c = data['W'].shape
    assert (r, b, data['U'].shape[-1]) == (8, 143, 76)
    changes = [dict(address=int(a), column=int(k), old=int(original['angle_words'][a,k]),
                    value=int(initial_words[a,k]))
               for a,k in np.argwhere(initial_words != original['angle_words'])]
    patch = estimate_family(original['angle_words'], initial_words, feature_patches=True)
    resources = resource_row(b, r=r, c=c)
    total_t = resources['T'] + patch['added_official_toffoli_both_passes']
    total_q = resources['Q']
    comparison_lambda = 46.905894137
    threshold = comparison_lambda * 14728 * 427 / (total_t * total_q)
    (args.out/'changes.json').write_text(json.dumps(changes, indent=2)+'\n')

    model = FixedAngles(data)
    ls = np.array([np.linalg.cholesky(model.G4[i,i]) for i in range(r)])
    qs = np.array([solve_triangular(ls[i], model.V[i*b:(i+1)*b], lower=True) for i in range(r)])
    orth = float(max(np.max(np.abs(q@q.T-np.eye(b))) for q in qs))
    assert orth < 1e-7
    cross = np.array([[qs[i]@qs[j].T for j in range(r)] for i in range(r)])
    aa = []
    for i in range(r):
        left = solve_triangular(ls[i], model.A[i], lower=True)
        aa.append(solve_triangular(ls[i], left.T, lower=True).T)
    aa = np.array(aa)
    y0 = ls.transpose(0,2,1) @ data['W']
    p0 = y0 @ y0.transpose(0,2,1)
    d0 = data['H2_I'] - data['W'].sum(1)
    scale = .02**2
    start = time.monotonic()
    calls = 0
    trace = []
    best = y0.ravel().copy()
    best_f = float('inf')

    class Budget(Exception):
        pass

    class Feasible(Exception):
        pass

    def objective(flat, budget=True):
        nonlocal calls, best, best_f
        if budget and time.monotonic()-start > args.seconds:
            raise Budget()
        calls += 1
        y = flat.reshape(r,b,c)
        delta = y@y.transpose(0,2,1)-p0
        kd = np.zeros_like(aa)
        for i in range(r):
            for j in range(r):
                gg = cross[i,j]
                kd[i] += gg@delta[j]@gg.T
        f = float(model.e20 + 2*np.einsum('rij,rij->',aa,delta)
                  + np.einsum('rij,rij->',kd,delta))/scale
        grad = 4*(aa+kd)@y/scale
        if f < best_f:
            best_f = f
            best = flat.copy()
        return f, grad.ravel()

    def data_at(flat):
        updated = dict(data)
        y = flat.reshape(r,b,c)
        w = np.array([solve_triangular(ls[i].T, y[i], lower=False) for i in range(r)])
        updated['W'] = w
        updated['H2_I'] = d0+w.sum(1)
        return updated

    initial = objective(best, budget=False)
    rng = np.random.default_rng(20261115)
    direction = rng.normal(size=best.size)
    direction /= np.linalg.norm(direction)
    center = best.copy()
    eps = 1e-6
    fd = (objective(center+eps*direction, budget=False)[0]
          - objective(center-eps*direction, budget=False)[0])/(2*eps)
    analytic = float(initial[1]@direction)
    grad_error = abs(fd-analytic)/max(1.,abs(fd))
    assert grad_error < 1e-5
    # Diagnostic finite differences must not become optimization checkpoints.
    best, best_f = center.copy(), initial[0]
    initial_record = dict(event='initial', error2=float(np.sqrt(initial[0]*scale)),
                          changed_words=len(changes), changes=changes,
                          estimated_T=total_t, estimated_Q=total_q,
                          added_task_toffoli=patch['added_official_toffoli_both_passes'],
                          lambda_break_even_user_log=threshold,
                          gradient_check=dict(finite_difference=fd, analytic=analytic, scaled_error=grad_error),
                          orthogonality_error=orth, preparation_seconds=time.monotonic()-begin)
    (args.out/'initial.json').write_text(json.dumps(initial_record, indent=2)+'\n')
    print(json.dumps(initial_record), flush=True)
    start = time.monotonic()

    def callback(flat):
        elapsed = time.monotonic()-start
        if not trace or elapsed-trace[-1]['seconds'] >= 10:
            row = dict(calls=calls, best_error2=float(np.sqrt(max(best_f,0)*scale)), seconds=elapsed)
            trace.append(row)
            np.savez_compressed(args.out/'checkpoint.npz', **data_at(best))
            (args.out/'progress.json').write_text(json.dumps(trace, indent=2)+'\n')
            print(json.dumps(row), flush=True)
        if best_f*scale <= args.stop_at**2:
            raise Feasible()

    block_cycles = 0
    block_updates = 0
    try:
        if args.method == 'lbfgs':
            opt = minimize(objective, center, jac=True, method='L-BFGS-B', callback=callback,
                           options=dict(maxiter=args.iterations, maxcor=20, ftol=1e-14, gtol=1e-9, maxls=30))
            termination = str(opt.message)
        else:
            y = center.reshape(r,b,c).copy()
            previous_f = initial[0]
            termination = 'block cycle limit reached'
            for cycle in range(args.iterations):
                # Q_i R Q_i.T, where R is the CURRENT global residual.
                delta = y@y.transpose(0,2,1)-p0
                projected = aa.copy()
                for i in range(r):
                    for j in range(r):
                        gg = cross[i,j]
                        projected[i] += gg@delta[j]@gg.T
                for i in np.roll(np.arange(r),cycle % r):
                    if time.monotonic()-start > args.seconds:
                        raise Budget()
                    old_p = y[i]@y[i].T
                    # Holding all other groups fixed, minimize ||P_i-M_i||_F
                    # over PSD P_i of rank <= C: retain M_i's top positive C.
                    target = old_p-projected[i]
                    values, vectors = np.linalg.eigh((target+target.T)*.5)
                    fresh = vectors[:,-c:]*np.sqrt(np.maximum(values[-c:],0.))
                    # Orthogonal alignment changes no PSD block; it keeps the
                    # factor gauge close to the preceding one for natural d.
                    uu, _, vh = np.linalg.svd(fresh.T@y[i],full_matrices=False)
                    fresh = fresh@(uu@vh)
                    step = fresh@fresh.T-old_p
                    y[i] = fresh
                    for j in range(r):
                        gg = cross[j,i]
                        projected[j] += gg@step@gg.T
                    block_updates += 1
                current_f = objective(y.ravel())[0]
                if current_f > previous_f+1e-8:
                    raise AssertionError('exact PSD block update increased objective')
                block_cycles += 1
                callback(y.ravel())
                if abs(previous_f-current_f) < 1e-12:
                    termination = 'exact PSD block objective converged'
                    break
                previous_f = current_f
    except Budget:
        termination = 'W refit time budget reached'
    except Feasible:
        termination = 'W refit reached error2 reserve'
    data = data_at(best)
    w_seconds = time.monotonic()-start
    np.savez_compressed(args.out/'weight_refit.npz', **data)
    identity = dict(attempted=False)
    # There is no reason to optimize H2_I while error_2 remains infeasible.
    if best_f*scale <= .02**2 and args.identity_seconds > 0:
        small = FixedW(model, data)
        istart = time.monotonic()
        xx = data['H2_I'].ravel().copy()
        icache = None
        iresult = None
        ibest = None
        ibestvalue = float('inf')
        ilatest = xx.copy()
        def ieval(x):
            nonlocal icache, iresult
            if time.monotonic()-istart > args.identity_seconds:
                raise Budget()
            if icache is None or not np.array_equal(x,icache):
                icache, iresult = x.copy(), small.evaluate(x)
            return iresult
        def iaccept(x, rr):
            nonlocal ibest, ibestvalue
            if np.all(rr[2] >= 0) and rr[-1]['Lambda'] > 49 and rr[0] < ibestvalue:
                ibest, ibestvalue = x.copy(), rr[0]
        def icallback(x):
            nonlocal ilatest
            ilatest = x.copy()
            iaccept(x,ieval(x))
        iinitial = ieval(xx)
        iaccept(xx,iinitial)
        try:
            iopt = minimize(lambda x:ieval(x)[:2], xx, jac=True, method='SLSQP',
                            constraints=[dict(type='ineq', fun=lambda x:ieval(x)[2], jac=lambda x:ieval(x)[3])],
                            callback=icallback, options=dict(maxiter=600, ftol=1e-12, disp=False))
            ilatest = iopt.x
            iaccept(ilatest,small.evaluate(ilatest))
            iterm = str(iopt.message)
        except Budget:
            iterm = 'H2_I time budget reached'
        chosen = ibest if ibest is not None else ilatest
        data['H2_I'] = chosen.reshape(r,c)
        identity = dict(attempted=True, termination=iterm, calls=small.calls,
                        feasible_checkpoint=ibest is not None, initial=iinitial[-1],
                        endpoint=small.evaluate(chosen)[-1], seconds=time.monotonic()-istart)

    metrics = evaluate_dfthc_angle_words(data['angle_words'], data['W'],
                                       data['H2_I']-data['W'].sum(1), model.S, model.beta, model.ref,
                                       brot=8, tree_edges=data['tree_edges'], energy_upper=UPPER_ENERGY)
    mismatch = abs(metrics['error_2']-float(np.sqrt(max(best_f,0)*scale)))
    assert mismatch < 1e-8
    assert np.array_equal(data['angle_words'],initial_words)
    path = args.out/'candidate.npz'
    np.savez_compressed(path, **data)
    passed = numeric_pass(metrics)
    report = dict(status='NUMERICAL_PASS' if passed else 'NUMERICAL_FAIL',
                  source=str(args.source), source_sha256=sha(args.source),
                  script_sha256=sha(__file__), candidate=str(path), candidate_sha256=sha(path),
                  initial=initial_record, official_numeric_metrics=metrics,
                  changed_words=len(changes), changes=changes, unchanged_tree=True,
                  integer_words_fixed_during_refit=True, W_shape=list(data['W'].shape),
                  natural_d_preserved_during_W_refit=True, identity_refit=identity,
                  patch_estimate=patch, unpatched_resource=resources,
                  estimated_T=total_t, estimated_Q=total_q,
                  conditional_cost=metrics['lambda_eff']*total_t*total_q,
                  lambda_break_even_user_log=threshold,
                  conditional_score_improvement=bool(passed and metrics['lambda_eff']<threshold),
                  comparison_scope='User logged lambda 46.905894137 at 14728T/427Q; source NPZ unavailable.',
                  gradient_check_scaled_error=grad_error, official_error2_mismatch=mismatch,
                  calls=calls, method=args.method, block_cycles=block_cycles,
                  block_updates=block_updates, termination=termination, W_refit_seconds=w_seconds,
                  seconds=time.monotonic()-begin, trace=trace,
                  peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
                  full_circuit_verified=False)
    (args.out/'result.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('trace','patch_estimate')}), flush=True)


if __name__ == '__main__':
    main()
