#!/usr/bin/env python3
"""Bounded integer free-mask search with exact multi-row LS weight transport.

For each affected group, V_new=V+E Q, and the least-squares weights are
W_new=(V_new V_new.T)^-1 V_new V.T W. This preserves the old represented
columns as closely as the new feature span permits. All candidates change
actual integer LSBs; a low-rank H2 identity supplies the exact shortlist.
"""
from __future__ import annotations
import argparse,hashlib,json,resource,time
from pathlib import Path
import numpy as np
from scipy.linalg import cho_factor,cho_solve
from inverse_v2_chemistry_screen import ROOT
from score_chemistry_fast_model import FastFixedAngles
from score2_chemistry_block_screen import onebody_error
from score2_chemistry_discrete_screen import unvectorize
from dfthcsos.scoreinfra.dfthc_math import reconstruct_u_vectors,evaluate_dfthc_angle_words
from dfthcsos.scoreinfra.reference import UPPER_ENERGY


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=ROOT/'dqi_inputs/chemistry_4033/submission_asterios_full.npz')
    p.add_argument('--patterns',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--columns',default='70,71,72,73,74')
    p.add_argument('--seconds',type=float,default=120.)
    p.add_argument('--shortlist',type=int,default=48)
    p.add_argument('--emit',type=int,default=5)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);start=time.monotonic()
    script_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    data=dict(np.load(a.source,allow_pickle=False));words=data['angle_words'].astype(np.int64)
    patterns=json.loads(a.patterns.read_text());columns=[int(v) for v in a.columns.split(',')]
    assert len(columns)==len(set(columns)) and all(5<=t<75 for t in columns)
    m=FastFixedAngles(data);w=data['W'];ii=data['H2_I'];d=ii-w.sum(1)
    R,B,C=w.shape;N=m.N;D=len(m.rows);v3=m.V.reshape(R,B,D)
    u=reconstruct_u_vectors(words/128.,data['tree_edges']);u/=np.linalg.norm(u,axis=1)[:,None]
    X=np.einsum('rbc,rbd->rcd',w,v3,optimize=True).reshape(R*C,D)
    target=m.ref['tei'][m.rows[:,None],m.cols[:,None],m.rows[None,:],m.cols[None,:]].copy()
    sl=m.S[m.rows,m.cols];diag=(m.rows==m.cols).astype(float)
    target+=.5*(np.outer(sl,diag)+np.outer(diag,sl));target*=m.scale[:,None]*m.scale[None,:]
    residual=X.T@X-target;del target
    e20=float(np.sum(residual*residual));assert abs(e20-m.e20)<1e-11
    XR=X@residual;X3=X.reshape(R,C,D);XR3=XR.reshape(R,C,D)
    coefficient=np.einsum('rbc,rc->rb',w,d).ravel()
    hp=m.hbase-(coefficient@m.outer_flat).reshape(N,N)
    lambda2=.25*np.sum((np.abs(w).sum(1)+np.abs(ii))**2,axis=1)
    baseline=m.evaluate(np.r_[w.ravel(),ii.ravel()],C,smooth=0.)[-1]
    base_eff=baseline['lambda_eff_smooth']

    def transport(pattern,t,exact=False):
        addresses=np.sort(np.array(pattern['addresses'],dtype=int))
        assert len(set(addresses.tolist()))==len(addresses) and np.all((0<=addresses)&(addresses<len(words)))
        table=words[addresses].copy();table[:,t]^=1
        un=reconstruct_u_vectors(table/128.,data['tree_edges']);un/=np.linalg.norm(un,axis=1)[:,None]
        body=addresses>=N;groups=sorted(set(((addresses[body]-N)//B).tolist()))
        if not groups:return None
        ww=w.copy();iinew=ii.copy();deltas=[];xs=[];xrs=[];orthogonality=[]
        for r in groups:
            select=body&(((addresses-N)//B)==r);b=(addresses[select]-N)%B
            uu=un[select];uo=u[addresses[select]]
            Q=(uu[:,m.rows]*uu[:,m.cols]-uo[:,m.rows]*uo[:,m.cols])*m.scale
            J=Q@v3[r].T;U=Q@Q.T;G=m.G4[r,r]
            cross=G.copy();cross[b]+=J
            Gnew=cross.copy();Gnew[:,b]+=J.T;Gnew[np.ix_(b,b)]+=U
            Gnew=(Gnew+Gnew.T)/2
            wr=cho_solve(cho_factor(Gnew,lower=True,check_finite=False),cross@w[r],check_finite=False)
            dx=(wr-w[r]).T@v3[r]+wr[b].T@Q
            ww[r]=wr;iinew[r]=d[r]+wr.sum(0)
            deltas.append(dx);xs.append(X3[r]);xrs.append(XR3[r])
            if exact:
                vn=v3[r].copy();vn[b]+=Q
                orthogonality.append(float(np.max(np.abs(vn@dx.T))))
        dx=np.concatenate(deltas);xx=np.concatenate(xs);xr=np.concatenate(xrs)
        U=dx@dx.T;A=dx@xx.T;G=xx@xx.T
        norm2=float(2*np.sum(U*G)+2*np.trace(A@A)+4*np.trace(A@U)+np.sum(U*U))
        estimate=float(4*np.sum(dx*xr)+norm2)
        bound=float(2*np.sqrt(e20)*np.sqrt(np.sum(U*U)))
        hchange=sum((d[r]@delta for r,delta in zip(groups,deltas)),start=np.zeros(D))
        hn=hp-unvectorize(m.rows,m.cols,m.scale,hchange,N)
        vals,vec=np.linalg.eigh(hn);one=u[:N].copy();one[addresses[~body]]=un[~body]
        e1=onebody_error(one,hn,vals,vec)
        newlambda2=lambda2.copy()
        for r in groups:newlambda2[r]=.25*np.sum((np.abs(ww[r]).sum(0)+np.abs(iinew[r]))**2)
        lh1=float(np.abs(vals).sum());lam=lh1+float(newlambda2.sum())
        gap=float(m.gap_const+lh1-vals.sum()+.5*np.sum(d*d))
        eff=float(np.sqrt(gap*(2*lam-gap))) if 0<gap<2*lam else None
        e2lower=float(np.sqrt(max(e20+estimate-bound,0.)));e2upper=float(np.sqrt(max(e20+estimate+bound,0.)))
        floor_eff=float(np.sqrt(max(3.91489802*(2*lam-3.91489802),0.)))
        row={'pattern':pattern['name'],'addresses':addresses.tolist(),'column':t,'changed_words':len(addresses),'changed_groups':groups,'error1':e1,'e2_lower':e2lower,'e2_upper':e2upper,'error2_estimate':float(np.sqrt(max(e20+estimate,0.))),'e2_squared_estimate_change':estimate,'e2_squared_bound':bound,'Lambda':lam,'E_gap':gap,'lambda_eff':eff,'lambda_at_gap_floor':floor_eff,'delta_lambda_h2':float(newlambda2.sum()-lambda2.sum()),'screen_objective':floor_eff-base_eff+2000*(e2lower-.02)+2*max(e1-.02,0.),'screen_objective_200':floor_eff-base_eff+200*(e2lower-.02)+2*max(e1-.02,0.)}
        if exact:
            omitted=float(2*np.sum((dx@residual)*dx))
            assert abs(omitted)<=bound+1e-10
            e2=float(np.sqrt(max(e20+estimate+omitted,0.)))
            row['error2_exact_transport']=e2;row['ls_normal_equation_max_abs']=max(orthogonality)
            assert row['ls_normal_equation_max_abs']<1e-10
            row['exact_shadow_objective']=floor_eff-base_eff+2000*(e2-.02)+2*max(e1-.02,0.)
            row['numerical_pass_before_refit']=bool(e1<=.02 and e2<=.02 and gap>3.914898 and lam>49 and eff is not None)
        dd={key:np.array(value,copy=True) for key,value in data.items()};dd['W']=ww;dd['H2_I']=iinew;dd['angle_words'][addresses,t]^=1
        return row,dd

    rows=[];best=float('inf');stop=False
    for pi,pattern in enumerate(patterns):
        for t in columns:
            if time.monotonic()-start>a.seconds:stop=True;break
            item=transport(pattern,t)
            if item is None:continue
            row,dd=item;row['pattern_index']=pi;rows.append(row)
            if row['screen_objective']<best:
                best=row['screen_objective'];np.savez_compressed(a.out/'screen_checkpoint.npz',**dd)
                (a.out/'screen_checkpoint.json').write_text(json.dumps({'screen_only':True,'record':row,'seconds':time.monotonic()-start},indent=2)+'\n')
        if pi%5==0 or stop:print(json.dumps({'event':'transport_masks','patterns_done':pi+1,'screened':len(rows),'best_proxy':best,'seconds':time.monotonic()-start}),flush=True)
        if stop:break
    # Different plausible constraint prices reduce dependence on one proxy.
    chosen=[];seen=set();per=max(1,a.shortlist//4)
    for key in ['screen_objective','screen_objective_200','e2_lower','lambda_at_gap_floor']:
        eligible=[r for r in rows if r['e2_upper']<.025 and r['error1']<.025]
        for row in sorted(eligible,key=lambda r:r[key])[:per]:
            token=(row['pattern_index'],row['column'])
            if token not in seen:chosen.append(row);seen.add(token)
    exact=[]
    for row in chosen:
        rr,dd=transport(patterns[row['pattern_index']],row['column'],exact=True)
        rr['pattern_index']=row['pattern_index'];exact.append((rr,dd))
    exact.sort(key=lambda item:item[0]['exact_shadow_objective']);emitted=[]
    for k,(row,dd) in enumerate(exact[:a.emit]):
        path=a.out/f'candidate_{k:02d}.npz';np.savez_compressed(path,**dd)
        entry=dict(row);entry['candidate']=str(path);entry['candidate_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        entry['changes']=[{'address':ad,'column':row['column'],'old':int(words[ad,row['column']]),'value':int(dd['angle_words'][ad,row['column']])} for ad in row['addresses']]
        if k<2:
            mm=evaluate_dfthc_angle_words(dd['angle_words'],dd['W'],dd['H2_I']-dd['W'].sum(1),m.S,m.beta,m.ref,brot=8,tree_edges=dd['tree_edges'],energy_upper=UPPER_ENERGY)
            entry['official_numeric_metrics']=mm
            assert abs(mm['error_2']-row['error2_exact_transport'])<1e-9
            assert abs(mm['error_1']-row['error1'])<1e-9
            assert abs(mm['lambda_eff']-row['lambda_eff'])<1e-8
        emitted.append(entry)
    result={'status':'BOUNDED_INTEGER_FREE_MASK_LS_TRANSPORT','source':str(a.source),'source_sha256':hashlib.sha256(a.source.read_bytes()).hexdigest(),'script_sha256':script_sha,'patterns':str(a.patterns),'patterns_sha256':hashlib.sha256(a.patterns.read_bytes()).hexdigest(),'columns':columns,'requested_seconds':a.seconds,'budget_stopped':stop,'screened':len(rows),'exact_shortlist':len(exact),'baseline':baseline,'emitted':emitted,'best_exact':[item[0] for item in exact[:30]],'all_changes_actual_integer_LSB_XOR':True,'all_tags_preserved':True,'gap_restoration_not_assumed_in_actual_metrics':True,'cost_qualification':'Input masks are intended free-function patches; final loader proof required','bound_qualification':'Analytic Frobenius bound in float64, not interval arithmetic','full_circuit_verified':False,'seconds':time.monotonic()-start,'peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024}
    (a.out/'transport.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in {'emitted','best_exact'}}),flush=True)


if __name__=='__main__':main()
