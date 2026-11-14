#!/usr/bin/env python3
"""Verify a W/H2_I-only refit with the unchanged official ANGLE verifier.

The full original arrays and all original loader files are required.  Only
W and H2_I are replaced.  Declared angle_words/tree_edges, when supplied,
must match the baseline exactly.  Official simulation still recovers the
words from the circuits and enforces both errors and both strict floors.
This script does not submit to Kaggle or replace any baseline file.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

import numpy as np


def digest(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--loaders',type=Path,required=True)
    p.add_argument('--verifier',type=Path,required=True)
    p.add_argument('--engine-dir',type=Path)
    p.add_argument('--out-dir',type=Path,required=True)
    p.add_argument('--baseline-cost',type=float,default=294988786.8708443)
    p.add_argument('--baseline-portfolio-receipt',type=Path,help='Optional exact baseline NPZ/loader hash and cost binding')
    p.add_argument('--logged-baseline-lambda',type=float,default=46.905894137)
    args=p.parse_args()
    if args.out_dir.exists():raise FileExistsError(args.out_dir)
    args.out_dir.mkdir(parents=True)
    start=time.monotonic()
    report={'created_utc':datetime.now(timezone.utc).isoformat(),'status':'PREPARING',
            'candidate_source':str(args.candidate.resolve()),'candidate_source_sha256':digest(args.candidate),
            'baseline_source':str(args.baseline.resolve()),'baseline_source_sha256':digest(args.baseline),
            'verifier':str(args.verifier.resolve()),'verifier_sha256':digest(args.verifier),
            'script_sha256':digest(__file__),'baseline_cost':args.baseline_cost,
            'logged_baseline_lambda':args.logged_baseline_lambda,
            'comparison_cost_provenance':'Numeric comparison only; no baseline receipt supplied',
            'kaggle_submission_performed':False,'observed_public_score':None}
    output_report=args.out_dir/'verification.json'
    try:
        with np.load(args.baseline,allow_pickle=False) as z:base={k:np.array(z[k]) for k in z.files}
        with np.load(args.candidate,allow_pickle=False) as z:trial={k:np.array(z[k]) for k in z.files}
        for name in ('W','H2_I'):
            if name not in trial:raise ValueError(f'Candidate missing {name}')
            if trial[name].shape!=base[name].shape:raise ValueError(f'{name} shape differs')
            if not np.all(np.isfinite(trial[name])):raise ValueError(f'Nonfinite {name}')
        comparisons={}
        for name in ('angle_words','tree_edges'):
            if name not in base:raise ValueError(f'Full baseline missing {name}')
            comparisons[name]=bool(np.array_equal(trial[name],base[name])) if name in trial else None
            if comparisons[name] is False:raise ValueError(f'Candidate {name} differs: loader reuse is not valid')
        report['declared_array_comparisons']=comparisons
        merged=dict(base)
        merged['W']=trial['W'];merged['H2_I']=trial['H2_I']
        target=args.out_dir/'submission.npz'
        np.savez_compressed(target,**merged)
        report['factorization']={'path':str(target.resolve()),'sha256':digest(target),
                                  'replaced_arrays':['W','H2_I'],
                                  'preserved_arrays':[k for k in base if k not in ('W','H2_I')]}
        count=(merged['angle_words'].shape[1]+4)//5
        circuits=[args.loaders/f'angle_k_{k}.kmb' for k in range(count)]
        if any(not f.is_file() for f in circuits):raise FileNotFoundError('Missing original loader file')
        report['loaders']=[{'name':f.name,'sha256':digest(f)} for f in circuits]
        if args.baseline_portfolio_receipt:
            receipt=json.loads(args.baseline_portfolio_receipt.read_text())
            pins={x['member']:x['sha256'] for x in receipt['members']}
            if pins['dfthcsos/submission.npz']!=report['baseline_source_sha256']:
                raise ValueError('Baseline NPZ does not match portfolio receipt')
            for row in report['loaders']:
                if pins['dfthcsos/'+row['name']]!=row['sha256']:
                    raise ValueError('Baseline loader does not match portfolio receipt')
            old=receipt['verification_evidence']['chemistry']['result']
            if old['status']!='PASS' or old['verified_shots']!=78080:
                raise ValueError('Baseline receipt is not the full chemistry PASS')
            if old['score']!=args.baseline_cost:
                raise ValueError('Comparison cost does not match baseline receipt')
            report['comparison_cost_provenance']={'receipt':str(args.baseline_portfolio_receipt.resolve()),
                                                  'sha256':digest(args.baseline_portfolio_receipt),
                                                  'all_baseline_npz_and_loader_hashes_match':True}
        if args.engine_dir:sys.path.insert(0,str(args.engine_dir.resolve()))
        sys.path.insert(0,str(args.verifier.resolve().parents[1]))
        spec=importlib.util.spec_from_file_location('official_fixed_word_verify',args.verifier)
        mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
        result=mod.verify(circuits,target,tree_edges=merged['tree_edges'])
        report['official_result']=result
        comparison_tolerance = max(1e-9, 32 * abs(float(np.spacing(max(abs(result['score']), abs(args.baseline_cost))))))
        report['comparison_roundoff_tolerance']=comparison_tolerance
        report['lower_than_comparison_cost']=bool(result['score'] < args.baseline_cost-comparison_tolerance)
        report['same_comparison_cost_within_roundoff']=bool(abs(result['score']-args.baseline_cost)<=comparison_tolerance)
        report['local_cost_reduction_percent']=100*(1-result['score']/args.baseline_cost)
        report['lambda_below_user_log']=bool(result['lambda_eff']<args.logged_baseline_lambda)
        report['status']=('PASS_AND_LOWER_COMPARISON_COST' if report['lower_than_comparison_cost'] else 'PASS_SAME_COMPARISON_COST' if report['same_comparison_cost_within_roundoff'] else 'PASS_WITHOUT_COMPARISON_GAIN')
    except Exception as ex:
        report['status']='REJECTED';report['error']=f'{type(ex).__name__}: {ex}'
    report['seconds']=time.monotonic()-start
    output_report.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(report,ensure_ascii=False),flush=True)
    if report['status']=='REJECTED':raise SystemExit(1)


if __name__=='__main__':main()
