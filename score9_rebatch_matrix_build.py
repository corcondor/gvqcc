#!/usr/bin/env python3
"""Independently check and compile the cross-only matrix-search export.

Pure-low/pure-high terms are reconstructed from the complete actual word
table by score9_rebatch_synth.synthesize. The original 19-circuit family is
read-only. This adapter emits one representative KMB and an exact proof.
"""
from __future__ import annotations
import argparse, hashlib, json
from collections import defaultdict
from pathlib import Path
import numpy as np
from score9_rebatch_synth import (
    bits, factor_columns, load_pool, prove, synthesize,
)

REPO=Path(__file__).resolve().parent
WORK=Path('/workspace/scratch/3815fb5fae06/score9_rebatch_synth')

def pin(path):
    return dict(path=str(path),bytes=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())

def tensor_mixed(terms):
    value=np.zeros((15,76),dtype=np.uint32)
    for a,b,w in terms:
        al=a&32767;ah=a>>15;bl=b&32767;bh=b>>15
        for i in bits(al):
            for h in bits(bh):value[i,h]^=w
        for i in bits(bl):
            for h in bits(ah):value[i,h]^=w
    return value

def tensor_raw(terms):
    value=np.zeros((15,76),dtype=np.uint32)
    for lo,hi,low,w in terms:
        high=lo|(hi<<64)
        assert high.bit_length()<=76 and low.bit_length()<=15 and w.bit_length()<=28
        for i in bits(low):
            for h in bits(high):value[i,h]^=w
    return value

def pair_export(terms):
    grouped=defaultdict(lambda:[0]*76)
    for lo,hi,low,w in terms:
        high=lo|(hi<<64)
        for h in bits(high):grouped[w][h]^=low
    mixed=[];ranks=[]
    for w,columns in sorted(grouped.items()):
        rankone=factor_columns(columns);ranks.append(dict(output_mask=w,rank=len(rankone)))
        for i in range(0,len(rankone),2):
            a,h1=rankone[i]
            if i+1<len(rankone):
                b,h2=rankone[i+1];mixed.append((a|(h2<<15),b|(h1<<15),w))
            else:mixed.append((a,h1<<15,w))
    return mixed,ranks

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--batch',type=int,default=5)
    p.add_argument('--work',type=Path,default=WORK)
    p.add_argument('--report',type=Path,default=REPO/'score9_rebatch_matrix_report.json')
    a=p.parse_args();k=a.batch
    result_path=REPO/f'score9_rebatch_matrix_k{k}_result.json'
    result=json.loads(result_path.read_text())
    row_path=a.work/'joint'/f'k{k:02d}_result.json';row=json.loads(row_path.read_text())
    source_pool=a.work/'joint/polytof/data/cpd/comm'/f'{9200+k}-{row["core_products_after_joint"]:05d}.npy'
    source=load_pool(source_pool);cross_source=tensor_mixed(source)
    raw=result['best_terms'];cross_raw=tensor_raw(raw)
    assert np.array_equal(cross_source,cross_raw),'raw export cross tensor differs'
    mixed,ranks=pair_export(raw)
    assert len(mixed)==result['best_packed_cost']
    assert np.array_equal(cross_source,tensor_mixed(mixed)),'paired export cross tensor differs'
    words_path=REPO/'score9_rebatch_synth_source_words_1232.npy'
    words=np.pad(np.load(words_path,allow_pickle=False).astype(np.uint64),((0,0),(0,1)))
    delta=words[:,4*k:4*k+4].copy()
    if k:delta^=words[:,4*k-4:4*k]
    circuit=synthesize(delta,row['output_basis'],mixed)
    proof=prove(circuit,delta)
    out=a.work/f'matrix_bridge_k{k}.kmb';circuit.to_file(out,format='kmb')
    assert circuit.operation_statistics().num_toffoli_like==80+len(mixed)
    manifest=dict(status='CROSS_MATRIX_EXPORT_BRIDGE_EXACT_PASS',batch=k,
                  output=pin(out),source_search_result=pin(result_path),source_joint_pool=pin(source_pool),
                  actual_1232_words=pin(words_path),source_basis=pin(row_path),
                  adapter=pin(Path(__file__)),builder=pin(REPO/'score9_rebatch_synth.py'),
                  raw_bilinear_terms=len(raw),paired_products=len(mixed),qubits=circuit.num_qubits,
                  ccx=int(circuit.operation_statistics().num_toffoli_like),
                  source_cross_sha256=hashlib.sha256(cross_source.tobytes()).hexdigest(),
                  independent_raw_cross_equal=True,paired_cross_equal=True,exact_proof=proof,
                  output_ranks=ranks,existing_19_circuit_family_modified=False,
                  full_official_verifier_run=False,native_family_rerun=False,
                  no_additional_gate_saving=result['best_packed_cost']==result['initial_packed_cost'])
    a.report.write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({key:manifest[key] for key in ('status','batch','raw_bilinear_terms','paired_products','ccx','qubits','no_additional_gate_saving')}))

if __name__=='__main__':main()
