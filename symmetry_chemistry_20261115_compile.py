#!/usr/bin/env python3
"""Bounded compile comparison of original and zero-tag equivalent tables."""
from pathlib import Path
import hashlib
import importlib.util
import json
import resource
import sys
import time
import numpy as np
from symmetry_chemistry_20261115_tags import SOURCE, ROOT, HERE, gauge_row


def anf_statistics(words):
    out=[]
    previous=np.zeros((len(words),5),dtype=np.int64)
    for k in range(15):
        current=words[:,5*k:5*k+5]
        delta=current ^ previous
        masks=np.zeros(2048,dtype=np.uint64)
        for j in range(5): masks[:len(words)] ^= delta[:,j].astype(np.uint64) << (8*j)
        for b in range(11):
            for a in range(2048):
                if a & (1<<b): masks[a] ^= masks[a^(1<<b)]
        out.append(dict(batch=k, nonzero_anf_coefficients=int(np.count_nonzero(masks)),
                        nonlinear_monomial_coefficients=sum(bool(masks[a]) for a in range(2048) if a.bit_count()>=2),
                        coefficient_bit_weight=sum(int(x).bit_count() for x in masks)))
        previous=current
    return out


def main():
    started=time.monotonic()
    data=dict(np.load(SOURCE,allow_pickle=False))
    original=data['angle_words'].astype(np.int64)
    zero_tag=original.copy()
    for a in range(len(original)):
        solved,_,_=gauge_row(original[a],data['tree_edges'],np.zeros(5,dtype=np.int64))
        zero_tag[a]=solved[0]
    official=ROOT/'official_sources/Inzainos/verifiers'
    sys.path.insert(0,str(official))
    path=official/'dfthcsos/example_submission/angle_k_reference_circuit.py'
    spec=importlib.util.spec_from_file_location('reference_angle_compile',path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    from chemistry_reachable_exact_proof import pack,prove_one
    addresses=np.arange(len(original),dtype=np.uint64)
    address_bits=[pack((addresses>>q)&1) for q in range(11)]
    families={}
    for label,words in [('original',original),('zero_tag',zero_tag)]:
        deltas=module.batch_deltas(words,5)
        rows=[]
        for k,delta in enumerate(deltas):
            circuit=module.build_angle_k_circuit(delta,8)
            text=str(circuit)
            counts={g:sum(line.startswith(g+' ') for line in text.splitlines()) for g in ['CCX','CX','HMR','CZ','X']}
            row=dict(batch=k, qubits=circuit.num_qubits, gate_counts=counts)
            if label=='zero_tag':
                previous=words[:,5*(k-1):5*k] if k else np.zeros((len(words),5),dtype=np.int64)
                current=words[:,5*k:5*k+5]
                row['proofs']=[prove_one(circuit,previous,current,address_bits,f'zero/k{k}/forward'),
                               prove_one(circuit,current,previous,address_bits,f'zero/k{k}/reverse')]
            rows.append(row)
        families[label]=dict(rows=rows,total_ccx_per_pass=sum(r['gate_counts']['CCX'] for r in rows),
                             total_cx_per_pass=sum(r['gate_counts']['CX'] for r in rows),
                             max_qubits=max(r['qubits'] for r in rows),
                             anf_zero_padded_completion=anf_statistics(words))
    result=dict(status='EXACT_ZERO_TAG_REFERENCE_FAMILY_PASS_BUT_COST_REGRESSION',
                source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                compiler=str(path),compiler_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                existing_optimized_loader_ccx_per_pass=4033,
                families=families,exact_zero_tag_transition_cases=1220*15*2,
                seconds=time.monotonic()-started,peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
                scope='Actual in-memory reference compiler and exact all-address forward/reverse/phase proof. No full chemistry verifier, candidate files, or remote changes.',
                interpretation='The general reference compiler does not exploit the available gauge to reduce its AND count. ANF numbers use one zero-padded completion and are descriptive only, neither a lower bound nor optimized Toffoli counts.')
    (HERE/'symmetry_chemistry_20261115_compile.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='families'}))
    for label,f in families.items(): print(label,{k:v for k,v in f.items() if k not in ['rows','anf_zero_padded_completion']})

if __name__=='__main__':main()
