#!/usr/bin/env python3
"""Screen actual LSB XORs on supplied free-function address masks.

The search changes integer words. The two-body shortlist uses an exact low-rank
residual identity; a float64 norm bound screens the omitted quadratic residual
term. Reported patch costs are provisional until a loader builder proves them.
"""
from __future__ import annotations
import argparse, hashlib, json, resource, time
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment
from inverse_v2_chemistry_screen import ROOT
from score_chemistry_fast_model import FastFixedAngles
from score2_chemistry_discrete_screen import decoder_directions
from dfthcsos.scoreinfra.dfthc_math import reconstruct_u_vectors, evaluate_dfthc_angle_words
from dfthcsos.scoreinfra.reference import UPPER_ENERGY

HIGH_NEEDS_AND = {0,5,6,7,13,14,15,16,17,19,21,22,23,24,28,30,32,33,34,35,36,39,41,43,44,45,46,48,49,51,52,55,57,58,66,67,68,70,71,72,73,74,75,76}


def onebody_error(one, hp, vals, vec):
    rr, cc = linear_sum_assignment(-np.abs(one @ vec))
    match = np.empty(len(vals), dtype=int); match[rr] = cc
    rec = np.einsum('j,jp,jq->pq', vals[match], one, one, optimize=True)
    return float(np.linalg.norm(rec-hp))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=ROOT/'dqi_inputs/chemistry_4033/submission_asterios_full.npz')
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--shortlist',type=int,default=160)
    p.add_argument('--emit',type=int,default=6)
    p.add_argument('--patterns',type=Path,required=True,help='JSON list of name/addresses/provisional_added_task_toffoli fields')
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    start=time.monotonic();data=dict(np.load(a.source,allow_pickle=False));words=data['angle_words'].astype(np.int64)
    m=FastFixedAngles(data);w=data['W'];identity=data['H2_I'];offset=identity-w.sum(1)
    R,B,C=w.shape;N=m.N;D=len(m.rows)
    u=reconstruct_u_vectors(words/128.,data['tree_edges']);u/=np.linalg.norm(u,axis=1)[:,None]
    V=m.V;v3=V.reshape(R,B,D)
    coeff=np.einsum('rbc,rc->rb',w,offset).ravel()
    hp=m.hbase-(coeff@m.outer_flat).reshape(N,N);vals,vec=np.linalg.eigh(hp)
    lh2=.25*np.sum((np.abs(w).sum(1)+np.abs(identity))**2)
    e20=m.e20;baseline=m.evaluate(np.r_[w.ravel(),identity.ravel()],C,smooth=0.)[-1]
    if True:
        X=np.einsum('rbc,rbd->rcd',w,v3,optimize=True).reshape(R*C,D)
        target=m.ref['tei'][m.rows[:,None],m.cols[:,None],m.rows[None,:],m.cols[None,:]].copy()
        sl=m.S[m.rows,m.cols];diag=(m.rows==m.cols).astype(float)
        target+=.5*(np.outer(sl,diag)+np.outer(diag,sl));target*=m.scale[:,None]*m.scale[None,:]
        residual=X.T@X-target;del target
        S=(m.P0@v3).reshape(R*B,D)
        A=S@residual
        assert abs(float(np.sum(residual*residual))-e20)<1e-11
    screened=[]
    patterns=json.loads(a.patterns.read_text())
    for pattern_index,pattern in enumerate(patterns):
        addresses=np.array(pattern['addresses'],dtype=int)
        assert addresses.ndim==1 and 0<len(addresses)<=1220 and len(set(addresses.tolist()))==len(addresses)
        assert np.all((0<=addresses)&(addresses<len(words)))
        addresses=np.sort(addresses)
        ub,tangent,plane=decoder_directions(words[addresses],data['tree_edges'])
        sign=1-2*(words[addresses]&1)
        unew=ub[:,None,:]+(np.cos(np.pi/128.)-1)*plane+np.sin(np.pi/128.)*sign[:,:,None]*tangent
        unew/=np.linalg.norm(unew,axis=2)[:,:,None]
        body=addresses>=N;idx=addresses[body]-N
        if len(idx):
            gr=idx//B;bi=idx%B
            P=np.einsum('ic,jc->ij',w[gr,bi],w[gr,bi])*(gr[:,None]==gr[None,:])
            sb=S[idx];ab=A[idx];BB=sb@sb.T
        for t in range(5,75):
            if len(idx):
                un=unew[body,t];uo=ub[body]
                Q=(un[:,m.rows]*un[:,m.cols]-uo[:,m.rows]*uo[:,m.cols])*m.scale
                U=Q@Q.T;AA=Q@sb.T;PU=P@U
                last=float(np.trace(PU@PU))
                norm2=2*np.sum(U*BB)+2*np.trace(AA@AA)+4*np.trace(P@AA@U)+last
                estimate=float(4*np.sum(Q*ab)+norm2)
                bound=2*np.sqrt(e20)*np.sqrt(max(last,0.))
                hdelta=np.einsum('b,bi,bj->ij',coeff[idx],un,un,optimize=True)-np.einsum('b,bi,bj->ij',coeff[idx],uo,uo,optimize=True)
                hn=hp-hdelta;ev,eq=np.linalg.eigh(hn)
            else:
                estimate=bound=0.;hn=hp;ev=vals;eq=vec
            one=u[:N].copy();one[addresses[~body]]=unew[~body,t]
            e1=onebody_error(one,hn,ev,eq)
            lambda1=float(np.abs(ev).sum());lam=lambda1+lh2
            gap=float(m.gap_const+lambda1-ev.sum()+.5*np.sum(offset*offset))
            eff=float(np.sqrt(gap*(2*lam-gap))) if 0<gap<2*lam else None
            added=int(pattern.get('provisional_added_task_toffoli_last' if t//5==14 else 'provisional_added_task_toffoli',0))
            e2est=float(np.sqrt(max(e20+estimate,0.)));e2lower=float(np.sqrt(max(e20+estimate-bound,0.)));e2upper=float(np.sqrt(max(e20+estimate+bound,0.)))
            # This ranking is a heuristic only; final metrics use the full tensor.
            objective=200*(e2lower-.02)+2*(e1-.02)+added*46.906589508623554/14728
            screened.append({'pattern_index':pattern_index,'pattern':pattern['name'],'column':t,'addresses':addresses.tolist(),'changed_words':len(addresses),'has_two_body_changes':bool(len(idx)),'provisional_added_task_toffoli':added,'error1':e1,'e2_estimate':e2est,'e2_lower':e2lower,'e2_upper':e2upper,'e2_squared_estimate_change':estimate,'e2_squared_bound':float(bound),'Lambda':float(lam),'E_gap':gap,'lambda_eff':eff,'screen_objective':float(objective)})
        print(json.dumps({'event':'feature_mask_screen','pattern':pattern['name'],'tested':len(screened),'seconds':time.monotonic()-start}),flush=True)
    screened.sort(key=lambda r:r['screen_objective']);exact=[]
    # Preserve promising one-body cases as well as the error2-ranked shortlist.
    chosen=screened[:a.shortlist]
    for row in sorted((r for r in screened if not r['has_two_body_changes']),key=lambda r:r['error1'])[:20]:
        if row not in chosen:chosen.append(row)
    for row0 in chosen:
        row=dict(row0);addresses=np.array(row['addresses']);t=row['column'];table=words[addresses].copy();table[:,t]^=1
        un=reconstruct_u_vectors(table/128.,data['tree_edges']);un/=np.linalg.norm(un,axis=1)[:,None]
        idx=addresses[addresses>=N]-N
        if len(idx):
            gr=idx//B;bi=idx%B;P=np.einsum('ic,jc->ij',w[gr,bi],w[gr,bi])*(gr[:,None]==gr[None,:])
            uu=un[addresses>=N];uo=u[N+idx]
            Q=(uu[:,m.rows]*uu[:,m.cols]-uo[:,m.rows]*uo[:,m.cols])*m.scale
            qrq=Q@residual@Q.T
            change=row['e2_squared_estimate_change']+2*np.sum(P*qrq)
            assert abs(2*np.sum(P*qrq))<=row['e2_squared_bound']+1e-10
        else:change=0.
        e2=float(np.sqrt(max(e20+change,0.)));row['error2_exact_rank_update']=e2
        row['exact_shadow_objective']=200*(e2-.02)+2*(row['error1']-.02)+row['provisional_added_task_toffoli']*46.906589508623554/14728
        row['fixed_weights_numerically_feasible']=bool(e2<=.02 and row['error1']<=.02 and row['E_gap']>3.914898 and row['Lambda']>49)
        exact.append(row)
    exact.sort(key=lambda r:r['exact_shadow_objective']);emitted=[]
    for k,row in enumerate(exact[:a.emit]):
        dd={key:np.array(value,copy=True) for key,value in data.items()};dd['angle_words'][row['addresses'],row['column']]^=1
        path=a.out/f'candidate_{k:02d}.npz';np.savez_compressed(path,**dd)
        item=dict(row);item['candidate']=str(path);item['candidate_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        item['changes']=[{'address':int(ad),'column':row['column'],'old':int(words[ad,row['column']]),'value':int(dd['angle_words'][ad,row['column']])} for ad in row['addresses']]
        if k<2:
            mm=evaluate_dfthc_angle_words(dd['angle_words'],w,offset,m.S,m.beta,m.ref,brot=8,tree_edges=dd['tree_edges'],energy_upper=UPPER_ENERGY)
            item['official_numeric_metrics']=mm
            assert abs(mm['error_2']-row['error2_exact_rank_update'])<1e-9
            assert abs(mm['error_1']-row['error1'])<1e-9
        emitted.append(item)
    result={'status':'INTEGER_FEATURE_MASK_LSB_SCREEN','source':str(a.source),'source_sha256':hashlib.sha256(a.source.read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'baseline':baseline,'screened':len(screened),'exact_shortlist':len(exact),'patterns_file':str(a.patterns),'patterns_sha256':hashlib.sha256(a.patterns.read_bytes()).hexdigest(),'emitted':emitted,'best_exact':exact[:50],'bound_qualification':'Analytic Frobenius norm bound evaluated in float64; not interval arithmetic','patch_cost_qualification':'Feature-space prediction; final loader construction/proof required','all_changes_actual_integer_LSB_XOR':True,'all_tags_preserved':True,'full_circuit_verified':False,'seconds':time.monotonic()-start,'peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024}
    (a.out/'feature_screen.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in {'emitted','best_exact'}}),flush=True)


if __name__=='__main__':main()
