"""Bounded multi-column orthogonal-gauge restarts of a passing chemistry fit."""
from __future__ import annotations
import argparse
import json
import time
from pathlib import Path
import numpy as np

from inverse_v2_chemistry_gauge import pair_minimum,norm


def local(z, rng, sweeps):
    n=z.shape[1]
    q,_=np.linalg.qr(rng.normal(size=(n,n)))
    x=z@q
    for _ in range(sweeps):
        changed=0
        for j in range(n):
            for k in range(j+1,n):
                a,b=x[:,j],x[:,k]
                before=float(np.abs(a).sum()**2+np.abs(b).sum()**2)
                theta,after=pair_minimum(a,b)
                if before-after>max(1e-12,before*1e-12):
                    c,s=np.cos(theta),np.sin(theta)
                    a,b=a.copy(),b.copy()
                    x[:,j],x[:,k]=c*a+s*b,-s*a+c*b
                    a,b=q[:,j].copy(),q[:,k].copy()
                    q[:,j],q[:,k]=c*a+s*b,-s*a+c*b
                    changed+=1
        if not changed:break
    return x,q


def main():
    p=argparse.ArgumentParser()
    p.add_argument('baseline',type=Path)
    p.add_argument('--seconds',type=float,default=60)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    data=dict(np.load(args.baseline))
    z=np.concatenate((data['W'],data['H2_I'][:,None,:]),axis=1)
    original=z.copy();transforms=np.broadcast_to(np.eye(z.shape[2]),(len(z),z.shape[2],z.shape[2])).copy()
    rng=np.random.default_rng(20261114)
    start=time.monotonic();count=0;accepted=[]
    while time.monotonic()-start<args.seconds:
        r=int(rng.integers(len(z)))
        n=3+count%3
        inds=np.sort(rng.choice(z.shape[2],n,replace=False))
        chunk=z[r][:,inds]
        before=float(.25*np.square(np.abs(chunk).sum(0)).sum())
        x,q=local(chunk,rng,25)
        after=float(.25*np.square(np.abs(x).sum(0)).sum())
        if before-after>max(1e-10,before*1e-10):
            z[r][:,inds]=x
            transforms[r][:,inds]=transforms[r][:,inds]@q
            row={'trial':count,'r':r,'columns':inds.tolist(),'lambda_h2_decrease':before-after,'new_lambda_h2':norm(z),'seconds':time.monotonic()-start}
            accepted.append(row);print(json.dumps(row),flush=True)
        count+=1
    data['W'],data['H2_I']=z[:,:-1,:],z[:,-1,:]
    gramerr=float(np.max(abs(original@original.transpose(0,2,1)-z@z.transpose(0,2,1))))
    ortherr=float(np.max(abs(transforms@transforms.transpose(0,2,1)-np.eye(z.shape[2]))))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(args.out,**data)
    report={'trials':count,'accepted':accepted,'lambda_h2_before':norm(original),'lambda_h2_after':norm(z),'orthogonality_max_error':ortherr,'extended_gram_max_error':gramerr,'full_circuit_verified':False,'elapsed_seconds':time.monotonic()-start}
    args.out.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


if __name__=='__main__':main()
