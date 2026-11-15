#!/usr/bin/env python3
"""Exact functional high/low tensor extraction and shared-AND repacking.

Unlike the formal COMM tensor, pure-low products are free and pure-high
products have only one quotient coordinate on the actual feature interface.
The unchanged public table is used only for independent final phase proofs.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import time

import kickmix as km
import numpy as np

from chemistry_joint_product_resynthesis import extract, synthesize
from chemistry_reachable_exact_proof import pack, prove_one
from score2_angle_feature_patch import feature_context, vector_basis, solve


def bits(value):
    while value:
        low = value & -value
        yield low.bit_length()-1
        value ^= low


def xor_selected(values, selection):
    answer = 0
    for i in bits(selection):
        answer ^= values[i]
    return answer


def normalize_swaps(circuit):
    lines = []
    for line in str(circuit).splitlines():
        p = line.split()
        if p and p[0] == 'SWAP':
            assert len(p) == 3
            a, b = p[1:]
            lines.extend([f'CX {a} {b}', f'CX {b} {a}', f'CX {a} {b}'])
        else:
            lines.append(line)
    return km.Circuit('\n'.join(lines)+'\n')


def make_context(circuit):
    circuit = normalize_swaps(circuit)
    ctx = feature_context(circuit)
    ex = ctx['extraction']
    one = (1 << 1220)-1
    def physical(coefficient):
        answer = 1 if coefficient >> len(ctx['pool']) & 1 else 0
        for i in bits(coefficient & ((1 << len(ctx['pool']))-1)):
            answer ^= 1 << (ctx['pool'][i]+1)
        return answer
    def evaluate(form):
        answer = one if form & 1 else 0
        for i, q in enumerate(ctx['pool']):
            if form >> (q+1) & 1:
                answer ^= ctx['functions'][i]
        return answer
    high_rows = []
    for function in ctx['functions']:
        h = sum(((function >> (16*a)) & 1) << a for a in range(77))
        if h & 1:
            h ^= (1 << 77)-1
        if solve(vector_basis(high_rows), h) is None:
            high_rows.append(h)
    assert len(high_rows) == 75
    hb = vector_basis(high_rows)
    hp = [physical(ctx['high']['expression'](h)) for h in high_rows]
    lp = [physical(ctx['low']['expression'](1 << l)) for l in range(1,16)]
    terms = []
    for a, b, w in ex['terms']:
        parts = []
        for f in (evaluate(a), evaluate(b)):
            constant = f & 1
            h = sum(((f >> (16*i)) & 1) << i for i in range(77))
            h ^= ((1 << 77)-1) if constant else 0
            l = (f & 65535) ^ (65535 if constant else 0)
            hc = solve(hb, h)
            assert hc is not None and not (l & 1)
            assert all(((f >> address) & 1) ==
                       (((h >> (address >> 4)) ^ (l >> (address & 15)) ^ constant) & 1)
                       for address in range(1220))
            parts.append((hc, l >> 1))
        (ha, la), (hb_, lb) = parts
        if ha and lb: terms.append((ha, lb, w))
        if hb_ and la: terms.append((hb_, la, w))
    missing = None
    for i in range(75):
        for j in range(i):
            if ctx['high']['expression'](high_rows[i] & high_rows[j]) is None:
                missing = (hp[i], hp[j])
                break
        if missing: break
    assert missing is not None
    missing_truth = evaluate(missing[0]) & evaluate(missing[1])
    base = vector_basis(ctx['functions']+[missing_truth])
    assert len(base) == len(ctx['functions'])+1
    return dict(circuit=circuit, ctx=ctx, extraction=ex, evaluate=evaluate,
                high_physical=hp, low_physical=lp, cross_terms=terms,
                missing=missing, missing_truth=missing_truth, augmented_basis=base,
                physical=physical)


def cross_tensor(terms):
    result = [0] * (75*15)
    for u, v, w in terms:
        for i in bits(u):
            for j in bits(v):
                result[15*i+j] ^= w
    return result


def core_values(context, terms):
    result = [0]*35
    for a,b,w in terms:
        f = context['evaluate'](a) & context['evaluate'](b)
        for j in bits(w): result[j] ^= f
    return result


def factor_group(terms):
    rows = [0]*15
    for u,v,_ in terms:
        for j in bits(v): rows[j] ^= u
    independent = []
    for row in rows:
        if solve(vector_basis(independent), row) is None:
            independent.append(row)
    basis = vector_basis(independent)
    lows = [0]*len(independent)
    for j,row in enumerate(rows):
        expression = solve(basis,row)
        assert expression is not None
        for i in bits(expression): lows[i] |= 1 << j
    return list(zip(independent,lows))


def repack(context, terms):
    assert cross_tensor(terms) == cross_tensor(context['cross_terms'])
    groups = defaultdict(list)
    for term in terms:
        if all(term): groups[term[2]].append(term)
    packed = []
    flexible = []
    rank_summary = []
    for w,group in sorted(groups.items()):
        factors = factor_group(group)
        def paired(order):
            out = []
            for at in range(0,len(order),2):
                u,v = factors[order[at]]
                h = xor_selected(context['high_physical'],u)
                l = xor_selected(context['low_physical'],v)
                if at+1 < len(order):
                    u2,v2 = factors[order[at+1]]
                    h2 = xor_selected(context['high_physical'],u2)
                    l2 = xor_selected(context['low_physical'],v2)
                    out.append((h ^ l2,h2 ^ l,w))
                else:
                    out.append((h,l,w))
            return out
        first = paired(list(range(len(factors))))
        position = len(packed)
        packed.extend(first)
        rank_summary.append(dict(output_direction=w,rank=len(factors),ands=len(first)))
        # An alternative pairing may switch the sole missing-high coordinate.
        value0 = core_values(context,first)
        for shift in range(1,min(len(factors),8)):
            order = list(range(shift,len(factors)))+list(range(shift))
            alt = paired(order)
            diff = core_values(context,alt)
            sample = next(bits(w))
            expression = solve(context['augmented_basis'],value0[sample]^diff[sample])
            assert expression is not None
            if expression >> len(context['ctx']['functions']) & 1:
                flexible.append((w,position,len(first),alt))
                break
    desired = core_values(context,context['extraction']['terms'])
    actual = core_values(context,packed)
    def difference_expressions():
        result=[]
        for original,candidate in zip(desired,actual):
            expression=solve(context['augmented_basis'],original^candidate)
            assert expression is not None, 'Cross match left a non-univariate residual'
            result.append(expression)
        return result
    coefficients = difference_expressions()
    n = len(context['ctx']['functions'])
    missing_direction = sum(((c >> n)&1) << j for j,c in enumerate(coefficients))
    choices = solve(vector_basis([x[0] for x in flexible]),missing_direction)
    if choices is not None:
        for i in bits(choices):
            _,start,length,alternative=flexible[i]
            packed[start:start+length]=alternative
        actual=core_values(context,packed)
        coefficients=difference_expressions()
        missing_direction=sum(((c>>n)&1)<<j for j,c in enumerate(coefficients))
        assert not missing_direction
    if missing_direction:
        a,b=context['missing']
        packed.append((a,b,missing_direction))
    linears=[]
    for i in range(n):
        w=sum(((c>>i)&1)<<j for j,c in enumerate(coefficients))
        if w:linears.append((context['physical'](1<<i),w))
    result=core_values(context,packed)
    for form,w in linears:
        f=context['evaluate'](form)
        for j in bits(w):result[j]^=f
    assert result==desired
    return packed,linears,dict(group_count=len(groups),group_ranks=rank_summary,
                               high_correction_ands=int(bool(missing_direction)),
                               flexible_groups=len(flexible))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['prepare','build'])
    p.add_argument('--loaders',type=Path,required=True)
    p.add_argument('--batch',type=int,required=True)
    p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--terms-json',type=Path)
    args=p.parse_args()
    started=time.monotonic()
    source=args.loaders/f'angle_k_{args.batch}.kmb'
    context=make_context(km.Circuit.from_file(source))
    args.workspace.mkdir(exist_ok=True,parents=True)
    metadata=dict(batch=args.batch,source_path=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  original_core_ands=len(context['extraction']['terms']),
                  original_cross_rank=len(context['cross_terms']),dimensions=[75,15,35],
                  low_only_products_free=True,high_only_quotient_dimension=1)
    if args.mode=='prepare':
        path=args.workspace/f'input_{args.batch}.txt'
        with path.open('w') as f:
            f.write(f"75 15 35 {len(context['cross_terms'])} {metadata['original_core_ands']}\n")
            for u,v,w in context['cross_terms']:
                f.write(f'{u&((1<<64)-1)} {u>>64} {v} {w}\n')
        packed,linears,detail=repack(context,context['cross_terms'])
        assert len(packed)==metadata['original_core_ands']
        metadata.update(status='EXACT_BASELINE_CROSS_REPACK_CHECK_PASS',baseline_repacked_ands=len(packed),
                        input=str(path),baseline_high_correction_ands=detail['high_correction_ands'])
    else:
        data=json.loads(args.terms_json.read_text())
        terms=[(int(u0)|(int(u1)<<64),int(v),int(w)) for u0,u1,v,w in data['best_terms']]
        packed,linears,detail=repack(context,terms)
        metadata.update(candidate_core_ands=len(packed),ccx_saved=metadata['original_core_ands']-len(packed),details=detail)
        if metadata['ccx_saved']>0:
            circuit=km.Circuit(synthesize(context['extraction'],packed,linears))
            table=args.loaders/'submission.npz'
            words=np.load(table,allow_pickle=False)['angle_words'].astype(np.uint64)
            previous=words[:,5*(args.batch-1):5*args.batch]
            current=words[:,5*args.batch:5*(args.batch+1)]
            a=np.arange(1220,dtype=np.uint64);abits=[pack((a>>q)&1) for q in range(11)]
            metadata['proofs']=[prove_one(circuit,previous,current,abits,'cross/forward'),
                                prove_one(circuit,current,previous,abits,'cross/reverse')]
            candidate=args.workspace/f'angle_k_{args.batch}.kmb'
            circuit.to_file(candidate,format='kmb')
            metadata.update(status='EXACT_REACHABLE_PHASE_PASS',candidate_path=str(candidate),
                            candidate_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),
                            candidate_qubits=circuit.num_qubits,
                            table_sha256=hashlib.sha256(table.read_bytes()).hexdigest(),
                            candidate_ccx=int(circuit.operation_statistics().num_toffoli_like))
        else:metadata['status']='NO_PACKED_AND_REDUCTION'
    metadata['seconds']=time.monotonic()-started
    report=args.workspace/f'{args.mode}_{args.batch}.json'
    report.write_text(json.dumps(metadata,indent=2)+'\n')
    print(json.dumps({k:v for k,v in metadata.items() if k not in ('details','proofs')},sort_keys=True))


if __name__=='__main__':main()
