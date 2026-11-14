#!/usr/bin/env python3
"""Algebraically identical fixed-angle metrics without materializing every X_rc.

h' = hbase - sum_rb (sum_c W_rbc d_rc) outer_rb.
For a matrix derivative A, <A,X_rc> = sum_b W_rbc <A,outer_rb>.
These contractions replace 352 dense 76x76 intermediates per evaluation.
"""
from __future__ import annotations
import numpy as np
from scipy.optimize import linear_sum_assignment
from inverse_v2_chemistry_refit import FixedAngles


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
