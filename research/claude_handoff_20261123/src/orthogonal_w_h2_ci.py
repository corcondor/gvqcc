#!/usr/bin/env python3
"""Global O(C)^R orthogonal FeMoCo gauge. Exact W/H2 invariants.

Public research tool. This tests full-column changes to all R blocks; the
reported lambda2 is a NUMERIC candidate screen, not a KickMix cost/score.
"""
import argparse, hashlib, json
from pathlib import Path
import numpy as np

def penalty(x):
    return .25*float(np.square(np.sum(np.abs(x),axis=1)).sum())

def sweep(x,steps=25,seed=91):
    y=x.copy()
    R,N,C=y.shape
    orth=np.tile(np.eye(C),(R,1,1))
    a=np.linspace(-np.pi/4,np.pi/4,steps)
    co,si=np.cos(a),np.sin(a)
    rng=np.random.default_rng(seed)
    applied=0
    for r in rng.permutation(R):
        pairs=[(i,j) for i in range(C) for j in range(i+1,C)]
        rng.shuffle(pairs)
        for i,j in pairs:
            u,v=y[r,:,i].copy(),y[r,:,j].copy()
            cand1=np.abs(u[:,None]*co[None,:]+v[:,None]*si[None,:]).sum(axis=0)
            cand2=np.abs(-u[:,None]*si[None,:]+v[:,None]*co[None,:]).sum(axis=0)
            idx=int(np.argmin(cand1*cand1+cand2*cand2))
            cur=float(np.abs(u).sum()**2+np.abs(v).sum()**2)
            nxt=float(cand1[idx]**2+cand2[idx]**2)
            if cur-nxt>2e-9:
                c,s=co[idx],si[idx]
                y[r,:,i]=c*u+s*v
                y[r,:,j]=-s*u+c*v
                ui,vj=orth[r,:,i].copy(),orth[r,:,j].copy()
                orth[r,:,i]=c*ui+s*vj
                orth[r,:,j]=-s*ui+c*vj
                applied+=1
    return y,orth,applied

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--candidate',type=Path,required=True)
    a=p.parse_args()
    with np.load(a.source,allow_pickle=False) as z:
        arrays={k:z[k].copy() for k in z.files}
    w=np.asarray(arrays['W'],dtype=np.float64)
    h=np.asarray(arrays['H2_I'],dtype=np.float64)
    R,B,C=w.shape
    assert h.shape==(R,C)
    x=np.concatenate((w,h[:,None,:]),axis=1)
    init=penalty(x)
    y,o,changes=sweep(x)
    w2,h2=y[:,:B,:],y[:,B,:]
    arrays['W']=w2;arrays['H2_I']=h2
    coeff_before=np.einsum('rbc,rc->rb',w,h-w.sum(axis=1))
    coeff_after=np.einsum('rbc,rc->rb',w2,h2-w2.sum(axis=1))
    inv_coeff=float(np.max(np.abs(coeff_after-coeff_before)))
    inv_norm=float(np.max(np.abs(np.sum(np.square(h2-w2.sum(axis=1)),axis=1)-np.sum(np.square(h-w.sum(axis=1)),axis=1))))
    inv_gram=float(np.max(np.abs(np.matmul(w2,w2.transpose(0,2,1))-np.matmul(w,w.transpose(0,2,1)))))
    inv_orth=float(np.max(np.abs(np.matmul(o.transpose(0,2,1),o)-np.eye(C))))
    assert max(inv_coeff,inv_norm,inv_gram,inv_orth)<1e-8
    assert penalty(y)<=init+1e-9
    a.candidate.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(a.candidate,**arrays)
    report={'source':str(a.source),'source_sha256':hashlib.sha256(a.source.read_bytes()).hexdigest(),
       'method':'global_blockwise_O(C)_all_pair_jacobi','R_B_C':[R,B,C],
       'lambda2_before':init,'lambda2_after':penalty(y),'accepted_rotations':changes,
       'physical_contraction_invariant_maxdiff':inv_coeff,
       'gram_invariant_maxdiff':inv_gram,'norm_invariant_maxdiff':inv_norm,
       'orthogonality_maxdiff':inv_orth,'candidate_sha256':hashlib.sha256(a.candidate.read_bytes()).hexdigest(),
       'official_KickMix_verified':False,'combined_score':None}
    a.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__': main()
