#!/usr/bin/env python3
"""Cooptimize coefficients for exact free nonlinear integer-angle masks.

The old derivative cache ranks candidates only.  Every shortlisted table is
decoded again, receives new tensor residuals, and is checked by the official
numeric evaluator.  No fixed-loader cost is claimed until circuit proof.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
from pathlib import Path
import argparse,copy,hashlib,json,time
import numpy as np
from scipy.optimize import minimize
from scipy.linalg import cho_factor,cho_solve
from score_chemistry_fast_model import FastFixedAngles
from dfthcsos.scoreinfra.dfthc_math import reconstruct_u_vectors,evaluate_dfthc_angle_words
from dfthcsos.scoreinfra.reference import UPPER_ENERGY

ROOT=Path('/workspace/scratch/3815fb5fae06')
BASE=ROOT/'score6_chem/transfer_full/submission.npz'
REPO=Path(__file__).resolve().parent

def rank_masks(words,keep):
    masks=np.load(REPO/'score8_chem_shared_features.npz')['masks']
    grad=np.load(REPO/'chemistry_discrete_v3_gradient.npz')['angle_gradient_radians']
    diag=np.load(REPO/'chemistry_discrete_v3_curvature.npz')['gauss_newton_proxy']
    score=grad*np.where(words%2==0,1.,-1.)*(np.pi/128)+diag*(np.pi/128)**2
    sums=np.zeros((256,75));sums[:77]=np.pad(score,((0,12),(0,0))).reshape(77,16,75).sum(1)
    candidates=[]
    for k in range(1,15):
        ix=np.where(masks[:,0]==k)[0];ms=masks[ix]
        s=sum(sums[ms[:,j],5*k:5*k+5] for j in range(1,4))
        for flat in np.argsort(s,axis=None)[:keep]:
            a,t=np.unravel_index(flat,s.shape)
            candidates.append(dict(mask_id=int(ix[a]),batch=k,angle=5*k+int(t),
                groups=list(map(int,ms[a,1:][ms[a,1:]<255])),proxy=float(s[a,t])))
    candidates.sort(key=lambda row:row['proxy']);return candidates[:keep]

def main():
    p=argparse.ArgumentParser();p.add_argument('--keep',type=int,default=8)
    p.add_argument('--seconds',type=float,default=45.);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    started=time.monotonic();base=dict(np.load(BASE));model=FastFixedAngles(base)
    r,b,c=base['W'].shape;N=model.N;n=base['W'].size;rows,cols,scale=model.rows,model.cols,model.scale
    target=model.ref['tei'][rows[:,None],cols[:,None],rows[None,:],cols[None,:]].copy()
    sl=model.S[rows,cols];ident=(rows==cols).astype(float)
    target+=.5*(np.outer(sl,ident)+np.outer(ident,sl));target*=scale[:,None]*scale[None,:]
    old_u=reconstruct_u_vectors(base['angle_words']/128.,base['tree_edges']);old_u/=np.linalg.norm(old_u,axis=1)[:,None]
    baseline=model.evaluate(np.r_[base['W'].ravel(),base['H2_I'].ravel()],c,smooth=0.)[-1]
    def rebuild(data):
        m=copy.copy(model);m.base=data
        u=reconstruct_u_vectors(data['angle_words']/128.,data['tree_edges']);u/=np.linalg.norm(u,axis=1)[:,None]
        m.one=u[:N];m.outer=np.einsum('ip,iq->ipq',u[N:],u[N:])
        m.V=m.outer[:,rows,cols]*scale;m.G=m.V@m.V.T;m.G4=m.G.reshape(r,b,r,b).transpose(0,2,1,3)
        m.P0=data['W']@data['W'].transpose(0,2,1)
        x=np.einsum('rbc,rbp->rcp',data['W'],m.V.reshape(r,b,-1),optimize=True).reshape(r*c,-1)
        residual=x.T@x-target;m.e20=float(np.sum(residual*residual));pj=m.V@residual
        m.A=np.array([pj[i*b:(i+1)*b]@m.V[i*b:(i+1)*b].T for i in range(r)])
        m.calls=0;m.prepare_fast();return m,u
    def valid(v):return v['error1']<=.02 and v['error2']<=.02 and v['gap']>3.914898 and v['Lambda_smooth']>49
    candidates=rank_masks(base['angle_words'],args.keep);report=[]
    print(json.dumps(dict(event='prepared',baseline=baseline,shortlist=candidates,seconds=time.monotonic()-started)),flush=True)
    for idx,proposal in enumerate(candidates):
        data={k:np.array(v,copy=True) for k,v in base.items()}
        for h in proposal['groups']:data['angle_words'][h*16:min(h*16+16,1220),proposal['angle']]^=1
        mm,u=rebuild(data);w=data['W'];ii=data['H2_I'];d=ii-w.sum(1)
        y=np.r_[w.ravel(),d.ravel()]
        def orig(z):
            ww=z[:n].reshape(w.shape);dd=z[n:].reshape(d.shape)
            return np.r_[ww.ravel(),(dd+ww.sum(1)).ravel()]
        def tr(g):
            z=g.copy();z[:n]=(z[:n].reshape(w.shape)+z[n:].reshape(ii.shape)[:,None,:]).ravel();return z
        def ev(z,smooth=0.):
            f,g,con,J,v=mm.evaluate(orig(z),c,smooth=smooth)
            ratio=(.01999998/.019999998)**2;con[:2]=(con[:2]+1)*ratio-1;J[:2]*=ratio
            con[2]+=(3.914898002-3.91489802)/.01
            return f,tr(g),con,np.array([tr(row) for row in J]),v
        initial=ev(y);fit_start=time.monotonic();trace=[];latest=y.copy();best=None;best_f=np.inf
        lag=np.array([.00020490204278176348,4.157669356168666,.05637299652286543])
        class Budget(Exception):pass
        for outer,rho in enumerate((10.,100.,1000.,10000.)):
            def objective(z):
                if time.monotonic()-fit_start>args.seconds:raise Budget()
                f,g,con,J,v=ev(z,smooth=1e-9);t=np.maximum(0,lag+rho*con)
                return f+(t@t-lag@lag)/(2*rho),g+t@J
            def callback(z):
                nonlocal latest
                latest=z.copy()
            try:
                opt=minimize(objective,y,jac=True,method='L-BFGS-B',callback=callback,
                    options=dict(maxiter=75,maxcor=15,maxls=30,ftol=1e-14,gtol=1e-9))
                y=opt.x;termination=str(opt.message)
            except Budget:y=latest;termination='bounded coefficient optimization complete'
            f,g,con,J,v=ev(y);lag=np.maximum(0,lag+rho*con)
            if valid(v) and f<best_f:best,best_f=y.copy(),f
            row=dict(outer=outer,metrics=v,seconds=time.monotonic()-fit_start,termination=termination)
            trace.append(row);print(json.dumps(dict(event='fit',index=idx,**row)),flush=True)
            if time.monotonic()-fit_start>args.seconds:break
        # Restore both exact error boundaries and the strict gap floor.
        for iteration in range(20):
            f,g,con,J,v=ev(y)
            if valid(v) and f<best_f:best,best_f=y.copy(),f
            if max(abs(con))<1e-9:break
            normal=np.linalg.norm(J,axis=1);Jn=J/normal[:,None];cn=con/normal
            step=-Jn.T@np.linalg.lstsq(Jn@Jn.T,cn,rcond=1e-12)[0]
            previous=np.linalg.norm(cn);accepted=False
            for ls in range(14):
                yy=y+(.5**ls)*step;vv=ev(yy)
                if np.linalg.norm(vv[2]/normal)<previous:y=yy;accepted=True;break
            if not accepted:break
        result=best if best is not None else y;xx=orig(result)
        data['W']=xx[:n].reshape(w.shape);data['H2_I']=xx[n:].reshape(ii.shape)
        data['U']=u[N:].reshape(r,b,N)
        official=evaluate_dfthc_angle_words(data['angle_words'],data['W'],data['H2_I']-data['W'].sum(1),mm.S,mm.beta,mm.ref,
            brot=8,tree_edges=data['tree_edges'],energy_upper=UPPER_ENERGY)
        passed=official['error_1']<=.02 and official['error_2']<=.02 and official['E_gap']>3.914898 and official['Lambda']>49 and official['gap_in_domain']
        path=args.out/f'candidate_{idx:02d}.npz';np.savez_compressed(path,**data)
        result=dict(index=idx,proposal=proposal,initial_metrics=initial[-1],official_numeric_metrics=official,numeric_pass=bool(passed),
            improved=bool(passed and official['lambda_eff']<baseline['lambda_eff_smooth']),changed_words=int(np.count_nonzero(data['angle_words']!=base['angle_words'])),
            path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),trace=trace,
            full_circuit_verified=False,seconds=time.monotonic()-fit_start)
        report.append(result);(args.out/'results.json').write_text(json.dumps(dict(baseline=baseline,candidates=report,total_seconds=time.monotonic()-started),indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items() if k!='trace'}),flush=True)

if __name__=='__main__':main()
