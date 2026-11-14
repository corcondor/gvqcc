#!/usr/bin/env python3
"""Compare the fast contraction with the original analytic evaluator."""
from __future__ import annotations
import argparse
import hashlib
import json
import time
from pathlib import Path
import numpy as np
from inverse_v2_chemistry_refit import FixedAngles
from inverse_v2_chemistry_screen import ROOT
from score_chemistry_fast_model import FastFixedAngles


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,default=ROOT/'dqi_inputs/chemistry_4033/submission_asterios_full.npz')
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    d=dict(np.load(a.baseline,allow_pickle=False))
    slow=FixedAngles(d)
    # Share immutable reference tensors instead of allocating a second FCIDUMP.
    fast=object.__new__(FastFixedAngles);fast.__dict__=slow.__dict__.copy();fast.prepare_fast()
    x=np.r_[d['W'].ravel(),d['H2_I'].ravel()]
    rng=np.random.default_rng(17);rows=[]
    for amplitude in (0.,1e-7,1e-6):
        y=x+amplitude*rng.normal(size=x.size)
        t=time.monotonic();old=slow.evaluate(y,d['W'].shape[-1]);ts=time.monotonic()-t
        t=time.monotonic();new=fast.evaluate(y,d['W'].shape[-1]);tf=time.monotonic()-t
        absolute=[float(np.max(np.abs(np.asarray(old[i])-np.asarray(new[i])))) for i in range(4)]
        scaled=[float(np.max(np.abs(np.asarray(old[i])-np.asarray(new[i]))/(1+np.abs(old[i])))) for i in range(4)]
        row={'amplitude':amplitude,'absolute_error':absolute,'scaled_error':scaled,'slow_seconds':ts,'fast_seconds':tf,'slow_metrics':old[-1],'fast_metrics':new[-1]}
        rows.append(row);print(json.dumps(row),flush=True)
    # Eigenvector derivatives amplify last-bit changes in h'; the metric and
    # derivative tolerances are separate, and all candidates still require the
    # unchanged official evaluator. This is floating-point validation, not an
    # assertion of bit-identical eigensystems.
    passed=all(max(r['absolute_error'][0],r['absolute_error'][2])<1e-9 and max(r['scaled_error'][1],r['scaled_error'][3])<1e-7 for r in rows)
    report={'status':'PASS' if passed else 'FAIL','cases':rows,'criteria':{'metric_and_constraint_absolute_error':1e-9,'gradient_scaled_error':1e-7},'model_sha256':hashlib.sha256(Path(__file__).with_name('score_chemistry_fast_model.py').read_bytes()).hexdigest(),'baseline_sha256':hashlib.sha256(a.baseline.read_bytes()).hexdigest(),'check_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    a.out.write_text(json.dumps(report,indent=2)+'\n')
    assert passed


if __name__=='__main__':main()
