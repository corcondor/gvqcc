#!/usr/bin/env python3
"""Validate positive trace smoothing, gap reserve, derivatives and input guards."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from score_chemistry_fast_model import FastFixedAngles
from inverse_v2_chemistry_screen import ROOT


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,default=ROOT/'dqi_inputs/chemistry_4033/submission_asterios_full.npz')
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    baseline=dict(np.load(a.baseline,allow_pickle=False))
    guards=[]
    for epsilon in (-1.,float('nan'),float('inf')):
        try:FastFixedAngles(baseline,eigen_smooth=epsilon)
        except ValueError:guards.append({'argument':'eigen_smooth','value':repr(epsilon),'rejected':True})
        else:raise AssertionError('invalid trace smoothing accepted')
    model=FastFixedAngles(baseline)
    c=baseline['W'].shape[-1]
    x=np.r_[baseline['W'].ravel(),baseline['H2_I'].ravel()]
    for epsilon in (-1.,float('nan'),float('inf')):
        try:model.evaluate(x,c,smooth=epsilon)
        except ValueError:guards.append({'argument':'smooth','value':repr(epsilon),'rejected':True})
        else:raise AssertionError('invalid weight smoothing accepted')
    rng=np.random.default_rng(1702)
    # An independently specified small perturbation moves off exact L1 kinks.
    y=x+1e-6*rng.normal(size=x.size)
    direction=rng.normal(size=x.size);direction/=np.linalg.norm(direction)
    base=model.evaluate(y,c,smooth=1e-6)
    exact_base=model.evaluate(y,c,smooth=0.)
    rows=[]
    for epsilon in (1e-7,1e-9):
        model.eigen_smooth=epsilon
        result=model.evaluate(y,c,smooth=1e-6)
        bias=result[-1]['gap']-base[-1]['gap']
        assert -1e-11<=bias<=model.N*epsilon+1e-11
        assert abs(result[-1]['error1']-base[-1]['error1'])<1e-12
        assert abs(result[-1]['error2']-base[-1]['error2'])<1e-12
        exact=model.evaluate(y,c,smooth=0.)
        assert abs(exact[0]-exact_base[0])<1e-10
        assert np.max(np.abs(exact[2]-exact_base[2]))<1e-10
        analytic=np.r_[result[1]@direction,result[3]@direction]
        checks=[]
        for step in (1e-6,1e-7,1e-8):
            plus=model.evaluate(y+step*direction,c,smooth=1e-6);ap=model.last_assignment
            minus=model.evaluate(y-step*direction,c,smooth=1e-6);am=model.last_assignment
            fd=np.r_[(plus[0]-minus[0])/(2*step),(plus[2]-minus[2])/(2*step)]
            error=float(np.max(np.abs(fd-analytic)/np.maximum(1,np.abs(fd))))
            row={'step':step,'finite_difference':fd.tolist(),'analytic':analytic.tolist(),'scaled_error':error,'assignment_changes':sum(u!=v for u,v in zip(ap,am))}
            checks.append(row)
            if error<1e-3 and ap==am:break
        assert checks[-1]['scaled_error']<1e-3 and checks[-1]['assignment_changes']==0
        rows.append({'epsilon':epsilon,'actual_gap_bias':bias,'conservative_bound':model.N*epsilon,'exact_mode_unchanged':True,'derivative_checks':checks})
    report={'status':'PASS','positive_trace_smoothing':rows,'invalid_parameter_guards':guards,'model_sha256':hashlib.sha256(Path(__file__).with_name('score_chemistry_fast_model.py').read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'baseline_sha256':hashlib.sha256(a.baseline.read_bytes()).hexdigest()}
    a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)


if __name__=='__main__':main()
