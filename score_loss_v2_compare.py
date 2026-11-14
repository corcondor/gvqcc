#!/usr/bin/env python3
"""Conditional public-score comparison using unchanged official DQI functions.

Run with the competition Kickmix runtime; this loads no circuit and simulates
no shot. The old chemistry lambda comes from the user, not an audited old ZIP.
"""
from pathlib import Path
import argparse
import json
import sys

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--verifier-dir',type=Path,default=Path(__file__).resolve().parents[1]/'official_sources/Inzainos/verifiers/dqi')
p.add_argument('--old-score',type=float,default=27.30683)
p.add_argument('--observed-score',type=float,default=27.27654)
p.add_argument('--old-t',type=float,default=382599.9932617188)
p.add_argument('--new-t',type=float,default=382115.5671582031)
p.add_argument('--old-lambda',type=float,default=46.905894137)
p.add_argument('--new-lambda',type=float,default=46.906589508623554)
p.add_argument('--shots',type=int,default=102400)
a=p.parse_args()
sys.path.insert(0,str(a.verifier_dir.resolve()))
from verify_submission_dqi import clopper_pearson_upper_bound,repetition_overhead
rows=[]
r0=repetition_overhead(clopper_pearson_upper_bound(0,a.shots))
for errors in range(3):
 eps=clopper_pearson_upper_bound(errors,a.shots)
 r=repetition_overhead(eps)
 cost_ratio=(a.new_t/a.old_t)*(r/r0)*(a.new_lambda/a.old_lambda)
 predicted=a.old_score*cost_ratio**(-1/3)
 rows.append(dict(hypothesized_new_total_failures=errors,eps_plus=eps,repetition_factor=r,total_cost_product_ratio=cost_ratio,predicted_score=predicted,predicted_display=f'{predicted:.5f}',difference_from_observed=predicted-a.observed_score))
print(json.dumps(dict(status='CONDITIONAL_EXPLANATION_NOT_SERVER_FAILURE_DIAGNOSIS',assumptions=['Old DQI had zero failures.','DQI Q, chemistry T/Q and invsqrt cost stay fixed.','Local native T averages approximate the unpublished public-test averages.','Old lambda is user-reported; original baseline ZIP was not supplied.','Both compared evaluations use102400 shots and official default confidence.','Old score is known only to5 displayed decimals.'],inputs={k:str(v) if isinstance(v,Path) else v for k,v in vars(a).items()},hypotheses=rows,toffoli_reduction_percent=100*(1-a.new_t/a.old_t),one_failure_R_increase_percent=100*(rows[1]['repetition_factor']/r0-1),extra_t_break_even_if_one_failure_eliminated=a.new_t*(rows[1]['repetition_factor']/r0-1)),indent=2))
