#!/usr/bin/env python3
"""Fixed-angle model copied without numerical changes for the public4030 experiment.

Official reference modules are used without changing their evaluation rules.
Set GVQCC_VERIFIERS_ROOT if the official verifier directory is elsewhere.
"""
from __future__ import annotations
import os,sys,time,json
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment
_verifiers=Path(os.environ.get("GVQCC_VERIFIERS_ROOT","/workspace/scratch/7f542e06b7cf/official_sources/Inzainos/verifiers"))
sys.path.insert(0,str(_verifiers))
from dfthcsos.scoreinfra.dfthc_math import reconstruct_u_vectors,symmetric_from_lower,evaluate_dfthc_angle_words
from dfthcsos.scoreinfra.reference import check_fcidump,load_reference,load_fixed_shifts,UPPER_ENERGY

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

class FastFixedAngles(FixedAngles):
    def __init__(self,baseline,eigen_smooth=0.):
        eigen_smooth=float(eigen_smooth)
        if not np.isfinite(eigen_smooth) or eigen_smooth<0:
            raise ValueError('eigen_smooth must be finite and nonnegative')
        super().__init__(baseline)
        self.eigen_smooth=eigen_smooth
        self.prepare_fast()

    def prepare_fast(self):
        self.outer_flat=self.outer.reshape(self.R*self.B,self.N*self.N)
        self.outer_trace=np.trace(self.outer.reshape(self.R,self.B,self.N,self.N),axis1=2,axis2=3)
        self.last_assignment=None
        if not hasattr(self,'eigen_smooth'):self.eigen_smooth=0.

    def evaluate(self,packed,c,*,smooth=1e-7):
        smooth=float(smooth)
        if not np.isfinite(smooth) or smooth<0:
            raise ValueError('smooth must be finite and nonnegative')
        if not np.isfinite(self.eigen_smooth) or self.eigen_smooth<0:
            raise ValueError('eigen_smooth must be finite and nonnegative')
        self.calls+=1
        size=self.R*self.B*c
        w=packed[:size].reshape(self.R,self.B,c)
        ii=packed[size:].reshape(self.R,c)
        d=ii-w.sum(1)
        coefficients=np.einsum('rbc,rc->rb',w,d)
        hp=self.hbase-(coefficients.ravel()@self.outer_flat).reshape(self.N,self.N)
        vals,vec=np.linalg.eigh(hp)
        rr,cc=linear_sum_assignment(-np.abs(self.one@vec))
        match=np.empty(self.N,dtype=int);match[rr]=cc
        self.last_assignment=tuple(int(v) for v in match)
        qrec=np.einsum('j,jp,jq->pq',vals[match],self.one,self.one,optimize=True)
        e1=qrec-hp
        err1sq=float(np.einsum('ij,ij->',e1,e1))
        evweights=np.empty(self.N)
        evweights[match]=np.einsum('jp,pq,jq->j',self.one,e1,self.one,optimize=True)
        ae1=2*((vec*evweights)@vec.T-e1)
        eig_eps=self.eigen_smooth if smooth else 0.
        absvals=np.sqrt(vals*vals+eig_eps*eig_eps) if eig_eps else np.abs(vals)
        signs=vals/absvals if eig_eps else np.sign(vals)
        sign=(vec*signs)@vec.T
        lh1=float(absvals.sum())
        absw=np.sqrt(w*w+smooth*smooth) if smooth else np.abs(w)
        absi=np.sqrt(ii*ii+smooth*smooth) if smooth else np.abs(ii)
        l1=absw.sum(1)+absi
        lh2=float(.25*np.sum(l1*l1));lam=lh1+lh2
        gap=float(self.gap_const+lh1-vals.sum()+.5*np.sum(d*d))
        eff=float(np.sqrt(max(1e-100,gap*(2*lam-gap))))
        projected=np.array([ae1.ravel(),sign.ravel()])@self.outer_flat.T
        av1,avl=projected.reshape(2,self.R,self.B)
        avg=avl-self.outer_trace
        def hgrad(av):
            ax=np.einsum('rbc,rb->rc',w,av)
            return ax[:,None,:]-av[:,:,None]*d[:,None,:],-ax
        gw1,gi1=hgrad(av1)
        gwl,gil=hgrad(avl)
        sw=w/absw if smooth else np.sign(w)
        si=ii/absi if smooth else np.sign(ii)
        gwl+=.5*l1[:,None,:]*sw;gil+=.5*l1*si
        gwg,gig=hgrad(avg)
        gwg-=d[:,None,:];gig+=d
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
        # Each smoothed |eigenvalue| overestimates the exact value by at most
        # eig_eps. The N*eps reserve makes this a conservative gap condition.
        constraints=np.array([err1sq/(.01999998**2)-1,err2sq/(.01999998**2)-1,(3.91489802+self.N*eig_eps-gap)/.01])
        derivs=np.array([pack(gw1,gi1)/(.01999998**2),pack(gw2,np.zeros_like(ii))/(.01999998**2),-pack(gwg,gig)/.01])
        return eff,pack(gwe,gie),constraints,derivs,{'lambda_eff_smooth':eff,'Lambda_smooth':lam,'gap':gap,'gap_lower_bound':gap-self.N*eig_eps,'eigen_trace_bias_bound':self.N*eig_eps,'error1':err1sq**.5,'error2':max(err2sq,0)**.5}
