#!/usr/bin/env python3
"""Finish independent phase/reachability checks without rerunning synthesis."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import kickmix as km
from chemistry_reachable_exact_proof import pack,prove_one
from score2_clifford_affine_reduce import expand_swaps_for_checker, checked_angle_words


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--table',type=Path,required=True)
    p.add_argument('--reference-table',type=Path)
    args=p.parse_args();start=time.monotonic()
    report=json.loads((args.candidate/'report.json').read_text())
    words=checked_angle_words(args.table)
    report['verified_table_sha256']=hashlib.sha256(args.table.read_bytes()).hexdigest()
    report['verified_word_shape']=list(words.shape)
    report.pop('angle_words_unchanged',None)
    if args.reference_table:
        reference=checked_angle_words(args.reference_table)
        report['reference_table_sha256']=hashlib.sha256(args.reference_table.read_bytes()).hexdigest()
        report['angle_words_unchanged']=bool(np.array_equal(words,reference))
        report['changed_word_count']=int(np.count_nonzero(words!=reference))
    addresses=np.arange(len(words),dtype=np.uint64);ab=[pack((addresses>>q)&1) for q in range(11)]
    zero=np.zeros((len(words),5),dtype=np.uint64);proofs=[]
    for k in range(15):
        path=args.candidate/f'angle_k_{k}.kmb';c=km.Circuit.from_file(path)
        row=next(x for x in report['blocks'] if x['file']==path.name)
        assert row['candidate_sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
        row['swap_gates']=sum(line.startswith('SWAP ') for line in str(c).splitlines())
        row['candidate_operations_with_swap_expanded']=len(c)+2*row['swap_gates']
        # This changes the checker representation only; the emitted KMB is untouched.
        expanded=expand_swaps_for_checker(c)
        previous=words[:,5*(k-1):5*k] if k else zero;current=words[:,5*k:5*(k+1)]
        for direction,incoming,want in [('forward',previous,current),('reverse',current,previous)]:
            proofs.append(prove_one(expanded,incoming,want,ab,f'k={k}/{direction}'))
    report.update(status='EXACT_ALL_BATCHES_AND_PHASE_PASS',reachable_phase_proofs=proofs,
                  validation_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  validation_seconds=time.monotonic()-start,
                  source_operations=sum(x['source_operations'] for x in report['blocks']),
                  candidate_operations=sum(x['candidate_operations'] for x in report['blocks']),
                  removed_operations=sum(x['removed_operations'] for x in report['blocks']),
                  candidate_operations_swap_expanded=sum(x['candidate_operations_with_swap_expanded'] for x in report['blocks']),
                  proof_swap_expansion='SWAP(a,b) is independently represented as CX(a,b); CX(b,a); CX(a,b) in the existing checker only',
                  exact_address_transition_cases=1220*15*2)
    report['removed_operations_swap_expanded']=report['source_operations']-report['candidate_operations_swap_expanded']
    (args.candidate/'submission.npz').write_bytes(args.table.read_bytes())
    (args.candidate/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('blocks','reachable_phase_proofs')},indent=2))


if __name__=='__main__':main()
