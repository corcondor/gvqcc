#!/usr/bin/env python3
"""A single conservative interpolation of the already-verified score6 endpoint.

This is not another optimization run. It preserves every word and loader and
evaluates the one requested 20% displacement using unchanged official math.
"""
from pathlib import Path
import argparse
import hashlib
import json
import time
import numpy as np
from score6_chem_transfer import BASE_SHA, BASE_COST, FastFixedAngles, valid, sha
from score6_chem_transfer import evaluate_dfthc_angle_words, UPPER_ENERGY

ENDPOINT_SHA = '16ee9ad3716309385aa9ce48c1f714e59484b79126ac6fe60591d3ba8bd7ebcf'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--endpoint',type=Path,required=True)
    p.add_argument('--baseline-receipt',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args(); a.out.mkdir(parents=True,exist_ok=False)
    started=time.monotonic()
    assert sha(a.baseline)==BASE_SHA and sha(a.endpoint)==ENDPOINT_SHA
    receipt=json.loads(a.baseline_receipt.read_text())
    assert receipt['factorization']['sha256']==BASE_SHA
    assert receipt['official_result']['status']=='PASS'
    assert receipt['official_result']['score']==BASE_COST
    base=dict(np.load(a.baseline,allow_pickle=False))
    other=dict(np.load(a.endpoint,allow_pickle=False))
    for key in base:
        if key not in {'W','H2_I'}:assert np.array_equal(base[key],other[key]),key
    fraction=.2
    data=dict(base)
    for key in ('W','H2_I'):data[key]=base[key]+fraction*(other[key]-base[key])
    model=FastFixedAngles(base)
    def official(d):
        return evaluate_dfthc_angle_words(d['angle_words'],d['W'],d['H2_I']-d['W'].sum(1),
            model.S,model.beta,model.ref,brot=8,tree_edges=d['tree_edges'],energy_upper=UPPER_ENERGY)
    matched=official(base)
    assert matched==receipt['official_result']['metrics'], 'Baseline receipt discrepancy'
    metrics=official(data)
    cost=metrics['lambda_eff']*14728*427
    report=dict(status='BACKOFF_NUMERIC_CHECK',fraction=fraction,
        source_npz_sha256=BASE_SHA,endpoint_sha256=ENDPOINT_SHA,
        baseline_receipt_sha256=sha(a.baseline_receipt),baseline_metrics_exactly_reproduced=True,
        baseline_metrics=matched,metrics=metrics,cost=cost,cost_gain=BASE_COST-cost,
        error2_margin_Ha=.02-metrics['error_2'],gap_margin_Ha=metrics['E_gap']-3.914898,
        angle_words_unchanged=True,tree_edges_unchanged=True,loaders_unchanged=True,
        full_official_verifier_run=False,script_sha256=sha(__file__),
        prior_discrepancy_resolution='The earlier claimed mismatch mixed distinct candidates/baseline receipts. The SHA-bound5f8 official baseline is reproduced exactly here; no platform discrepancy was established.',
        saved=False,seconds=time.monotonic()-started)
    if valid(metrics) and .02-metrics['error_2']>=5e-9 and cost<BASE_COST:
        dest=a.out/'candidate.npz';np.savez_compressed(dest,**data)
        report.update(saved=True,path=str(dest),sha256=sha(dest))
    (a.out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
