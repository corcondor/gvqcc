#!/usr/bin/env python3
"""Compare completed matched-input receipts; performs no simulations."""
from pathlib import Path
import hashlib
import json


def main():
    root=Path(__file__).resolve().parent
    paths=[root/'outcome_dqi_chart_norm_paired.json',root/'score5_dqi_norm_fanout_paired.json']
    before,after=[json.loads(p.read_text()) for p in paths]
    assert before['shots']==after['shots']==16896
    assert len(before['batches'])==len(after['batches'])==66
    assert before['failures']==after['failures']
    groups={}
    for old,new in zip(before['batches'],after['batches']):
        assert set(old)==set(new)
        for key in old:
            if key!='toffolis':assert old[key]==new[key],(key,old['group'],old['batch'])
        assert old['toffolis']-new['toffolis']==16*256
        g=groups.setdefault(old['group'],dict(shots=0,value_errors=0,phase_errors=0))
        g['shots']+=256;g['value_errors']+=new['value_errors'];g['phase_errors']+=new['phase_errors']
    result=dict(status='ALL_MATCHED_INPUT_OUTPUT_PHASE_AND_CLASSICAL_HASHES_EQUAL',
                source_sha256=before['circuit_sha256'],candidate_sha256=after['circuit_sha256'],
                shots=16896,batches=66,exact_mean_Toffoli_decrease=16,
                all_failures_identical=True,groups=groups,
                receipts={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
                scope='Includes16384 fixed independent shots and512 prior regression shots. The numerator-zero regression remains; no new failure or phase error is introduced. No new simulation or server scoring.')
    (root/'score5_dqi_norm_fanout_comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
