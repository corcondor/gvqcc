#!/usr/bin/env python3
"""Global exact orthogonal gauge search in FeMoCo C-index.
Per-r W and H2 must be rotated by the SAME orthogonal matrix.
This preserves both 2-body X^T X and 1-body co, not lambda2.
No official scoring claim; compare native KickMix separately.
"""
from __future__ import annotations
import argparse,json,hashlib,math,time,sys
from pathlib import Path
import numpy as np
from longtrain.physical_verify import Physical

def cost(A):
    return .25*np.square(np.abs(A).sum(axis=0)).sum()

def plane_candidates(A, indices, theta_vals):
    i,j=indices[:,0],indices[:,1]
    ai=A[:,i];aj=A[:,j]
    base=np.square(np.abs(ai).sum(axis=0))+np.square(np.abs(aj).sum(axis=0))
    scores=[]
    for theta in theta_vals:
        c,s=np.cos(theta),np.sin(theta)
        a=np.abs(c*ai+s*aj).sum(axis=0)
        b=np.abs(-s*ai+c*aj).sum(axis=0)
        scores.append(a*a+b*b-base)
    scores=np.asarray(scores)
    m=np.unravel_index(np.argmin(scores),scores.shape)
    return float(scores[m]/4),tuple(indices[m[1]]),float(theta_vals[m[0]])

def search(A, max_rounds=10, angles=(.015,.035,.075,.15,.3,.55,.785398), seed=100):
    rng=np.random.default_rng(seed)
    n=A.shape[1]
    idx=np.array([(i,j) for i in range(n) for j in range(i+1,n)],dtype=np.int32)
    grid=np.array([a*z for a in angles for z in (-1,1)])
    hist=[]
    for t in range(max_rounds):
        gain,(i,j),theta=plane_candidates(A,idx,grid)
        if gain >= -1e-11: break
        c,s=np.cos(theta),np.sin(theta)
        a=A[:,i].copy();b=A[:,j].copy()
        A[:,i]=c*a+s*b;A[:,j]=-s*a+c*b
        hist.append(dict(step=t,r_i=int(i),r_j=int(j),theta=theta,delta_lambda2=gain,lambda2_r=cost(A)))
    return A,hist

def evaluate(path, data_path):
    with np.load(path) as z: d={k:np.array(z[k]) for k in z.files}
    model=Physical(data_path)
    b=model.evaluate(d)
    return d,b,model

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source',required=True);ap.add_argument('--data',default='chem_gpu_inputs.npz')
    ap.add_argument('--out',required=True);ap.add_argument('--rounds',type=int,default=10)
    ap.add_argument('--seed',type=int,default=42)
    args=ap.parse_args()
    src=Path(args.source);out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    d,initial,physical=evaluate(src,args.data)
    W=d['W'].copy();H2=d['H2_I'].copy()
    records=[]
    for r in range(W.shape[0]):
        A=np.concatenate([W[r],H2[r,None]],axis=0)
        before=cost(A)
        A,trace=search(A,args.rounds,seed=args.seed+r)
        W[r]=A[:-1];H2[r]=A[-1];
        records.append(dict(r=r,before=before,after=cost(A),trace=trace))
        print('r',r,'start',before,'after',cost(A),'rotations',len(trace),flush=True)
    d['W']=W;d['H2_I']=H2
    output=out/(src.stem+f'_C_ORTHOGONAL_GAUGE_{args.rounds}_{args.seed}.npz')
    np.savez_compressed(output,**d)
    after=physical.evaluate(d)
    result={"source":str(src),"source_sha256":hashlib.sha256(src.read_bytes()).hexdigest(),"output":str(output),"output_sha256":hashlib.sha256(output.read_bytes()).hexdigest(),"initial":initial,"after":after,"nonzero_change_W":int(np.count_nonzero(W != evaluate(src,args.data)[0]['W'])),"angle_words_changed":False,"KMB_recompile_required":False,"rotations":records,"official_KickMix_verification":False}
    (out/'orthogonal_gauge_result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('RESULT',json.dumps(dict(initial_lambda=initial['lambda_eff'],after_lambda=after['lambda_eff'],delta_lambda=after['lambda_eff']-initial['lambda_eff'],initial_err1=initial['error_1'],after_err1=after['error_1'],initial_err2=initial['error_2'],after_err2=after['error_2'],output=str(output)),indent=2),flush=True)
if __name__=='__main__':main()