#!/usr/bin/env python3
"""Constrained H2_I-only refit, with fixed FeMoCo ANGLE data and exact physics.

Usage:
 python research/chemistry_h2_constrained_refit.py submission.npz \
  --verifier-root /path/to/official_verifiers --output candidate.npz

This does NOT run Kickmix, is NOT a full submission verifier, and does not
claim to fix any DQI failures. Requires numpy and scipy.
"""
import argparse
import hashlib
import json
import sys
import numpy as np
from scipy.optimize import linear_sum_assignment


def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        while b:=f.read(1<<20):
            h.update(b)
    return h.hexdigest()


def run(args):
    sys.path.insert(0,str(args.verifier_root.resolve()))
    from dfthcsos.scoreinfra.reference import (
        load_reference,load_fixed_shifts,PACKAGED_FCIDUMP,UPPER_ENERGY)
    from dfthcsos.scoreinfra.dfthc_math import (
        symmetric_from_lower,reconstruct_u_vectors,split_u_vectors,
        reconstruct_x,evaluate_dfthc_angle_words)
    with np.load(args.source,allow_pickle=False) as a:
        original={k:a[k].copy() for k in a.files}
    p=dict(original)
    p.update(load_fixed_shifts())  # Submitted shift fields are ignored.
    ref=load_reference(PACKAGED_FCIDUMP)
    N=int(ref['orbitals'])
    S=np.asarray(symmetric_from_lower(p['Hsym_lower'],N),dtype='float64')
    beta=float(p['H1_I'])-float(np.trace(S))/2
    w=np.asarray(p['W'],dtype='float64')
    wsum=w.sum(axis=1)
    W0=np.asarray(p['H2_I'],dtype='float64')-wsum
    words=p['angle_words']
    edges=p['tree_edges']
    brot=int(p['brot'])
    u=reconstruct_u_vectors(words/(1<<(brot-1)),edges)
    u/=np.linalg.norm(u,axis=1,keepdims=True)
    one,ub=split_u_vectors(u,w)
    X=reconstruct_x(ub,w)
    X=np.tril(X)+np.swapaxes(np.tril(X,k=-1),-1,-2)
    X=X.reshape(-1,N,N)
    h1=ref['oei']-.5*np.einsum('prrq->pq',ref['tei'])
    M0=h1-.5*ref['electrons']*S+beta*np.eye(N)
    wl1=np.sum(np.abs(w),axis=1)
    # Exactly-zero H2_I coordinates are held fixed for the nonsmooth L1 term.
    fixed=np.flatnonzero(np.abs(p['H2_I'].ravel())<1e-8)
    def fast(x):
        W=x.reshape(W0.shape)
        M=M0-np.einsum('x,xpq->pq',x,X,optimize=True)
        ev,V=np.linalg.eigh(M)
        rows,cols=linear_sum_assignment(-np.abs(one@V))
        paired=np.empty(N)
        paired[rows]=ev[cols]
        restored=np.einsum('j,jp,jq->pq',paired,one,one,optimize=True)
        err1=float(np.linalg.norm(restored-M))
        lam1=float(np.abs(ev).sum())
        lam2=float(.25*np.square(wl1+np.abs(W+wsum)).sum())
        L=lam1+lam2
        eso=float(ref['ecore']-ref['electrons']*beta-(lam1-ev.sum())-.5*np.square(W).sum())
        gap=float(UPPER_ENERGY-eso)
        score=float(np.sqrt(gap*(2*L-gap))) if 0<gap<2*L else float('inf')
        return score,err1
    def physics(x):
        return evaluate_dfthc_angle_words(words,w,x.reshape(W0.shape),S,beta,ref,
            brot=brot,tree_edges=edges,energy_upper=UPPER_ENERGY)
    x=W0.ravel().copy()
    start=physics(x)
    if not(start['error_1']<=.02 and start['error_2']<=.02 and start['gap_in_domain']):
        raise ValueError('Source parameters not physically admissible')
    if abs(fast(x)[0]-start['lambda_eff'])>1e-8:
        raise AssertionError('Native H2_I coordinate interpretation mismatch')
    history=[]
    for iteration in range(args.iterations):
        base=fast(x)[0]
        grad=np.zeros_like(x)
        egrad=np.zeros_like(x)
        for j in range(len(x)):
            if j in fixed: continue
            delta=np.zeros_like(x)
            delta[j]=1e-5
            plus=fast(x+delta)
            minus=fast(x-delta)
            grad[j]=(plus[0]-minus[0])/(2e-5)
            egrad[j]=(plus[1]-minus[1])/(2e-5)
        M=M0-np.einsum('x,xpq->pq',x,X,optimize=True)
        ev,V=np.linalg.eigh(M)
        Z=V[:,np.argsort(np.abs(ev))[:2]]
        C=np.array([-np.einsum('p,apq,q->a',Z[:,i],X,Z[:,j])
            for i,j in ((0,0),(0,1),(1,1))])
        C[:,fixed]=0
        def tangent(y):
            z=y-C.T@np.linalg.lstsq(C@C.T,C@y,rcond=None)[0]
            z[fixed]=0
            return z
        g=tangent(grad)
        ge=tangent(egrad)
        best=None
        for alpha in (-3,-1,0,.25,.5,1,2):
            direction=-(g+alpha*ge)
            norm=np.linalg.norm(direction)
            if norm<1e-15: continue
            direction/=norm
            for step in (5e-5,1e-4,2e-4,5e-4,.001,.002,.003,.004,
                         .006,.008,.01,.015,.02):
                trial=x+step*direction
                value,err1=fast(trial)
                if err1<=.01999999995 and value<base-1e-10:
                    if best is None or value<best[0]:
                        best=(value,trial.copy(),err1)
        if best is None: break
        x=best[1]
        history.append({'iteration':iteration,'lambda_eff':best[0],'error_1':best[2]})
    after=physics(x)
    if not(after['error_1']<.02 and after['error_2']<.02 and
           after['gap_in_domain'] and after['lambda_eff']<start['lambda_eff']):
        raise AssertionError('No feasible improved physics candidate')
    if abs(fast(x)[0]-after['lambda_eff'])>1e-8:
        raise AssertionError('Independent official physics mismatch')
    output=dict(original)
    output['H2_I']=(x.reshape(W0.shape)+wsum).astype(original['H2_I'].dtype)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(args.output,**output)
    record={'source_sha256':sha(args.source),'candidate_sha256':sha(args.output),
            'status':'PHYSICS_ONLY; NATIVE_VERIFIER_NOT_RUN',
            'changed':['H2_I'], 'iterations':len(history),
            'before':{k:float(v) if not isinstance(v,(bool,np.bool_)) else bool(v)
                      for k,v in start.items()},
            'after':{k:float(v) if not isinstance(v,(bool,np.bool_)) else bool(v)
                     for k,v in after.items()},
            'trace':history}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({k:record[k] for k in ('source_sha256','candidate_sha256',
                     'status','iterations','before','after')},indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('source',type=__import__('pathlib').Path)
    ap.add_argument('--verifier-root',type=__import__('pathlib').Path,required=True)
    ap.add_argument('--output',type=__import__('pathlib').Path,required=True)
    ap.add_argument('--report',type=__import__('pathlib').Path,required=True)
    ap.add_argument('--iterations',type=int,default=20)
    run(ap.parse_args())
