#!/usr/bin/env python3
"""Evaluate v27 coefficient transfer against the actual retained 4033 words.

This never transfers a4030 cost or assumes that the v27 words match. It also
tests a bounded two-dimensional W/H2 interpolation with every old word fixed.
Only a strictly feasible, lower-cost official-numeric endpoint is saved.
No loader is modified, no full-circuit verifier or submission is performed.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
from pathlib import Path
import resource
import sys
import time
import zipfile
import zlib

import numpy as np
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent/'official_sources/Inzainos/verifiers'))
from dfthcsos.scoreinfra.dfthc_math import evaluate_dfthc_angle_words, reconstruct_u_vectors
from dfthcsos.scoreinfra.reference import UPPER_ENERGY
from score_chemistry_fast_model import FastFixedAngles

BASE_SHA = '5f8dd37ac194b09b5ba870c4150a487b6665775375d9abc864d38b32a2cb7357'
BASE_COST = 294988052.12610483


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def valid(m):
    return bool(m['gap_in_domain'] and m['error_1'] <= .02 and m['error_2'] <= .02
                and m['E_gap'] > 3.914898 and m['Lambda'] > 49)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--baseline', type=Path, default=Path('/workspace/scratch/3815fb5fae06/score2_best_family/submission.npz'))
    p.add_argument('--portfolio', type=Path, default=Path('/workspace/scratch/3815fb5fae06/score5_final_submission/submission.zip'))
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--seconds', type=float, default=35)
    a = p.parse_args()
    assert not a.out.exists()
    a.out.mkdir(parents=True)
    started = time.monotonic()
    assert sha(a.baseline) == BASE_SHA
    base = dict(np.load(a.baseline, allow_pickle=False))
    with zipfile.ZipFile(a.portfolio) as z:
        assert hashlib.sha256(z.read('dfthcsos/submission.npz')).hexdigest() == BASE_SHA
        loader_pins = {f'angle_k_{k}.kmb':hashlib.sha256(z.read(f'dfthcsos/angle_k_{k}.kmb')).hexdigest()
                       for k in range(15)}
        assert all(sha(a.baseline.parent/name) == h for name,h in loader_pins.items())
    public = dict(np.load(ROOT/'outcome_v27_public_weights.npz', allow_pickle=False))
    other_words = np.load(ROOT/'outcome_v27_actual_words_uint8.npy', allow_pickle=False)
    patch = json.loads((ROOT/'outcome_v27_chem_h2_patch.json').read_text())['replacement']
    raw = zlib.decompress(base64.b64decode(patch['zlib_base64']))
    assert hashlib.sha256(raw).hexdigest() == patch['raw_sha256']
    public_i = np.frombuffer(raw,dtype=patch['dtype']).copy().reshape(patch['shape'])
    model = FastFixedAngles(base)
    r,b,c = base['W'].shape

    def official(w, ii):
        return evaluate_dfthc_angle_words(base['angle_words'],w,ii-w.sum(1),
            model.S,model.beta,model.ref,brot=8,tree_edges=base['tree_edges'],energy_upper=UPPER_ENERGY)

    cases = []
    for label,w,ii in [('retained_baseline',base['W'],base['H2_I']),
                       ('v27_H2_only_on_retained_words_and_W',base['W'],public_i),
                       ('v27_W_H2_on_retained_words',public['W'],public_i)]:
        m = official(w,ii)
        cases.append(dict(name=label,metrics=m,numeric_pass=valid(m),
                          cost_if_valid=m['lambda_eff']*14728*427))
        print(json.dumps(cases[-1]),flush=True)
    assert cases[0]['numeric_pass'] and abs(cases[0]['cost_if_valid']-BASE_COST)<.005
    u = reconstruct_u_vectors(base['angle_words']/128,base['tree_edges'])
    v = reconstruct_u_vectors(other_words/128,base['tree_edges'])
    sign = np.where(np.einsum('ij,ij->i',u,v) < 0,-1,1)
    signed_errors = np.linalg.norm(u-sign[:,None]*v,axis=1)
    packed = np.r_[base['W'].ravel(),base['H2_I'].ravel()]
    directions = np.zeros((len(packed),2))
    directions[:r*b*c,0]=(public['W']-base['W']).ravel()
    directions[r*b*c:,1]=(public_i-base['H2_I']).ravel()
    old_tol = .01999998
    tolerance = .0199999998
    ratio = (old_tol/tolerance)**2
    cache = {}
    best = None
    trace = []
    calls = 0
    search_started=time.monotonic()

    def at(x):
        nonlocal calls,best
        key=tuple(float(y) for y in x)
        if key in cache:return cache[key]
        calls+=1
        eff,grad,con,jac,metrics=model.evaluate(packed+directions@x,c,smooth=0.)
        con=con.copy();jac=jac.copy()
        con[:2]=ratio*(con[:2]+1)-1
        jac[:2]*=ratio
        con[2]+=(3.9148980001-3.91489802)/.01
        value=(eff,grad@directions,con,jac@directions,metrics)
        cache.clear();cache[key]=value
        if np.max(con)<=0 and (best is None or eff<best[0]):
            best=(eff,np.array(x),metrics)
            trace.append(dict(call=calls,x=list(key),lambda_eff=eff,**metrics))
            (a.out/'checkpoint.json').write_text(json.dumps(trace,indent=2)+'\n')
        if time.monotonic()-search_started>a.seconds:raise TimeoutError('Bounded transfer search time reached')
        return value

    results=[]
    for start in ([0.,0.],[.05,0.],[0.,.05],[-.05,0.]):
        if time.monotonic()-search_started>a.seconds:break
        try:
            res=minimize(lambda x:at(x)[0],start,jac=lambda x:at(x)[1],method='SLSQP',
                bounds=[(-1,1),(-1,1)],constraints=[{'type':'ineq','fun':lambda x:-at(x)[2],
                    'jac':lambda x:-at(x)[3]}],options={'maxiter':120,'ftol':1e-12})
            results.append(dict(success=bool(res.success),message=str(res.message),x=res.x.tolist(),fun=float(res.fun)))
        except TimeoutError:break
    endpoint=None
    if best is not None:
        value=packed+directions@best[1]
        w=value[:r*b*c].reshape(r,b,c);ii=value[r*b*c:].reshape(r,c)
        m=official(w,ii);cost=m['lambda_eff']*14728*427
        endpoint=dict(x=best[1].tolist(),metrics=m,numeric_pass=valid(m),cost_if_valid=cost,
                      numeric_cost_gain=BASE_COST-cost,saved=False)
        if valid(m) and cost<BASE_COST-1e-5:
            candidate=dict(base,W=w,H2_I=ii)
            path=a.out/'candidate.npz';np.savez_compressed(path,**candidate)
            endpoint.update(saved=True,path=str(path),sha256=sha(path))
    report=dict(status='BOUNDED_FIXED_WORD_COEFFICIENT_TRANSFER_COMPLETE',source_npz_sha256=BASE_SHA,
        script_sha256=sha(__file__),loader_sha256=loader_pins,loaders_unchanged=True,
        angle_words_unchanged=True,current_loader_toffoli_per_pass=4033,total_toffoli=14728,total_qubits=427,
        v27_word_mismatch_count=int(np.count_nonzero(base['angle_words']!=other_words)),
        max_v27_signed_vector_difference=float(signed_errors.max()),
        v27_sign_equivalent_vectors=int(np.count_nonzero(signed_errors<1e-12)),
        official_numeric_cases=cases,search_calls=calls,search_seconds=time.monotonic()-search_started,
        optimizer_results=results,feasible_trace=trace,endpoint=endpoint,
        full_official_verifier_run=False,new_submission=False,
        limits=['The v27 4030-loader cost/receipt is not transferred to the retained4033 family.',
                'Numeric endpoints still require unchanged official full-circuit validation before acceptance.',
                'This is a bounded two-direction search, not an optimality or impossibility proof.'],
        elapsed_seconds=time.monotonic()-started,peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
    (a.out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('loader_sha256','feasible_trace','optimizer_results')},indent=2),flush=True)


if __name__=='__main__':main()
