#!/usr/bin/env python3
"""Two exact classical gauge charts for the DQI diagonal oracle.

The first chart is the accepted x*prod(x+r,r=1..69) chart. The second
replaces root69 by root70. Both retain69 zero physical masks. Comparing
their exact mode counts cannot increase the number of executed scan cells.
The quantum decoder and its input domain are unchanged by this identity.

Derived classical primitives and original gauge integration credit Syed
Asad Ali (Apache-2.0) and the local score3_gauge_sort implementation.
"""
from __future__ import annotations

import argparse
from collections import Counter
from functools import cache
import hashlib
import json
from pathlib import Path
import time

from dqi_gauge_expand import load_original, initialize_builder, save_circuit
from score3_gauge_sort import (odd_even_network, compare_exchange, equal_word,
                              increment_exact, greater_than)


def mode_with_count(original, builder, words, *, stage=lambda _: None):
    """Read-only4025-word exact mode, including one virtual zero.

Both the label and exact maximum multiplicity remain live. Classical
workspace is cleared before release; no quantum operation is emitted.
"""
    import kickmix as km
    if len(words) != 4025 or any(len(w) != 12 for w in words):
        raise ValueError('Expected4025 classical12-bit words')
    flat = [q for w in words for q in w]
    assert len(set(flat)) == len(flat) and all(isinstance(q, km.b) for q in flat)
    entry_q = builder.num_allocated_qubits
    code = original.Classical(builder)
    private = [builder.alloc_bits(13) for _ in range(4096)]
    greater, equal = builder.alloc_bits(2)
    count, best = builder.alloc_bits(12), builder.alloc_bits(12)
    work, label = builder.alloc_bits(2), builder.alloc_bits(12)
    for row in private:
        code.store(row, False)
    for source, target in zip(words, private):
        for a, b in zip(source, target[:12]):
            code.cx(a, b)
    for row in private[4026:]:
        code.store(row[12], True)
    for row in (count, best, work, label):
        code.store(row, False)
    code.store(greater, False)
    code.store(equal, False)
    for index, (a, b) in enumerate(odd_even_network(4096), 1):
        compare_exchange(code, private[a], private[b], greater)
        if index % 65536 == 0:
            stage(dict(comparators=index))
    code.store(count[0], True)
    code.store(best[0], True)
    for index in range(1, 4026):
        current, previous = private[index][:12], private[index-1][:12]
        equal_word(code, current, previous, equal)
        code.cx(True, equal)
        code.push(equal)
        code.store(count, False)
        code.pop()
        code.store(equal, False)
        increment_exact(code, count, work)
        greater_than(code, count, best, greater)
        code.push(greater)
        code.store(best, False)
        for a, b in zip(count, best):
            code.cx(a, b)
        code.store(label, False)
        for a, b in zip(current, label):
            code.cx(a, b)
        code.pop()
        code.store(greater, False)
    for row in private:
        code.store(row, False)
        builder.free(row)
    for row in (count, work):
        code.store(row, False)
        builder.free(row)
    code.store(greater, False)
    code.store(equal, False)
    builder.free(km.array([greater, equal]))
    assert builder.num_allocated_qubits == entry_q
    return label, best, dict(instructions=code.instructions, quantum_qubits=0,
                            toffoli_like=0, retained_classical_bits=24)


def geometry(original):
    old = original.geometry()
    points = old['plan'].points
    F = original.F
    h = [0, 1]
    for root in [*range(1, 69), 70]:
        out = [0]*(len(h)+1)
        for i, c in enumerate(h):
            out[i] ^= F.mul(c, root)
            out[i+1] ^= c
        h = out
    values = tuple(original.OriginalScan.evaluate(h, x) for x in points)
    ratio = tuple(F.mul(x ^ 70, F.invert(x ^ 69)) if x != 69 else 0
                  for x in points)
    indices = old['residual_indices']
    assert all(values[i] == F.mul(old['values'][i], ratio[i]) for i in indices)
    assert all(values[i] for i in indices)
    index69 = points.index(69)
    assert values[index69] and not values[old['pivot_index']]
    return dict(original=old, h_coefficients=tuple(h[1:]), h_values=values,
                ratio=ratio, inverse_ratio=tuple(F.invert(x) if x else 0 for x in ratio),
                new_pivot_index=index69)


