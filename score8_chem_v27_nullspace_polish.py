#!/usr/bin/env python3
"""Stable fixed-W v27 polish in a frozen small-eigenspace affine nullspace.

For fixed W, h1_prime is affine in H2_I.  Impose delta(h1_prime) V0=0
exactly as linear equations, where V0 spans the near-zero eigenvectors.
This preserves their eigenvalues and eigenvectors and removes the spectral
absolute-value/assignment instability from the remaining optimization.
All acceptance values come from the unchanged official numeric evaluator.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
from pathlib import Path
import argparse,hashlib,json,time
import numpy as np
from scipy.linalg import null_space
from scipy.optimize import minimize
from score_chemistry_fast_model import FastFixedAngles
from score_chemistry_identity_polish import FixedW
from dfthcsos.scoreinfra.dfthc_math import evaluate_dfthc_angle_words
from dfthcsos.scoreinfra.reference import UPPER_ENERGY

BASE=Path('/workspace/scratch/3815fb5fae06/score8_v27_chemistry/submission.npz')

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,default=BASE);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--seconds',type=float,default=100.);p.add_argument('--small-count',type=int,default=3)
    p.add_argument('--words',type=Path,help='Authoritative circuit-recovered table; NPZ declaration is not trusted')
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False);started=time.monotonic()
    original=dict(np.load(a.source));data=dict(original)
    if a.words:data['angle_words']=np.load(a.words).astype(original['angle_words'].dtype)
    model=FastFixedAngles(data);small=FixedW(model,data);x0=data['H2_I'].ravel().copy()
    initial=small.evaluate(x0);hp=model.hbase-np.einsum('i,ipq->pq',x0-small.wsum,small.x)
    vals,vec=np.linalg.eigh(hp);order=np.argsort(abs(vals));v0=vec[:,order[:a.small_count]]
    constraints=np.einsum('ipq,qk->ipk',small.x,v0,optimize=True).reshape(x0.size,-1).T
    Z=null_space(constraints,rcond=1e-11)
    maximum_residual=float(np.max(abs(constraints@Z))) if Z.size else 0.
    assert maximum_residual<1e-9
    target_error=.019999998;target_gap=3.914898002
    def ev(z):
        x=x0+Z@z;f,g,c,J,met=small.evaluate(x)
        ratio=(.01999998/target_error)**2;c[0]=1-(1-c[0])*ratio;J[0]*=ratio
        c[1]+=(3.91489802-target_gap)/.01
        return f,Z.T@g,c,J@Z,met
    z0=np.zeros(Z.shape[1]);v=ev(z0);rng=np.random.default_rng(2026111573);direction=rng.normal(size=z0.size);direction/=np.linalg.norm(direction)
    checks=[]
    for step in (1e-4,1e-5,1e-6,1e-7):
        pp=ev(z0+step*direction);mm=ev(z0-step*direction)
        fd=np.r_[(pp[0]-mm[0])/(2*step),(pp[2]-mm[2])/(2*step)];an=np.r_[v[1]@direction,v[3]@direction]
        error=float(np.max(abs(fd-an)/np.maximum(1,abs(fd))));checks.append(dict(step=step,fd=fd.tolist(),analytic=an.tolist(),scaled_error=error))
    gradient_error=min(row['scaled_error'] for row in checks)
    preparation=dict(event='prepared',source_sha256=hashlib.sha256(a.source.read_bytes()).hexdigest(),
        baseline_metrics=initial[-1],smallest_eigenvalues=vals[order[:10]].tolist(),frozen_count=a.small_count,
        constraint_shape=list(constraints.shape),free_dimension=Z.shape[1],nullspace_maximum_residual=maximum_residual,
        projected_objective_gradient_norm=float(np.linalg.norm(v[1])),gradient_checks=checks,gradient_error=gradient_error,
        actual_word_sha256=hashlib.sha256(data['angle_words'].astype(np.uint8).tobytes()).hexdigest(),
        declared_word_differences=int(np.count_nonzero(data['angle_words']!=original['angle_words'])),
        seconds=time.monotonic()-started)
    print(json.dumps(preparation),flush=True)
    if gradient_error>1e-4:raise RuntimeError('Reduced derivative check did not resolve spectral instability')
    if a.words and (abs(initial[-1]['lambda_eff']-46.909726478631555)>1e-7 or model.e20>.02**2):
        raise RuntimeError('Authoritative public v27 baseline was not reproduced')
    opt_start=time.monotonic();latest=z0.copy();best=None;bestf=np.inf;trace=[];cache_x=None;cache_value=None
    class Budget(Exception):pass
    def evaluate(z):
        nonlocal cache_x,cache_value
        if time.monotonic()-opt_start>a.seconds:raise Budget()
        if cache_x is None or not np.array_equal(z,cache_x):cache_x=z.copy();cache_value=ev(z)
        return cache_value
    def callback(z):
        nonlocal latest,best,bestf
        latest=z.copy();result=evaluate(z);f,g,c,J,met=result
        if np.min(c)>-1e-9 and f<bestf:
            best,bestf=z.copy(),f
            dd=dict(original);dd['H2_I']=(x0+Z@z).reshape(data['H2_I'].shape);np.savez_compressed(a.out/'checkpoint.npz',**dd)
        row=dict(iteration=len(trace)+1,metrics=met,constraints=c.tolist(),seconds=time.monotonic()-opt_start)
        trace.append(row)
        if len(trace)%10==0:print(json.dumps(row),flush=True)
    try:
        opt=minimize(lambda z:evaluate(z)[:2],z0,jac=True,method='SLSQP',
            constraints=[dict(type='ineq',fun=lambda z:evaluate(z)[2],jac=lambda z:evaluate(z)[3])],
            callback=callback,options=dict(maxiter=500,ftol=1e-14,disp=False))
        latest=opt.x;termination=str(opt.message)
    except Budget:termination='bounded nullspace optimization complete'
    records=[]
    for label,z in [('best',best),('latest',latest)]:
        if z is None:continue
        result=dict(original);result['H2_I']=(x0+Z@z).reshape(data['H2_I'].shape)
        metrics=evaluate_dfthc_angle_words(data['angle_words'],result['W'],result['H2_I']-result['W'].sum(1),model.S,model.beta,model.ref,
            brot=8,tree_edges=result['tree_edges'],energy_upper=UPPER_ENERGY)
        passed=metrics['error_1']<=.02 and metrics['error_2']<=.02 and metrics['E_gap']>3.914898 and metrics['Lambda']>49 and metrics['gap_in_domain']
        path=a.out/(label+'.npz');np.savez_compressed(path,**result)
        row=dict(label=label,path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),official_numeric_metrics=metrics,
            numeric_pass=bool(passed),improved=bool(passed and metrics['lambda_eff']<initial[-1]['lambda_eff']),
            cost=metrics['lambda_eff']*14722*427 if passed else None,
            H2_I_change_norm=float(np.linalg.norm(result['H2_I']-data['H2_I'])),
            frozen_subspace_action_change_maximum=float(np.max(abs(constraints@(Z@z)))),full_circuit_verified=False)
        records.append(row);print(json.dumps(row),flush=True)
    report=dict(status='EXACT_PINNED_V27_FROZEN_EIGENSPACE_POLISH',preparation=preparation,candidates=records,
        termination=termination,trace=trace,seconds=time.monotonic()-started,source=str(a.source),
        source_sha256=hashlib.sha256(a.source.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        authoritative_words_path=str(a.words) if a.words else None,submitted_arrays_changed=['H2_I'],
        declared_word_table_preserved=True,physical_angle_circuit_unchanged=True)
    (a.out/'results.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
