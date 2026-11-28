"""Independent physical evaluator for the 76-orbital FeMoCo GVQCC reference.

Derived from the user's own previous `eval_chem_reference.py` reproduction;
requires an externally supplied `chem_gpu_inputs.npz`. It does not claim
native KickMix correctness. No competition data is stored in the repository.
"""
from __future__ import annotations
from pathlib import Path
import math


def evaluate_factorization(candidate_npz: str | Path, reference_npz: str | Path) -> dict:
    import numpy as np
    from scipy.optimize import linear_sum_assignment
    n=76
    with np.load(reference_npz,allow_pickle=False) as z:
        tpack=z['T_pack_lower'];Sref=z['S'];ecore=float(z['ecore']);electrons=int(z['electrons'])
        target_h1=z['h1_thc'];energy_upper=float(z['energy_upper'])
    with np.load(candidate_npz,allow_pickle=False) as z:
        w=z['W'];h=z['H2_I'];words=z['angle_words'];edges=z['tree_edges'];h1i=float(z['H1_I']);low=z['Hsym_lower']
    r,b,c=w.shape
    if words.shape!=(n+r*b,n-1):raise ValueError('wrong angle shape relative to R,B')
    if h.shape!=(r,c):raise ValueError('wrong H2_I shape')
    if edges.shape!=(n-1,2):raise ValueError('wrong Givens tree')
    tri=np.tril_indices(n)
    sm=np.zeros((n,n),dtype=np.float32);sm[tri]=low
    sm=sm+sm.T-np.diag(np.diag(sm));sm=np.asarray(sm,dtype=np.float64)
    if not np.array_equal(sm,Sref):raise ValueError('submitted fixed shift S mismatches the reference')
    beta=h1i-.5*np.trace(sm)
    if abs(beta-4.955104996915907)>=1e-12:raise ValueError('submitted fixed shift beta mismatch')
    # Givens decoding is identical to the scoring's 7-bit convention.
    u=np.zeros((len(words),n),dtype=np.float64);u[:,0]=1
    for j,(p,child) in enumerate(edges):
        a=np.pi*words[:,j]/64.0
        co=np.cos(a);si=np.sin(a)
        p0=u[:,p].copy();c0=u[:,child].copy()
        u[:,p]=co*p0-si*c0
        u[:,child]=si*p0+co*c0
    uu=u[n:].reshape(r,b,n)
    X=np.einsum('rbp,rbq,rbc->rcpq',uu,uu,w,optimize=True)
    X=np.tril(X)+np.swapaxes(np.tril(X,k=-1),-2,-1)
    wR=h-w.sum(axis=1)
    h1prime=target_h1-.5*electrons*sm+beta*np.eye(n)-np.einsum('rc,rcpq->pq',wR,X,optimize=True)
    eigenval,eigenvec=np.linalg.eigh(h1prime)
    overlaps=np.abs(u[:n]@eigenvec)
    i,j=linear_sum_assignment(-overlaps)
    match=np.empty_like(eigenval);match[i]=eigenval[j]
    rebuilt=np.einsum('i,ip,iq->pq',match,u[:n],u[:n],optimize=True)
    e1=float(np.linalg.norm(h1prime-rebuilt))
    pidx,qidx=np.tril_indices(n);p=len(pidx)
    tri2=np.tril_indices(p)
    tt=np.zeros((p,p),dtype=np.float64)
    tt[tri2]=tpack
    tt=tt+tt.T-np.diag(tt.diagonal())
    off=(pidx!=qidx).astype(float)
    weights=np.sqrt(np.outer(1.0+off,1.0+off))
    xx=X[...,pidx,qidx].reshape(r*c,p)
    pred=xx.T@xx
    e2=float(np.linalg.norm(pred*weights-tt))
    lambda_h1=float(np.abs(eigenval).sum())
    lambda_h2=.25*np.sum((np.sum(abs(w),axis=1)+np.abs(h))**2)
    lam=float(lambda_h1+lambda_h2)
    e_sos=ecore-electrons*beta-(lambda_h1-eigenval.sum())-.5*np.sum(wR**2)
    egap=float(energy_upper-e_sos)
    eff=math.sqrt(egap*(2*lam-egap)) if 0<egap<=2*lam else float('nan')
    physical=all(map(math.isfinite,(e1,e2,lam,egap,eff))) and e1<=0.020 and e2<=0.020 and lam>49 and egap>3.914898
    return {'error_1':e1,'error_2':e2,'Lambda':lam,'E_gap':egap,
            'lambda_eff':eff,'passes_physical_gates':bool(physical),
            'R':r,'B':b,'C':c,'num_angles':int(words.shape[1]),
            'verification_scope':'INDEPENDENT_NUMERICAL_PHYSICS_NOT_NATIVE_KICKMIX'}
