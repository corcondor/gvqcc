#!/usr/bin/env python3
"""Exact full-label DQI gauge mode by a fixed classical sorting network.

The 4025 twelve-bit masks are read-only.  Private thirteen-bit words contain
their copies, the virtual zero pivot, and sentinel 4096 padding to 4096 words.
A Batcher odd-even mergesort network sorts ascending.  An exact twelve-bit
run counter selects the largest multiplicity, retaining the least label on
ties.  All selector operations and storage are classical: no quantum ancilla
and no Toffoli are introduced.  Full-decoder correctness remains a separate
qualification after the native selector tests and exact gauge-boundary splice.

Gauge integration is derived from dqi_gauge_dynamic.py / dqi_gauge_expand.py,
which credit Syed Asad Ali's Apache-2.0 adaptive_gauge64.py.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import resource
import time

from dqi_gauge_expand import load_original, initialize_builder, save_circuit


def odd_even_network(size):
    """Yield ascending comparators of Batcher odd-even mergesort."""
    if size < 1 or size & (size-1):
        raise ValueError('sorting size must be a positive power of two')
    def merge(lo,n,stride):
        step = 2*stride
        if step < n:
            yield from merge(lo,n,step)
            yield from merge(lo+stride,n,step)
            for i in range(lo+stride,lo+n-stride,step):
                yield i,i+stride
        else:
            yield lo,lo+stride
    def sort(lo,n):
        if n > 1:
            half = n//2
            yield from sort(lo,half)
            yield from sort(lo+half,half)
            yield from merge(lo,n,1)
    yield from sort(0,size)


def greater_than(code,left,right,greater):
    """Set greater=(left>right), preserving both private little-endian words.

    Scanning LSB to MSB overwrites the answer whenever the bits differ.  For
    d=a XOR b, g ^= a; conditional-clear(g,d); g ^= a replaces g by a exactly
    when d=1.  The private right bit temporarily holds d and is then restored.
