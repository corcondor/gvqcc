"""Exact-reference relaxed-span lower bounds for six reduced-bit tables.

The allowed H2 tensor is relaxed to P A P with arbitrary symmetric A, where
P projects onto the span of all R*B outer products. Its best approximation
to the exact fixed-shift target T is P T P. The reported distance is an
unconditional necessary lower bound for any W at the specified angles,
up to the small recorded floating-point projection residual.
"""
from __future__ import annotations
import json
import time
from pathlib import Path
import numpy as np
from inverse_v2_chemistry_screen import ROOT
from dfthcsos.scoreinfra.dfthc_math import reconstruct_u_vectors,symmetric_from_lower
from dfthcsos.scoreinfra.reference import check_fcidump,load_reference,load_fixed_shifts,FCIDUMP_SHA256


def main():
    start=time.monotonic()
    data=dict(np.load(ROOT/'dqi_inputs/chemistry_4033/submission_asterios_full.npz'))
    ref=load_reference(check_fcidump())
    shifts=load_fixed_shifts()
    s=np.asarray(symmetric_from_lower(shifts['Hsym_lower'],76),dtype=float)
    rows,cols=np.tril_indices(76)
    scales=np.where(rows==cols,1.,np.sqrt(2.))
    target=ref['tei'][rows[:,None],cols[:,None],rows[None,:],cols[None,:]].copy()
    ident=(rows==cols).astype(float)
    target+=.5*(np.outer(s[rows,cols],ident)+np.outer(ident,s[rows,cols]))
    target*=scales[:,None]*scales[None,:]
    target_squared=float(np.einsum('ij,ij->',target,target))
    del ref
    print(json.dumps({'reference_loaded_seconds':time.monotonic()-start,'target_frobenius_squared':target_squared}),flush=True)
    report=[]
    for brot,mode in ((7,'nearest_even'),(7,'half_up'),(7,'floor'),(6,'half_up'),(6,'nearest_even'),(6,'floor')):
        div=1<<(8-brot)
        if mode=='nearest_even':words=np.rint(data['angle_words']/div).astype(np.int64)
        elif mode=='half_up':words=(data['angle_words']+div//2)//div
        else:words=data['angle_words']//div
        words%=(1<<brot)
        u=reconstruct_u_vectors(words/(1<<(brot-1)),data['tree_edges'])[76:]
        u/=np.linalg.norm(u,axis=1)[:,None]
        v=(u[:,rows]*u[:,cols]*scales).T
        q,r=np.linalg.qr(v,mode='reduced')
        middle=q.T@(target@q)
        squared=target_squared-float(np.einsum('ij,ij->',middle,middle))
        # A conservative roundoff indicator, not an interval-arithmetic proof.
        orth=float(np.linalg.norm(q.T@q-np.eye(q.shape[1])))
        span=float(np.linalg.norm(v-q@r))
        item={'brot':brot,'rounding':mode,'exact_reference_relaxed_error2_lower_bound':max(squared,0)**.5,'threshold':.020,'rejected_for_any_W_at_fixed_angles':squared>.020**2,'QR_span_residual':span,'QR_orthogonality_residual':orth,'squared_norm_subtraction_scale':target_squared,'elapsed_seconds':time.monotonic()-start}
        report.append(item);print(json.dumps(item),flush=True)
    out={'reference_sha256':FCIDUMP_SHA256,'target':'tei + (S tensor I + I tensor S)/2','method':'all-RB outer-product span, no rank or per-r restrictions','floating_point':'float64; margins are >9x the threshold, QR residuals reported','results':report}
    path=ROOT/'dqi_inputs/chemistry_4033/screen/exact_projection_bounds.json'
    path.write_text(json.dumps(out,indent=2)+'\n')


if __name__=='__main__':main()
