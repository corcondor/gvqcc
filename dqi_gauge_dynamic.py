"""Promote a fixed128 classical gauge using observed residual-mask labels.

Derived counter/comparison construction: Syed Asad Ali, Apache-2.0,
adaptive_gauge64.py.  This file never edits the verified baseline circuit.
All original candidates precede new candidates; strict capped comparison
therefore guarantees pointwise nondecreasing exact zero-mask count.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import resource
import time

from dqi_gauge_expand import load_original, select_expanded, initialize_builder, save_circuit


def equal_word(code, a, b, equal, different):
    # b is a private copy, so even when the chosen label came from a itself
    # this temporary XOR cannot destroy the source.  Restore a before return.
    # This uses37 instructions instead of49 for12bits.
    for left,right in zip(a,b):code.cx(right,left)
    code.store(equal, True)
    for left in a:code.store(equal,False,control=left)
    for left,right in zip(a,b):code.cx(right,left)


def count_label(original,code,words,label,counter,work,equal,different,candidate_copy):
    code.store(counter,False)
    code.store(candidate_copy,False)
    for source,target in zip(label,candidate_copy):code.cx(source,target)
    code.store(equal,True)
    for bit in candidate_copy:
        code.store(equal,False,control=bit)
    code.cx(equal,counter[0])  # virtual zero pivot
    for word in words:
        equal_word(code,word,candidate_copy,equal,different)
        original._increment_saturated(code,counter,equal,work)
    code.store(equal,False)
    code.store(candidate_copy,False)


def replace_variable(code,counter,best,label,candidate,comparison):
    equal,greater,different=comparison
    code.store(equal,True)
    code.store(greater,False)
    code.store(different,False)
    for bit in (2,1,0):
        code.cx(counter[bit],different)
        code.cx(best[bit],different)
        code.cx(True,best[bit])
        code.push(equal)
        code.push(counter[bit])
        code.store(greater,True,control=best[bit])
        code.pop(); code.pop()
        code.cx(True,best[bit])
        code.store(equal,False,control=different)
        code.store(different,False)
    code.push(greater)
    code.store(best,False)
    for source,target in zip(counter,best): code.cx(source,target)
    code.store(label,False)
    for source,target in zip(candidate,label): code.cx(source,target)
    code.pop()
    code.store(equal,False)
    code.store(greater,False)


def select_dynamic(original,builder,words,dynamic=32,stage=lambda _:None):
    if not 1<=dynamic<=128: raise ValueError('Require1..128 observed candidates')
    entry_q=builder.num_allocated_qubits
    label,fixed_ledger=select_expanded(original,builder,words,128,stage=stage)
    code=original.Classical(builder)
    best=builder.alloc_bits(3)
    counter=builder.alloc_bits(3)
    work=builder.alloc_bits(3)
    compare=builder.alloc_bits(3)
    equality=builder.alloc_bits(2)
    candidate_copy=builder.alloc_bits(12)
    code.store(work,False);code.store(compare,False);code.store(equality,False)
    count_label(original,code,words,label,best,work,*equality,candidate_copy)
    for i,candidate in enumerate(words[:dynamic]):
        count_label(original,code,words,candidate,counter,work,*equality,candidate_copy)
        replace_variable(code,counter,best,label,candidate,compare)
        stage({'stage':'observed_mask_candidate','candidate':i+1,'total':dynamic})
    code.store(best,False);code.store(counter,False)
    for wires in (best,counter,work,compare,equality,candidate_copy): builder.free(wires)
    assert builder.num_allocated_qubits==entry_q
    return label,{'fixed_ledger':fixed_ledger,'observed_candidates':dynamic,
                  'promotion_classical_instructions':code.instructions,
                  'selector_instructions':fixed_ledger['selector_instructions']+code.instructions,
                  'retained_label_bits':12,'additional_quantum_bits':0,'static_toffoli_like':0,
                  'equality_implementation':'Temporarily XOR each input word with a private candidate copy, test zero, then restore input.',
                  'pointwise_rule':'Original128 first, then input words in order; replace only on strictly larger count capped at7.'}


def oracle(words,dynamic=32):
    from collections import Counter
    counts=Counter(int(w) for w in words);counts[0]+=1
    candidates=list(range(128))+[int(w) for w in words[:dynamic]]
    chosen=max(candidates,key=lambda label:min(7,counts[label]))
    return chosen,counts[chosen]


def native_check(original,dynamic=32):
    import kickmix as km
    import numpy as np
    begin=time.monotonic()
    rng=np.random.default_rng(20261115)
    cases=[];names=[]
    for i in range(dynamic):
        row=np.full(4025,4095,dtype=np.uint16)
        row[:dynamic]=np.arange(256,256+dynamic,dtype=np.uint16)
        row[dynamic:dynamic+8]=256+i
        cases.append(row);names.append('observed_winner_'+str(i))
    for a,b in ((6,7),(7,8),(7,4000),(0,1),(1,1),(5,6)):
        row=np.full(4025,4095,dtype=np.uint16)
        row[:dynamic]=np.arange(256,256+dynamic,dtype=np.uint16)
        row[dynamic:dynamic+a]=63
        row[dynamic+a:dynamic+a+b]=256
        cases.append(row);names.append(f'old{a}_new{b+1}')
    for x in (0,63,127,128,2048,4095):
        cases.append(np.full(4025,x,dtype=np.uint16));names.append('constant'+str(x))
    for i in range(64):
        cases.append(rng.integers(0,4096,4025,dtype=np.uint16));names.append('random'+str(i))
    values=np.array(cases,dtype=np.uint16)
    expected=np.array([oracle(row,dynamic)[0] for row in values],dtype=np.uint16)
    b=km.CircuitBuilder();words=[b.alloc_bits(12) for _ in range(4025)]
    output,ledger=select_dynamic(original,b,words,dynamic)
    circuit=b.finish_circuit()
    del b
    assert circuit.num_qubits==0 and circuit.operation_statistics().num_toffoli_like==0
    wires=km.array([bit for word in words for bit in word])
    inbits=(((values[:,:,None]>>np.arange(12,dtype=np.uint16))&1).reshape(len(values),-1).astype(bool).T.copy())
    sim=km.Simulator(batch_size=len(values),seed=20261115,debug_print=False)
    sim.write_across_shots(wires,inbits);sim.do(circuit)
    actual=(sim.read_across_shots(output).T.astype(np.uint16)*(1<<np.arange(12,dtype=np.uint16))).sum(axis=1)
    bad=np.flatnonzero(actual!=expected)
    assert not len(bad),[(names[i],int(actual[i]),int(expected[i])) for i in bad[:8]]
    assert np.array_equal(sim.read_across_shots(wires),inbits)
    output_ids={int(str(x)[1:]) for x in output}
    scratch=km.array([km.b(i) for i in range(48300,circuit.num_bits) if i not in output_ids])
    assert not sim.read_across_shots(scratch).any()
    assert not sim.read_phase_flipped_across_shots().any()
    return {'status':'PASS','fixtures':len(values),'forced_dynamic_winners':dynamic,
            'input_masks_preserved':True,'scratch_cleared':True,'phase_unchanged':True,
            'quantum_bits':circuit.num_qubits,'toffoli_like':0,'instructions':len(circuit),
            'ledger':ledger,'fixture_sha256':hashlib.sha256(values.tobytes()).hexdigest(),
            'seconds':time.monotonic()-begin,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'scope':'Native classical selector only; no whole-decoder correctness or official score claim.'}


def build_and_splice(original,baseline,reference_pieces,out_dir,dynamic=32):
    """Preserve decoder body after exact old-gauge prefix/suffix comparison."""
    import kickmix as km
    from kmb_splice import open_circuit,compare_ranges,write_segments
    expected='e986d41663fa78ea2ed4ab0a47ebc4d99441ad1660b80e02872e7508cbce92a7'
    with baseline.open('rb') as f: actual=hashlib.file_digest(f,'sha256').hexdigest()
    if actual!=expected: raise ValueError('Expected the verified480CCX gauge128 baseline')
    if out_dir.exists(): raise FileExistsError(out_dir)
    out_dir.mkdir(parents=True)
    started=time.monotonic()
    meta=json.loads((reference_pieces/'gauge_pieces.json').read_text())
    fixed_pivot=meta['fixed_pivot']
    b,S,E=initialize_builder(154799)
    geometry=original.geometry()
    original.OriginalMasks.open_gauge(b,S,E,geometry['plan'])
    normalized=[E[i] for i in geometry['residual_indices']]
    for i in geometry['residual_indices']:original.scale_mask(b,E[i],geometry['inverses'][i])
    selected,ledger=select_dynamic(original,b,normalized,dynamic)
    pivot=km.array([km.b(i) for i in fixed_pivot])
    assert not set(pivot)&set(selected)
    b.bit_store(pivot,False);b.cx(selected,pivot);b.bit_store(selected,False);b.free(selected)
    for word in normalized:
        for i in range(12):b.cx(pivot[i],word[i])
    phase_cz=0
    for scalar,syndrome in zip(geometry['coefficients'],S):
        for output in range(12):
            column=original.F.mul(scalar,1<<output)
            for source in range(12):
                if column>>source&1:b.cz(pivot[source],syndrome[output]);phase_cz+=1
    prefix=save_circuit(b,out_dir/'dynamic_prefix.kmb')
    for word in normalized:
        for i in range(12):b.cx(pivot[i],word[i])
    for i in geometry['residual_indices']:original.scale_mask(b,E[i],geometry['inverses'][i],inverse=True)
    b.bit_store(pivot,False)
    original.OriginalMasks.close_gauge(b,E,geometry['plan'])
    pair=save_circuit(b,out_dir/'dynamic_pair.kmb')
    del b
    base=open_circuit(baseline)
    old=open_circuit(reference_pieces/'gauge128_pair.kmb')
    new=open_circuit(out_dir/'dynamic_pair.kmb')
    old_prefix=meta['expanded_prefix']['instructions']
    old_suffix=len(old.opcodes)-old_prefix
    cut=len(base.opcodes)-old_suffix
    checks={'prefix':compare_ranges(base,0,old_prefix,old,0,old_prefix),
            'suffix':compare_ranges(base,cut,len(base.opcodes),old,old_prefix,len(old.opcodes))}
    assert all(c['equal'] for c in checks.values()),'Gauge boundary mismatch'
    candidate=out_dir/f'dqi_ccx480_gauge128_dynamic{dynamic}.kmb'
    written=write_segments(candidate,base,[(new,0,prefix['instructions']),
         (base,old_prefix,cut),(new,prefix['instructions'],len(new.opcodes))])
    report={'status':'SPLICED_REQUIRES_FULL_DECODER_VERIFICATION','baseline_sha256':actual,
            'dynamic_candidates':dynamic,'prefix':prefix,'pair':pair,'selector_ledger':ledger,
            'phase_compensation_cz':phase_cz,'all12_label_bits_shifted_and_compensated':True,
            'boundary_checks':checks,'decoder_body_preserved_byte_for_byte':True,'candidate':written,
            'candidate_path':str(candidate),'seconds':time.monotonic()-started,
            'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'scope':'New candidate only. No full-decoder verification or leaderboard score claim.'}
    for circuit in (base,old,new):circuit.close()
    (out_dir/'dynamic_build.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--dynamic',type=int,default=32)
    p.add_argument('--build-out-dir',type=Path)
    p.add_argument('--baseline',type=Path)
    p.add_argument('--reference-pieces',type=Path)
    a=p.parse_args();assert not a.output.exists()
    original=load_original(a.source_root)
    if a.build_out_dir:
        if not(a.baseline and a.reference_pieces):p.error('Build requires baseline and reference pieces')
        result=build_and_splice(original,a.baseline,a.reference_pieces,a.build_out_dir,a.dynamic)
    else:result=native_check(original,a.dynamic)
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main()
