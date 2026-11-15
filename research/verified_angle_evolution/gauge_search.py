"""Exact-physics channel-orthogonal gauge descent on the pinned Score10 factors.

Changes W/H2_I but not the Hamiltonian in exact arithmetic. Reports a
CONDITIONAL numerical cost: official FCIDUMP/Kickmix verification is required
before it is considered an accepted contest result.
"""
from __future__ import annotations
import argparse,hashlib,json,math,zipfile
from pathlib import Path
import numpy as np
from scipy.optimize import minimize_scalar
from evaluator import BASE_CHEM_COST,BASE_T,BASE_Q,BASE_SCORE

ROOT=Path(__file__).resolve().parent
EGAP=3.9148980009995284

def lambda_h2(w,h):return .25*np.sum((np.sum(np.abs(w),axis=1)+np.abs(h))**2)

def pair_cost(a,b,ha,hb,t):
    c=math.cos(t);s=math.sin(t)
    return .25*((np.abs(c*a+s*b).sum()+abs(c*ha+s*hb))**2+
               (np.abs(-s*a+c*b).sum()+abs(-s*ha+c*hb))**2)

def optimize(w,h,sweeps=2,limit=0.002,accept_margin=5e-13):
    w=w.copy();h=h.copy();R,B,C=w.shape;history=[]
    for sweep in range(sweeps):
        grads=[]
        for r in range(R):
            a=w[r];hh=h[r];a_abs=np.abs(a).sum(axis=0)+np.abs(hh)
            smooth=np.sign(a).T@a + np.outer(np.sign(hh),hh)
            zero=(a==0).astype(float).T@np.abs(a)+np.outer((hh==0).astype(float),np.abs(hh))
            for i in range(C):
                for j in range(i+1,C):
                    d=.5*(a_abs[i]*smooth[i,j]-a_abs[j]*smooth[j,i])
                    kink=.5*(a_abs[i]*zero[i,j]+a_abs[j]*zero[j,i])
                    if d+kink<-1e-11 or d-kink>1e-11:
                        grads.append((abs(d)-kink,r,i,j))
        grads.sort(reverse=True)
        accepted=0
        for _,r,i,j in grads:
            a=w[r,:,i].copy();b=w[r,:,j].copy()
            ha=float(h[r,i]);hb=float(h[r,j]);before=pair_cost(a,b,ha,hb,0)
            sols=[(before,0)]
            for width in (limit,limit/10):
                for lo,hi in ((-width,0),(0,width)):
                    fit=minimize_scalar(lambda theta:pair_cost(a,b,ha,hb,theta),bounds=(lo,hi),
                                        method='bounded',options={'xatol':1e-13,'maxiter':100})
                    sols.append((float(fit.fun),float(fit.x)))
            result,theta=min(sols)
            if result < before-accept_margin and abs(theta)>1e-13:
                c=math.cos(theta);s=math.sin(theta)
                w[r,:,i]=c*a+s*b;w[r,:,j]=-s*a+c*b
                h[r,i]=c*ha+s*hb;h[r,j]=-s*ha+c*hb
                history.append({'sweep':sweep,'r':r,'i':i,'j':j,'theta':theta,'gain':before-result})
                accepted+=1
        if accepted==0:break
    return w,h,history

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True)
    ap.add_argument('--output',type=Path,default=ROOT/'runs/gauge');ap.add_argument('--sweeps',type=int,default=2)
    ap.add_argument('--limit',type=float,default=0.002);args=ap.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(args.source) as f:
        with f.open('dfthcsos/submission.npz') as g:data=dict(np.load(g,allow_pickle=False))
    w0=data['W'];h0=data['H2_I'];lam0=lambda_h2(w0,h0)
    w,h,hist=optimize(w0,h0,sweeps=args.sweeps,limit=args.limit)
    lam1=lambda_h2(w,h)
    d0=h0-w0.sum(axis=1);d=h-w.sum(axis=1)
    max_gram=max(float(np.max(np.abs(w[r]@w[r].T-w0[r]@w0[r].T))) for r in range(w.shape[0]))
    max_linear=max(float(np.max(np.abs(w[r]@d[r]-w0[r]@d0[r]))) for r in range(w.shape[0]))
    max_d2=max(float(abs(np.dot(d[r],d[r])-np.dot(d0[r],d0[r]))) for r in range(w.shape[0]))
    leff0=BASE_CHEM_COST/(BASE_T*BASE_Q)
    lambda0=.5*(leff0**2/EGAP+EGAP)
    leff1=math.sqrt(EGAP*(2*(lambda0+lam1-lam0)-EGAP))
    predicted=BASE_SCORE*(leff0/leff1)**(1/3)
    outdata=dict(data);outdata.update(W=w,H2_I=h)
    out=args.output/'chemistry_gauge_unverified.npz'
    np.savez_compressed(out,**outdata)
    rec={'status':'MATHEMATICALLY_EQUIVALENT_GAUGE_CANDIDATE_OFFICIAL_UNVERIFIED',
         'source_zip':str(args.source),'output_npz':str(out),
         'source_zip_sha256':hashlib.sha256(args.source.read_bytes()).hexdigest(),
         'npz_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
         'lambda_h2_old':float(lam0),'lambda_h2_new':float(lam1),'delta_lambda_h2':float(lam1-lam0),
         'lambda_eff_baseline':leff0,'lambda_eff_conditional':float(leff1),
         'score_baseline':BASE_SCORE,'score_conditional':float(predicted),
         'score_delta_conditional':float(predicted-BASE_SCORE),
         'n_accepted':len(hist),'max_gram_error':max_gram,'max_linear_error':max_linear,'max_d2_error':max_d2,
         'max_other_array_change':0,
         'fully_verified':False,'submitted':False,'history':hist}
    assert all(np.array_equal(data[k],outdata[k]) for k in data if k not in ('W','H2_I'))
    (args.output/'gauge_result.json').write_text(json.dumps(rec,indent=2)+'\n')
    print(json.dumps({k:v for k,v in rec.items() if k!='history'},indent=2))
if __name__=='__main__':main()