"""
    if len(left) != len(right):
        raise ValueError('comparison widths differ')
    code.store(greater,False)
    for a,b in zip(left,right):
        code.cx(a,b)
        code.cx(a,greater)
        code.store(greater,False,control=b)
        code.cx(a,greater)
        code.cx(a,b)


def compare_exchange(code,left,right,greater):
    """Ascending exchange in 6*width+3 instructions; leave comparison in gt.

    Keeping right=a XOR b after comparison lets the swap use two XORs per bit:
    conditional left ^= right, then unconditional right ^= left.  This maps
    (a,b) to (b,a) when greater, and otherwise restores (a,b).
    """
    if len(left) != len(right):
        raise ValueError('comparison widths differ')
    code.store(greater,False)
    for a,b in zip(left,right):
        code.cx(a,b)
        code.cx(a,greater)
        code.store(greater,False,control=b)
        code.cx(a,greater)
    code.push(greater)
    for a,b in zip(left,right):
        code.cx(b,a)
    code.pop()
    for a,b in zip(left,right):
        code.cx(a,b)


def equal_word(code,left,right,equal):
    if len(left) != len(right):
        raise ValueError('equality widths differ')
    for a,b in zip(left,right):
        code.cx(b,a)
    code.store(equal,True)
    for a in left:
        code.store(equal,False,control=a)
    for a,b in zip(left,right):
        code.cx(b,a)


def increment_exact(code,counter,work):
    """Increment a little-endian counter modulo 2**width; clear two work bits."""
    carry,other = work
    code.store(carry,True)
    for bit in counter[:-1]:
        code.store(other,False)
        code.and_into_zero(carry,bit,other)
        code.cx(carry,bit)
        carry,other = other,carry
    code.cx(carry,counter[-1])
    code.store(work,False)


def select_sorted(original,builder,words,*,stage=lambda _:None):
    import kickmix as km
    if len(words) != 4025 or any(len(w) != 12 for w in words):
        raise ValueError('require 4025 twelve-bit classical words')
    inputs = [bit for word in words for bit in word]
    if any(not isinstance(bit,km.b) for bit in inputs) or len(set(inputs)) != len(inputs):
        raise ValueError('input masks must be disjoint classical words')
    entry_q = builder.num_allocated_qubits
    code = original.Classical(builder)
    private = [builder.alloc_bits(13) for _ in range(4096)]
    greater,equal = builder.alloc_bits(2)
    count = builder.alloc_bits(12)
    best = builder.alloc_bits(12)
    work = builder.alloc_bits(2)
    label = builder.alloc_bits(12)
    for row in private:
        code.store(row,False)
    for source,target in zip(words,private):
        for a,b in zip(source,target[:12]):
            code.cx(a,b)
    # private[4025] is the virtual zero; all remaining words are sentinel 4096.
    for row in private[4026:]:
        code.store(row[12],True)
    for row in (count,best,work,label):
        code.store(row,False)
    code.store(greater,False)
    code.store(equal,False)
    initial_instructions = code.instructions
    comparisons = 0
    for a,b in odd_even_network(4096):
        compare_exchange(code,private[a],private[b],greater)
        comparisons += 1
        if comparisons % 32768 == 0:
            stage(dict(stage='sorting',comparators=comparisons))
    sorting_instructions = code.instructions-initial_instructions
    assert sorting_instructions == comparisons*(6*13+3)
    # The first valid word is zero because the virtual pivot is included.
    # At most 4026 equal words fit exactly into a twelve-bit counter.
    code.store(count[0],True)
    code.store(best[0],True)
    for index in range(1,4026):
        current,previous = private[index][:12],private[index-1][:12]
        equal_word(code,current,previous,equal)
        code.cx(True,equal)  # equal now means a new run
        code.push(equal)
        code.store(count,False)
        code.pop()
        code.store(equal,False)
        increment_exact(code,count,work)
        greater_than(code,count,best,greater)
        code.push(greater)
        code.store(best,False)
        for a,b in zip(count,best):
            code.cx(a,b)
        code.store(label,False)
        for a,b in zip(current,label):
            code.cx(a,b)
        code.pop()
        code.store(greater,False)
    run_instructions = code.instructions-initial_instructions-sorting_instructions
    for row in private:
        code.store(row,False)
        builder.free(row)
    for row in (count,best,work):
        code.store(row,False)
        builder.free(row)
    code.store(greater,False)
    code.store(equal,False)
    builder.free(km.array([greater,equal]))
    assert builder.num_allocated_qubits == entry_q
    return label,dict(algorithm='Batcher odd-even mergesort followed by exact run counting',
                      input_words=4025,virtual_zero_words=1,padded_words=4096,
                      private_word_bits=13,sentinel=4096,count_bits=12,count_cap=None,
                      comparators=comparisons,sorting_instructions=sorting_instructions,
                      run_instructions=run_instructions,selector_instructions=code.instructions,
                      peak_classical_work_bits=4096*13+2+12+12+2+12,
                      retained_label_bits=12,additional_quantum_bits=0,static_toffoli_like=0,
                      tie_rule='largest exact count; least numerical label on ties',
                      input_masks_read_only=True)


def oracle(words):
    counts = Counter(int(x) for x in words)
    counts[0] += 1
    chosen = min(counts,key=lambda x:(-counts[x],x))
    return chosen,counts[chosen]


def native_primitives(original):
    import kickmix as km
    import numpy as np
    rows=[]
    # Exhaustive four-bit comparator, all thirteen single-bit boundaries,
    # and the actual sentinel versus every twelve-bit value in both orders.
    pairs=[(a,b) for a in range(16) for b in range(16)]
    for i in range(13):
        for a in (0,(1<<i)-1,1<<i,(1<<(i+1))-1):
            for b in (0,(1<<i)-1,1<<i,(1<<(i+1))-1):
                pairs.append((a,b))
    pairs += [(a,4096) for a in range(4096)] + [(4096,a) for a in range(4096)]
    values=np.array(pairs,dtype=np.uint16)
    builder=km.CircuitBuilder();left=builder.alloc_bits(13);right=builder.alloc_bits(13);gt=builder.alloc_bits(1)[0]
    code=original.Classical(builder);compare_exchange(code,left,right,gt)
    circ=builder.finish_circuit();wires=km.array(list(left)+list(right))
    bits=((values[:,:,None]>>np.arange(13,dtype=np.uint16))&1).reshape(len(values),-1).astype(bool).T.copy()
    sim=km.Simulator(batch_size=len(values),seed=20261115,debug_print=False)
    sim.write_across_shots(wires,bits);sim.do(circ)
    actual=(sim.read_across_shots(wires).T.reshape(len(values),2,13).astype(np.uint16)*(1<<np.arange(13,dtype=np.uint16))).sum(axis=2)
    assert np.array_equal(actual,np.sort(values,axis=1))
    assert np.array_equal(sim.read_across_shots(km.array([gt]))[0],values[:,0]>values[:,1])
    assert not sim.read_phase_flipped_across_shots().any()
    rows.append(dict(test='compare_exchange',fixtures=len(values),width=13,instructions=len(circ)))
    # Zero-one principle: native exhaustive binary inputs qualify these exact
    # small network instances.  Larger-network validity also uses its recursive
    # odd-even merge construction, not extrapolation from sampled large inputs.
    for n in (2,4,8,16):
        values=np.arange(1<<n,dtype=np.uint32)
        bits=((values[:,None]>>np.arange(n))&1).astype(bool).T.copy()
        builder=km.CircuitBuilder();w=builder.alloc_bits(n);gt=builder.alloc_bits(1)[0];code=original.Classical(builder)
        pairs=list(odd_even_network(n))
        for a,b in pairs:
            compare_exchange(code,km.array([w[a]]),km.array([w[b]]),gt)
        code.store(gt,False)
        circ=builder.finish_circuit();sim=km.Simulator(batch_size=len(values),seed=20261115,debug_print=False)
        sim.write_across_shots(w,bits);sim.do(circ)
        assert np.array_equal(sim.read_across_shots(w),np.sort(bits,axis=0))
        assert not sim.read_across_shots(km.array([gt])).any()
        assert not sim.read_phase_flipped_across_shots().any()
        rows.append(dict(test='network_zero_one_exhaustive',size=n,fixtures=len(values),comparators=len(pairs)))
    # All 4096 counter states verify the exact increment including wraparound;
    # the selector's reachable count is only 1..4026, so wraparound is unused.
    builder=km.CircuitBuilder();counter=builder.alloc_bits(12);work=builder.alloc_bits(2);code=original.Classical(builder)
    increment_exact(code,counter,work);circ=builder.finish_circuit()
    values=np.arange(4096,dtype=np.uint16);bits=((values[:,None]>>np.arange(12))&1).astype(bool).T.copy()
    sim=km.Simulator(batch_size=4096,seed=20261115,debug_print=False);sim.write_across_shots(counter,bits);sim.do(circ)
    actual=(sim.read_across_shots(counter).T.astype(np.uint16)*(1<<np.arange(12,dtype=np.uint16))).sum(axis=1)
    assert np.array_equal(actual,(values+1)%4096)
    assert not sim.read_across_shots(work).any()
    rows.append(dict(test='exact_increment',fixtures=4096,width=12,instructions=len(circ)))
    return rows


def native_check(original,*,selector_path=None):
    import kickmix as km
    import numpy as np
    begin=time.monotonic();primitives=native_primitives(original)
    print(json.dumps(dict(event='native_primitives_passed',tests=primitives)),flush=True)
    rng=np.random.default_rng(20261115)
    cases=[];names=[]
    for x in (0,1,63,127,128,255,256,2047,2048,4095):
        cases.append(np.full(4025,x,dtype=np.uint16));names.append('constant_'+str(x))
    # Long-count and least-label ties exceed the old saturated counter's range.
    for lo,hi,count in ((17,2048,7),(128,4095,9),(255,256,1000),(1024,2048,2000)):
        row=np.arange(4025,dtype=np.uint16)
        row[:count]=lo;row[count:2*count]=hi
        cases.append(row);names.append(f'tie_{lo}_{hi}_{count}')
    for count in (6,7,8,15,16,31,32,63,64,127,128,255,256,511,512,1023,1024,2047,2048,4025):
        row=np.arange(4025,dtype=np.uint16)
        row[:count]=4095
        cases.append(row);names.append('count_'+str(count))
    row=np.arange(4025,dtype=np.uint16)
    cases.extend((row,row[::-1]));names.extend(('ascending','descending'))
    for i in range(64):
        cases.append(rng.integers(0,4096,4025,dtype=np.uint16));names.append('random_'+str(i))
    values=np.array(cases,dtype=np.uint16)
    expected=np.array([oracle(row)[0] for row in values],dtype=np.uint16)
    builder=km.CircuitBuilder();words=[builder.alloc_bits(12) for _ in range(4025)]
    output,ledger=select_sorted(original,builder,words,stage=lambda row:print(json.dumps(row),flush=True))
    circuit=builder.finish_circuit();del builder
    assert circuit.num_qubits==0 and circuit.operation_statistics().num_toffoli_like==0
    if selector_path is not None:
        circuit.to_file(str(selector_path),format='kmb')
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
    return dict(status='PASS',primitive_tests=primitives,fixtures=len(values),
                fixture_names=names,fixture_sha256=hashlib.sha256(values.tobytes()).hexdigest(),
                input_masks_preserved=True,scratch_cleared=True,phase_unchanged=True,
                quantum_bits=0,toffoli_like=0,instructions=len(circuit),ledger=ledger,
                selected_labels=actual.tolist(),expected_labels=expected.tolist(),
                selector_path=str(selector_path) if selector_path else None,
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                seconds=time.monotonic()-begin,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                scope='Native exact classical selector only; whole-decoder verification is separate.')


def build_and_splice(original,baseline,reference_pieces,out_dir):
    import kickmix as km
    from kmb_splice import open_circuit,compare_ranges,write_segments
    expected='e986d41663fa78ea2ed4ab0a47ebc4d99441ad1660b80e02872e7508cbce92a7'
    with baseline.open('rb') as handle:
        actual=hashlib.file_digest(handle,'sha256').hexdigest()
    if actual!=expected:
        raise ValueError('Expected verified 480CCX gauge128 baseline')
    if out_dir.exists():
        raise FileExistsError(out_dir)
    out_dir.mkdir(parents=True);started=time.monotonic()
    meta=json.loads((reference_pieces/'gauge_pieces.json').read_text())
    b,S,E=initialize_builder(154799)
    geometry=original.geometry()
    original.OriginalMasks.open_gauge(b,S,E,geometry['plan'])
    normalized=[E[i] for i in geometry['residual_indices']]
    for i in geometry['residual_indices']:
        original.scale_mask(b,E[i],geometry['inverses'][i])
    selected,ledger=select_sorted(original,b,normalized,stage=lambda row:print(json.dumps(row),flush=True))
    pivot=km.array([km.b(i) for i in meta['fixed_pivot']])
    assert not set(pivot)&set(selected)
    b.bit_store(pivot,False);b.cx(selected,pivot);b.bit_store(selected,False);b.free(selected)
    for word in normalized:
        for bit in range(12):
            b.cx(pivot[bit],word[bit])
    phase_cz=0
    for scalar,syndrome in zip(geometry['coefficients'],S):
        for output in range(12):
            column=original.F.mul(scalar,1<<output)
            for source in range(12):
                if column>>source&1:
                    b.cz(pivot[source],syndrome[output]);phase_cz+=1
    prefix=save_circuit(b,out_dir/'sort_prefix.kmb')
    for word in normalized:
        for bit in range(12):
            b.cx(pivot[bit],word[bit])
    for i in geometry['residual_indices']:
        original.scale_mask(b,E[i],geometry['inverses'][i],inverse=True)
    b.bit_store(pivot,False)
    original.OriginalMasks.close_gauge(b,E,geometry['plan'])
    pair=save_circuit(b,out_dir/'sort_pair.kmb');del b
    base=open_circuit(baseline)
    old=open_circuit(reference_pieces/'gauge128_pair.kmb')
    new=open_circuit(out_dir/'sort_pair.kmb')
    old_prefix=meta['expanded_prefix']['instructions']
    old_suffix=len(old.opcodes)-old_prefix
    cut=len(base.opcodes)-old_suffix
    checks=dict(prefix=compare_ranges(base,0,old_prefix,old,0,old_prefix),
                suffix=compare_ranges(base,cut,len(base.opcodes),old,old_prefix,len(old.opcodes)))
    assert all(x['equal'] for x in checks.values()),'Gauge boundary mismatch'
    candidate=out_dir/'dqi_ccx480_gauge_sort4096.kmb'
    written=write_segments(candidate,base,[(new,0,prefix['instructions']),
                            (base,old_prefix,cut),(new,prefix['instructions'],len(new.opcodes))])
    report=dict(status='SPLICED_REQUIRES_FULL_DECODER_VERIFICATION',baseline_sha256=actual,
                prefix=prefix,pair=pair,selector_ledger=ledger,phase_compensation_cz=phase_cz,
                all12_label_bits_shifted_and_compensated=True,boundary_checks=checks,
                decoder_body_preserved_byte_for_byte=True,candidate=written,candidate_path=str(candidate),
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                seconds=time.monotonic()-started,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                scope='New exact-mode candidate. Full decoder verification and score evaluation are separate.')
    for circuit in (base,old,new):
        circuit.close()
    (out_dir/'sort_build.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--selector-path',type=Path)
    parser.add_argument('--build-out-dir',type=Path)
    parser.add_argument('--baseline',type=Path)
    parser.add_argument('--reference-pieces',type=Path)
    args=parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    original=load_original(args.source_root)
    if args.build_out_dir:
        if not(args.baseline and args.reference_pieces):
            parser.error('build requires baseline and reference pieces')
        result=build_and_splice(original,args.baseline,args.reference_pieces,args.build_out_dir)
    else:
        result=native_check(original,selector_path=args.selector_path)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':
    main()