def select_two_charts(original, builder, words, spec, *, stage=lambda _: None):
    """Return mutually exclusive old/new labels, retaining old chart on ties."""
    import kickmix as km
    old_label, old_count, old_ledger = mode_with_count(
        original, builder, words, stage=lambda row: stage(dict(chart=0, **row)))
    indices = spec['original']['residual_indices']
    for index, word in zip(indices, words):
        original.scale_mask(builder, word, spec['inverse_ratio'][index])
    new_label, new_count, new_ledger = mode_with_count(
        original, builder, words, stage=lambda row: stage(dict(chart=1, **row)))
    for index, word in zip(indices, words):
        original.scale_mask(builder, word, spec['inverse_ratio'][index], inverse=True)
    code = original.Classical(builder)
    choose = builder.alloc_bits(1)[0]
    greater_than(code, new_count, old_count, choose)
    code.push(choose)
    code.store(old_label, False)
    code.pop()
    code.cx(True, choose)
    code.push(choose)
    code.store(new_label, False)
    code.pop()
    code.store(choose, False)
    builder.free(km.array([choose]))
    for count in (old_count, new_count):
        code.store(count, False)
        builder.free(count)
    return old_label, new_label, dict(charts=[old_ledger, new_ledger],
        comparison_instructions=code.instructions, exact_count_comparison=True,
        tie_rule='Retain the accepted original chart',
        additional_quantum_bits=0, static_toffoli_like=0)


def xor_scaled_mask(original, builder, source, target, scalar):
    """target ^= transpose(M_scalar)*source, preserving source."""
    assert len(source) == len(target) == 12 and not set(source) & set(target)
    count = 0
    for out in range(12):
        column = original.F.mul(scalar, 1 << out)
        for bit in range(12):
            if column >> bit & 1:
                builder.cx(source[bit], target[out])
                count += 1
    return count


def compensation(original, builder, syndromes, label, coefficients):
    count = 0
    for scalar, syndrome in zip(coefficients, syndromes):
        for out in range(12):
            column = original.F.mul(scalar, 1 << out)
            for bit in range(12):
                if column >> bit & 1:
                    builder.cz(label[bit], syndrome[out])
                    count += 1
    return count


def open_two_charts(original, builder, syndromes, masks, *,
                    fixed_old_pivot=None, fixed_new_pivot=None, stage=lambda _: None):
    import kickmix as km
    spec = geometry(original)
    old = spec['original']
    original.OriginalMasks.open_gauge(builder, syndromes, masks, old['plan'])
    words = [masks[i] for i in old['residual_indices']]
    for i in old['residual_indices']:
        original.scale_mask(builder, masks[i], old['inverses'][i])
    label0, label1, ledger = select_two_charts(original, builder, words, spec, stage=stage)
    labels = [label0, label1]
    for k, fixed in enumerate((fixed_old_pivot, fixed_new_pivot)):
        if fixed is not None:
            fixed = km.array([km.b(int(i)) for i in fixed])
            assert not set(fixed) & set(labels[k])
            builder.bit_store(fixed, False)
            builder.cx(labels[k], fixed)
            builder.bit_store(labels[k], False)
            builder.free(labels[k])
            labels[k] = fixed
    label0, label1 = labels
    shifts = 0
    for i in old['residual_indices']:
        builder.cx(label0, masks[i])
        shifts += 12 + xor_scaled_mask(original, builder, label1, masks[i], spec['ratio'][i])
    phases = compensation(original, builder, syndromes, label0, old['coefficients'])
    phases += compensation(original, builder, syndromes, label1, spec['h_coefficients'])
    ledger.update(shift_CX=shifts, compensation_CZ=phases,
                  old_label=[int(str(x)[1:]) for x in label0],
                  new_label=[int(str(x)[1:]) for x in label1])
    return dict(spec=spec, labels=(label0, label1), ledger=ledger)


