#!/usr/bin/env python3
"""Fixed-8-bit-angle cost-aware C44->C43/42/41 DF-THC search (CUDA/CPU).

Experimental numerical search: no result is a verified circuit, score, or
submission until the unchanged official 78,080-shot verifier passes. The script
never submits to Kaggle. Requires the official FeMoCo reference, scoreinfra,
and inverse_v2_chemistry_refit.py from this repository's research environment.

Example:
  OPENBLAS_NUM_THREADS=1 python research_20261116/chemistry_cascade_gpu.py \
    --base-npz /path/to/verified_c44/submission.npz \
    --out-dir /tmp/chem_cascade --device cuda --steps 1500 --seeds 3
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import time
from pathlib import Path
import numpy as np
import torch
from scipy.optimize import linear_sum_assignment

GAP_FLOOR=3.914898
TARGET_ERROR=0.01999999

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1<<20), b''):h.update(block)
    return h.hexdigest()

def spectral_init(w0,ii0,g4,rank,seed=0,noise=0.):
    """Physical Gram-weighted rank projection (not a claim of global best)."""
    r,b,c=w0.shape
    rng=np.random.default_rng(seed)
    outw=np.empty((r,b,rank));outi=np.empty((r,rank))
    for k in range(r):
        w=w0[k].copy()
        if noise:
            w+=noise*max(np.linalg.norm(w),1.)/math.sqrt(w.size)*rng.normal(size=w.shape)
        gram=w.T@g4[k,k]@w
        _,v=np.linalg.eigh(.5*(gram+gram.T))
        eigen=np.linalg.eigvalsh(.5*(gram+gram.T))
        keep=v[:,np.argsort(eigen)[-rank:][::-1]]
        outw[k]=w@keep
        outi[k]=ii0[k]@keep
    return outw,outi

class Model:
    """GPU autodiff using exact cached reference contractions, full 8-bit U."""
    def __init__(self, m, device):
        self.m=m;self.device=torch.device(device)
        self.r,self.b,_=m.base['W'].shape;self.n=m.N
        def t(v):return torch.as_tensor(np.asarray(v).copy(),dtype=torch.float64,device=self.device)
        self.G4=t(m.G4);self.P0=t(m.P0);self.A=t(m.A);self.e20=t(m.e20)
        self.outer=t(m.outer.reshape(self.r,self.b,self.n,self.n))
        self.hbase=t(m.hbase);self.one=t(m.one);self.gap_const=t(m.gap_const)

    def metrics(self,w,ii):
        d=ii-w.sum(1)
        delta=w@w.transpose(1,2)-self.P0
        # Pairs of physical projectors: tensor Gram contraction, no 76^4 allocation.
        kd=torch.zeros_like(delta)
        for s in range(self.r):
            g=self.G4[:,s,:,:]
            kd=kd+g@delta[s]@g.transpose(1,2)
        e2sq=self.e20+2*torch.sum(self.A*delta)+torch.sum(kd*delta)
        x=torch.einsum('rbc,rbpq->rcpq',w,self.outer)
        hp=self.hbase-torch.einsum('rc,rcpq->pq',d,x)
        val,vec=torch.linalg.eigh(hp)
        a,b=linear_sum_assignment(-np.abs((self.one@vec).detach().cpu().numpy()))
        matched=np.empty(self.n,dtype=int);matched[a]=b
        idx=torch.as_tensor(matched,dtype=torch.long,device=self.device)
        qrec=torch.einsum('j,jp,jq->pq',val[idx],self.one,self.one)
        e1=torch.linalg.matrix_norm(qrec-hp)
        e2=torch.sqrt(torch.clamp(e2sq,min=0))
        traceabs=torch.sum(torch.abs(val))
        norms=torch.sum(torch.abs(w),dim=1)+torch.abs(ii)
        lam=traceabs+.25*torch.sum(norms*norms)
        gap=self.gap_const+traceabs-torch.sum(val)+.5*torch.sum(d*d)
        leff=torch.sqrt(torch.clamp(gap*(2*lam-gap),min=1e-30))
        return dict(error_1=e1,error_2=e2,Lambda=lam,E_gap=gap,lambda_eff=leff)

    def loss(self,w,ii,penalty):
        m=self.metrics(w,ii)
        a=torch.relu(m['error_1']/TARGET_ERROR-1)
        b=torch.relu(m['error_2']/TARGET_ERROR-1)
        c=torch.relu((GAP_FLOOR+1e-6-m['E_gap'])/.01)
        d=torch.relu((49.+1e-5-m['Lambda'])/10)
        return torch.log(m['lambda_eff'])+penalty*(a*a+b*b+c*c+d*d),m

def official_resources(m,rank,angle_onepass=4025,angle_temporary=77):
    from dfthcsos.scoreinfra.costs_prepare import SpinFreeData_V1
    c=SpinFreeData_V1(R=m.R,B=m.B,C=rank,N=m.N,chi=10,beta=8)
    T=int(c.outer_state_prep()+c.inner_state_prep()+c.givens_rotations()+2*angle_onepass)
    outer=c.outer_state_prep_qubit_cost()
    inner=c.inner_state_prep_qubit_cost()
    Q=int(outer['persistent']+inner['persistent']+40+
          max(outer['temporary'],inner['temporary'],angle_temporary))
    return T,Q

def valid_numeric(m,t,q,base_cost):
    try:
        return (m['error_1']<=.020 and m['error_2']<=.020
          and m['Lambda']>49 and m['E_gap']>GAP_FLOOR
          and 0<m['E_gap']<2*m['Lambda'] and
          math.isfinite(m['lambda_eff']) and
          m['lambda_eff']*t*q<base_cost)
    except (KeyError,ValueError,TypeError):return False

def search(base_path,out_dir,device,steps,seeds,ranks,lr,angle_onepass,base_cost):
    # The official reference and frozen 8-bit angle words are mandatory.
    from inverse_v2_chemistry_refit import FixedAngles
    from dfthcsos.scoreinfra.dfthc_math import evaluate_dfthc_angle_words
    from dfthcsos.scoreinfra.reference import UPPER_ENERGY
    base=dict(np.load(base_path,allow_pickle=False))
    m=FixedAngles(base)
    if base['W'].shape!=(8,143,44):raise ValueError('Expected R8 B143 C44')
    t0,q0=official_resources(m,44,angle_onepass)
    if (t0,q0)!=(14712,427):
        raise RuntimeError(f'Wrong baseline resources: {(t0,q0)}')
    g=Model(m,device)
    out_dir.mkdir(parents=True,exist_ok=False)
    source_sha=sha(base_path);start=time.monotonic();rows=[]
    for rank in ranks:
        T,Q=official_resources(m,rank,angle_onepass)
        for trial in range(seeds):
            w0,i0=spectral_init(base['W'],base['H2_I'],m.G4,rank,
                seed=20261116+100*rank+trial,noise=trial*.003)
            w=torch.nn.Parameter(torch.as_tensor(w0.copy(),dtype=torch.float64,device=device))
            ii=torch.nn.Parameter(torch.as_tensor(i0.copy(),dtype=torch.float64,device=device))
            opt=torch.optim.Adam([w,ii],lr=lr)
            best=None;best_state=None;trace=[]
            for step in range(steps):
                penalty=[1.,10.,100.,1000.,10000.][min(4,step*5//steps)]
                opt.zero_grad(set_to_none=True)
                loss,_=g.loss(w,ii,penalty)
                if not torch.isfinite(loss):
                    raise FloatingPointError(f'Nonfinite at C={rank} trial={trial} step={step}')
                loss.backward()
                torch.nn.utils.clip_grad_norm_([w,ii],10.)
                opt.step()
                if (step+1)%50==0 or step==steps-1:
                    with torch.no_grad():
                        v={k:float(z.detach().cpu()) for k,z in g.metrics(w,ii).items()}
                    exceed=max(v['error_1']/.020-1,0)+max(v['error_2']/.020-1,0)
                    cost=v['lambda_eff']*T*Q
                    key=(exceed>0,exceed,cost)
                    trace.append({'step':step+1,'penalty':penalty,**v,'cost':cost})
                    if best is None or key<best:
                        best=key
                        best_state=(w.detach().cpu().numpy().copy(),ii.detach().cpu().numpy().copy())
            candidate={**base,'W':best_state[0],'H2_I':best_state[1]}
            # Authoritative exact-words reference check, no surrogate tolerance.
            exact=evaluate_dfthc_angle_words(candidate['angle_words'],candidate['W'],
                candidate['H2_I']-candidate['W'].sum(1),m.S,m.beta,m.ref,
                brot=8,tree_edges=candidate['tree_edges'],energy_upper=UPPER_ENERGY)
            path=out_dir/f'C{rank}_seed{trial}.npz'
            np.savez_compressed(path,**candidate)
            eligible=valid_numeric(exact,T,Q,base_cost)
            result={'C':rank,'trial':trial,'T':T,'Q':Q,'candidate_path':str(path),
                'candidate_sha256':sha(path),'base_sha256':source_sha,
                'exact_numerical':exact,'score_cost':exact['lambda_eff']*T*Q,
                'angle_words_unmodified':bool(np.array_equal(candidate['angle_words'],base['angle_words'])),
                'classification':'ELIGIBLE_FOR_NATIVE_CHECK' if eligible else 'NUMERIC_ONLY_REJECTED',
                'official_78080_shots_pass':False,'kaggle_submitted':False,'trace':trace}
            (out_dir/f'C{rank}_seed{trial}.json').write_text(
                json.dumps(result,indent=2,allow_nan=False)+'\n')
            rows.append({k:result[k] for k in ('C','trial','score_cost','classification')})
            print(json.dumps(rows[-1]),flush=True)
    (out_dir/'summary.json').write_text(json.dumps({'device':device,
        'input_sha256':source_sha,'elapsed_seconds':time.monotonic()-start,'runs':rows,
        'scope':'NUMERICAL SEARCH ONLY, official circuit validation not performed'},indent=2)+'\n')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--base-npz',type=Path,required=True)
    ap.add_argument('--out-dir',type=Path,required=True)
    ap.add_argument('--device',choices=['auto','cpu','cuda'],default='auto')
    ap.add_argument('--ranks',type=int,nargs='+',default=[43,42,41])
    ap.add_argument('--steps',type=int,default=1500)
    ap.add_argument('--seeds',type=int,default=3)
    ap.add_argument('--lr',type=float,default=2e-4)
    ap.add_argument('--angle-onepass',type=int,default=4025)
    ap.add_argument('--cost-to-beat',type=float,default=294762732.98)
    args=ap.parse_args()
    device='cuda' if args.device=='auto' and torch.cuda.is_available() else (
        'cpu' if args.device=='auto' else args.device)
    if device=='cuda' and not torch.cuda.is_available():
        raise SystemExit('No CUDA device. GPU run not performed.')
    if args.steps<=0 or args.seeds<=0 or any(c not in (43,42,41) for c in args.ranks):
        raise SystemExit('Invalid search parameters')
    torch.set_num_threads(1)
    search(args.base_npz,args.out_dir,device,args.steps,args.seeds,
           args.ranks,args.lr,args.angle_onepass,args.cost_to_beat)

if __name__=='__main__':main()
