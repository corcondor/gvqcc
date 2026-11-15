#!/usr/bin/env python3
"""Check the C40 dual witness directly against the official target integrals."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.linalg import block_diag, eigh, solve_triangular
from dfthcsos.scoreinfra.dfthc_math import reconstruct_u_vectors, symmetric_from_lower
from dfthcsos.scoreinfra.reference import check_fcidump, load_fixed_shifts, load_reference


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('npz', 'words', 'projection', 'dual', 'out'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    d = dict(np.load(a.npz, allow_pickle=False))
    words = np.load(a.words, allow_pickle=False)[:1220].astype(np.uint8)
    assert hashlib.sha256(words.tobytes()).hexdigest() == "8caf7416de79102103757e3ab7ab4b6bbebfad9b1bf1ecd564c20eb948dbfcea"
    u = reconstruct_u_vectors(words.astype(np.float64)/128, d['tree_edges'])
    u /= np.linalg.norm(u, axis=1)[:,None]
    r,b,c = d['W'].shape
    n = u.shape[1]
    i,j = np.tril_indices(n)
    scale = np.where(i==j,1.,np.sqrt(2.))
    pack = u[n:,i]*u[n:,j]*scale
    features = []
    for group in pack.reshape(r,b,-1):
        lower = np.linalg.cholesky(group @ group.T)
        features.append(solve_triangular(lower,group,lower=True))
    white = np.concatenate(features)
    projection = dict(np.load(a.projection,allow_pickle=False))
    f = projection['features']
    q_t = solve_triangular(f.T,white,lower=True)
    assert np.linalg.norm(q_t@q_t.T-np.eye(r*b)) < 1e-9
    assert np.linalg.norm(f.T@q_t-white) < 1e-9
    assert np.linalg.norm(f.T@f-white@white.T) < 1e-9
    shifts = load_fixed_shifts()
    shift = np.asarray(symmetric_from_lower(shifts['Hsym_lower'],n),dtype=float)
    tei = load_reference(check_fcidump())['tei']
    t = tei[i[:,None],j[:,None],i[None,:],j[None,:]].copy()
    delta = (i==j).astype(float)
    t += .5*(np.outer(shift[i,j],delta)+np.outer(delta,shift[i,j]))
    t *= scale[:,None]*scale[None,:]
    ref_sq = np.sum(t*t)
    core = q_t @ t @ q_t.T
    with np.load(a.dual, allow_pickle=False) as w:
        adjustment = w['dual']

    def blockrows(x):
        return [x[l*b:(l+1)*b,l*b:(l+1)*b] for l in range(r)]

    raw = (projection['target']-core)+adjustment
    finv = solve_triangular(f,np.eye(r*b),lower=False)
    corrections = block_diag(*blockrows(f.T@raw@f))
    dual = raw - finv.T@corrections@finv
    dual = .5*(dual+dual.T)
    leakage = np.linalg.norm(block_diag(*blockrows(f.T@dual@f)))
    eig = eigh(core+dual,eigvals_only=True,check_finite=False)[::-1]
    rows = {}
    finite_data_margin = 2e-9
    for cap in [312,320,328,336,344,352]:
        subtracted = float(np.sum(np.maximum(eig[:cap],0.)**2))
        bound = np.sqrt(max(0.,float(ref_sq)-subtracted-finite_data_margin))
        rows[str(cap)]=dict(error2_lower_bound=bound,top_eigenvalue_norm_sq=subtracted,
                            exceeds_tolerance=bool(bound>.02))
    result = dict(status='ORIGINAL_TARGET_DIRECT_DUAL_CHECK', ref_norm_sq=float(ref_sq),
                  grouped_dual_overlap_frobenius=float(leakage),
                  grouped_orthogonal_correction_norm=float(np.linalg.norm(dual-raw)),
                  q_orthogonality_error=float(np.linalg.norm(q_t@q_t.T-np.eye(r*b))),
                  fixed_float64_subtraction_reserve=finite_data_margin,
                  source_npz_sha256=hashlib.sha256(a.npz.read_bytes()).hexdigest(),
                  records=rows,
                  scope='Float64 necessary bound, not an interval-certified calculation.')
    a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)


if __name__ == '__main__':
    main()