def close_two_charts(original, builder, masks, record):
    spec = record['spec']
    old = spec['original']
    label0, label1 = record['labels']
    for i in old['residual_indices']:
        builder.cx(label0, masks[i])
        xor_scaled_mask(original, builder, label1, masks[i], spec['ratio'][i])
    for i in old['residual_indices']:
        original.scale_mask(builder, masks[i], old['inverses'][i], inverse=True)
    for label in (label0, label1):
        builder.bit_store(label, False)
        builder.free(label)
    original.OriginalMasks.close_gauge(builder, masks, old['plan'])


def transpose_product(field, scalar, mask):
    return sum(((field.mul(scalar, 1 << i) & mask).bit_count() & 1) << i for i in range(12))


def mode(values):
    counts = Counter(map(int, values))
    counts[0] += 1
    label = min(counts, key=lambda k: (-counts[k], k))
    return label, counts[label]


def model(original, fixtures, seed):
    import numpy as np
    start = time.monotonic()
    spec = geometry(original)
    ratios = [spec['inverse_ratio'][i] for i in spec['original']['residual_indices']]
    transforms = np.empty((4025,4096), dtype=np.uint16)
    transforms[:,0] = 0
    for bit in range(12):
        basis = np.array([transpose_product(original.F, r, 1 << bit) for r in ratios], dtype=np.uint16)
        transforms[:,1<<bit:1<<(bit+1)] = transforms[:,:1<<bit] ^ basis[:,None]
    rng = np.random.default_rng(seed)
    totals = Counter()
    zero_counts = []
    idx = np.arange(4025)
    for _ in range(fixtures):
        values = rng.integers(0,4096,4025,dtype=np.uint16)
        transformed = transforms[idx, values]
        a, b = np.bincount(values,minlength=4096), np.bincount(transformed,minlength=4096)
        a[0] += 1; b[0] += 1
        n0, n1 = int(a.max()), int(b.max())
        totals['old'] += n0; totals['new_chart'] += n1; totals['best'] += max(n0,n1)
        totals['strict_promotions'] += n1 > n0
        zero_counts.append((n0,n1))
    saving = 11*(totals['best']-totals['old'])/fixtures
    return dict(status='CLASSICAL_MASK_MODEL_ONLY', fixtures=fixtures, fixture_seed=seed,
        old_extra_zeros=totals['old']/fixtures,
        alternative_extra_zeros=totals['new_chart']/fixtures,
        selected_extra_zeros=totals['best']/fixtures,
        strict_promotions=totals['strict_promotions'],
        predicted_mean_Toffoli_saving=saving,
        distribution='4025 independent uniform12-bit residual masks and one virtual zero per chart',
        pointwise_nonincrease_proved=True, full_decoder_verification=False,
        count_pairs_sha256=hashlib.sha256(np.asarray(zero_counts,dtype=np.uint16).tobytes()).hexdigest(),
        seconds=time.monotonic()-start)


