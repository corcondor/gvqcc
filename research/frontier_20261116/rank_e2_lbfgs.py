#!/usr/bin/env python3
"""C43/42 two-body feasibility first: analytic Gram gradient + L-BFGS.

The physical two-body residual depends on W W^T, not the one-body offsets.
This stage does not claim valid chemistry until the official one- and two-body,
SOS gap, state-prep cost and 78,080 native shots all pass.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from scipy.optimize import minimize

class E2GramOracle:
    def __init__(self, fixed):
        self.g4=np.asarray(fixed.G4,dtype=np.float64)
        self.a=np.asarray(fixed.A,dtype=np.float64)
        self.p0=np.asarray(fixed.P0,dtype=np.float64)
        self.e20=float(fixed.e20)
        if self.g4.ndim!=4 or self.g4.shape[0]!=self.g4.shape[1]:
            raise ValueError("Bad rank-group Gram shape")
        r,_,b,b2=self.g4.shape
        if b!=b2 or self.a.shape!=(r,b,b) or self.p0.shape!=(r,b,b):
            raise ValueError("Incompatible Gram arrays")
        self.r,self.b=r,b

    def loss_and_gradient(self,w):
        """E2² and analytic gradient 4(A+K)W, K_r = sum_s G_rs delta_s G_rsᵀ."""
        w=np.asarray(w,dtype=np.float64)
        if w.ndim!=3 or w.shape[:2]!=(self.r,self.b):
            raise ValueError("Unexpected factor dimensions")
        delta=w@w.transpose(0,2,1)-self.p0
        k=np.zeros_like(delta)
        for s in range(self.r):
            g=self.g4[:,s]
            k+=(g@delta[s])@g.transpose(0,2,1)
        squared=self.e20+2*np.einsum("rij,rij->",self.a,delta)+np.einsum("rij,rij->",k,delta)
        grad=4*((self.a+k)@w)
        return float(squared),grad

    def minimize(self,w,iterations=800,seconds=500,stop_e2=.019999):
        shape=np.asarray(w).shape
        if len(shape)!=3 or shape[:2]!=(self.r,self.b):raise ValueError("Invalid start")
        if iterations<1 or seconds<=0:raise ValueError("Invalid optimization budget")
        start=time.monotonic(); best=(float("inf"),np.asarray(w).copy())
        steps=0
        class Done(Exception):pass
        def objective(x):
            nonlocal best
            if time.monotonic()-start>seconds:raise Done()
            v,g=self.loss_and_gradient(x.reshape(shape))
            if not (np.isfinite(v) and np.isfinite(g).all()):raise FloatingPointError("Nonfinite tensor objective")
            if v<best[0]:best=(v,x.reshape(shape).copy())
            return v,g.ravel()
        def callback(x):
            nonlocal steps
            steps+=1
            val,_=self.loss_and_gradient(x.reshape(shape))
            if stop_e2 is not None and val<=stop_e2**2:raise Done()
        try:
            result=minimize(objective,best[1].ravel(),jac=True,method="L-BFGS-B",callback=callback,
                  options={"maxiter":iterations,"maxls":30,"ftol":1e-15,"gtol":1e-12,"maxcor":18})
            status=str(result.message)
            v,_=self.loss_and_gradient(result.x.reshape(shape))
            if v<best[0]:best=(v,result.x.reshape(shape).copy())
        except Done:
            status="TIME_OR_E2_TARGET"
        return best[1],{"status":status,"error2":float(np.sqrt(max(best[0],0))),
            "iterations":steps,"seconds":round(time.monotonic()-start,3)}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base-npz",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--ranks",type=int,nargs="+",choices=(43,42),default=[43,42])
    p.add_argument("--seeds",type=int,default=4)
    p.add_argument("--iterations",type=int,default=800)
    p.add_argument("--seconds",type=float,default=500)
    p.add_argument("--stop-e2",type=float,default=.019999)
    args=p.parse_args()
    if args.seeds<1 or not (0<args.stop_e2<=.020):p.error("Bad seeds or E2 threshold")
    from inverse_v2_chemistry_refit import FixedAngles
    from dfthcsos.scoreinfra.dfthc_math import evaluate_dfthc_angle_words
    from dfthcsos.scoreinfra.reference import UPPER_ENERGY
    from rank43_42_joint_gpu import compressed_start,as_candidate
    base=dict(np.load(args.base_npz,allow_pickle=False))
    if base["W"].shape!=(8,143,44):raise ValueError("Expected R8/B143/C44 public family")
    fixed=FixedAngles(base)
    oracle=E2GramOracle(fixed)
    args.output_dir.mkdir(parents=True,exist_ok=False)
    source_sha=hashlib.sha256(args.base_npz.read_bytes()).hexdigest()
    rows=[]
    for rank in args.ranks:
        for seed in range(args.seeds):
            w,d=compressed_start(base,fixed.G4,rank,20261116+100*rank+seed,
                    jitter=0 if seed==0 else min(.015,.003*seed))
            before,_=oracle.loss_and_gradient(w)
            w,trace=oracle.minimize(w,args.iterations,args.seconds,args.stop_e2)
            result=as_candidate(base,w,d)
            check=evaluate_dfthc_angle_words(result["angle_words"],result["W"],
                      result["H2_I"]-result["W"].sum(1),
                      fixed.S,fixed.beta,fixed.ref,brot=8,tree_edges=result["tree_edges"],
                      energy_upper=UPPER_ENERGY)
            candidate=args.output_dir/f"C{rank}_seed{seed}.npz"
            np.savez_compressed(candidate,**result)
            row={"rank":rank,"seed":seed,"initial_e2":float(np.sqrt(max(before,0))),
                "e2_minimization":trace,"official_numeric_metrics":check,
                "source_sha256":source_sha,
                "candidate_sha256":hashlib.sha256(candidate.read_bytes()).hexdigest(),
                "candidate_file":str(candidate),"full_native_verified":False,
                "note":"E2-only stage; E1/Gap/T/Q and native verifier still required"}
            (args.output_dir/f"C{rank}_seed{seed}.json").write_text(json.dumps(row,indent=2)+"\n")
            rows.append({"rank":rank,"seed":seed,"e2":check["error_2"],
                         "e1":check["error_1"],"gap":check["E_gap"]})
            print(json.dumps(rows[-1]),flush=True)
    (args.output_dir/"summary.json").write_text(json.dumps(
        {"source":source_sha,"rows":rows,"status":"NUMERIC_ONLY"},indent=2)+"\n")

if __name__=="__main__":main()
