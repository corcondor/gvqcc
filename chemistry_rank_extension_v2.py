"""Screen a new DFTHC factor column without changing the quantized angles.

This is a local Lagrangian-curvature diagnostic, not a proof of optimality or
a verified submission. It uses the exact official constraints and records
the full T*Q break-even requirement when C changes. Existing inputs are read
only. A negative curvature is only a proposed refit initialization.
"""
from __future__ import annotations
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from scipy.optimize import linear_sum_assignment, minimize, nnls
from inverse_v2_chemistry_refit import FixedAngles
from dfthcsos.scoreinfra.costs_prepare import SpinFreeData_V1

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=float, default=100)
    parser.add_argument('--output', type=Path, default=Path(__file__).with_suffix('.json'))
    args = parser.parse_args()
    source = ROOT / 'dqi_inputs/chemistry_4033/submission_asterios_full.npz'
    base = dict(np.load(source, allow_pickle=False))
    m = FixedAngles(base)
    w, ii = base['W'], base['H2_I']
    d = ii - w.sum(axis=1)
    r, b, c = w.shape
    n = w.size
    x = np.r_[w.ravel(), ii.ravel()]
    eff, g, cons, jac, met = m.evaluate(x, c, smooth=0)
    def natural(a):
        a = a.copy()
        a[:n] = (a[:n].reshape(w.shape) + a[n:].reshape(ii.shape)[:,None,:]).ravel()
        return a
    gg = natural(g)
    jj = np.array([natural(row) for row in jac])
    scales = np.linalg.norm(jj, axis=1)
    support = np.r_[np.abs(w.ravel()) > 1e-7, np.ones(ii.size, dtype=bool)]
    mu_normalized, residual = nnls((jj/scales[:,None])[:,support].T, -gg[support])
    mu = mu_normalized/scales
    xx = np.einsum('rbc,rbpq->rcpq', w, m.outer.reshape(r,b,m.N,m.N), optimize=True)
    hp = m.hbase - np.einsum('rc,rcpq->pq', d, xx)
    vals, vec = np.linalg.eigh(hp)
    rows, cols = linear_sum_assignment(-np.abs(m.one @ vec))
    match = np.empty(m.N, dtype=int); match[rows] = cols
    qrec = np.einsum('j,jp,jq->pq', vals[match], m.one, m.one, optimize=True)
    e1 = qrec - hp
    evw = np.empty(m.N)
    evw[match] = np.einsum('jp,pq,jq->j', m.one, e1, m.one, optimize=True)
    ae1 = 2*((vec*evw)@vec.T - e1)
    sign = (vec*np.sign(vals))@vec.T
    outer = m.outer.reshape(r,b,m.N,m.N)
    av = np.einsum('pq,rbpq->rb', ae1, outer)
    sv = np.einsum('pq,rbpq->rb', sign, outer)
    tv = np.trace(outer, axis1=2, axis2=3)
    gap = met['gap']; lam = met['Lambda_smooth']
    a = gap/eff
    z = (lam-gap)/eff - mu[2]/.01
    tol2 = .01999998**2
    k = a/4
    started = time.monotonic(); rng = np.random.default_rng(20261115)
    diagnostics=[]; directions=[]
    for rr in range(r):
        q = np.zeros((b+1,b+1))
        q[:b,:b] = 2*mu[1]/tol2*m.A[rr]
        cross = -a*sv[rr] - z*(sv[rr]-tv[rr]) - mu[0]/tol2*av[rr]
        q[:b,b] = q[b,:b] = cross/2
        q[b,b] = z/2
        def objective(v):
            norm2 = v@v
            combined = v[-1] + v[:-1].sum()
            l1 = np.abs(v[:-1]).sum() + abs(combined)
            sc = np.sign(combined)
            gl1 = np.r_[np.sign(v[:-1])+sc,sc]
            numerator = v@q@v+k*l1*l1
            gradient = 2*q@v+2*k*l1*gl1
            return numerator/norm2, gradient/norm2-2*numerator*v/norm2**2
        eig, evec = np.linalg.eigh(q)
        seeds=[evec[:,0], np.r_[w[rr,:,np.argmax(np.linalg.norm(w[rr],axis=0))],d[rr,np.argmax(np.linalg.norm(w[rr],axis=0))]],rng.normal(size=b+1)]
        best=None
        for v in seeds:
            if time.monotonic()-started>args.seconds: break
            opt = minimize(objective,v/np.linalg.norm(v),jac=True,method='L-BFGS-B',options={'maxiter':180,'maxls':30,'ftol':1e-13,'gtol':1e-8})
            direction=opt.x/np.linalg.norm(opt.x)
            row={'lagrangian_curvature':float(objective(direction)[0]),'iterations':int(opt.nit),'optimizer_success':bool(opt.success),'termination':str(opt.message)}
            if best is None or row['lagrangian_curvature']<best[0]['lagrangian_curvature']: best=(row,direction)
        if best is None: break
        row,v=best
        # Check the analytic quadratic expansion with actual C45 values.
        finite=[]
        for amplitude in (1e-3,1e-4):
            nw=np.zeros((r,b,c+1));nw[:,:,:c]=w
            ni=np.zeros((r,c+1));ni[:,:c]=ii
            nw[rr,:,c]=amplitude*v[:-1]
            ni[rr,c]=amplitude*(v[-1]+v[:-1].sum())
            fe,_,ce,_,me=m.evaluate(np.r_[nw.ravel(),ni.ravel()],c+1,smooth=0)
            finite.append({'amplitude':amplitude,'lagrangian_difference_over_amplitude_squared':float(((fe-eff)+mu@(ce-cons))/amplitude**2),'metrics':me})
        row.update(group=rr,finite_difference=finite)
        diagnostics.append(row);directions.append(v)
        print(json.dumps(row),flush=True)
    cost=[]
    for cc in range(43,53):
        model=SpinFreeData_V1(R=r,B=b,C=cc,N=76,chi=10,beta=8)
        oq=model.outer_state_prep_qubit_cost(); iq=model.inner_state_prep_qubit_cost()
        t=model.outer_state_prep()+model.inner_state_prep()+model.givens_rotations()+8066
        nq=oq['persistent']+iq['persistent']+40+max(oq['temporary'],iq['temporary'],77)
        threshold=eff*(14728*427)/(t*nq)
        cost.append({'C':cc,'T':t,'Q':nq,'lambda_eff_must_be_below':threshold,'required_lambda_reduction_percent':100*(1-threshold/eff)})
    report={'scope':'New-factor-column local curvature screen; no full refit, no circuit verification, no claimed score gain','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'baseline':met,'angle_words_unchanged':True,'lagrange_multiplier_estimate':mu.tolist(),'stationarity_residual_on_nonzero_support':float(residual),'diagnostics':diagnostics,'rank_resource_break_even':cost,'seconds':time.monotonic()-started}
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    np.savez_compressed(args.output.with_suffix('.npz'),directions=np.asarray(directions))
    print(json.dumps({'output':str(args.output),'seconds':report['seconds']}),flush=True)


if __name__=='__main__':
    main()
