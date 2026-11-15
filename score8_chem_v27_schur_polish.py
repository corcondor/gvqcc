#!/usr/bin/env python3
"""Relax frozen eigenvectors to a six-equation Schur-complement constraint."""
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
WORDS=Path(__file__).with_name('score8_chem_v27_recovered_words.npy')
START=Path('/workspace/scratch/3815fb5fae06/score8_chem_v27_actual_nullspace3/best.npz')

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
    p.add_argument('--seconds',type=float,default=180.);p.add_argument('--start',type=Path,default=START)
    p.add_argument('--radius',type=float,default=.03);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    started=time.monotonic();original=dict(np.load(BASE));data=dict(original);data['angle_words']=np.load(WORDS).astype(original['angle_words'].dtype)
    model=FastFixedAngles(data);small=FixedW(model,data);xpub=data['H2_I'].ravel()
    initial_h=model.hbase-np.einsum('i,ipq->pq',xpub-small.wsum,small.x)
    vals,vec=np.linalg.eigh(initial_h);ids=np.argsort(abs(vals));U=vec[:,ids[:3]];V=vec[:,ids[3:]]
    sr,sc=np.tril_indices(3);weight=np.where(sr==sc,1.,np.sqrt(2.));target=U.T@initial_h@U
    target_error=.019999998;target_gap=3.914898002;eq_scale=.001
    x0=np.load(a.start)['H2_I'].ravel();latest=x0.copy();best=x0.copy();trace=[]
    def ev(x):
        f,g,con,J,metrics=small.evaluate(x)
        ratio=(.01999998/target_error)**2;con[0]=1-(1-con[0])*ratio;J[0]*=ratio
        con[1]+=(3.91489802-target_gap)/.01
        hp=model.hbase-np.einsum('i,ipq->pq',x-small.wsum,small.x)
        aa=U.T@hp@U;bb=U.T@hp@V;dd=V.T@hp@V;sol=np.linalg.solve(dd,bb.T)
        schur=aa-bb@sol-target;eff=U-V@sol
        coeff=np.einsum('ipq,pk,ql->ikl',small.x,eff,eff,optimize=True)
        ec=schur[sr,sc]*weight/eq_scale;ej=-(coeff[:,sr,sc]*weight).T/eq_scale
        return f,g,con,J,ec,ej,metrics
    initial=ev(x0);best_value=initial[0]
    tangent=null_space(initial[5],rcond=1e-10);rng=np.random.default_rng(2026111588)
    direction=tangent@rng.normal(size=tangent.shape[1]);direction/=np.linalg.norm(direction)
    checks=[]
    for step in (1e-4,1e-5,1e-6,1e-7):
        pp=ev(x0+step*direction);mm=ev(x0-step*direction)
        fd=np.r_[(pp[0]-mm[0])/(2*step),(pp[2]-mm[2])/(2*step),(pp[4]-mm[4])/(2*step)]
        an=np.r_[initial[1]@direction,initial[3]@direction,initial[5]@direction]
        checks.append(dict(step=step,fd=fd.tolist(),analytic=an.tolist(),scaled_error=float(np.max(abs(fd-an)/np.maximum(1,abs(fd))))))
    check_error=min(x['scaled_error'] for x in checks)
    preparation=dict(event='prepared',initial=initial[-1],initial_schur_residual=float(np.max(abs(initial[4]))),
        tangent_dimension=tangent.shape[1],gradient_checks=checks,gradient_error=check_error,seconds=time.monotonic()-started)
    print(json.dumps(preparation),flush=True)
    if check_error>1e-3:raise RuntimeError('Tangent derivative check failed')
    opt_start=time.monotonic();cache_x=None;cache_result=None
    class Budget(Exception):pass
    def evaluate(x):
        nonlocal cache_x,cache_result
        if time.monotonic()-opt_start>a.seconds:raise Budget()
        if cache_x is None or not np.array_equal(x,cache_x):cache_x=x.copy();cache_result=ev(x)
        return cache_result
    def callback(x):
        nonlocal latest,best,best_value
        latest=x.copy();v=evaluate(x);metrics=v[-1]
        if min(v[2])>=-1e-8 and max(abs(v[4]))<1e-8 and v[0]<best_value:
            best,best_value=x.copy(),v[0];out=dict(original);out['H2_I']=best.reshape(8,44);np.savez_compressed(a.out/'checkpoint.npz',**out)
        row=dict(iteration=len(trace)+1,metrics=metrics,constraints=v[2].tolist(),schur_residual=float(np.max(abs(v[4]))),seconds=time.monotonic()-opt_start)
        trace.append(row)
        if len(trace)%10==0:print(json.dumps(row),flush=True)
    try:
        opt=minimize(lambda x:evaluate(x)[:2],x0,jac=True,method='SLSQP',
            constraints=[dict(type='ineq',fun=lambda x:evaluate(x)[2],jac=lambda x:evaluate(x)[3]),
                         dict(type='eq',fun=lambda x:evaluate(x)[4],jac=lambda x:evaluate(x)[5])],
            bounds=list(zip(x0-a.radius,x0+a.radius)),callback=callback,options=dict(maxiter=1000,ftol=2e-13,disp=False))
        latest=opt.x;termination=str(opt.message)
    except Budget:termination='bounded Schur optimization complete'
    rows=[]
    for label,x in [('best',best),('latest',latest)]:
        result=dict(original);result['H2_I']=x.reshape(8,44)
        metrics=evaluate_dfthc_angle_words(data['angle_words'],result['W'],result['H2_I']-result['W'].sum(1),model.S,model.beta,model.ref,
            brot=8,tree_edges=data['tree_edges'],energy_upper=UPPER_ENERGY)
        passed=metrics['error_1']<=.02 and metrics['error_2']<=.02 and metrics['E_gap']>3.914898 and metrics['Lambda']>49 and metrics['gap_in_domain']
        path=a.out/(label+'.npz');np.savez_compressed(path,**result)
        row=dict(label=label,path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),official_numeric_metrics=metrics,
            numeric_pass=bool(passed),improves_start=bool(passed and metrics['lambda_eff']<initial[-1]['lambda_eff']),
            cost=metrics['lambda_eff']*14722*427 if passed else None,H2_I_change_from_start=float(np.linalg.norm(x-x0)),
            exact_schur_residual=float(np.max(abs(ev(x)[4]))),full_circuit_verified=False)
        rows.append(row);print(json.dumps(row),flush=True)
    report=dict(status='ACTUAL_V27_SCHUR_COMPLEMENT_IDENTITY_POLISH',source=str(BASE),source_sha256=hashlib.sha256(BASE.read_bytes()).hexdigest(),
        start=str(a.start),start_sha256=hashlib.sha256(a.start.read_bytes()).hexdigest(),preparation=preparation,termination=termination,
        trace=trace,candidates=rows,seconds=time.monotonic()-started,submitted_arrays_changed=['H2_I'],
        authoritative_word_raw_sha256=hashlib.sha256(np.load(WORDS).tobytes()).hexdigest())
    (a.out/'results.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
