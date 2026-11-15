#!/usr/bin/env python3
"""Small independent algebra checks; no production search or full simulation."""
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.linalg import solve_triangular
from inverse_v2_chemistry_refit import FixedAngles
from score_chemistry_fast_model import FastFixedAngles

HERE=Path(__file__).resolve().parent

def main():
    rng=np.random.default_rng(31415926)
    n,r,b,c=4,2,3,2
    rows,cols=np.tril_indices(n);dimension=len(rows)
    scale=np.where(rows==cols,1.,np.sqrt(2.))
    u=rng.normal(size=(r,b,n));u/=np.linalg.norm(u,axis=2)[:,:,None]
    outer=np.einsum('rbi,rbj->rbij',u,u)
    v=outer[:,:,rows,cols]*scale
    w0=.2*rng.normal(size=(r,b,c));d0=.03*rng.normal(size=(r,c));ii0=d0+w0.sum(1)
    p0=w0@w0.transpose(0,2,1)
    gram=np.array([[v[i]@v[j].T for j in range(r)] for i in range(r)])
    x0=np.einsum('rbc,rbd->rcd',w0,v).reshape(r*c,dimension)
    noise=rng.normal(size=(dimension,dimension));noise=.001*(noise+noise.T)
    target=x0.T@x0-noise
    residual=x0.T@x0-target
    a=np.array([v[i]@residual@v[i].T for i in range(r)])
    e20=float(np.sum(residual*residual))
    ls=np.linalg.cholesky(gram[np.arange(r),np.arange(r)])
    qs=np.array([solve_triangular(ls[i],v[i],lower=True) for i in range(r)])
    aa=np.array([solve_triangular(ls[i],solve_triangular(ls[i],a[i],lower=True).T,lower=True).T for i in range(r)])
    yp0=ls.transpose(0,2,1)@p0@ls
    cross=np.array([[qs[i]@qs[j].T for j in range(r)] for i in range(r)])
    yy=ls.transpose(0,2,1)@(w0+.025*rng.normal(size=w0.shape))
    def white(y):
        delta=y@y.transpose(0,2,1)-yp0
        kd=np.zeros_like(aa)
        for i in range(r):
            for j in range(r):kd[i]+=cross[i,j]@delta[j]@cross[i,j].T
        return float(e20+2*np.sum(aa*delta)+np.sum(kd*delta)),4*(aa+kd)@y
    w=np.array([solve_triangular(ls[i].T,yy[i],lower=False) for i in range(r)])
    x=np.einsum('rbc,rbd->rcd',w,v).reshape(r*c,dimension)
    direct=float(np.sum((x.T@x-target)**2));value,grad=white(yy)
    white_errors=[]
    for _ in range(3):
        direction=rng.normal(size=yy.shape);direction/=np.linalg.norm(direction)
        step=1e-6;fd=(white(yy+step*direction)[0]-white(yy-step*direction)[0])/(2*step)
        white_errors.append(abs(fd-float(np.sum(grad*direction))))
    assert abs(value-direct)<1e-12 and max(white_errors)<1e-8
    # Explicitly expand the symmetric-pair isometry back into a four-tensor.
    basis=np.zeros((dimension,n,n))
    for k,(i,j) in enumerate(zip(rows,cols)):
        basis[k,i,j]=1/scale[k];basis[k,j,i]=1/scale[k]
    packed_residual=x.T@x-target
    full=np.einsum('ab,aij,bkl->ijkl',packed_residual,basis,basis)
    isometry_error=abs(np.linalg.norm(full)-np.linalg.norm(packed_residual))
    assert isometry_error<1e-12
    # The PSD rank bound is attained in the relaxed matrix family by clipping
    # negative eigenvalues and retaining the largest k positive ones.
    q,_=np.linalg.qr(rng.normal(size=(dimension,dimension)))
    spectrum=np.linspace(-.4,1.,dimension);t=(q*spectrum)@q.T;k=4
    vals,vecs=np.linalg.eigh(t);positive=np.flatnonzero(vals>0)[::-1][:k]
    approximation=(vecs[:,positive]*vals[positive])@vecs[:,positive].T
    lower=float(np.sqrt(np.sum(vals[vals<0]**2)+np.sum(np.sort(vals[vals>0])[::-1][k:]**2)))
    bound_error=abs(np.linalg.norm(t-approximation)-lower)
    assert bound_error<1e-12
    # Exercise the production fast evaluator on this independently constructed
    # small model; bypass only the heavy FCIDUMP-loading constructor.
    fast=object.__new__(FastFixedAngles)
    fast.R=r;fast.B=b;fast.N=n;fast.calls=0;fast.outer=outer.reshape(r*b,n,n)
    fast.one=np.eye(n);fast.P0=p0;fast.G4=gram;fast.A=a;fast.e20=e20
    x0full=np.einsum('rbc,rbij->rcij',w0,outer)
    intended_hp=np.diag([-.2,.05,.4,1.1]);pert=rng.normal(size=(n,n));intended_hp+=.005*(pert+pert.T)
    fast.hbase=intended_hp+np.einsum('rc,rcij->ij',d0,x0full)
    vals0=np.linalg.eigvalsh(intended_hp)
    fast.gap_const=1.-np.abs(vals0).sum()+vals0.sum()-.5*np.sum(d0*d0)
    fast.eigen_smooth=0.;fast.prepare_fast()
    slow=object.__new__(FixedAngles);slow.__dict__=fast.__dict__.copy()
    packed=np.r_[w0.ravel(),ii0.ravel()]
    old=slow.evaluate(packed,c,smooth=0.)
    new=fast.evaluate(packed,c,smooth=0.)
    fast_differences=[float(np.max(np.abs(np.asarray(old[i])-np.asarray(new[i])))) for i in range(4)]
    assert max(fast_differences)<1e-8
    smooth_rows=[]
    for eigen_epsilon in (1e-9,1e-4,.01):
        fast.eigen_smooth=eigen_epsilon
        smooth=fast.evaluate(packed,c,smooth=1e-4)
        exact=fast.evaluate(packed,c,smooth=0.)
        bias=smooth[-1]['gap']-exact[-1]['gap']
        reserve=smooth[-1]['gap_lower_bound']
        assert -1e-12<=bias<=n*eigen_epsilon+1e-12
        assert reserve<=exact[-1]['gap']+1e-12
        assert smooth[0]>=exact[0]-1e-12
        errors=[]
        for _ in range(3):
            direction=rng.normal(size=packed.shape);direction/=np.linalg.norm(direction)
            step=1e-6
            plus=fast.evaluate(packed+step*direction,c,smooth=1e-4)
            minus=fast.evaluate(packed-step*direction,c,smooth=1e-4)
            fd=np.r_[(plus[0]-minus[0])/(2*step),(plus[2]-minus[2])/(2*step)]
            analytic=np.r_[smooth[1]@direction,smooth[3]@direction]
            errors.append(float(np.max(np.abs(fd-analytic)/np.maximum(1.,np.abs(fd)))))
        assert max(errors)<1e-6
        smooth_rows.append(dict(eigen_epsilon=eigen_epsilon,gap_bias=bias,gap_bias_upper_bound=n*eigen_epsilon,
          exact_gap=exact[-1]['gap'],reported_gap_lower_bound=reserve,gradient_scaled_errors=errors))
    report=dict(status='PASS_SMALL_INDEPENDENT_ALGEBRA_CHECKS',seed=31415926,
        whitening=dict(direct_vs_whitened_error2_squared_difference=abs(value-direct),gradient_absolute_errors=white_errors,
                       feature_orthogonality_error=float(np.max(np.abs(qs@qs.transpose(0,2,1)-np.eye(b))))),
        rank_bound=dict(pair_isometry_norm_error=isometry_error,optimal_relaxed_PSD_truncation_norm_error=bound_error),
        fast_model=dict(exact_contraction_max_absolute_errors=fast_differences,positive_epsilon_checks=smooth_rows),
        model_sha256=hashlib.sha256((HERE/'score_chemistry_fast_model.py').read_bytes()).hexdigest(),
        check_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope='Small algebra/gradient checks, no production optimization, no decoder verification, no score claim.')
    (HERE/'score_independent_review_checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
