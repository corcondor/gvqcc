#!/usr/bin/env python3
"""Screen actual +/-1 eight-bit word changes with exact two-body rank updates.

For one changed projector v -> v+q, H2 changes by q s^T+s q^T+k q q^T.
All candidates use decoded integer words; derivatives only screen candidates.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import resource
import time
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment
from inverse_v2_chemistry_screen import ROOT
from score_chemistry_fast_model import FastFixedAngles
from dfthcsos.scoreinfra.dfthc_math import reconstruct_u_vectors,evaluate_dfthc_angle_words
from dfthcsos.scoreinfra.reference import UPPER_ENERGY


def decoder_directions(words,edges):
    """Return u and exact finite-angle sine/cosine directions for each word."""
    n,a=words.shape;N=a+1
    u=np.zeros((n,N));u[:,0]=1.
    tangent=np.zeros((n,a,N));plane=np.zeros_like(tangent)
    for t,(p,c) in enumerate(edges):
        theta=np.pi*words[:,t]/128.;co=np.cos(theta);si=np.sin(theta)
        up=u[:,p].copy();uc=u[:,c].copy()
        u[:,p]=co*up-si*uc;u[:,c]=si*up+co*uc
        if t:
            for tensor in (tangent,plane):
                vp=tensor[:,:t,p].copy();vc=tensor[:,:t,c].copy()
                tensor[:,:t,p]=co[:,None]*vp-si[:,None]*vc
                tensor[:,:t,c]=si[:,None]*vp+co[:,None]*vc
        tangent[:,t,p]=-u[:,c];tangent[:,t,c]=u[:,p]
        plane[:,t,p]=u[:,p];plane[:,t,c]=u[:,c]
    norm=np.linalg.norm(u,axis=1)
    return u/norm[:,None],tangent/norm[:,None,None],plane/norm[:,None,None]


def unvectorize(rows,cols,scale,v,N):
    out=np.zeros(v.shape[:-1]+(N,N))
    out[...,rows,cols]=v/scale
    out[...,cols,rows]=v/scale
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=ROOT/'dqi_inputs/chemistry_4033/submission_asterios_full.npz')
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--shortlist',type=int,default=1500)
    p.add_argument('--keep',type=int,default=40)
    p.add_argument('--emit',type=int,default=8)
    p.add_argument('--tag-changes',action='store_true')
    args=p.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    start=time.monotonic();data=dict(np.load(args.source,allow_pickle=False))
    words=data['angle_words'].astype(np.int64);edges=data['tree_edges']
    assert words.shape==(1220,75)
    model=FastFixedAngles(data)
    R,B,C=data['W'].shape;N=model.N;D=len(model.rows)
    w=data['W'];identity=data['H2_I'];offset=identity-w.sum(1)
    u=reconstruct_u_vectors(words/128.,edges);u/=np.linalg.norm(u,axis=1)[:,None]
    V=model.V;v3=V.reshape(R,B,D)
    X=np.einsum('rbc,rbd->rcd',w,v3,optimize=True).reshape(R*C,D)
    target=model.ref['tei'][model.rows[:,None],model.cols[:,None],model.rows[None,:],model.cols[None,:]].copy()
    sl=model.S[model.rows,model.cols];ident=(model.rows==model.cols).astype(float)
    target+=.5*(np.outer(sl,ident)+np.outer(ident,sl));target*=model.scale[:,None]*model.scale[None,:]
    residual=X.T@X-target;del target
    e20=float(np.einsum('ij,ij->',residual,residual));assert abs(e20-model.e20)<1e-12
    projected=V@residual
    S=(model.P0@v3).reshape(R*B,D)
    A=(model.P0@projected.reshape(R,B,D)).reshape(R*B,D)
    smat=unvectorize(model.rows,model.cols,model.scale,S,N)
    amat=unvectorize(model.rows,model.cols,model.scale,A,N)
    kappa=np.sum(w*w,axis=2).ravel();snorm=np.sum(S*S,axis=1)
    estimates=np.empty((R*B,75,2));bounds=np.empty_like(estimates)
    sine=np.sin(np.pi/128.);cosine=np.cos(np.pi/128.)-1.
    for lo in range(0,R*B,32):
        hi=min(R*B,lo+32)
        ub,tangent,plane=decoder_directions(words[N+lo:N+hi],edges)
        assert np.max(np.abs(ub-u[N+lo:N+hi]))<1e-12
        au=np.einsum('bij,bj->bi',amat[lo:hi],ub)
        su=np.einsum('bij,bj->bi',smat[lo:hi],ub)
        for sign_index,sgn in enumerate((-1,1)):
            du=cosine*plane+sgn*sine*tangent
            unew=ub[:,None,:]+du
            unew/=np.linalg.norm(unew,axis=2)[:,:,None]
            du=unew-ub[:,None,:]
            dua=np.einsum('bti,bij,btj->bt',du,amat[lo:hi],du,optimize=True)
            dus=np.einsum('bti,bij,btj->bt',du,smat[lo:hi],du,optimize=True)
            dotA=2*np.einsum('bti,bi->bt',du,au)+dua
            dotS=2*np.einsum('bti,bi->bt',du,su)+dus
            # Compute ||u'u'^T-uu^T||^2 from du to avoid cancellation near zero.
            h=np.einsum('bti,bi->bt',du,ub);dd=np.sum(du*du,axis=2)
            qnorm=2*dd+2*h*h+4*h*dd+dd*dd
            kk=kappa[lo:hi,None]
            change=4*dotA+2*snorm[lo:hi,None]*qnorm+2*dotS*dotS+4*kk*qnorm*dotS+kk*kk*qnorm*qnorm
            bound=2*kk*np.sqrt(e20)*qnorm
            estimates[lo:hi,:,sign_index]=change;bounds[lo:hi,:,sign_index]=bound
        if lo%256==0:print(json.dumps({'event':'screen','rows_done':hi,'seconds':time.monotonic()-start}),flush=True)
    allowed=np.ones_like(estimates,dtype=bool)
    for j,sgn in enumerate((-1,1)):
        old=words[N:];new=(old+sgn)%256
        tag0=((old>>6)^(old>>7))&1;tag1=((new>>6)^(new>>7))&1
        if not args.tag_changes:allowed[:,:,j]=tag0==tag1
    lower=estimates-bounds
    order=np.argsort(np.where(allowed,lower,np.inf).ravel())[:args.shortlist]
    records=[]
    basepacked=np.r_[w.ravel(),identity.ravel()];base_metrics=model.evaluate(basepacked,C,smooth=0.)[-1]
    coefficient=np.einsum('rbc,rc->rb',w,offset).ravel()
    hp=model.hbase-(coefficient@model.outer_flat).reshape(N,N)
    lambda_h2=.25*np.sum((np.abs(w).sum(1)+np.abs(identity))**2)
    for lo in range(0,len(order),128):
        selected=order[lo:lo+128]
        triplets=np.array(np.unravel_index(selected,estimates.shape)).T
        changed_words=np.array([words[N+i].copy() for i,t,j in triplets])
        for q,(i,t,j) in enumerate(triplets):changed_words[q,t]=(changed_words[q,t]+(-1 if j==0 else 1))%256
        candidate_u=reconstruct_u_vectors(changed_words/128.,edges);candidate_u/=np.linalg.norm(candidate_u,axis=1)[:,None]
        original_u=u[N+triplets[:,0]]
        dv=(candidate_u[:,model.rows]*candidate_u[:,model.cols]-original_u[:,model.rows]*original_u[:,model.cols])*model.scale
        qr=np.einsum('ij,ij->i',dv@residual,dv)
        qs=np.einsum('ij,ij->i',dv,S[triplets[:,0]])
        qa=np.einsum('ij,ij->i',dv,A[triplets[:,0]])
        qn=np.einsum('ij,ij->i',dv,dv);kk=kappa[triplets[:,0]]
        new_sq=e20+4*qa+2*kk*qr+2*snorm[triplets[:,0]]*qn+2*qs*qs+4*kk*qn*qs+kk*kk*qn*qn
        for q,(i,t,j) in enumerate(triplets):
            address=N+int(i);sgn=-1 if j==0 else 1
            old=int(words[address,t]);new=(old+sgn)%256
            deltaO=np.outer(candidate_u[q],candidate_u[q])-np.outer(original_u[q],original_u[q])
            hnew=hp-coefficient[i]*deltaO
            vals,vec=np.linalg.eigh(hnew);rr,cc=linear_sum_assignment(-np.abs(model.one@vec));match=np.empty(N,dtype=int);match[rr]=cc
            hrec=np.einsum('j,jp,jq->pq',vals[match],model.one,model.one,optimize=True)
            err1=float(np.linalg.norm(hrec-hnew));lh1=float(np.abs(vals).sum());lam=lh1+lambda_h2
            gap=float(model.gap_const+lh1-vals.sum()+.5*np.sum(offset*offset))
            eff=float(np.sqrt(gap*(2*lam-gap))) if 0<gap<2*lam else None
            records.append({'address':address,'angle':int(t),'batch':int(t//5),'step':sgn,'old_word':old,'new_word':new,'changed_bits':int(old^new).bit_count(),'tag_preserved':bool((((old>>6)^(old>>7))&1)==(((new>>6)^(new>>7))&1)),'error2_exact_rank_update':float(np.sqrt(max(new_sq[q],0.))),'error2_squared_change':float(new_sq[q]-e20),'screen_lower_change':float(lower[i,t,j]),'screen_upper_change':float(estimates[i,t,j]+bounds[i,t,j]),'fixed_weight_metrics':{'error_1':err1,'Lambda':lam,'E_gap':gap,'lambda_eff':eff},'estimated_added_task_toffoli':20 if t//5==14 else 40})
        if lo%512==0:print(json.dumps({'event':'exact_shortlist','done':min(lo+128,len(order)),'best_error2':min(r['error2_exact_rank_update'] for r in records),'seconds':time.monotonic()-start}),flush=True)
    records.sort(key=lambda item:item['error2_exact_rank_update'])
    emitted=[]
    for idx,row in enumerate(records[:args.emit]):
        candidate=dict(data);table=words.copy();table[row['address'],row['angle']]=row['new_word'];candidate['angle_words']=table.astype(data['angle_words'].dtype)
        path=args.out/f'candidate_{idx:02d}.npz';np.savez_compressed(path,**candidate)
        item=dict(row);item['candidate']=str(path);item['candidate_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        # The leading two cases receive an independent full tensor evaluation.
        if idx<2:
            metrics=evaluate_dfthc_angle_words(candidate['angle_words'],w,offset,model.S,model.beta,model.ref,brot=8,tree_edges=edges,energy_upper=UPPER_ENERGY)
            item['official_numeric_metrics']=metrics
            assert abs(metrics['error_2']-row['error2_exact_rank_update'])<1e-9
            assert abs(metrics['error_1']-row['fixed_weight_metrics']['error_1'])<1e-9
        emitted.append(item)
    for row in records:
        assert row['screen_lower_change']-1e-10<=row['error2_squared_change']<=row['screen_upper_change']+1e-10
    report={'status':'INTEGER_WORD_SCREEN_COMPLETED','source':str(args.source),'source_sha256':hashlib.sha256(args.source.read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'baseline_metrics':base_metrics,'screened_word_moves':int(np.sum(allowed)),'exact_shortlist_moves':len(records),'all_moves_are_integer_mod256':True,'tag_changes_allowed':args.tag_changes,'negative_analytic_upper_bound_moves':int(np.sum((estimates+bounds<0)&allowed)),'bound_floating_point_qualification':'Analytic norm bound evaluated in float64, not interval arithmetic','shortlist_error2_improvements':int(sum(r['error2_exact_rank_update']<np.sqrt(e20)-1e-12 for r in records)),'best_moves':records[:args.keep],'emitted':emitted,'seconds':time.monotonic()-start,'peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,'full_circuit_verified':False,'not_an_exhaustive_joint_angle_optimization':True}
    (args.out/'screen.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in {'best_moves','emitted'}}),flush=True)


if __name__=='__main__':main()
