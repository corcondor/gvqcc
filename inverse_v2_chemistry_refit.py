"""Bounded fixed-angle C43 refit with analytic derivatives and exact reference.

This is an experiment, not a submission generator. Final candidates are
rechecked by the unchanged official numerical evaluator. H2 residuals are
expanded about the passing baseline to avoid cancellation of large norms.
"""
from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment, minimize

from inverse_v2_chemistry_screen import ROOT
from dfthcsos.scoreinfra.dfthc_math import reconstruct_u_vectors, symmetric_from_lower, evaluate_dfthc_angle_words
from dfthcsos.scoreinfra.reference import check_fcidump, load_reference, load_fixed_shifts, UPPER_ENERGY


class FixedAngles:
    def __init__(self, baseline):
        t=time.monotonic()
        self.base=baseline
        self.R,self.B,self.C0=baseline['W'].shape
        self.N=baseline['U'].shape[-1]
        shifts=load_fixed_shifts()
        self.S=np.asarray(symmetric_from_lower(shifts['Hsym_lower'],self.N),dtype=float)
        self.beta=float(shifts['H1_I'])-.5*np.trace(self.S)
        self.ref=load_reference(check_fcidump())
        self.hbase=self.ref['h1_thc']-.5*self.ref['electrons']*self.S+self.beta*np.eye(self.N)
        self.gap_const=UPPER_ENERGY-self.ref['ecore']+self.ref['electrons']*self.beta
        u=reconstruct_u_vectors(baseline['angle_words']/128,baseline['tree_edges'])
        u/=np.linalg.norm(u,axis=1)[:,None]
        self.one=u[:self.N]
        self.outer=np.einsum('ip,iq->ipq',u[self.N:],u[self.N:])
        rows,cols=np.tril_indices(self.N)
        self.rows,self.cols=rows,cols
        self.scale=np.where(rows==cols,1.0,np.sqrt(2.0))
        self.V=self.outer[:,rows,cols]*self.scale
        self.G=self.V@self.V.T
        self.G4=self.G.reshape(self.R,self.B,self.R,self.B).transpose(0,2,1,3)
        self.P0=baseline['W']@baseline['W'].transpose(0,2,1)
        x=np.einsum('rbc,rbp->rcp',baseline['W'],self.V.reshape(self.R,self.B,-1),optimize=True).reshape(-1,len(rows))
        target=self.ref['tei'][rows[:,None],cols[:,None],rows[None,:],cols[None,:]].copy()
        sl=self.S[rows,cols]
        ident=(rows==cols).astype(float)
        target+=.5*(np.outer(sl,ident)+np.outer(ident,sl))
        target*=self.scale[:,None]*self.scale[None,:]
        residual=x.T@x-target
        self.e20=float(np.einsum('ij,ij->',residual,residual))
        projected=self.V@residual
        self.A=np.array([projected[r*self.B:(r+1)*self.B]@self.V[r*self.B:(r+1)*self.B].T for r in range(self.R)])
        self.calls=0
        print(json.dumps({'prepared_seconds':time.monotonic()-t,'baseline_error2':self.e20**.5}),flush=True)

    def evaluate(self, packed, c, *, smooth=1e-7):
        self.calls+=1
        size=self.R*self.B*c
        w=packed[:size].reshape(self.R,self.B,c)
        ii=packed[size:].reshape(self.R,c)
        d=ii-w.sum(1)
        x=np.einsum('rbc,rbpq->rcpq',w,self.outer.reshape(self.R,self.B,self.N,self.N),optimize=True)
        hp=self.hbase-np.einsum('rc,rcpq->pq',d,x)
        vals,vec=np.linalg.eigh(hp)
        rr,cc=linear_sum_assignment(-np.abs(self.one@vec))
        match=np.empty(self.N,dtype=int);match[rr]=cc
        qrec=np.einsum('j,jp,jq->pq',vals[match],self.one,self.one,optimize=True)
        e1=qrec-hp
        err1sq=float(np.einsum('ij,ij->',e1,e1))
        evweights=np.empty(self.N)
        evweights[match]=np.einsum('jp,pq,jq->j',self.one,e1,self.one,optimize=True)
        ae1=2*((vec*evweights)@vec.T-e1)
        sign=(vec*np.sign(vals))@vec.T
        lh1=float(np.abs(vals).sum())
        absw=np.sqrt(w*w+smooth*smooth) if smooth else np.abs(w)
        absi=np.sqrt(ii*ii+smooth*smooth) if smooth else np.abs(ii)
        l1=absw.sum(1)+absi
        lh2=float(.25*np.sum(l1*l1))
        lam=lh1+lh2
        gap=float(self.gap_const+lh1-vals.sum()+.5*np.sum(d*d))
        eff=float(np.sqrt(max(1e-100,gap*(2*lam-gap))))

        def hgrad(a):
            ax=np.einsum('pq,rcpq->rc',a,x)
            av=np.einsum('pq,rbpq->rb',a,self.outer.reshape(self.R,self.B,self.N,self.N))
            return ax[:,None,:]-av[:,:,None]*d[:,None,:],-ax

        gw1,gi1=hgrad(ae1)
        gwl,gil=hgrad(sign)
        sw=w/absw if smooth else np.sign(w)
        si=ii/absi if smooth else np.sign(ii)
        gwl+=.5*l1[:,None,:]*sw
        gil+=.5*l1*si
        gwg,gig=hgrad(sign-np.eye(self.N))
        gwg-=d[:,None,:]
        gig+=d
        gwe=gap/eff*gwl+(lam-gap)/eff*gwg
        gie=gap/eff*gil+(lam-gap)/eff*gig

        delta=w@w.transpose(0,2,1)-self.P0
        kd=np.zeros_like(self.A)
        for r in range(self.R):
            for s in range(self.R):
                g=self.G4[r,s]
                kd[r]+=g@delta[s]@g.T
        err2sq=float(self.e20+2*np.einsum('rij,rij->',self.A,delta)+np.einsum('rij,rij->',kd,delta))
        gw2=4*(self.A+kd)@w
        def pack(a,b):return np.r_[a.ravel(),b.ravel()]
        constraints=np.array([err1sq/(.01999998**2)-1,err2sq/(.01999998**2)-1,(3.91489802-gap)/.01])
        derivs=np.array([pack(gw1,gi1)/(.01999998**2),pack(gw2,np.zeros_like(ii))/(.01999998**2),-pack(gwg,gig)/.01])
        return eff,pack(gwe,gie),constraints,derivs,{'lambda_eff_smooth':eff,'Lambda_smooth':lam,'gap':gap,'error1':err1sq**.5,'error2':max(err2sq,0)**.5}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('candidate',type=Path)
    p.add_argument('--seconds',type=float,default=150)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--iterations',type=int,default=80)
    args=p.parse_args()
    base=dict(np.load(ROOT/'dqi_inputs/chemistry_4033/submission_asterios_full.npz'))
    data=dict(np.load(args.candidate))
    model=FixedAngles(base)
    c=data['W'].shape[2]
    x=np.r_[data['W'].ravel(),data['H2_I'].ravel()]
    result=model.evaluate(x,c)
    print(json.dumps({'initial':result[-1],'constraints':result[2].tolist()}),flush=True)
    # Check analytic gradients in nonzero directions before trusting the fit.
    rng=np.random.default_rng(20261114)
    d=rng.normal(size=x.shape);d/=np.linalg.norm(d)
    step=1e-6
    plus=model.evaluate(x+step*d,c);minus=model.evaluate(x-step*d,c)
    fd=np.r_[(plus[0]-minus[0])/(2*step),(plus[2]-minus[2])/(2*step)]
    an=np.r_[result[1]@d,result[3]@d]
    rel=float(np.max(np.abs(fd-an)/np.maximum(1,np.abs(fd))))
    print(json.dumps({'gradient_directional_fd':fd.tolist(),'analytic':an.tolist(),'scaled_max_error':rel}),flush=True)
    if rel>1e-3:raise RuntimeError('analytic gradient check failed')
    start=time.monotonic();lag=np.zeros(3);trace=[];latest=x.copy()
    class Budget(Exception):pass
    for outer,penalty in enumerate((2.,10.,50.,250.,1250.)):
        def objective(xx):
            if time.monotonic()-start>args.seconds:raise Budget()
            eff,g,con,cg,metrics=model.evaluate(xx,c)
            shifted=np.maximum(0,lag+penalty*con)
            f=eff+(np.sum(shifted**2)-np.sum(lag**2))/(2*penalty)
            grad=g+shifted@cg
            return f,grad
        def accepted_step(xx):
            nonlocal latest
            latest=xx.copy()
        try:
            latest=x.copy()
            opt=minimize(objective,x,jac=True,method='L-BFGS-B',callback=accepted_step,options={'maxiter':args.iterations,'maxcor':10,'ftol':1e-13,'gtol':1e-8,'maxls':25})
            x=opt.x
            msg=str(opt.message)
        except Budget:
            x=latest;msg='time budget reached'
        eff,g,con,cg,metrics=model.evaluate(x,c)
        lag=np.maximum(0,lag+penalty*con)
        row={'outer':outer,'penalty':penalty,'metrics':metrics,'constraints':con.tolist(),'seconds':time.monotonic()-start,'calls':model.calls,'termination':msg}
        trace.append(row);print(json.dumps(row),flush=True)
        if time.monotonic()-start>args.seconds:break
    size=model.R*model.B*c
    data['W']=x[:size].reshape(model.R,model.B,c)
    data['H2_I']=x[size:].reshape(model.R,c)
    metrics=evaluate_dfthc_angle_words(data['angle_words'],data['W'],data['H2_I']-data['W'].sum(1),model.S,model.beta,model.ref,brot=8,tree_edges=data['tree_edges'],energy_upper=UPPER_ENERGY)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(args.out,**data)
    report={'source':str(args.candidate),'official_numeric_metrics':metrics,'trace':trace,'gradient_check_scaled_error':rel,'full_circuit_verified':False}
    args.out.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'official_numeric_metrics':metrics}),flush=True)


if __name__=='__main__':main()
