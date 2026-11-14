#!/usr/bin/env python3
"""Refit H2_I against an actually changed integer angle table, keeping W fixed."""
from __future__ import annotations
import argparse,hashlib,json,time,resource
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from inverse_v2_chemistry_screen import ROOT
from score_chemistry_fast_model import FastFixedAngles
from score_chemistry_identity_polish import FixedW
from dfthcsos.scoreinfra.dfthc_math import evaluate_dfthc_angle_words
from dfthcsos.scoreinfra.reference import UPPER_ENERGY


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--added-toffoli',type=int,default=8)
    p.add_argument('--iterations',type=int,default=600)
    p.add_argument('--seconds',type=float,default=90.)
    args=p.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    start=time.monotonic();data=dict(np.load(args.source,allow_pickle=False))
    old=dict(np.load(ROOT/'dqi_inputs/chemistry_4033/submission_asterios_full.npz',allow_pickle=False))
    assert np.array_equal(data['tree_edges'],old['tree_edges'])
    locations=np.argwhere(data['angle_words']!=old['angle_words'])
    changes=[{'address':int(a),'column':int(t),'old':int(old['angle_words'][a,t]),'value':int(data['angle_words'][a,t])} for a,t in locations]
    assert len(changes)>0
    base=FastFixedAngles(data);model=FixedW(base,data)
    fixed_error2=float(np.sqrt(base.e20));x=data['H2_I'].ravel().copy()
    initial=model.evaluate(x);print(json.dumps({'event':'initial','metrics':initial[-1],'error2':fixed_error2,'changes':changes}),flush=True)
    rng=np.random.default_rng(37);direction=rng.normal(size=x.size);direction/=np.linalg.norm(direction)
    analytic=np.r_[initial[1]@direction,initial[3]@direction];checks=[]
    for h in (1e-6,1e-7,1e-8):
        plus=model.evaluate(x+h*direction);minus=model.evaluate(x-h*direction)
        fd=np.r_[(plus[0]-minus[0])/(2*h),(plus[2]-minus[2])/(2*h)]
        error=float(np.max(np.abs(fd-analytic)/np.maximum(1,np.abs(fd))))
        checks.append({'step':h,'finite_difference':fd.tolist(),'analytic':analytic.tolist(),'scaled_error':error})
        if error<1e-3:break
    print(json.dumps({'event':'derivative_check','checks':checks}),flush=True)
    assert error<1e-3
    best=None;best_value=float('inf');trace=[];latest=x.copy();cached_x=None;cached=None
    def feasible(result):
        mm=result[-1]
        return fixed_error2<=.02 and mm['error_1']<=.019999995 and mm['E_gap']>=3.914898005 and mm['Lambda']>49 and mm['lambda_eff'] is not None
    def accept(xx,rr,label):
        nonlocal best,best_value
        if feasible(rr) and rr[0]<best_value:
            best=xx.copy();best_value=rr[0]
            print(json.dumps({'event':'feasible','label':label,'metrics':rr[-1]}),flush=True)
    accept(x,initial,'initial')
    class Budget(Exception):pass
    def evaluate(xx):
        nonlocal cached_x,cached
        if time.monotonic()-start>args.seconds:raise Budget()
        if cached_x is None or not np.array_equal(xx,cached_x):cached_x=xx.copy();cached=model.evaluate(xx)
        return cached
    def callback(xx):
        nonlocal latest
        latest=xx.copy();rr=evaluate(xx);accept(xx,rr,'iterate')
        if len(trace)%25==0:print(json.dumps({'iteration':len(trace)+1,'metrics':rr[-1],'seconds':time.monotonic()-start}),flush=True)
        trace.append({'metrics':rr[-1],'constraints':rr[2].tolist()})
    try:
        opt=minimize(lambda xx:evaluate(xx)[:2],x,jac=True,method='SLSQP',constraints=[{'type':'ineq','fun':lambda xx:evaluate(xx)[2],'jac':lambda xx:evaluate(xx)[3]}],callback=callback,options={'maxiter':args.iterations,'ftol':1e-12,'disp':False})
        latest=opt.x;termination=str(opt.message)
        accept(latest,model.evaluate(latest),'endpoint')
    except Budget:termination='time budget'
    chosen=best if best is not None else latest;data['H2_I']=chosen.reshape(data['H2_I'].shape)
    metrics=evaluate_dfthc_angle_words(data['angle_words'],data['W'],data['H2_I']-data['W'].sum(1),base.S,base.beta,base.ref,brot=8,tree_edges=data['tree_edges'],energy_upper=UPPER_ENERGY)
    passed=bool(metrics['error_1']<=.02 and metrics['error_2']<=.02 and metrics['E_gap']>3.914898 and metrics['Lambda']>49 and metrics['gap_in_domain'] and np.isfinite(metrics['lambda_eff']))
    path=args.out/'candidate.npz';np.savez_compressed(path,**data)
    report={'status':'NUMERICAL_PASS' if passed else 'NUMERICAL_FAIL','source':str(args.source),'source_sha256':hashlib.sha256(args.source.read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'candidate':str(path),'candidate_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'changes':changes,'changed_words':len(changes),'changed_addresses':len({c['address'] for c in changes}),'official_numeric_metrics':metrics,'provisional_added_task_toffoli':args.added_toffoli,'comparison_cost_with_provisional_patch':metrics['lambda_eff']*(14728+args.added_toffoli)*427,'break_even_lambda_for_reproduced_baseline':46.906589508623554*14728/(14728+args.added_toffoli),'provisional_net_improvement':bool(passed and metrics['lambda_eff']*(14728+args.added_toffoli)<46.906589508623554*14728),'gradient_checks':checks,'termination':termination,'iterations':len(trace),'calls':model.calls,'seconds':time.monotonic()-start,'peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,'W_fixed_during_this_refit':True,'integer_words_fixed_during_this_refit':True,'full_circuit_verified':False,'trace':trace}
    (args.out/'refit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='trace'}),flush=True)


if __name__=='__main__':main()
