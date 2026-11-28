#!/usr/bin/env python3
"""Cross-20 high selectors, with rank-r measurement uncompute.

Research, NOT official KickMix scoring. For high selector
 beta(h)=sum_{i=1}^r A_i(h)B_i(h) over GF(2), X-basis measurement
of the high scratch produces (-1)^(m beta). Conditional CZ on
all r linear-flag pairs cancels that phase with no CCX inverse.

The direct high cofactor basis remains the public v5 heuristic;
this changes its physical reversible scheduling and HMR correction.
"""
from __future__ import annotations
import argparse,hashlib,json,math,sys
from collections import Counter
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
for local,hosted in (('gvqcc_multiform','.'),('gvqcc_multiform_v3','multiangle_v3'),('gvqcc_multiform_v4','multiangle_v4'),('gvqcc_multiform_v5','multiangle_v5')):
    sys.path.insert(0,str(ROOT/(local if (ROOT/local).exists() else hosted)))
from multi_angle_synthesis import Circuit,TARGETS,delta_table,word_masks
from partition_patterns import high_flags,monomial_cache,mobius
from global_cofactor import discover_global
from hmr_patterns import MeasuredCircuit
from high_group_basis import cf_cost,emit_low_basis,select_basis,high_groups
from screen_global_axis import greedy_basis
from global_20_basis import factor_selector,emit_high
from basis_exchange import optimize as optimize_basis


def compile_rank_r(words:np.ndarray,slot:int,support:int=2,criterion='pure',global_mode='canonical',basis_exchange=False,initial_basis='global'):
    rows=word_masks(delta_table(words,slot)); H=math.ceil(len(rows)/64)
    global_row,_=discover_global(rows,6,global_mode) if global_mode else ([0]*64,{})
    groups=[[int(v)^global_row[j] for j,v in enumerate(rows[i*64:(i+1)*64])]+[0]*(64-len(rows[i*64:(i+1)*64])) for i in range(H)]
    swaps=None
    if initial_basis=='global':
        info=greedy_basis(rows,global_mode,support,criterion)
        selected_masks=[int(x,16) for x in info['chosen_high_cofactor_masks']]
        selectors=[int(x,16) for x in info['inverse_selector_masks']]
        coefficients=[]
        for mask in selected_masks:
            group=[0]*64
            for h in range(H):
                if mask>>h&1:group=[x^y for x,y in zip(group,groups[h])]
            coefficients.append(mobius(group,6))
    elif initial_basis=='grouped':
        selected_masks=[];selectors=[];coefficients=[]
        for members in high_groups(H,'fixed-upper'):
            chosen,local_selectors,_=select_basis([groups[h] for h in members],min(8,len(members)))
            for j,candidate in enumerate(chosen):
                localmask=candidate[3]
                selected_masks.append(sum((1<<members[i]) for i in range(len(members)) if localmask>>i&1))
                selectors.append(sum((1<<members[i]) for i in range(len(members)) if local_selectors[j]>>i&1))
                coefficients.append(candidate[4])
    else:
        raise ValueError(initial_basis)
    if basis_exchange:
        selected_masks,selectors,coefficients,swaps=optimize_basis(selected_masks,selectors,coefficients)
    # Source function recovery before we touch circuit emission.
    for h in range(H):
        values=[0]*64
        for j,sel in enumerate(selectors):
            if sel>>h&1:values=[x^y for x,y in zip(values,coefficients[j])]
        if values!=mobius(groups[h],6):raise AssertionError(('wrong_basis',slot,h))

    c=Circuit(); hiA,hiB,_=high_flags(c,6); low=monomial_cache(c,6)
    prefix=len(c.gates);high,active,tmp=c.new(3)
    for mon,output in enumerate(mobius(global_row,6)):
        for j,q in enumerate(TARGETS):
            if output>>j&1:
                if mon==0:c.emit('X',q)
                else:c.emit('CX',int(low[mon]),q)

    inverse_segments={};hist=Counter();high_ranks=0
    for selector,coefs in zip(selectors,coefficients):
        if cf_cost(coefs)[0] == 0:continue
        factors=factor_selector(selector)
        r=len(factors)
        hist[r]+=1;high_ranks+=r
        forward=emit_high(c,factors,hiA,hiB,high,active,tmp)
        emit_low_basis(c,low,high,active,tmp,coefs)
        begin=len(c.gates)
        c.undo(forward)
        inverse_segments[begin]=(len(c.gates),factors)
    c.undo(tuple(c.gates[:prefix]))
    if tuple(c.gates[-prefix:])!=tuple(reversed(c.gates[:prefix])):raise AssertionError('bad prefix')
    # Low AND inverses that operate only on fresh scratch; target XORs are
    # dirty but none of their qubits is ever used as a CCX control.
    low_uncompute={}
    for i,(op,qs) in enumerate(c.gates):
        if op!='CCX' or qs[2]!=active:continue
        j=i+1
        while j<len(c.gates) and c.gates[j][0]=='CX' and c.gates[j][1][0]==active and c.gates[j][1][1] in TARGETS:j+=1
        if j>i+1 and j<len(c.gates) and c.gates[j]==(op,qs):low_uncompute[j]=qs

    operations=[];i=0;high_measured=Counter()
    while i<len(c.gates):
        if i in inverse_segments:
            end,factors=inverse_segments[i]
            # Each dropped inverse is pure linear CX around r CCX high updates.
            old=c.gates[i:end]
            if sum(op=='CCX' and qs[-1]==high for op,qs in old)!=len(factors):
                raise AssertionError(('invalid inverse span',slot))
            operations.append(('HMR',(high,),0))
            for a,b in factors:
                # Original selector uses two scratch XORs as controls.
                for bit in range(8):
                    if a>>bit&1:operations.append(('CX',(hiA[bit],active),None))
                for bit in range(3):
                    if b>>bit&1:operations.append(('CX',(hiB[bit],tmp),None))
                operations.append(('CZ',(active,tmp),0))
                for bit in reversed(range(3)):
                    if b>>bit&1:operations.append(('CX',(hiB[bit],tmp),None))
                for bit in reversed(range(8)):
                    if a>>bit&1:operations.append(('CX',(hiA[bit],active),None))
            high_measured[len(factors)]+=1
            i=end;continue
        op,qs=c.gates[i]
        if i in low_uncompute or (i>=len(c.gates)-prefix and op=='CCX'):
            a,b,t=qs
            operations.extend((('HMR',(t,),0),('CZ',(a,b),0)))
        else:operations.append((op,qs,None))
        i+=1
    out=MeasuredCircuit(c.alloc,operations)
    stat=dict(slot=slot,Q=c.alloc,CCX=int(out.counts['CCX']),CX=int(out.counts['CX']),
              HMR=int(out.counts['HMR']),CZ=int(out.counts['CZ']),
              selector_rank_hist=dict(high_measured),measured_high=sum(high_measured.values()),
              selected_high_rank_sum=high_ranks,
              original_high_inverse_ccx=high_ranks,
              sum_output_low_products=sum(cf_cost(coef)[1] for coef in coefficients),
              support=support,criterion=criterion,global_mode=global_mode,
              basis_exchange=basis_exchange,initial_basis=initial_basis,exchanges=swaps,
              source_basis=[hex(m) for m in selected_masks],selectors=[hex(sel) for sel in selectors])
    if out.num_qubits>128:raise AssertionError('qubit overflow')
    return out,stat


