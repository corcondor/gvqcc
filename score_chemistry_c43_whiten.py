#!/usr/bin/env python3
"""Test C43 two-body feasibility in exact whitened feature coordinates.

For each rho, V_r is the 143 by 2926 matrix of symmetric vector dyads.
G_rr=L_r L_r.T, Q_r=L_r^-1 V_r, and Y_r=L_r.T W_r.  Thus
W_r.T V_r=Y_r.T Q_r exactly.  This reparameterization does not change
the approximation family or submitted angle words.  The search objective
is the actual two-body residual, not any sampling score.
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
from dfthcsos.scoreinfra.dfthc_math import evaluate_dfthc_angle_words
from dfthcsos.scoreinfra.reference import UPPER_ENERGY


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--seconds',type=float,default=120.)
    p.add_argument('--iterations',type=int,default=500)
    args=p.parse_args()
    if args.out.exists() or args.out.with_suffix('.json').exists():
        raise FileExistsError(args.out)
    baseline=dict(np.load(ROOT/'dqi_inputs/chemistry_4033/submission_asterios_full.npz',allow_pickle=False))
    data=dict(np.load(args.source,allow_pickle=False))
    assert np.array_equal(data['angle_words'],baseline['angle_words'])
    assert np.array_equal(data['tree_edges'],baseline['tree_edges'])
    model=FixedAngles(baseline)
    r,b,c=data['W'].shape
    assert r==model.R and b==model.B
    ls=np.array([np.linalg.cholesky(model.G4[i,i]) for i in range(r)])
    qs=np.array([solve_triangular(ls[i],model.V[i*b:(i+1)*b],lower=True) for i in range(r)])
    orth=float(max(np.max(np.abs(q@q.T-np.eye(b))) for q in qs))
    assert orth<1e-7
    cross=np.array([[qs[i]@qs[j].T for j in range(r)] for i in range(r)])
    al=[]
    for i in range(r):
        aa=solve_triangular(ls[i],model.A[i],lower=True)
        al.append(solve_triangular(ls[i],aa.T,lower=True).T)
    aa=np.array(al)
    p0=ls.transpose(0,2,1)@model.P0@ls
    yy=ls.transpose(0,2,1)@data['W']
    scale=.02**2
    start=time.monotonic();calls=0;latest=yy.ravel().copy();trace=[]
    best=latest.copy();best_f=float('inf')

    class Budget(Exception):pass

    def objective(flat):
        nonlocal calls,best,best_f
        if time.monotonic()-start>args.seconds:raise Budget()
        calls+=1
        y=flat.reshape(r,b,c)
        delta=y@y.transpose(0,2,1)-p0
        kd=np.zeros_like(aa)
        for i in range(r):
            for j in range(r):
                gg=cross[i,j]
                kd[i]+=gg@delta[j]@gg.T
        f=float(model.e20+2*np.einsum('rij,rij->',aa,delta)+np.einsum('rij,rij->',kd,delta))/scale
        grad=4*(aa+kd)@y/scale
        if f<best_f:
            best_f=f;best=flat.copy()
        return f,grad.ravel()

    initial=objective(latest)
    original_packed=np.r_[data['W'].ravel(),data['H2_I'].ravel()]
    initial_original=model.evaluate(original_packed,c)[-1]
    print(json.dumps({'event':'initial','whitened_error2':float(np.sqrt(initial[0]*scale)),
                      'original_metrics':initial_original,'orthogonality_error':orth}),flush=True)
    rng=np.random.default_rng(20261114);direction=rng.normal(size=latest.size);direction/=np.linalg.norm(direction)
    eps=1e-6
    fd=(objective(latest+eps*direction)[0]-objective(latest-eps*direction)[0])/(2*eps)
    analytic=float(initial[1]@direction)
    gradient_error=abs(fd-analytic)/max(1.,abs(fd))
    print(json.dumps({'event':'gradient_check','finite_difference':fd,'analytic':analytic,'scaled_error':gradient_error}),flush=True)
    if gradient_error>1e-5:raise AssertionError('gradient check failed')

    def callback(flat):
        nonlocal latest
        latest=flat.copy()
        if len(trace)==0 or time.monotonic()-trace[-1]['seconds']-start>=10:
            row={'calls':calls,'best_error2':float(np.sqrt(max(best_f,0)*scale)),'seconds':time.monotonic()-start}
            trace.append(row);print(json.dumps(row),flush=True)

    try:
        opt=minimize(objective,latest,jac=True,method='L-BFGS-B',callback=callback,
                     options={'maxiter':args.iterations,'maxcor':20,'ftol':1e-14,'gtol':1e-9,'maxls':30})
        latest=opt.x;message=str(opt.message)
    except Budget:
        latest=best;message='time budget reached'
    y=latest.reshape(r,b,c)
    w=np.array([solve_triangular(ls[i].T,y[i],lower=False) for i in range(r)])
    # Keep the natural one-body offset d fixed during this two-body stage.
    d=data['H2_I']-data['W'].sum(1)
    data['W']=w;data['H2_I']=d+w.sum(1)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(args.out,**data)
    exact=evaluate_dfthc_angle_words(data['angle_words'],w,d,model.S,model.beta,model.ref,brot=8,tree_edges=data['tree_edges'],energy_upper=UPPER_ENERGY)
    report={'source':str(args.source),'source_sha256':hashlib.sha256(args.source.read_bytes()).hexdigest(),
            'candidate':str(args.out),'candidate_sha256':hashlib.sha256(args.out.read_bytes()).hexdigest(),
            'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'parameterization':'Y_r=L_r.T W_r; exact Cholesky whitening of V_r V_r.T',
            'orthogonality_error':orth,'gradient_check_error':gradient_error,'official_numeric_metrics':exact,
            'two_body_error_pass':bool(exact['error_2']<=.02),'full_circuit_verified':False,
            'calls':calls,'seconds':time.monotonic()-start,'termination':message,'trace':trace,
            'peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024}
    args.out.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


if __name__=='__main__':main()
