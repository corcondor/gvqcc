#!/usr/bin/env python3
"""Independent physical verifier for FeMoCo reference inputs from chem_gpu_inputs.npz.
Implements official e1/e2, Lambda, gap, lambda_eff, with exact reference T_pack.
NOT KickMix. Baseline must reproduce official V8 receipt within numerical tolerance.
"""
import numpy as np, math, hashlib, json, argparse
from pathlib import Path
from scipy.optimize import linear_sum_assignment
N=76

def decode(words,edges,beta=7):
    v=np.zeros((len(words),N),dtype=np.float64);v[:,0]=1
    for i,(p,q) in enumerate(edges):
        p=int(p);q=int(q); t=np.pi*words[:,i]/float(1 << (beta-1))
        c,s=np.cos(t),np.sin(t)
        a,b=v[:,p].copy(),v[:,q].copy()
        v[:,p]=c*a-s*b;v[:,q]=s*a+c*b
    return v

class Physical:
 def __init__(self, data=None):
    if data is None: data=Path(__file__).resolve().parent/'data'/'chem_gpu_inputs.npz'
    with np.load(data) as d:self.ds={k:np.array(d[k]) for k in d.files}
    self.ii,self.jj=np.tril_indices(N); self.sc=np.where(self.ii==self.jj,1.,np.sqrt(2.))
    M=len(self.ii); self.T=np.zeros((M,M),np.float64)
    ti,tj=np.tril_indices(M)
    self.T[ti,tj]=self.ds['T_pack_lower'];self.T[tj,ti]=self.ds['T_pack_lower']
    self.Tnorm2=np.sum(self.T*self.T)
    self.h1base=self.ds['h1_thc'] - 0.5*self.ds['electrons']*self.ds['S']+self.ds['beta1']*np.eye(N)
    self.sum_fixed=float(self.ds['ecore']-self.ds['electrons']*self.ds['beta1']);self.upper=float(self.ds['energy_upper'])

 def evaluate(self,z,verbose=False,full=False):
    words=np.asarray(z['angle_words'],dtype=np.int64);w=np.asarray(z['W'],dtype=np.float64);H2=np.asarray(z['H2_I'],dtype=np.float64)
    R,B,C=w.shape; assert words.shape==(N+R*B,N-1)
    brot=int(z['brot']) if 'brot' in z else 7
    v=decode(words,z['tree_edges'],brot)
    V1=v[:N];U=v[N:];u=U.reshape(R,B,N)
    packed=(U[:,self.ii]*U[:,self.jj])*self.sc
    X=np.einsum('rbc,rbm->rcm',w,packed.reshape(R,B,-1),optimize=True).reshape(R*C,-1)
    if full:
      err2=float(np.linalg.norm(X.T@X-self.T))
    else:
      xtx=X@X.T
      err2=float(np.sqrt(max(0,float(np.sum(xtx*xtx)-2*np.sum((X@self.T)*X)+self.Tnorm2))))
    W0=H2-w.sum(axis=1)
    co=np.einsum('rbc,rc->rb',w,W0).reshape(-1)
    h1p=self.h1base-(U.T*co)@U
    h1p=.5*(h1p+h1p.T)
    ev,phi=np.linalg.eigh(h1p)
    match=np.abs(V1@phi);i,j=linear_sum_assignment(-match)
    lam=np.empty(N);lam[i]=ev[j]
    h1rec=(V1.T*lam)@V1
    err1=float(np.linalg.norm(h1rec-h1p))
    lam1=float(np.sum(np.abs(ev)));lam2=float(.25*np.sum(np.square(np.sum(np.abs(w),axis=1)+np.abs(H2))))
    Lambda=lam1+lam2
    eso=self.sum_fixed-(lam1-float(np.sum(ev)))-.5*float(np.sum(W0*W0))
    gap=float(self.upper-eso)
    le=math.sqrt(gap*(2*Lambda-gap)) if 0<gap<2*Lambda else float('nan')
    result=dict(shape=[R,B,C],brot=brot,error_1=err1,error_2=err2,Lambda=Lambda,E_gap=gap,lambda_eff=le,
        gap_in_domain=0<gap<2*Lambda,admissible=err1<=0.02 and err2<=0.02 and Lambda>49 and gap>3.914898 and 0<gap<2*Lambda,
        lambda1=lam1,lambda2=lam2,e_sos=eso)
    if verbose:print(json.dumps(result,indent=2))
    return result

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--npz',default=str(Path(__file__).resolve().parent/'V8_submission.npz'));a.add_argument('--full',action='store_true');args=a.parse_args()
 with np.load(args.npz) as z:d={k:np.array(z[k]) for k in z.files}
 Physical().evaluate(d,verbose=True,full=args.full)