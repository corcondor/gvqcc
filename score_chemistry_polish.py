#!/usr/bin/env python3
"""Fixed-word C44 polish with analytic constraints and feasible checkpoints.

The submitted angle_words and every other array except W/H2_I are preserved.
This is a numerical search; only the unchanged official evaluator determines
whether a saved factorization is feasible. Circuit files are never modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import resource
import time
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

from inverse_v2_chemistry_refit import FixedAngles
from inverse_v2_chemistry_screen import ROOT
from dfthcsos.scoreinfra.dfthc_math import evaluate_dfthc_angle_words
from dfthcsos.scoreinfra.reference import UPPER_ENERGY


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=ROOT/'dqi_inputs/chemistry_4033/submission_asterios_full.npz')
    p.add_argument('--baseline',type=Path,default=ROOT/'dqi_inputs/chemistry_4033/submission_asterios_full.npz')
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--seconds',type=float,default=240)
    p.add_argument('--iterations',type=int,default=100)
    p.add_argument('--smooth',type=float,default=1e-5)
    p.add_argument('--penalties',default='2,10,50,250,1250,6250')
    p.add_argument('--objective-weight',type=float,default=1)
    p.add_argument('--gap-equality',action='store_true',help='restore E_gap to its internal target from either side')
    p.add_argument('--offset-coordinates',action='store_true',help='optimize W,d where H2_I=d+sum_b W')
    p.add_argument('--whiten-weights',action='store_true',help='optimize Y=L.T W where V_r V_r.T=L L.T')
    p.add_argument('--fast-model',action='store_true',help='use validated contracted h1/gradient evaluation')
    p.add_argument('--initial-lag',default='0,0,0',help='initial augmented-Lagrangian multipliers')
    p.add_argument('--eigen-smooth',type=float,default=0.,help='smooth h1 trace norm and reserve N*epsilon in the gap constraint')
    p.add_argument('--lambda-budget',type=float,help='add an explicit upper bound on the smooth lambda_eff')
    p.add_argument('--branch-release',action='store_true',help='take a bounded lower-violation step off a detected assignment discontinuity, then recheck derivatives')
    args=p.parse_args()
    if not np.isfinite(args.smooth) or args.smooth<0 or not np.isfinite(args.eigen_smooth) or args.eigen_smooth<0:
        raise ValueError('smoothing widths must be finite and nonnegative')
    if args.lambda_budget is not None and (not np.isfinite(args.lambda_budget) or args.lambda_budget<=0):
        raise ValueError('lambda budget must be finite and positive')
    script_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out.mkdir(parents=True,exist_ok=True)
    baseline=dict(np.load(args.baseline,allow_pickle=False))
    data=dict(np.load(args.source,allow_pickle=False))
    assert np.array_equal(data['angle_words'],baseline['angle_words'])
    assert np.array_equal(data['tree_edges'],baseline['tree_edges'])
    if args.fast_model:
        from score_chemistry_fast_model import FastFixedAngles
        model=FastFixedAngles(baseline,eigen_smooth=args.eigen_smooth)
    else:
        assert args.eigen_smooth==0.,'--eigen-smooth requires --fast-model'
        model=FixedAngles(baseline)
    c=data['W'].shape[2]
    if args.whiten_weights:
        cholesky=np.linalg.cholesky(np.array([model.G4[r,r] for r in range(model.R)]))
        to_w=np.linalg.inv(cholesky).transpose(0,2,1)
        weights0=cholesky.transpose(0,2,1)@data['W']
    else:weights0=data['W']
    identity0=data['H2_I']-data['W'].sum(1) if args.offset_coordinates else data['H2_I']
    x=np.r_[weights0.ravel(),identity0.ravel()]
    size=data['W'].size
    best=None
    best_eff=float('inf')
    trace=[]
    start=time.monotonic()
    evaluation_time=0.

    def physical(xx):
        if not (args.offset_coordinates or args.whiten_weights):return xx
        ww=xx[:size].reshape(data['W'].shape)
        if args.whiten_weights:ww=to_w@ww
        ii=xx[size:].reshape(data['H2_I'].shape)
        if args.offset_coordinates:ii=ii+ww.sum(1)
        return np.r_[ww.ravel(),ii.ravel()]

    def chain_gradient(gradient):
        gw=gradient[:size].reshape(data['W'].shape)
        gi=gradient[size:].reshape(data['H2_I'].shape)
        if args.offset_coordinates:gw=gw+gi[:,None,:]
        if args.whiten_weights:gw=to_w.transpose(0,2,1)@gw
        return np.r_[gw.ravel(),gi.ravel()]

    def evaluate(xx,smooth=args.smooth):
        nonlocal evaluation_time
        t=time.monotonic()
        result=model.evaluate(physical(xx),c,smooth=smooth)
        if args.offset_coordinates or args.whiten_weights:
            ff,gg,cc,jj,mm=result
            result=(ff,chain_gradient(gg),cc,np.array([chain_gradient(row) for row in jj]),mm)
        if args.lambda_budget is not None:
            ff,gg,cc,jj,mm=result
            result=(ff,gg,np.r_[cc,(ff-args.lambda_budget)/.01],np.vstack([jj,gg/.01]),mm)
        evaluation_time+=time.monotonic()-t
        return result

    def save(xx,name):
        dd=dict(data)
        pp=physical(xx)
        dd['W']=pp[:size].reshape(data['W'].shape)
        dd['H2_I']=pp[size:].reshape(data['H2_I'].shape)
        path=args.out/(name+'.npz')
        temporary=args.out/('.'+name+'.npz.tmp')
        with temporary.open('wb') as handle:np.savez_compressed(handle,**dd)
        temporary.replace(path)
        return path

    def candidate(xx,metrics,con,label):
        nonlocal best,best_eff
        # The optimization targets 20 nHa of margin; checkpoints use 5 nHa.
        # This allows a converging penalty method to save a valid point before
        # it reaches its stricter internal target exactly.
        feasible=(metrics['error1']<=.019999995 and metrics['error2']<=.019999995 and metrics['gap']>=3.914898005)
        if args.lambda_budget is not None:feasible=feasible and metrics['lambda_eff_smooth']<=args.lambda_budget
        if feasible:
            exact=evaluate(xx,0.)
            em=exact[-1]
            exact_feasible=(em['error1']<=.019999995 and em['error2']<=.019999995 and em['gap']>=3.914898005 and em['Lambda_smooth']>49 and np.isfinite(exact[0]))
            if args.lambda_budget is not None:exact_feasible=exact_feasible and exact[0]<=args.lambda_budget
            if exact_feasible and exact[0]<best_eff:
                best=xx.copy();best_eff=exact[0]
                save(best,'best_feasible')
                print(json.dumps({'event':'best_feasible','label':label,'metrics':exact[-1],'seconds':time.monotonic()-start}),flush=True)

    initial=evaluate(x)
    objective_reference=initial[0]
    print(json.dumps({'event':'initial','metrics':initial[-1],'constraints':initial[2].tolist()}),flush=True)
    candidate(x,initial[-1],initial[2],'initial')
    # One directional check catches convention/shape mistakes in a new source.
    rng=np.random.default_rng(20261114)
    direction=rng.normal(size=x.size);direction/=np.linalg.norm(direction)
    gradient_checks=[]
    branch_releases=[]
    for attempt in range(3):
        an=np.r_[initial[1]@direction,initial[3]@direction]
        probes=[];changed=False
        for step in (1e-6,1e-7,1e-8,1e-9):
            plus=evaluate(x+step*direction)
            plus_assignment=getattr(model,'last_assignment',None)
            minus=evaluate(x-step*direction)
            minus_assignment=getattr(model,'last_assignment',None)
            if step==1e-6:probes=[(step,plus),(-step,minus)]
            fd=np.r_[(plus[0]-minus[0])/(2*step),(plus[2]-minus[2])/(2*step)]
            gradient_error=float(np.max(np.abs(fd-an)/np.maximum(1,np.abs(fd))))
            changes=sum(a!=b for a,b in zip(plus_assignment,minus_assignment)) if plus_assignment is not None else None
            changed=changed or bool(changes)
            row={'event':'gradient_check','attempt':attempt,'step':step,'finite_difference':fd.tolist(),'analytic':an.tolist(),'scaled_error':gradient_error,'assignment_changes':changes}
            if changes:
                row['plus_error1']=plus[-1]['error1'];row['minus_error1']=minus[-1]['error1']
            gradient_checks.append(row);print(json.dumps(row),flush=True)
            if gradient_error<1e-3:break
        if gradient_error<1e-3:break
        if not args.branch_release or not changed or attempt==2:break
        def merit(result):
            violation=np.maximum(result[2],0.)
            return float(violation@violation)
        eligible=[(step,result) for step,result in probes if result[-1]['error1']<=max(.020,initial[-1]['error1']) and merit(result)<merit(initial)-1e-15]
        if not eligible:break
        step,result=min(eligible,key=lambda item:merit(item[1]))
        row={'event':'assignment_boundary_release','parameter_step':step,'old_merit':merit(initial),'new_merit':merit(result),'old_metrics':initial[-1],'new_metrics':result[-1]}
        branch_releases.append(row);print(json.dumps(row),flush=True)
        x=x+step*direction;initial=result;objective_reference=initial[0]
    if gradient_error>=1e-3:
        (args.out/'gradient_failure.json').write_text(json.dumps({'source':str(args.source),'script_sha256':script_sha,'gradient_checks':gradient_checks,'branch_releases':branch_releases},indent=2)+'\n')
        raise AssertionError('directional derivative gate failed; no optimization was run')
    lag=np.array([float(v) for v in args.initial_lag.split(',')])
    assert lag.shape==initial[2].shape
    latest=x.copy()
    accepted_count=0
    class Budget(Exception):pass
    for outer,penalty in enumerate(float(y) for y in args.penalties.split(',')):
        latest=x.copy()
        stage_calls=0
        def objective(xx):
            nonlocal stage_calls
            if time.monotonic()-start>args.seconds:raise Budget()
            eff,g,con,cg,metrics=evaluate(xx)
            stage_calls+=1
            shifted=np.maximum(0,lag+penalty*con)
            if args.gap_equality:shifted[2]=lag[2]+penalty*con[2]
            # The square is order-equivalent on the accepted positive domain.
            # Unlike the legacy sqrt clamp, its extension gives line search
            # finite derivatives when a rejected trial crosses E_gap=0.
            gap=metrics['gap'];lam=metrics['Lambda_smooth']
            f=gap*(2*lam-gap)/(2*objective_reference)
            gradient=g*(eff/objective_reference)
            return (args.objective_weight*f+(shifted@shifted-lag@lag)/(2*penalty),args.objective_weight*gradient+shifted@cg)
        def accepted(xx):
            nonlocal latest,accepted_count
            latest=xx.copy()
            # Evaluation is inexpensive relative to the long search, and this
            # keeps an admissible intermediate point if a later stage regresses.
            result=evaluate(xx)
            accepted_count+=1
            if accepted_count%25==0:
                print(json.dumps({'event':'accepted_step','step':accepted_count,'outer':outer,'metrics':result[-1],'constraints':result[2].tolist(),'seconds':time.monotonic()-start}),flush=True)
            candidate(xx,result[-1],result[2],f'outer{outer}')
        try:
            opt=minimize(objective,x,jac=True,method='L-BFGS-B',callback=accepted,options={'maxiter':args.iterations,'maxcor':20,'ftol':1e-14,'gtol':1e-8,'maxls':30})
            x=opt.x;message=str(opt.message)
        except Budget:
            x=latest;message='time budget'
        result=evaluate(x)
        next_lag=lag+penalty*result[2]
        lag=np.maximum(0,next_lag)
        if args.gap_equality:lag[2]=next_lag[2]
        row={'outer':outer,'penalty':penalty,'metrics':result[-1],'constraints':result[2].tolist(),'lag':lag.tolist(),'calls':stage_calls,'seconds':time.monotonic()-start,'message':message}
        trace.append(row);print(json.dumps(row),flush=True)
        save(x,'latest')
        candidate(x,result[-1],result[2],f'end{outer}')
        if time.monotonic()-start>args.seconds:break

    reports=[]
    for name,xx in [('latest',x)]+([('best_feasible',best)] if best is not None else []):
        pp=physical(xx)
        dd=dict(data);dd['W']=pp[:size].reshape(data['W'].shape);dd['H2_I']=pp[size:].reshape(data['H2_I'].shape)
        metrics=evaluate_dfthc_angle_words(dd['angle_words'],dd['W'],dd['H2_I']-dd['W'].sum(1),model.S,model.beta,model.ref,brot=8,tree_edges=dd['tree_edges'],energy_upper=UPPER_ENERGY)
        path=save(xx,name)
        numeric_pass=bool(metrics['error_1']<=.020 and metrics['error_2']<=.020 and metrics['Lambda']>49.0 and metrics['E_gap']>3.914898 and metrics['gap_in_domain'] and np.isfinite(metrics['lambda_eff']))
        row={'name':name,'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'official_numeric_metrics':metrics,'official_numeric_thresholds_pass':numeric_pass,'exact_angle_words_unchanged':bool(np.array_equal(dd['angle_words'],baseline['angle_words'])),'full_circuit_verified':False}
        reports.append(row);print(json.dumps(row),flush=True)
    report={'source':str(args.source),'source_sha256':hashlib.sha256(args.source.read_bytes()).hexdigest(),'baseline':str(args.baseline),'script_sha256':script_sha,'smooth':args.smooth,'eigen_smooth':args.eigen_smooth,'objective_weight':args.objective_weight,'lambda_budget':args.lambda_budget,'gap_equality':args.gap_equality,'offset_coordinates':args.offset_coordinates,'whiten_weights':args.whiten_weights,'fast_model':args.fast_model,'initial_lag':args.initial_lag,'gradient_scaled_error':gradient_error,'gradient_checks':gradient_checks,'branch_releases':branch_releases,'trace':trace,'candidates':reports,'seconds':time.monotonic()-start,'evaluation_seconds':evaluation_time,'calls':model.calls,'peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024}
    (args.out/'results.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
