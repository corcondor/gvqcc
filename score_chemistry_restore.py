#!/usr/bin/env python3
"""Minimum-norm Newton restoration of the three official chemistry constraints."""
from __future__ import annotations
import argparse
import hashlib
import json
import resource
import time
from pathlib import Path
import numpy as np
from inverse_v2_chemistry_refit import FixedAngles
from inverse_v2_chemistry_screen import ROOT
from dfthcsos.scoreinfra.dfthc_math import evaluate_dfthc_angle_words
from dfthcsos.scoreinfra.reference import UPPER_ENERGY


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--baseline',type=Path,default=ROOT/'dqi_inputs/chemistry_4033/submission_asterios_full.npz')
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--iterations',type=int,default=20)
    a=p.parse_args()
    started=time.monotonic()
    script_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    source_bytes=a.source.read_bytes()
    import io
    data=dict(np.load(io.BytesIO(source_bytes),allow_pickle=False))
    baseline=dict(np.load(a.baseline,allow_pickle=False))
    assert np.array_equal(data['angle_words'],baseline['angle_words'])
    assert np.array_equal(data['tree_edges'],baseline['tree_edges'])
    model=FixedAngles(baseline)
    c=data['W'].shape[-1];size=data['W'].size
    x=np.r_[data['W'].ravel(),data['H2_I'].ravel()]
    trace=[]
    result=model.evaluate(x,c,smooth=0.)
    for it in range(a.iterations):
        f,g,v,jac,metrics=result
        row={'iteration':it,'metrics':metrics,'constraints':v.tolist(),'seconds':time.monotonic()-started}
        trace.append(row);print(json.dumps(row),flush=True)
        if np.max(np.abs(v))<1e-8:break
        # Unit-length rows prevent the gap derivative scale from overwhelming
        # the two error constraints in the 3x3 normal system.
        norm=np.linalg.norm(jac,axis=1)
        jj=jac/norm[:,None]
        delta=-jj.T@np.linalg.solve(jj@jj.T+1e-14*np.eye(3),v/norm)
        merit=float(v@v)
        for bt in range(20):
            alpha=2.**(-bt)
            trial=x+alpha*delta
            rr=model.evaluate(trial,c,smooth=0.)
            if float(rr[2]@rr[2])<merit:
                x=trial;result=rr;break
        else:
            row['termination']='no decreasing restoration step'
            break
    data['W']=x[:size].reshape(data['W'].shape)
    data['H2_I']=x[size:].reshape(data['H2_I'].shape)
    metrics=evaluate_dfthc_angle_words(data['angle_words'],data['W'],data['H2_I']-data['W'].sum(1),model.S,model.beta,model.ref,brot=8,tree_edges=data['tree_edges'],energy_upper=UPPER_ENERGY)
    numeric_pass=bool(metrics['error_1']<=.020 and metrics['error_2']<=.020 and metrics['Lambda']>49 and metrics['E_gap']>3.914898 and metrics['gap_in_domain'] and np.isfinite(metrics['lambda_eff']))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(a.out,**data)
    report={'source':str(a.source),'source_sha256':hashlib.sha256(source_bytes).hexdigest(),'script_sha256':script_sha,'candidate':str(a.out),'candidate_sha256':hashlib.sha256(a.out.read_bytes()).hexdigest(),'official_numeric_thresholds_pass':numeric_pass,'official_numeric_metrics':metrics,'exact_angle_words_unchanged':True,'trace':trace,'seconds':time.monotonic()-started,'calls':model.calls,'peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,'full_circuit_verified':False}
    a.out.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='trace'}),flush=True)


if __name__=='__main__':main()
