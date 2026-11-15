#!/usr/bin/env python3
"""Recompute scalar costs from a frozen completed-batch progress receipt.

This does not execute a circuit, resample inputs, or issue an official PASS.
It applies the unchanged official confidence and repetition functions only.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--progress',type=Path,required=True)
    p.add_argument('--verifier',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    observed=json.loads(a.progress.read_text())
    assert observed['process_exit_code']==137
    assert observed['official_verifier_returned'] is False
    last=observed['terminal_completed_batch_callback']
    assert last['batches']==last['total_batches']==400 and last['shots']==102400
    assert hashlib.sha256(a.verifier.read_bytes()).hexdigest()==observed['verifier_sha256']
    spec=importlib.util.spec_from_file_location('frozen_official_dqi_verifier',a.verifier)
    v=importlib.util.module_from_spec(spec);sys.modules[spec.name]=v;spec.loader.exec_module(v)
    failures=last['value_errors']+last['phase_errors']
    plus=v.clopper_pearson_upper_bound(failures,last['shots'],log2_delta=observed['log2_delta'])
    r=v.repetition_overhead(plus)
    exact_sum=round(last['mean_toffolis']*last['shots'])
    assert exact_sum/last['shots']==last['mean_toffolis']
    result=dict(status='RECOVERED_SCALAR_COST_NOT_OFFICIAL_PASS',
        source_progress_sha256=hashlib.sha256(a.progress.read_bytes()).hexdigest(),
        verifier_sha256=observed['verifier_sha256'],
        observed_shots=last['shots'],value_errors=last['value_errors'],phase_errors=last['phase_errors'],
        aggregate_Toffoli=exact_sum,mean_Toffoli=last['mean_toffolis'],
        effective_error_rate=plus,repetition_factor=r,
        recovered_resource_cost=r*observed['num_qubits']**2*last['mean_toffolis'],
        official_PASS_claimed=False,official_verifier_returned=False,
        original_process_exit_code=137,new_circuit_execution=False,new_samples=False)
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
