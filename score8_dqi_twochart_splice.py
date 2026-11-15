#!/usr/bin/env python3
"""Native-check the bound cell, then assemble the new whole DQI candidate."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import time

import kmb_splice as S
from dqi_gauge_expand import load_original
from score8_dqi_twochart import transpose_product


def native_point_check(original, pieces, binding):
    import kickmix as km
    import numpy as np
    c=km.Circuit.from_file(str(pieces/'point69.kmb'))
    rng=np.random.default_rng(202611151403)
    d=np.concatenate([np.arange(4096,dtype=np.uint16),np.zeros(4096,dtype=np.uint16)])
    v=rng.integers(0,4096,len(d),dtype=np.uint16)
    m=np.concatenate([rng.integers(0,4096,4096,dtype=np.uint16),np.arange(4096,dtype=np.uint16)])
    m[:4096:16]=0
    meta=json.loads((pieces/'pieces.json').read_text())
    q=km.array([km.q(i) for i in range(889)])
    mask=km.array([km.b(i) for i in meta['new_pivot']])
    inputs=rng.integers(0,2,(889,len(d)),dtype=np.uint8).astype(bool)
    for word,values in ((binding['point69_locator'],d),(binding['point69_value'],v)):
        inputs[np.asarray(word)]=((values[:,None]>>np.arange(12))&1).T.astype(bool)
    inputs[np.asarray(binding['clean_ladder'])]=False
    mb=((m[:,None]>>np.arange(12))&1).T.astype(bool)
    transformed=np.array([transpose_product(original.F,binding['normalized_mask_factor'],int(x)) for x in m],dtype=np.uint16)
    expected=np.array([bool(not int(x) and ((int(y)&int(z)).bit_count()&1)) for x,y,z in zip(d,v,transformed)])
    seed_results=[]
    for seed in (202611151404,202611151405):
        sim=km.Simulator(batch_size=len(d),seed=seed,debug_print=False,counting_operations=True)
        sim.write_across_shots(q,inputs);sim.write_across_shots(mask,mb);sim.do(c)
        assert np.array_equal(sim.read_across_shots(q),inputs)
        assert np.array_equal(sim.read_across_shots(mask),mb)
        assert np.array_equal(sim.read_phase_flipped_across_shots(),expected)
        measured=int(sim.operation_statistics().num_toffoli_like)
        assert measured==11*int(np.count_nonzero(m))
        seed_results.append(dict(seed=seed,total_Toffoli=measured,phase_errors=0,value_errors=0))
        del sim
    result=dict(status='PASS_NATIVE_BOUND_POINT69',fixtures=len(d),seeds=seed_results,
        complete_locator_values=4096,zero_locator_mask_values=4096,
        arbitrary_other_quantum_data_preserved=True,mask_preserved=True,clean_ladder_restored=True,
        phase_law='[locator=0] * dot(value, transpose(M_factor)*mask)',
        executed_T_law='11*[mask!=0]',factor=binding['normalized_mask_factor'],
        circuit_sha256=binding['extra_cell']['sha256'])
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root',type=Path,required=True)
    p.add_argument('--pieces',type=Path,required=True)
    p.add_argument('--binding',type=Path,required=True)
    p.add_argument('--profile',type=Path)
    p.add_argument('--old-pieces',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    a=p.parse_args();started=time.monotonic()
    binding=json.loads(a.binding.read_text());meta=json.loads((a.pieces/'pieces.json').read_text())
    native=json.loads((a.pieces/'native_gauge.json').read_text())
    assert native['status']=='PASS_NATIVE_TWO_CHART_GAUGE'
    original=load_original(a.source_root)
    cell=native_point_check(original,a.pieces,binding)
    (a.pieces/'native_point69.json').write_text(json.dumps(cell,indent=2)+'\n')
    oldmeta=json.loads((a.old_pieces/'sort_build.json').read_text())
    base=S.open_circuit(binding['baseline_path'],a.profile)
    old=S.open_circuit(a.old_pieces/'sort_pair.kmb')
    prefix=S.open_circuit(a.pieces/'prefix.kmb');suffix=S.open_circuit(a.pieces/'suffix.kmb')
    extra=S.open_circuit(a.pieces/'point69.kmb')
    assert base.profile['raw_kmb_sha256']==binding['baseline_sha256']
    assert prefix.profile['raw_kmb_sha256']==meta['prefix']['sha256']
    assert suffix.profile['raw_kmb_sha256']==meta['suffix']['sha256']
    assert extra.profile['raw_kmb_sha256']==binding['extra_cell']['sha256']
    old_prefix=oldmeta['prefix']['instructions']
    old_suffix=len(old.opcodes)-old_prefix
    cut=len(base.opcodes)-old_suffix;insert=binding['insertion_operation']
    assert old_prefix<insert<cut
    checks=dict(prefix=S.compare_ranges(base,0,old_prefix,old,0,old_prefix),
        suffix=S.compare_ranges(base,cut,len(base.opcodes),old,old_prefix,len(old.opcodes)))
    assert all(row['equal'] for row in checks.values()),'Original gauge boundary changed'
    a.output.parent.mkdir(parents=True,exist_ok=True)
    segments=[(prefix,0,len(prefix.opcodes)),(base,old_prefix,insert),
              (extra,0,len(extra.opcodes)),(base,insert,cut),(suffix,0,len(suffix.opcodes))]
    candidate=S.write_segments(a.output,base,segments)
    assert candidate['header']['num_qubits']==889
    assert candidate['header']['num_ops_with_3_target_qubits']==382905
    report=dict(status='SPLICED_NEW_CANDIDATE_REQUIRES_OFFICIAL_VERIFICATION',
        input_sha256=base.profile['raw_kmb_sha256'],output_path=str(a.output),output=candidate,
        boundary_checks=checks,point69_native_check=cell,
        old_gauge_prefix_operations=old_prefix,old_gauge_suffix_operations=old_suffix,
        point69_old_operation_boundary=insert,new_point69_operations=len(extra.opcodes),
        new_point69_operation_boundary=len(prefix.opcodes)+insert-old_prefix,
        static_Toffoli=382905,static_Toffoli_delta=11,whole_quantum_width=889,
        other_decoder_bytes_preserved=True,
        expected_cost_statement='Both charts have69 fixed zeros. Exact maximum multiplicity selection weakly reduces executed scan Toffolis for every mask input. Fresh-HMR non-scan statistics are unchanged; whole fixed-seed T totals may differ because the simulator random stream shifts.',
        native_gauge_receipt_sha256=hashlib.sha256((a.pieces/'native_gauge.json').read_bytes()).hexdigest(),
        binding_receipt_sha256=hashlib.sha256(a.binding.read_bytes()).hexdigest(),
        elapsed_seconds=time.monotonic()-started)
    a.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='boundary_checks'},indent=2),flush=True)
    for c in (base,old,prefix,suffix,extra):c.close()


if __name__=='__main__':main()
