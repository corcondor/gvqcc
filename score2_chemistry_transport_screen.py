#!/usr/bin/env python3
"""Integer angle search with analytic least-squares transport of all W columns.

For one feature v_b -> v_b+q, write q=c^T V+q_perp, mu=||q_perp||²,
alpha=1+c_b, eta=(G^-1)_bb. The exact least-squares weights reproducing the
old X as closely as the new feature span permits are
  W' = W - ((alpha*c+mu*G^-1 e_b)/(alpha²+mu*eta)) W_b.
The induced X change remains rank one, enabling exact H2 residual evaluation.
"""
from __future__ import annotations
import argparse,hashlib,json,resource,time
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment
from inverse_v2_chemistry_screen import ROOT
from score_chemistry_fast_model import FastFixedAngles
from score2_chemistry_discrete_screen import decoder_directions,unvectorize
from dfthcsos.scoreinfra.dfthc_math import reconstruct_u_vectors,evaluate_dfthc_angle_words
from dfthcsos.scoreinfra.reference import UPPER_ENERGY


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=ROOT/'dqi_inputs/chemistry_4033/submission_asterios_full.npz')
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--shortlist',type=int,default=600)
    p.add_argument('--emit',type=int,default=8)
    p.add_argument('--error2-shadow-price',type=float,default=200.)
    p.add_argument('--error2-upper-cutoff',type=float,default=.025)
    args=p.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    started=time.monotonic();data=dict(np.load(args.source,allow_pickle=False));words=data['angle_words'].astype(np.int64)
    model=FastFixedAngles(data);w=data['W'];ii=data['H2_I'];offset=ii-w.sum(1)
    R,B,C=w.shape;N=model.N;D=len(model.rows);u=reconstruct_u_vectors(words/128.,data['tree_edges']);u/=np.linalg.norm(u,axis=1)[:,None]
    V=model.V;v3=V.reshape(R,B,D);X=np.einsum('rbc,rbd->rcd',w,v3,optimize=True).reshape(R*C,D)
    target=model.ref['tei'][model.rows[:,None],model.cols[:,None],model.rows[None,:],model.cols[None,:]].copy()
    sl=model.S[model.rows,model.cols];ident=(model.rows==model.cols).astype(float)
    target+=.5*(np.outer(sl,ident)+np.outer(ident,sl));target*=model.scale[:,None]*model.scale[None,:]
    residual=X.T@X-target;del target
    e20=float(np.einsum('ij,ij->',residual,residual));projected=V@residual
    S=(model.P0@v3).reshape(R*B,D);A=(model.P0@projected.reshape(R,B,D)).reshape(R*B,D)
    amat=unvectorize(model.rows,model.cols,model.scale,A,N)
    kappa=np.sum(w*w,axis=2);snorm=np.sum(S*S,axis=1).reshape(R,B)
    coefficient=np.einsum('rbc,rc->rb',w,offset)
    hp=model.hbase-(coefficient.ravel()@model.outer_flat).reshape(N,N)
    vals,vec=np.linalg.eigh(hp);sign=(vec*np.sign(vals))@vec.T
    lh2r=.25*np.sum((np.abs(w).sum(1)+np.abs(ii))**2,axis=1)
    baseline=model.evaluate(np.r_[w.ravel(),ii.ravel()],C,smooth=0.)[-1]
    rows=[];group_inverse=[]
    all_b=np.repeat(np.arange(B),150);all_t=np.tile(np.repeat(np.arange(75),2),B);all_step=np.tile([-1,1],B*75)
    co=np.cos(np.pi/128.)-1.;si=np.sin(np.pi/128.)
    for r in range(R):
        G=model.G4[r,r];Gi=np.linalg.inv(G);group_inverse.append(Gi)
        ub,tangent,plane=decoder_directions(words[N+r*B:N+(r+1)*B],data['tree_edges'])
        candidate=(ub[:,None,None,:]+co*plane[:,:,None,:]+si*tangent[:,:,None,:]*np.array([-1,1])[None,None,:,None]).reshape(-1,N)
        candidate/=np.linalg.norm(candidate,axis=1)[:,None]
        dvprod=(candidate@ub.T)**2-G[all_b]
        projection=dvprod@Gi
        du=candidate-ub[all_b];dd=np.sum(du*du,axis=1);h=np.sum(du*ub[all_b],axis=1)
        qnorm=2*dd+2*h*h+4*h*dd+dd*dd
        mu=np.maximum(0.,qnorm-np.sum(dvprod*projection,axis=1))
        alpha=1+projection[np.arange(len(all_b)),all_b];den=alpha*alpha+mu*np.diag(Gi)[all_b]
        H=model.P0[r]@model.A[r];dualA=np.sum(Gi.T*H,axis=1)
        vsign=np.einsum('bi,ij,bj->b',ub,sign,ub);dualsign=Gi@vsign
        old_words=words[N+r*B+all_b,all_t];new_words=(old_words+all_step)%256
        tags=((old_words>>6)^(old_words>>7))&1;newtags=((new_words>>6)^(new_words>>7))&1
        for lo in range(0,len(all_b),256):
            hi=min(len(all_b),lo+256);b=all_b[lo:hi];pr=projection[lo:hi];aa=alpha[lo:hi];mm=mu[lo:hi];de=den[lo:hi]
            z=-(aa[:,None]*pr+mm[:,None]*Gi[:,b].T)/de[:,None]
            weight=w[r][None,:,:]+z[:,:,None]*w[r,b,None,:]
            identity=ii[r][None,:]+np.sum(z,axis=1)[:,None]*w[r,b]
            delta_lh2=.25*np.sum((np.abs(weight).sum(1)+np.abs(identity))**2,axis=1)-lh2r[r]
            un=candidate[lo:hi];uo=ub[b];d=du[lo:hi];am=amat[r*B+b]
            dvA=2*np.einsum('bi,bij,bj->b',d,am,uo)+np.einsum('bi,bij,bj->b',d,am,d)
            qa=(aa*(dvA-np.sum(pr*H[b],axis=1))-mm*dualA[b])/de
            qn=mm/de;kk=kappa[r,b]
            est=4*qa+2*snorm[r,b]*qn-kk*kk*qn*qn
            bound=2*kk*np.sqrt(e20)*qn
            e2=np.sqrt(np.maximum(e20+est,0.));e2upper=np.sqrt(np.maximum(e20+est+bound,0.))
            dvsign=np.einsum('bi,ij,bj->b',un,sign,un)-vsign[b]
            qs=(aa*(dvsign-pr@vsign)-mm*dualsign[b])/de
            delta_lh1=-coefficient[r,b]*qs
            lam=baseline['Lambda_smooth']+delta_lh2+delta_lh1
            proxy=np.sqrt(np.maximum(3.91489802*(2*lam-3.91489802),0.))
            for j in range(hi-lo):
                q=lo+j
                if tags[q]!=newtags[q] or den[q]<1e-12 or e2upper[j]>args.error2_upper_cutoff:continue
                added=20 if all_t[q]//5==14 else 40
                objective=float(proxy[j]-baseline['lambda_eff_smooth']+args.error2_shadow_price*(e2[j]-.020)+added/14728*baseline['lambda_eff_smooth'])
                rows.append({'r':r,'b':int(b[j]),'address':int(N+r*B+b[j]),'angle':int(all_t[q]),'step':int(all_step[q]),'old_word':int(old_words[q]),'new_word':int(new_words[q]),'tag_preserved':True,'estimated_added_task_toffoli':added,'transport_e2_estimate':float(e2[j]),'transport_e2_upper_bound':float(e2upper[j]),'projector_outside_span_norm_squared':float(mm[j]),'transport_X_error_squared':float(kk[j]*qn[j]),'delta_lambda_h2':float(delta_lh2[j]),'proxy_lambda_at_gap_floor':float(proxy[j]),'screen_objective':objective})
        print(json.dumps({'event':'transport_screen','group':r,'eligible':len(rows),'best_proxy_objective':min(x['screen_objective'] for x in rows) if rows else None,'seconds':time.monotonic()-started}),flush=True)
    rows.sort(key=lambda row:row['screen_objective']);shortlist=rows[:args.shortlist]
    exact=[];candidates=[]
    for row in shortlist:
        r,b,t=row['r'],row['b'],row['angle'];address=row['address'];Gi=group_inverse[r]
        table=words[address:address+1].copy();table[0,t]=row['new_word']
        un=reconstruct_u_vectors(table/128.,data['tree_edges'])[0];un/=np.linalg.norm(un)
        dv=(un[model.rows]*un[model.cols]-u[address,model.rows]*u[address,model.cols])*model.scale
        dp=v3[r]@dv;c=Gi@dp;perp=dv-c@v3[r];mu=float(perp@perp);alpha=1+c[b];den=alpha*alpha+mu*Gi[b,b]
        z=-(alpha*c+mu*Gi[:,b])/den
        q=z@v3[r]+(1+z[b])*dv
        qn=float(q@q);qs=float(q@S[r*B+b]);qa=float(q@A[r*B+b]);qr=float(q@residual@q);kk=kappa[r,b]
        e2sq=e20+4*qa+2*kk*qr+2*snorm[r,b]*qn+2*qs*qs+4*kk*qn*qs+kk*kk*qn*qn
        wr=w[r]+z[:,None]*w[r,b,None,:];ir=offset[r]+wr.sum(0)
        lh2=float(lh2r.sum()-lh2r[r]+.25*np.sum((np.abs(wr).sum(0)+np.abs(ir))**2))
        qmat=unvectorize(model.rows,model.cols,model.scale,q,N)
        hn=hp-coefficient[r,b]*qmat;vals,vec=np.linalg.eigh(hn)
        rr,cc=linear_sum_assignment(-np.abs(model.one@vec));match=np.empty(N,dtype=int);match[rr]=cc
        hrec=np.einsum('j,jp,jq->pq',vals[match],model.one,model.one,optimize=True)
        err1=float(np.linalg.norm(hrec-hn));lh1=float(np.abs(vals).sum());lam=lh1+lh2
        gap=float(model.gap_const+lh1-vals.sum()+.5*np.sum(offset*offset));eff=float(np.sqrt(gap*(2*lam-gap))) if 0<gap<2*lam else None
        item=dict(row);item.update(error2_exact_transport=float(np.sqrt(max(e2sq,0.))),transport_metrics={'error_1':err1,'error_2':float(np.sqrt(max(e2sq,0.))),'Lambda':lam,'E_gap':gap,'lambda_eff':eff},exact_shadow_objective=float(np.sqrt(3.91489802*(2*lam-3.91489802))-baseline['lambda_eff_smooth']+args.error2_shadow_price*(np.sqrt(max(e2sq,0.))-.02)+row['estimated_added_task_toffoli']/14728*baseline['lambda_eff_smooth']))
        exact.append(item);candidates.append((item,wr,ir))
    candidates.sort(key=lambda item:item[0]['exact_shadow_objective']);emitted=[]
    for i,(row,wr,ir) in enumerate(candidates[:args.emit]):
        dd={k:np.array(v,copy=True) for k,v in data.items()};dd['angle_words'][row['address'],row['angle']]=row['new_word'];dd['W'][row['r']]=wr;dd['H2_I'][row['r']]=ir
        path=args.out/f'candidate_{i:02d}.npz';np.savez_compressed(path,**dd)
        entry=dict(row);entry.update(candidate=str(path),candidate_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),changes=[{'address':row['address'],'column':row['angle'],'old':row['old_word'],'value':row['new_word']}])
        if i<2:
            metrics=evaluate_dfthc_angle_words(dd['angle_words'],dd['W'],dd['H2_I']-dd['W'].sum(1),model.S,model.beta,model.ref,brot=8,tree_edges=dd['tree_edges'],energy_upper=UPPER_ENERGY)
            entry['official_numeric_metrics']=metrics
            assert abs(metrics['error_2']-row['error2_exact_transport'])<1e-9
            assert abs(metrics['error_1']-row['transport_metrics']['error_1'])<1e-9
        emitted.append(entry)
    result={'status':'INTEGER_WORD_AND_EXACT_LS_WEIGHT_TRANSPORT_SCREEN','source':str(args.source),'source_sha256':hashlib.sha256(args.source.read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'baseline_metrics':baseline,'eligible_screen_moves':len(rows),'exact_shortlist_moves':len(exact),'error2_shadow_price':args.error2_shadow_price,'error2_upper_cutoff':args.error2_upper_cutoff,'emitted':emitted,'best_exact_moves':[x[0] for x in candidates[:40]],'seconds':time.monotonic()-started,'peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,'all_changes_are_one_integer_word':True,'full_circuit_verified':False,'screen_proxy_is_not_an_official_score':True}
    (args.out/'transport.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in {'emitted','best_exact_moves'}}),flush=True)


if __name__=='__main__':main()
