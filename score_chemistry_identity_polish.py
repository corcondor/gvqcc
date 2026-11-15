#!/usr/bin/env python3
"""Polish 352 H2_I coordinates with W and all decoded angle words fixed.

error_2 is independent of H2_I. A feasible W can therefore be held fixed
while the small smooth constrained problem restores the gap/error_1 tradeoff.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import resource
import time
from pathlib import Path
import numpy as np
from scipy.optimize import minimize, linear_sum_assignment
from inverse_v2_chemistry_refit import FixedAngles
from inverse_v2_chemistry_screen import ROOT
from dfthcsos.scoreinfra.dfthc_math import evaluate_dfthc_angle_words
from dfthcsos.scoreinfra.reference import UPPER_ENERGY


class FixedW:
    def __init__(self,model,data):
        self.model=model
        self.w=data['W']
        self.wsum=self.w.sum(1).ravel()
        self.l1w=np.abs(self.w).sum(1).ravel()
        self.x=np.einsum('rbc,rbpq->rcpq',self.w,model.outer.reshape(model.R,model.B,model.N,model.N),optimize=True).reshape(-1,model.N,model.N)
        self.reference=46.906589508623554
        self.calls=0
    def evaluate(self,ii):
        self.calls+=1
        m=self.model;d=ii-self.wsum
        hp=m.hbase-np.einsum('i,ipq->pq',d,self.x)
        vals,vec=np.linalg.eigh(hp)
        rr,cc=linear_sum_assignment(-np.abs(m.one@vec))
        match=np.empty(m.N,dtype=int);match[rr]=cc
        rec=np.einsum('j,jp,jq->pq',vals[match],m.one,m.one,optimize=True)
        e=rec-hp
        e1=float(np.einsum('ij,ij->',e,e))
        weights=np.empty(m.N)
        weights[match]=np.einsum('jp,pq,jq->j',m.one,e,m.one,optimize=True)
        a1=2*((vec*weights)@vec.T-e)
        sign=(vec*np.sign(vals))@vec.T
        lh1=float(np.abs(vals).sum())
        l1=self.l1w+np.abs(ii)
        lam=lh1+.25*float(l1@l1)
        gap=float(m.gap_const+lh1-vals.sum()+.5*(d@d))
        rad=gap*(2*lam-gap)
        f=rad/(2*self.reference)
        gl=-np.einsum('pq,ipq->i',sign,self.x)+.5*l1*np.sign(ii)
        gg=-np.einsum('pq,ipq->i',sign-np.eye(m.N),self.x)+d
        ge=-np.einsum('pq,ipq->i',a1,self.x)
        g=(gap*gl+(lam-gap)*gg)/self.reference
        constraints=np.array([1-e1/(.01999998**2),(gap-3.91489802)/.01])
        jac=np.array([-ge/(.01999998**2),gg/.01])
        metrics={'lambda_eff':float(np.sqrt(rad)) if rad>0 else None,'Lambda':lam,'E_gap':gap,'error_1':float(np.sqrt(e1))}
        return f,g,constraints,jac,metrics


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--iterations',type=int,default=300)
    p.add_argument('--seconds',type=float,default=120)
    a=p.parse_args()
    start=time.monotonic();script_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    data=dict(np.load(a.source,allow_pickle=False))
    baseline=dict(np.load(ROOT/'dqi_inputs/chemistry_4033/submission_asterios_full.npz',allow_pickle=False))
    assert np.array_equal(data['angle_words'],baseline['angle_words'])
    assert np.array_equal(data['tree_edges'],baseline['tree_edges'])
    full=FixedAngles(baseline)
    model=FixedW(full,data)
    x=data['H2_I'].ravel().copy()
    initial=model.evaluate(x)
    print(json.dumps({'event':'initial','metrics':initial[-1],'constraints':initial[2].tolist()}),flush=True)
    rng=np.random.default_rng(37);d=rng.normal(size=x.size);d/=np.linalg.norm(d);h=1e-6
    plus=model.evaluate(x+h*d);minus=model.evaluate(x-h*d)
    fd=np.r_[(plus[0]-minus[0])/(2*h),(plus[2]-minus[2])/(2*h)]
    an=np.r_[initial[1]@d,initial[3]@d]
    gradient_error=float(np.max(np.abs(fd-an)/np.maximum(1,np.abs(fd))))
    print(json.dumps({'event':'gradient_check','fd':fd.tolist(),'analytic':an.tolist(),'scaled_error':gradient_error}),flush=True)
    assert gradient_error<1e-3
    best=x.copy() if np.min(initial[2])>=0 else None
    best_value=initial[0] if best is not None else float('inf')
    latest=x.copy();trace=[];cache_x=None;cache_result=None
    class Budget(Exception):pass
    def evaluate(xx):
        nonlocal cache_x,cache_result
        if time.monotonic()-start>a.seconds:raise Budget()
        if cache_x is None or not np.array_equal(xx,cache_x):
            cache_x=xx.copy();cache_result=model.evaluate(xx)
        return cache_result
    def callback(xx):
        nonlocal best,best_value,latest
        latest=xx.copy();rr=evaluate(xx)
        row={'iteration':len(trace)+1,'metrics':rr[-1],'constraints':rr[2].tolist(),'seconds':time.monotonic()-start}
        trace.append(row)
        if len(trace)%10==0:print(json.dumps(row),flush=True)
        if np.min(rr[2])>=0 and rr[0]<best_value:
            best=xx.copy();best_value=rr[0]
    try:
        opt=minimize(lambda xx:evaluate(xx)[:2],x,jac=True,method='SLSQP',constraints=[{'type':'ineq','fun':lambda xx:evaluate(xx)[2],'jac':lambda xx:evaluate(xx)[3]}],callback=callback,options={'maxiter':a.iterations,'ftol':1e-12,'disp':False})
        latest=opt.x;termination=str(opt.message)
    except Budget:termination='time budget'
    chosen=best if best is not None else latest
    data['H2_I']=chosen.reshape(data['H2_I'].shape)
    metrics=evaluate_dfthc_angle_words(data['angle_words'],data['W'],data['H2_I']-data['W'].sum(1),full.S,full.beta,full.ref,brot=8,tree_edges=data['tree_edges'],energy_upper=UPPER_ENERGY)
    passed=bool(metrics['error_1']<=.020 and metrics['error_2']<=.020 and metrics['Lambda']>49 and metrics['E_gap']>3.914898 and metrics['gap_in_domain'] and np.isfinite(metrics['lambda_eff']))
    a.out.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(a.out,**data)
    report={'source':str(a.source),'source_sha256':hashlib.sha256(a.source.read_bytes()).hexdigest(),'script_sha256':script_sha,'candidate':str(a.out),'candidate_sha256':hashlib.sha256(a.out.read_bytes()).hexdigest(),'official_numeric_metrics':metrics,'official_numeric_thresholds_pass':passed,'W_unchanged':True,'angle_words_unchanged':True,'full_circuit_verified':False,'gradient_scaled_error':gradient_error,'termination':termination,'calls':model.calls,'seconds':time.monotonic()-start,'peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,'trace':trace}
    a.out.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='trace'}),flush=True)


if __name__=='__main__':main()
