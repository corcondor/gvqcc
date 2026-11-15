#!/usr/bin/env python3
"""Necessary H2 error bound for every W on a retained original-word prefix.

Every represented H2 lies in S tensor S, with S the row span of retained
projector vectors V. Relaxing group partitions, rank, and PSD constraints gives
min_Z ||T-Pi_S Z Pi_S||_F = ||T-Pi_S T Pi_S||_F. Shorter prefixes have smaller
row spaces, so this bound also applies to every smaller B at the same R.
The theorem is exact; the reported numerical evaluation is float64, not an
interval arithmetic proof. Orthogonality and span/projection residuals are
reported explicitly.
"""
from __future__ import annotations
import argparse,hashlib,json,resource,time
from pathlib import Path
import numpy as np
from scipy.linalg import qr
from inverse_v2_chemistry_refit import FixedAngles
from inverse_v2_chemistry_screen import ROOT


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=ROOT/'dqi_inputs/chemistry_4033/submission_asterios_full.npz')
    p.add_argument('--bases',type=int,default=142)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():raise FileExistsError(a.out)
    start=time.monotonic();data=dict(np.load(a.source,allow_pickle=False));R,B0,C=data['W'].shape
    assert 0<a.bases<B0
    m=FixedAngles(data);D=len(m.rows);V=m.V[:R*a.bases]
    Q,tri=qr(V.T,mode='economic',check_finite=False)
    orth=Q.T@Q-np.eye(Q.shape[1]);span=V-(V@Q)@Q.T
    target=m.ref['tei'][m.rows[:,None],m.cols[:,None],m.rows[None,:],m.cols[None,:]].copy()
    sl=m.S[m.rows,m.cols];diag=(m.rows==m.cols).astype(float)
    target+=.5*(np.outer(sl,diag)+np.outer(diag,sl));target*=m.scale[:,None]*m.scale[None,:]
    small=Q.T@target@Q;projected=Q@small@Q.T;residual=target-projected
    bound=float(np.linalg.norm(residual));orthogonal=float(np.linalg.norm(Q.T@residual@Q))
    assert np.linalg.norm(orth)<1e-9 and np.linalg.norm(span)<1e-9 and orthogonal<1e-8
    result={'status':'NUMERICALLY_EVALUATED_NECESSARY_SPAN_BOUND','source':str(a.source),'source_sha256':hashlib.sha256(a.source.read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'R':R,'B_original':B0,'B_prefix':a.bases,'retained_two_body_vectors':R*a.bases,'num_total_prefix_addresses':m.N+R*a.bases,'symmetric_coordinate_dimension':D,'relaxed_span_dimension':Q.shape[1],'smallest_abs_qr_diagonal':float(np.min(np.abs(np.diag(tri)))),'error2_necessary_lower_bound':bound,'error2_limit':.020,'excess_above_limit':bound-.020,'above_limit_in_float64':bool(bound>.020),'applies_to_all_smaller_original_prefixes':True,'relaxed_constraints':['group partition','PSD of coefficient matrices','factor rank C','W/H2_I lambda and gap costs'],'orthogonality_frobenius_error':float(np.linalg.norm(orth)),'span_frobenius_error':float(np.linalg.norm(span)),'projected_residual_frobenius_error':orthogonal,'target_frobenius_norm':float(np.linalg.norm(target)),'baseline_original_error2':float(np.sqrt(m.e20)),'scope':'Fixed original integer-word prefix only; does not exclude remapped tables, new words, or other parameterizations. Numeric float64 evaluation of an exact subspace theorem, not an interval proof.','no_candidate_generated':True,'seconds':time.monotonic()-start,'peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)


if __name__=='__main__':main()