def evaluate(seed:Path,out_dir:Path,supports=(2,3),slots=range(15),basis_exchange=False,initial_basis='global'):
    out_dir.mkdir(parents=True,exist_ok=True)
    with np.load(seed,allow_pickle=False) as z:words=np.asarray(z['angle_words'],dtype=np.int64)
    from independent_interleaved import independent_verify
    all_records=[]
    for support in supports:
        dirname=out_dir/f'support_{support}';dirname.mkdir(exist_ok=True)
        for k in slots:
            circuit,stat=compile_rank_r(words,k,support,basis_exchange=basis_exchange,initial_basis=initial_basis)
            path=dirname/f'angle_k_{k}.kmx';path.write_text('\n'.join(circuit.kmx_lines())+'\n',encoding='utf-8')
            cert=independent_verify(path,words,k)
            rec={**stat,**cert,**dict(source=seed.name,input_sha256=hashlib.sha256(seed.read_bytes()).hexdigest(),
                     KMB_issued=False,official_verified=False)}
            all_records.append(rec)
            print(json.dumps({key:rec.get(key) for key in ('slot','support','CCX','CX','HMR','CZ','Q','measured_high','selector_rank_hist')}),flush=True)
    with (out_dir/'ledger.jsonl').open('w') as f:
        for rec in all_records:f.write(json.dumps(rec,sort_keys=True)+'\n')
    group=[]
    for s in supports:
        records=[x for x in all_records if x['support']==s]
        group.append(dict(support=s,basis_exchange=basis_exchange,CCX=sum(x['CCX'] for x in records),
                          CX=sum(x['CX'] for x in records),HMR=sum(x['HMR'] for x in records),
                          CZ=sum(x['CZ'] for x in records),Q=max(x['Q'] for x in records)))
    summary=dict(seed=str(seed),records=len(all_records),groups=group,scope='EXACT_CLASSICAL_ORACLE_AND_SYMBOLIC_MEASUREMENT_PHASE; NO_OFFICIAL_PASS')
    (out_dir/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('SUMMARY',json.dumps(summary),flush=True)
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seed',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--supports',type=int,nargs='+',default=[2,3])
    p.add_argument('--slots',type=int,nargs='*',default=list(range(15)))
    p.add_argument('--basis-exchange',action='store_true')
    p.add_argument('--initial-basis',choices=['global','grouped'],default='global')
    a=p.parse_args();evaluate(a.seed,a.out,a.supports,a.slots,a.basis_exchange,a.initial_basis)
