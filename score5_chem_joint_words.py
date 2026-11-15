#!/usr/bin/env python3
"""Combine a bounded sparse integer-word shortlist and refit its rank-43 W.

The 4030 circuits are not locally available.  Feature-patch counts below are
explicitly conditional on their having the old proved feature interface.
Generic-patch counts are also recorded; no new full-circuit PASS is claimed.
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
from score2_angle_sparse_patch import estimate_family
from dfthcsos.scoreinfra.dfthc_math import reconstruct_u_vectors,evaluate_dfthc_angle_words
from dfthcsos.scoreinfra.reference import UPPER_ENERGY


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--original-c44',type=Path,required=True)
    p.add_argument('--screen',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--seconds',type=float,default=30.)
    p.add_argument('--max-changes',type=int,default=20)
    p.add_argument('--max-added-t',type=int,default=76)
    a=p.parse_args()
    if a.out.exists(): raise FileExistsError(a.out)
    a.out.mkdir(parents=True)
    started=time.monotonic()
    source=dict(np.load(a.source,allow_pickle=False))
    data={k:np.array(v,copy=True) for k,v in source.items()}
    full=dict(np.load(a.original_c44,allow_pickle=False))
    screen=json.loads(a.screen.read_text())
    assert sha(a.source)==screen['source_sha256']
    assert np.array_equal(data['angle_words'],full['angle_words'])
    assert data['W'].shape==(8,143,43) and full['W'].shape==(8,143,44)
    old_words=data['angle_words'].copy()
    assert hashlib.sha256(old_words.astype(np.uint8).tobytes()).hexdigest()=='8caf7416de79102103757e3ab7ab4b6bbebfad9b1bf1ecd564c20eb948dbfcea'
    # The first experiment used an SVD gauge.  Re-express its factors in the
    # near-original Householder gauge without changing XX.T, H1, or error2.
    uold=reconstruct_u_vectors(old_words/128.,data['tree_edges'])
    uold/=np.linalg.norm(uold,axis=1)[:,None]
    gcheck=[]
    for r in range(8):
        u=uold[76+143*r:76+143*(r+1)]
        L=np.linalg.cholesky((u@u.T)**2)
        _,_,vh=np.linalg.svd(L.T@full['W'][r],full_matrices=False)
        drop=vh[-1].copy();j=int(np.argmax(np.abs(drop)))
        e=np.zeros(44);e[j]=-np.copysign(1.,drop[j])
        h=drop-e;h/=np.linalg.norm(h)
        hh=np.eye(44)-2*np.outer(h,h)
        keep=[k for k in range(44) if k!=j]
        rotate=vh[:43]@hh[:,keep]
        assert np.max(np.abs(rotate@rotate.T-np.eye(43)))<1e-10
        old_aug=np.concatenate([data['W'][r],data['H2_I'][r:r+1]],axis=0)
        new_aug=old_aug@rotate
        gcheck.append(float(np.max(np.abs(old_aug@old_aug.T-new_aug@new_aug.T))))
        data['W'][r],data['H2_I'][r]=new_aug[:-1],new_aug[-1]
    assert max(gcheck)<1e-10
    choices=[];addresses=set()
    rows=screen['best_exact_moves']
    for row in rows:
        if len(choices)>=a.max_changes: break
        address,t=int(row['address']),int(row['angle'])
        if address in addresses or row['error2_exact_transport']>=screen['baseline_metrics']['error2']: continue
        assert row['tag_preserved'] and int(old_words[address,t])==row['old_word']
        trial=data['angle_words'].copy();trial[address,t]=row['new_word']
        cost=estimate_family(old_words,trial,feature_patches=True)
        if cost['added_official_toffoli_both_passes']>a.max_added_t: continue
        data['angle_words']=trial;addresses.add(address)
        choices.append({k:row[k] for k in ['address','angle','old_word','new_word','step','error2_exact_transport']})
    if not choices: raise ValueError('No improving integer move under the stated budget')
    changed=data['angle_words']
    feature_cost=estimate_family(old_words,changed,feature_patches=True)
    generic_cost=estimate_family(old_words,changed,feature_patches=False)
    assert np.count_nonzero(changed!=old_words)==len(choices)<=a.max_changes
    assert np.array_equal(((changed>>6)^(changed>>7))&1,((old_words>>6)^(old_words>>7))&1)
    unew=reconstruct_u_vectors(changed/128.,data['tree_edges'])
    unew/=np.linalg.norm(unew,axis=1)[:,None]
    natural=data['H2_I']-data['W'].sum(1)
    projection_residuals=[]
    # Joint row-space projection for ALL changes in a rho, not the sum of
    # independent rank-one updates evaluated at the old table.
    for r in range(8):
        lo,hi=76+r*143,76+(r+1)*143
        uu,vv=unew[lo:hi],uold[lo:hi]
        g=(uu@uu.T)**2;cross=(uu@vv.T)**2
        L=np.linalg.cholesky(g)
        rhs=cross@data['W'][r]
        first=solve_triangular(L,rhs,lower=True)
        fresh=solve_triangular(L.T,first,lower=False)
        projection_residuals.append(float(np.max(np.abs(g@fresh-rhs))))
        data['W'][r]=fresh
    data['H2_I']=natural+data['W'].sum(1)
    data['U']=unew[76:].reshape(8,143,76)
    np.savez_compressed(a.out/'transport.npz',**data)
    (a.out/'changes.json').write_text(json.dumps([dict(address=x['address'],column=x['angle'],old=x['old_word'],value=x['new_word']) for x in choices],indent=2)+'\n')
    model=FixedAngles(data)
    r,b,c=data['W'].shape
    ls=np.array([np.linalg.cholesky(model.G4[i,i]) for i in range(r)])
    qs=np.array([solve_triangular(ls[i],model.V[i*b:(i+1)*b],lower=True) for i in range(r)])
    cross=np.array([[qs[i]@qs[j].T for j in range(r)] for i in range(r)])
    aa=[]
    for i in range(r):
        first=solve_triangular(ls[i],model.A[i],lower=True)
        aa.append(solve_triangular(ls[i],first.T,lower=True).T)
    aa=np.array(aa)
    y0=ls.transpose(0,2,1)@data['W'];p0=y0@y0.transpose(0,2,1)
    d0=data['H2_I']-data['W'].sum(1)
    best=y0.ravel().copy();best_f=float('inf');calls=0;trace=[];scale=.02**2
    start=time.monotonic()
    class Budget(Exception): pass
    class Feasible(Exception): pass
    def objective(flat,budget=True):
        nonlocal best,best_f,calls
        if budget and time.monotonic()-start>a.seconds: raise Budget()
        calls+=1;y=flat.reshape(r,b,c);delta=y@y.transpose(0,2,1)-p0
        kd=np.zeros_like(aa)
        for i in range(r):
            for j in range(r):
                gg=cross[i,j];kd[i]+=gg@delta[j]@gg.T
        f=float(model.e20+2*np.einsum('rij,rij->',aa,delta)+np.einsum('rij,rij->',kd,delta))/scale
        grad=4*(aa+kd)@y/scale
        if f<best_f: best_f,best=f,flat.copy()
        return f,grad.ravel()
    initial=objective(y0.ravel(),False)
    direction=np.cos(np.arange(best.size)+.5);direction/=np.linalg.norm(direction)
    center=y0.ravel();step=1e-6
    fd=(objective(center+step*direction,False)[0]-objective(center-step*direction,False)[0])/(2*step)
    analytic=float(initial[1]@direction);derr=abs(fd-analytic)/max(1.,abs(fd))
    assert derr<1e-5
    best,best_f=center.copy(),initial[0];start=time.monotonic()
    print(json.dumps(dict(event='joint_initial',changes=len(choices),feature_added_T_conditional=feature_cost['added_official_toffoli_both_passes'],generic_added_T=generic_cost['added_official_toffoli_both_passes'],initial_error2=float(np.sqrt(initial[0]*scale)),gradient_error=derr,seconds=start-started)),flush=True)
    def save_candidate(flat,path):
        result=dict(data);y=flat.reshape(r,b,c)
        result['W']=np.array([solve_triangular(ls[i].T,y[i],lower=False) for i in range(r)])
        result['H2_I']=d0+result['W'].sum(1)
        np.savez_compressed(path,**result)
        return result
    def callback(flat):
        elapsed=time.monotonic()-start
        if not trace or elapsed-trace[-1]['seconds']>=10:
            row=dict(calls=calls,best_error2=float(np.sqrt(max(best_f,0)*scale)),seconds=elapsed)
            trace.append(row);print(json.dumps(row),flush=True)
            save_candidate(best,a.out/'checkpoint.npz')
        if best_f*scale < .0199999**2: raise Feasible()
    try:
        opt=minimize(objective,center,jac=True,method='L-BFGS-B',callback=callback,
            options=dict(maxiter=4000,maxcor=20,ftol=1e-14,gtol=1e-9,maxls=30))
        termination=str(opt.message)
    except Budget: termination='bounded W refit complete'
    except Feasible: termination='two-body reserve reached; H2 restoration required'
    refit_seconds=time.monotonic()-start
    candidate=save_candidate(best,a.out/'candidate.npz')
    metrics=evaluate_dfthc_angle_words(candidate['angle_words'],candidate['W'],candidate['H2_I']-candidate['W'].sum(1),model.S,model.beta,model.ref,brot=8,tree_edges=candidate['tree_edges'],energy_upper=UPPER_ENERGY)
    assert abs(metrics['error_2']-np.sqrt(best_f*scale))<1e-9
    added=feature_cost['added_official_toffoli_both_passes']
    report=dict(status='TWO_BODY_FEASIBLE_NEEDS_OTHER_GATES' if metrics['error_2']<=.02 else 'SPARSE_WORD_JOINT_REFIT_NOT_FEASIBLE',
        source_path=str(a.source),source_sha256=sha(a.source),screen_sha256=sha(a.screen),original_c44_sha256=sha(a.original_c44),
        choices=choices,changed_words=len(choices),all_changes_are_integer_words=True,tags_preserved=True,
        feature_patch_cost=feature_cost,feature_cost_scope='CONDITIONAL old4033 feature profile; v27 KMB not locally inspected',
        generic_patch_cost=generic_cost,total_T_if_feature_profile_matches=14644+added,Q_if_profile_matches=427,
        source_error2=screen['baseline_metrics']['error2'],transport_error2=float(np.sqrt(initial[0]*scale)),
        source_gauge_gram_max_error=max(gcheck),projection_normal_equation_max_error=max(projection_residuals),
        gradient_check=dict(fd=fd,analytic=analytic,scaled_error=derr),official_numeric_metrics=metrics,
        refit_seconds=refit_seconds,total_seconds=time.monotonic()-started,calls=calls,termination=termination,trace=trace,
        full_circuit_verified=False,loader_candidate_generated=False,new_accepted_score_improvement=False,
        candidate_path=str(a.out/'candidate.npz'),candidate_sha256=sha(a.out/'candidate.npz'),
        script_sha256=sha(__file__),peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
    (a.out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in {'choices','feature_patch_cost','generic_patch_cost','trace'}}),flush=True)


if __name__=='__main__': main()