def build_pieces(original, destination, baseline_bits=208169):
    """Emit separate prefix and suffix with fixed retained-bit interfaces."""
    import kickmix as km
    destination.mkdir(parents=True, exist_ok=True)
    pivot0 = [49458,49457,49456,49455,49454,49453,49452,49451,49450,49449,49448,49447]
    pivot1 = list(range(baseline_bits, baseline_bits+12))
    reserved = baseline_bits+12
    b, S, E = initialize_builder(reserved)
    rec = open_two_charts(original,b,S,E,fixed_old_pivot=pivot0,fixed_new_pivot=pivot1,
        stage=lambda row:print(json.dumps(dict(stage='two_chart_gauge',**row)),flush=True))
    prefix=save_circuit(b,destination/'prefix.kmb')
    del b
    b, S, E = initialize_builder(reserved)
    closing = dict(spec=rec['spec'], labels=tuple(km.array([km.b(i) for i in ids]) for ids in (pivot0,pivot1)))
    close_two_charts(original,b,E,closing)
    suffix=save_circuit(b,destination/'suffix.kmb')
    del b
    result=dict(status='GAUGE_PIECES_BUILT_NOT_DECODER_VERIFIED',prefix=prefix,suffix=suffix,
        old_pivot=pivot0,new_pivot=pivot1,reserved_classical_through=reserved,
        selector=rec['ledger'],extra_physical_point=69,preserved_existing_scan_point=70,
        quantum_width=840,quantum_nonclifford_gates=0,
        needed_integration='Replace original gauge prefix/suffix and insert one conditional point69 scan cell.')
    (destination/'pieces.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def native_gauge_check(original, destination, seed=202611151402):
    """Native classical logic plus quantum phase compensation qualification.

Input syndromes are generated independently from sparse physical error
words. Compare the prefix phase with the difference between the original
mask oracle and the newly represented residual-mask oracle. This checks
the value/phase identity, not only a no-op prefix/closing round trip.
"""
    import kickmix as km
    import numpy as np
    started=time.monotonic()
    spec=geometry(original);old=spec['original'];indices=list(old['residual_indices'])
    meta=json.loads((destination/'pieces.json').read_text())
    rng=np.random.default_rng(seed)
    cases=[];names=[];oracle_labels=[]
    for chart in (0,1):
        for label in (0,1,2,7,2048,4095):
            values=np.zeros(4095,dtype=np.uint16)
            for i in indices:
                scalar=old['values'][i] if chart==0 else spec['h_values'][i]
                values[i]=transpose_product(original.F,scalar,label)
            cases.append(values);names.append(f'chart{chart}_constant{label}')
    for k in range(12):
        values=rng.integers(0,4096,4095,dtype=np.uint16)
        values[list(old['plan'].selected_indices)]=0
        cases.append(values);names.append(f'zero_selected_random{k}')
    for k in range(8):
        cases.append(rng.integers(0,4096,4095,dtype=np.uint16));names.append(f'original_random{k}')
    values=np.asarray(cases,dtype=np.uint16)
    normalized=[]
    for row,name in zip(values,names):
        if name.startswith('original_random'):
            oracle_labels.append(None);continue
        r0=[transpose_product(original.F,old['inverses'][i],int(row[i])) for i in indices]
        r1=[transpose_product(original.F,spec['inverse_ratio'][i],x) for i,x in zip(indices,r0)]
        label0,n0=mode(r0);label1,n1=mode(r1)
        oracle_labels.append((0,label1) if n1>n0 else (label0,0))
    errors=[];syndromes=np.zeros((len(cases),70),dtype=np.uint16)
    for shot in range(len(cases)):
        support=rng.choice(4095,size=(1,18,31,35)[shot%4],replace=False)
        magnitudes=rng.integers(1,4096,len(support),dtype=np.uint16)
        error={int(i):int(e) for i,e in zip(support,magnitudes)};errors.append(error)
        for index,e in error.items():
            point=old['plan'].points[index];power=point
            for j in range(70):
                syndromes[shot,j]^=original.F.mul(e,power)
                power=original.F.mul(power,point)
    quantum=km.array([km.q(i) for i in range(840)])
    classical=km.array([km.b(i) for i in range(49140)])
    qb=(((syndromes[:,:,None]>>np.arange(12,dtype=np.uint16))&1).reshape(len(cases),-1).astype(bool).T.copy())
    cb=(((values[:,:,None]>>np.arange(12,dtype=np.uint16))&1).reshape(len(cases),-1).astype(bool).T.copy())
    prefix=km.Circuit.from_file(str(destination/'prefix.kmb'))
    suffix=km.Circuit.from_file(str(destination/'suffix.kmb'))
    sim=km.Simulator(batch_size=len(cases),seed=seed,debug_print=False)
    sim.write_across_shots(quantum,qb);sim.write_across_shots(classical,cb)
    sim.do(prefix)
    def decode(bits):
        return (bits.T.reshape(len(cases),-1,12).astype(np.uint16)*(1<<np.arange(12,dtype=np.uint16))).sum(axis=2)
    transformed=decode(sim.read_across_shots(classical))
    labels=decode(sim.read_across_shots(km.array([km.b(i) for i in meta['old_pivot']+meta['new_pivot']])))
    phase=sim.read_phase_flipped_across_shots().copy()
    expected=[];old_zero=[];new_zero=[]
    for shot,error in enumerate(errors):
        wanted=0
        for index,e in error.items():
            wanted^=(int(values[shot,index])&e).bit_count()&1
            point=old['plan'].points[index]
            if point<=68:
                changed=0
            elif point==69:
                changed=transpose_product(original.F,spec['h_values'][index],int(labels[shot,1]))
            elif point==70:
                changed=transpose_product(original.F,old['values'][index],int(labels[shot,0]))
            else:
                changed=transpose_product(original.F,old['values'][index],int(transformed[shot,index]))
            wanted^=(changed&e).bit_count()&1
        expected.append(bool(wanted))
        if oracle_labels[shot] is not None:
            assert tuple(map(int,labels[shot]))==oracle_labels[shot],(names[shot],labels[shot],oracle_labels[shot])
    assert np.array_equal(phase,expected),[(names[i],bool(phase[i]),expected[i]) for i in range(len(cases)) if phase[i]!=expected[i]]
    assert np.array_equal(sim.read_across_shots(quantum),qb)
    sim.do(suffix)
    assert np.array_equal(sim.read_across_shots(quantum),qb)
    assert np.array_equal(sim.read_across_shots(classical),cb)
    assert np.array_equal(sim.read_phase_flipped_across_shots(),phase)
    scratch=km.array([km.b(i) for i in range(49140,max(prefix.num_bits,suffix.num_bits))])
    assert not sim.read_across_shots(scratch).any()
    assert prefix.operation_statistics().num_toffoli_like==suffix.operation_statistics().num_toffoli_like==0
    result=dict(status='PASS_NATIVE_TWO_CHART_GAUGE',fixtures=len(cases),seed=seed,
        fixture_names=names,selected_labels=labels.tolist(),
        independent_mode_oracle_cases=sum(x is not None for x in oracle_labels),
        physical_error_weights=[len(e) for e in errors],
        quantum_inputs_preserved=True,classical_inputs_restored=True,
        phase_matches_original_minus_residual_oracle=True,
        all_classical_scratch_cleared=True,quantum_qubits=840,Toffoli_count=0,
        prefix_sha256=meta['prefix']['sha256'],suffix_sha256=meta['suffix']['sha256'],
        fixture_sha256=hashlib.sha256(values.tobytes()+syndromes.tobytes()).hexdigest(),
        seconds=time.monotonic()-started,
        scope='Native exact gauge identity only; no whole decoder verification yet.')
    (destination/'native_gauge.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--fixtures',type=int,default=16384)
    p.add_argument('--seed',type=int,default=202611151401)
    p.add_argument('--pieces',type=Path)
    p.add_argument('--action',choices=('model','build','native'),default='model')
    a=p.parse_args()
    original=load_original(a.source_root)
    if a.action=='model':result=model(original,a.fixtures,a.seed)
    elif a.action=='build':result=build_pieces(original,a.pieces)
    else:result=native_gauge_check(original,a.pieces)
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':
    main()
