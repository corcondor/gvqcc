#!/usr/bin/env python3
"""Reduce B using an unchanged ANGLE address prefix and refit exact H2.

New group boundaries are intentionally N+r*B_new. Every submitted word is
copied from the original prefix; no row remapping or continuous theta is used.
Each old X_r is first projected onto its new feature span. The subsequent
L-BFGS search uses exact Cholesky-whitened coordinates and the actual full
two-body residual. W/H2_I use the original natural d offset during this stage.
"""
from __future__ import annotations
import argparse,hashlib,json,resource,time
from pathlib import Path
import numpy as np
from scipy.linalg import solve_triangular
from scipy.optimize import minimize
from inverse_v2_chemistry_refit import FixedAngles
from inverse_v2_chemistry_screen import ROOT
from dfthcsos.scoreinfra.costs_prepare import SpinFreeData_V1
from dfthcsos.scoreinfra.dfthc_math import reconstruct_u_vectors,evaluate_dfthc_angle_words
from dfthcsos.scoreinfra.reference import UPPER_ENERGY


def resource_row(b,r=8,c=44,n=76):
    m=SpinFreeData_V1(R=r,B=b,C=c,N=n,chi=10,beta=8)
    oq=m.outer_state_prep_qubit_cost();iq=m.inner_state_prep_qubit_cost()
    t=8066+m.outer_state_prep()+m.inner_state_prep()+m.givens_rotations()
    q=40+oq['persistent']+iq['persistent']+max(77,oq['temporary'],iq['temporary'])
    return {'B':b,'num_vectors':n+r*b,'T':int(t),'Q':int(q),'ANGLE_toffoli_per_pass':4033,'outer_toffoli':m.outer_state_prep(),'inner_toffoli':m.inner_state_prep(),'givens_toffoli':m.givens_rotations(),'outer_qubits':oq,'inner_qubits':iq,'same_lambda_cost_reduction_percent':100*(1-t*q/(14728*427)),'lambda_break_even_user_log':46.905894137*14728*427/(t*q),'lambda_break_even_reproduced':46.90658950862355*14728*427/(t*q),'cost_scope':'Conditional on unchanged 4033/pass original ANGLE family valid on this prefix; new full verification is separate.'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=ROOT/'dqi_inputs/chemistry_4033/submission_asterios_full.npz')
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--bases',type=int,default=142)
    p.add_argument('--seconds',type=float,default=160.)
    p.add_argument('--iterations',type=int,default=5000)
    p.add_argument('--stop-at',type=float,default=.01999)
    p.add_argument('--resources-only',action='store_true')
    a=p.parse_args()
    if a.out.exists():raise FileExistsError(a.out)
    a.out.mkdir(parents=True)
    resources=[resource_row(b) for b in [143,142,141,140,139,138,136,132,129,128]]
    (a.out/'resources.json').write_text(json.dumps(resources,indent=2)+'\n')
    if a.resources_only:print(json.dumps(resources),flush=True);return
    begin=time.monotonic();script_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    base=dict(np.load(a.source,allow_pickle=False));R,B0,C=base['W'].shape;N=base['U'].shape[-1];B=a.bases
    assert 0<B<B0 and R==8 and C==44 and N==76
    source_sha=hashlib.sha256(a.source.read_bytes()).hexdigest()
    m=FixedAngles(base);D=len(m.rows);Vold=m.V.reshape(R,B0,D)
    Xold=np.einsum('rbc,rbd->rcd',base['W'],Vold,optimize=True)
    V=m.V[:R*B].reshape(R,B,D)
    L=np.array([np.linalg.cholesky(v@v.T) for v in V])
    Q=np.array([solve_triangular(L[r],V[r],lower=True,check_finite=False) for r in range(R)])
    orth=float(max(np.max(np.abs(q@q.T-np.eye(B))) for q in Q));assert orth<1e-7
    Y=np.einsum('rbd,rcd->rbc',Q,Xold,optimize=True)
    d=base['H2_I']-base['W'].sum(1)
    prefix=base['angle_words'][:N+R*B].copy()
    uv=reconstruct_u_vectors(prefix/128.,base['tree_edges']);uv/=np.linalg.norm(uv,axis=1)[:,None]
    template={key:np.array(value,copy=True) for key,value in base.items()}
    template['angle_words']=prefix;template['U']=uv[N:].reshape(R,B,N)
    def physical(flat):
        yy=np.asarray(flat).reshape(R,B,C)
        w=np.array([solve_triangular(L[r].T,yy[r],lower=False,check_finite=False) for r in range(R)])
        data=dict(template);data['W']=w;data['H2_I']=d+w.sum(1)
        return data
    def save(flat,name):
        data=physical(flat);path=a.out/(name+'.npz');np.savez_compressed(path,**data);return path,data
    initial_path,initial_data=save(Y.ravel(),'initial_ls')
    initial_metrics=evaluate_dfthc_angle_words(prefix,initial_data['W'],d,m.S,m.beta,m.ref,brot=8,tree_edges=base['tree_edges'],energy_upper=UPPER_ENERGY)
    initial_X=np.einsum('rbc,rbd->rcd',Y,Q,optimize=True).reshape(R*C,D)
    target=m.ref['tei'][m.rows[:,None],m.cols[:,None],m.rows[None,:],m.cols[None,:]].copy()
    sl=m.S[m.rows,m.cols];diag=(m.rows==m.cols).astype(float)
    target+=.5*(np.outer(sl,diag)+np.outer(diag,sl));target*=m.scale[:,None]*m.scale[None,:]
    residual=initial_X.T@initial_X-target;del target
    e20=float(np.sum(residual*residual));assert abs(np.sqrt(e20)-initial_metrics['error_2'])<1e-9
    normal=float(max(np.max(np.abs(Q[r]@(initial_X.reshape(R,C,D)[r]-Xold[r]).T)) for r in range(R)))
    assert normal<1e-10
    cross=np.array([[Q[r]@Q[s].T for s in range(R)] for r in range(R)])
    aq=Q.reshape(R*B,D)@residual
    A=np.array([aq[r*B:(r+1)*B]@Q[r].T for r in range(R)])
    P0=Y@Y.transpose(0,2,1)
    del residual,aq
    scale=.02**2;start=time.monotonic();calls=0;trace=[];best=Y.ravel().copy();best_value=e20/scale;last_checkpoint=start
    class Budget(Exception):pass
    class Feasible(Exception):pass
    def objective(flat,enforce_budget=True):
        nonlocal calls,best,best_value
        if enforce_budget and time.monotonic()-start>a.seconds:raise Budget()
        calls+=1;y=flat.reshape(R,B,C);delta=y@y.transpose(0,2,1)-P0;kd=np.zeros_like(A)
        for r in range(R):
            for s in range(R):
                g=cross[r,s];kd[r]+=g@delta[s]@g.T
        value=float(e20+2*np.einsum('rij,rij->',A,delta)+np.einsum('rij,rij->',kd,delta))/scale
        gradient=(4*(A+kd)@y/scale).ravel()
        if value<best_value:best_value=value;best=flat.copy()
        return value,gradient
    first=objective(Y.ravel());rng=np.random.default_rng(20261115);direction=rng.normal(size=best.size);direction/=np.linalg.norm(direction);h=1e-6
    plus=objective(Y.ravel()+h*direction);minus=objective(Y.ravel()-h*direction)
    fd=(plus[0]-minus[0])/(2*h);an=float(first[1]@direction);gradient_error=abs(fd-an)/max(1.,abs(fd));assert gradient_error<1e-5
    initial_record={'event':'initial','B':B,'metrics':initial_metrics,'resources':resource_row(B),'orthogonality_error':orth,'ls_normal_equation_error':normal,'gradient_scaled_error':gradient_error,'prefix_words_exact':bool(np.array_equal(prefix,base['angle_words'][:N+R*B])),'seconds_total':time.monotonic()-begin}
    (a.out/'initial.json').write_text(json.dumps(initial_record,indent=2)+'\n');print(json.dumps(initial_record),flush=True)
    def callback(flat):
        nonlocal last_checkpoint
        now=time.monotonic()
        if now-last_checkpoint>=10:
            save(best,'checkpoint');last_checkpoint=now
            row={'event':'refit','B':B,'calls':calls,'best_error2':float(np.sqrt(max(best_value,0)*scale)),'seconds_refit':now-start};trace.append(row)
            (a.out/'progress.json').write_text(json.dumps({'initial':initial_record,'trace':trace},indent=2)+'\n');print(json.dumps(row),flush=True)
        if best_value*scale<=a.stop_at*a.stop_at:raise Feasible()
    try:
        opt=minimize(objective,Y.ravel(),jac=True,method='L-BFGS-B',callback=callback,options={'maxiter':a.iterations,'maxcor':20,'ftol':1e-14,'gtol':1e-9,'maxls':30})
        termination=str(opt.message)
    except Budget:termination='time budget'
    except Feasible:termination='target two-body error reached'
    path,data=save(best,'candidate')
    exact=evaluate_dfthc_angle_words(prefix,data['W'],data['H2_I']-data['W'].sum(1),m.S,m.beta,m.ref,brot=8,tree_edges=base['tree_edges'],energy_upper=UPPER_ENERGY)
    assert abs(exact['error_2']-np.sqrt(max(best_value,0)*scale))<1e-8
    numeric_pass=bool(exact['error_1']<=.02 and exact['error_2']<=.02 and exact['E_gap']>3.914898 and exact['Lambda']>49 and exact['gap_in_domain'] and np.isfinite(exact['lambda_eff']))
    rc=resource_row(B);cost=exact['lambda_eff']*rc['T']*rc['Q']
    report={'status':'NUMERICAL_PASS' if numeric_pass else 'NUMERICAL_FAIL','B_original':B0,'B_new':B,'R':R,'C':C,'N':N,'num_vectors':len(prefix),'source':str(a.source),'source_sha256':source_sha,'script_sha256':script_sha,'initial_candidate':str(initial_path),'initial_metrics':initial_metrics,'candidate':str(path),'candidate_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'official_numeric_metrics':exact,'numerical_pass':numeric_pass,'two_body_pass':bool(exact['error_2']<=.02),'resources':rc,'comparison_cost_with_original_loader_prefix':cost,'comparison_user_cost_from_logged_lambda':46.905894137*14728*427,'lower_than_user_log_cost_if_full_pass':bool(numeric_pass and cost<46.905894137*14728*427),'prefix_word_equality':bool(np.array_equal(data['angle_words'],base['angle_words'][:N+R*B])),'tree_edges_unchanged':bool(np.array_equal(data['tree_edges'],base['tree_edges'])),'natural_d_max_change':float(np.max(np.abs(data['H2_I']-data['W'].sum(1)-d))),'orthogonality_error':orth,'ls_normal_equation_error':normal,'gradient_scaled_error':gradient_error,'full_circuit_verified':False,'scope':'Finite local error2 minimization after prefix/group-boundary change; no infeasibility proof. Retained original family would require full prefix verifier check.','calls':calls,'termination':termination,'seconds_refit':time.monotonic()-start,'seconds_total':time.monotonic()-begin,'peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,'trace':trace}
    (a.out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({key:value for key,value in report.items() if key!='trace'}),flush=True)


if __name__=='__main__':main()
