"""A necessary H2 feasibility bound for fixed rounded Givens vectors.

Relax all rank and per-r constraints: permit any symmetric matrix acting
in the span of all R*B outer-product vectors u_b^r (u_b^r)^T. The closest
matrix to the baseline H2 is its two-sided orthogonal projection. If even
that relaxed fit is >0.040 away from a passing 0.020-error baseline, no
weights W can make these fixed angles feasible. QR retains all columns,
including any numerical completion for deficient columns, making the
relaxation conservative. Orthogonality and span residuals are reported.
"""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path

import numpy as np

from inverse_v2_chemistry_screen import ROOT, h2_coefs
from dfthcsos.scoreinfra.dfthc_math import reconstruct_u_vectors


def main():
    data=dict(np.load(ROOT/'dqi_inputs/chemistry_4033/submission.npz'))
    data.update(dict(np.load(ROOT/'dqi_inputs/chemistry_4033/asterios_refit.npz')))
    base=h2_coefs(data,8).reshape(352,-1)
    start=time.monotonic()
    report=[]
    for brot,mode in ((7,'nearest_even'),(7,'half_up'),(7,'floor'),(6,'half_up'),(6,'nearest_even'),(6,'floor')):
        divisor=1<<(8-brot)
        if mode=='nearest_even':words=np.rint(data['angle_words']/divisor).astype(np.int64)
        elif mode=='half_up':words=(data['angle_words']+divisor//2)//divisor
        else:words=data['angle_words']//divisor
        words%=(1<<brot)
        u=reconstruct_u_vectors(words/(1<<(brot-1)),data['tree_edges'])[76:]
        vectors=np.einsum('ip,iq->ipq',u,u).reshape(1144,-1).T
        q,r=np.linalg.qr(vectors,mode='reduced')
        span_residual=float(np.linalg.norm(vectors-q@r))
        orth_residual=float(np.linalg.norm(q.T@q-np.eye(q.shape[1])))
        coefficients=base@q
        residual=base-coefficients@q.T
        ga=coefficients@coefficients.T
        gb=residual@residual.T
        # The projection is orthogonal, hence cross Gram blocks vanish.
        squared=2*np.einsum('ij,ij->',ga,gb)+np.einsum('ij,ij->',gb,gb)
        distance=float(np.sqrt(max(squared,0)))
        item={'brot':brot,'rounding':mode,'minimum_distance_to_baseline_H2_in_relaxed_span':distance,'error2_lower_bound':max(0,distance-.020),'impossible_for_any_W_at_these_fixed_angles':distance>.040,'QR_span_residual':span_residual,'QR_orthogonality_residual':orth_residual,'projection_cross_residual':float(np.linalg.norm(residual@q)),'elapsed_seconds':time.monotonic()-start}
        report.append(item);print(json.dumps(item),flush=True)
    path=ROOT/'dqi_inputs/chemistry_4033/screen/projection_bounds.json'
    path.write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
