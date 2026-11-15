#!/usr/bin/env python3
"""Spectral necessary error bound for any R*C-term real SOS factorization.

Pack each symmetric N by N coefficient matrix with sqrt(2) on off-diagonal
entries, an isometry for the Frobenius norm.  The submitted two-body tensor
then has the form X.T X, positive semidefinite and rank at most R*C.
For a real symmetric target T, every such approximation has squared error
at least sum_{lambda<0} lambda^2 plus the discarded positive eigenvalues
squared.  This bound allows arbitrary X and hence is independent of the
Givens tree, vector quantization, rho grouping, and local optimizer.
Numerical eigenvalue residuals are reported; this is not interval arithmetic.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import resource
import time
import numpy as np
from scipy.linalg import eigh
from inverse_v2_chemistry_screen import ROOT
from dfthcsos.scoreinfra.reference import check_fcidump,load_reference,load_fixed_shifts
from dfthcsos.scoreinfra.dfthc_math import symmetric_from_lower


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    if args.out.exists():raise FileExistsError(args.out)
    started=time.monotonic()
    fcidump=check_fcidump();ref=load_reference(fcidump)
    n=ref['orbitals'];rows,cols=np.tril_indices(n)
    scale=np.where(rows==cols,1.,np.sqrt(2.))
    shift=load_fixed_shifts()
    s=np.asarray(symmetric_from_lower(shift['Hsym_lower'],n),dtype=float)
    target=ref['tei'][rows[:,None],cols[:,None],rows[None,:],cols[None,:]].copy()
    ident=(rows==cols).astype(float);sl=s[rows,cols]
    target+=.5*(np.outer(sl,ident)+np.outer(ident,sl))
    target*=scale[:,None]*scale[None,:]
    symmetry=float(np.max(np.abs(target-target.T)))
    if symmetry>1e-12:raise AssertionError('unexpected target asymmetry')
    print(json.dumps({'event':'matrix_ready','dimension':len(rows),'symmetry_error':symmetry,'seconds':time.monotonic()-started}),flush=True)
    vals,vecs=eigh(target,driver='evd',check_finite=True)
    residual=float(np.linalg.norm(target@vecs-vecs*vals,ord='fro'))
    orth=float(np.linalg.norm(vecs.T@vecs-np.eye(len(vals)),ord='fro'))
    negative_sq=float(np.sum(vals[vals<0]**2))
    positives=vals[vals>0][::-1]
    records=[]
    for c in range(40,47):
        rank=8*c
        lower=float(np.sqrt(negative_sq+np.sum(positives[rank:]**2)))
        records.append({'R':8,'C':c,'rank_cap':rank,'frobenius_error_lower_bound':lower,
                        'margin_to_20_mHa':lower-.020,'excluded_if_numerical_error_negligible':bool(lower>.020)})
    result={'status':'SPECTRAL_NECESSARY_BOUND_COMPUTED','reference_fcidump':str(fcidump),
            'reference_sha256':hashlib.sha256(Path(fcidump).read_bytes()).hexdigest(),
            'matrix_dimension':len(vals),'symmetry_error':symmetry,
            'negative_eigenvalue_error_floor':float(np.sqrt(negative_sq)),
            'eigendecomposition_frobenius_residual':residual,'eigenvectors_orthogonality_frobenius_error':orth,
            'bound_scope':'All real PSD rank<=R*C matrices; relaxes all submitted factorization structure. Numerical float64 calculation, not interval-certified.',
            'records':records,'eigenvalues_near_rank344':positives[335:355].tolist(),
            'seconds':time.monotonic()-started,'peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
            'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
