#!/usr/bin/env python3
"""Exact high-selector group basis synthesis for 7bit/J5 ANGLE tables.

An invertible GF(2) transform is chosen for cofactors sharing one
precomputed high one-hot factor. If G=M F is a new basis of high cofactors,
F=M^{-1} G: the jth new high-selector is the XOR of the (M^-1) column
of old one-hots. The selector still costs one CCX + only free CX gates.

For groups <=8 high states, try all nonempty GF(2) combinations of source
cofactors and run weighted linear-matroid greedy. The additive weight of a
candidate G is its actual emitter cost (one high selector plus number of
nonconstant low output factors). This proves an optimum *only within this
particular fixed-gauge, fixed-output-basis emitter and allowed-mask class*.
There is no claim of global optimal quantum-circuit multiplicative complexity.

HMR replaces fresh ancilla inverse-CCX and its CZ correction, checking
all independently measured relative-phase symbols on every legal address.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
ROOT=Path(__file__).resolve().parents[1]
for local, hosted in [('gvqcc_multiform', 'gvqcc_multiform'),
                      ('gvqcc_multiform_v3', 'multiangle_v3'),
                      ('gvqcc_multiform_v4', 'multiangle_v4')]:
    sys.path.insert(0, str(ROOT / (local if (ROOT / local).exists() else hosted)))
from multi_angle_synthesis import Circuit, TARGETS, delta_table, word_masks, rank_output_basis, emit_fanout
from partition_patterns import high_flags, monomial_cache, mobius, convert_hmr
from global_cofactor import discover_global
from hmr_patterns import prove as proof_hmr

FULL_LOW=64


def inverse_rows(masks:Sequence[int],m:int)->list[int]:
    if len(masks)!=m:raise ValueError('not square')
    a=[int(mask) | (1<<(m+i)) for i,mask in enumerate(masks)]
    for col in range(m):
        pos=next((r for r in range(col,m) if a[r]&(1<<col)),None)
        if pos is None:raise ValueError('singular basis')
        a[col],a[pos]=a[pos],a[col]
        for r in range(m):
            if r!=col and a[r]&(1<<col):a[r]^=a[col]
    assert [x&((1<<m)-1) for x in a]==[1<<i for i in range(m)]
    return [x>>m for x in a]


def xor_coeff(a:Sequence[int],b:Sequence[int])->tuple[int,...]:
    return tuple(x^y for x,y in zip(a,b))


def cf_cost(coeff:Sequence[int])->tuple[int,int,int]:
    outs,forms=rank_output_basis(list(coeff))
    if not outs:return 0,0,0
    # One high selector CCX plus one per nontrivial low form.
    return 1+sum(f!=1 for f in forms), sum(f!=1 for f in forms),len(outs)


@dataclass
class GroupCertificate:
    members:list[int]
    chosen_masks:list[int]
    selector_masks:list[int]
    method:str
    weight_sum:int
    original_weight_sum:int
    exact_gain:int
    candidate_count:int
    support_limit:int
    selected_nonzero:int


def group_candidates(cofactors:list[list[int]], max_support:int):
    m=len(cofactors)
    coeff_per=[tuple(mobius(group,6)) for group in cofactors]
    all_coeff={0:(0,)*64}
    candidates=[]
    for mask in range(1,1<<m):
        bit=(mask&-mask).bit_length()-1
        coeff=xor_coeff(all_coeff[mask^(1<<bit)],coeff_per[bit])
        all_coeff[mask]=coeff
        if mask.bit_count()<=max_support:
            ccx,paid,basis=cf_cost(coeff)
            candidates.append((ccx,paid,basis,mask,coeff))
    return candidates,all_coeff


def select_basis(cofactors:list[list[int]],max_support:int,tiebreak:str='sparse'):
    if tiebreak not in ('sparse','dense','output'):
        raise ValueError(tiebreak)
    m=len(cofactors)
    candidates,_=group_candidates(cofactors,max_support)
    if tiebreak=='sparse':
        candidates.sort(key=lambda x:(x[0],x[3].bit_count(),x[3]))
    elif tiebreak=='dense':
        candidates.sort(key=lambda x:(x[0],-x[3].bit_count(),x[3]))
    else:
        candidates.sort(key=lambda x:(x[0],x[2],x[3].bit_count(),x[3]))
    pivots={};chosen=[]
    for cand in candidates:
        x=cand[3]
        while x:
            p=x.bit_length()-1
            if p in pivots:x^=pivots[p]
            else:
                pivots[p]=x;chosen.append(cand);break
        if len(chosen)==m:break
    assert len(chosen)==m
    masks=[x[3] for x in chosen]
    inverse=inverse_rows(masks,m)
    selectors=[sum(((inverse[i]>>j)&1)<<i for i in range(m)) for j in range(m)]
    baseline=sum(cf_cost(mobius(group,6))[0] for group in cofactors)
    cost=sum(x[0] for x in chosen)
    return chosen,selectors,dict(baseline_cost=baseline,chosen_cost=cost,gain=baseline-cost,
                                 candidates=len(candidates),distinct_masks=len(set(masks)),m=m)


def verify_group(cofactors:list[list[int]],basis:list,selectors:list[int]):
    for i,group in enumerate(cofactors):
        selected=[j for j,mask in enumerate(selectors) if mask>>i&1]
        reconstructed=[0]*64
        for j in selected:
            original=basis[j][4]
            # Invert Möbius to recover G_j(low) on each of 64 low addresses.
            arr=list(original)
            for bit in range(6):
                for idx in range(64):
                    if idx&(1<<bit):arr[idx]^=arr[idx^(1<<bit)]
            reconstructed=[x^y for x,y in zip(reconstructed,arr)]
        if reconstructed!=group:
            raise AssertionError(('high_basis_invalid',i,selected))
    return True


def high_groups(H:int, axis:str):
    if axis=='fixed-upper':
        return [[i for i in range(H) if i>>3==b] for b in range(math.ceil(H/8))]
    if axis=='fixed-lower':
        return [[i for i in range(H) if i&7==a] for a in range(8) if a<H]
    raise ValueError(axis)


def emit_high_selector(c:Circuit,hiA:list[int],hiB:list[int],high:int,tmp:int,
                       members:list[int],selector_mask:int,axis:str):
    chosen=[members[i] for i in range(len(members)) if selector_mask>>i&1]
    if not chosen:raise ValueError('empty selector')
    if axis=='fixed-upper':
        fixed=hiB[chosen[0]>>3]
        variable=[hiA[i&7] for i in chosen]
        assert all(i>>3==chosen[0]>>3 for i in chosen)
    elif axis=='fixed-lower':
        fixed=hiA[chosen[0]&7]
        variable=[hiB[i>>3] for i in chosen]
        assert all(i&7==chosen[0]&7 for i in chosen)
    else:raise ValueError(axis)
    # Simultaneous one-hot XOR stored in tmp, valid for all high inputs.
    for w in variable:c.emit('CX',w,tmp)
    c.emit('CCX',fixed,tmp,high)
    for w in reversed(variable):c.emit('CX',w,tmp)
    return [w for w in variable]


def emit_low_basis(c:Circuit,cache:Sequence[int|None],high:int,active:int,tmp:int,
                   coeff:Sequence[int])->None:
    masks,forms=rank_output_basis(list(coeff))
    for out,form in zip(masks,forms):
        if form==1:
            emit_fanout(c,high,out)
        elif form.bit_count()==1:
            q=cache[form.bit_length()-1]
            if q is None:raise AssertionError('null low feature')
            c.emit('CCX',high,int(q),active)
            emit_fanout(c,active,out)
            c.emit('CCX',high,int(q),active)
        else:
            ops=[]
            for mon in range(64):
                if form>>mon&1:ops.append(('X',(tmp,)) if mon==0 else ('CX',(int(cache[mon]),tmp)))
            for op,qq in ops:c.emit(op,*qq)
            c.emit('CCX',high,tmp,active)
            emit_fanout(c,active,out)
            c.emit('CCX',high,tmp,active)
            c.undo(ops)


def compile_group(words:np.ndarray,slot:int,axis='fixed-upper',max_support=8,
                  global_mode:str|None='canonical',tiebreak='sparse'):
    if global_mode not in (None,'canonical','rref-high','rref-low'):raise ValueError(global_mode)
    rows=word_masks(delta_table(words,slot))
    H=math.ceil(len(rows)/FULL_LOW)
    low,global_stat=discover_global(rows,6,global_mode) if global_mode else ([0]*64,{})
    cofactors=[[int(v)^low[j] for j,v in enumerate(rows[64*i:64*(i+1)])]+[0]*(64-len(rows[64*i:64*(i+1)])) for i in range(H)]
    selected=[];certs=[]
    for members in high_groups(H,axis):
        group=[cofactors[h] for h in members]
        basis,selectors,meta=select_basis(group,max_support,tiebreak)
        verify_group(group,basis,selectors)
        for j,sel in enumerate(selectors):
            selected.append((members,sel,basis[j][4]))
        certs.append(GroupCertificate(members=members,chosen_masks=[b[3] for b in basis],
                      selector_masks=selectors,method=tiebreak,weight_sum=meta['chosen_cost'],
                      original_weight_sum=meta['baseline_cost'],exact_gain=meta['gain'],
                      candidate_count=meta['candidates'],support_limit=max_support,
                      selected_nonzero=sum(b[0]!=0 for b in basis)))
    c=Circuit();hiA,hiB,_=high_flags(c,6);cache=monomial_cache(c,6)
    prefix=len(c.gates)
    high,active,tmp=c.new(3)
    for mon,output in enumerate(mobius(low,6)):
        if not output:continue
        for j,q in enumerate(TARGETS):
            if output>>j&1:
                if mon==0:c.emit('X',q)
                else:c.emit('CX',int(cache[mon]),q)
    emitted=0
    for members,sel,coeff in selected:
        cost,_,_=cf_cost(coeff)
        if not cost:continue
        forward_start=len(c.gates)
        emit_high_selector(c,hiA,hiB,high,tmp,members,sel,axis)
        forwards=list(c.gates[forward_start:])
        emit_low_basis(c,cache,high,active,tmp,coeff)
        c.undo(forwards)
        emitted+=1
    c.undo(tuple(c.gates[:prefix]))
    assert tuple(c.gates[-prefix:])==tuple(reversed(c.gates[:prefix]))
    stat=dict(slot=slot,method=f'group6-{axis}-support{max_support}-{tiebreak}-global{global_mode}',
              qubits=c.alloc,CCX_pre_hmr=c.counts['CCX'],CX_pre_hmr=c.counts['CX'],
              prefix_len=prefix,high_blocks=H,group_count=len(certs),selectors_emitted=emitted,
              low_cost_basis=sum(x.weight_sum for x in certs),
              low_cost_original=sum(x.original_weight_sum for x in certs),
              low_cost_gain=sum(x.exact_gain for x in certs),
              certificates=[asdict(x) for x in certs],
              global_stat=global_stat)
    converted,stat2=convert_hmr(c,stat)
    stat2.update(CX=int(converted.counts['CX']), X=int(converted.counts['X']))
    return converted,stat2


def test_cases():
    rng=np.random.default_rng(21)
    for m in range(1,9):
        for _ in range(6):
            data=rng.integers(0,2**9,size=(m,64),dtype=np.int64).tolist()
            for support in (2,3,8):
                basis,selectors,meta=select_basis(data,support)
                verify_group(data,basis,selectors)
                assert meta['gain']>=0
            if m<=4:
                # Exact enumeration of all invertible bases for 3D (168 ordered bases).
                cand,_=group_candidates(data,m)
                if m==3:
                    cost={x[3]:x[0] for x in cand}
                    best=min(cost[a]+cost[b]+cost[c] for a in cost for b in cost for c in cost
                             if len({a,b,c})==3 and (a^b)!=c)
                    actual=select_basis(data,m)[2]['chosen_cost']
                    assert actual==best,(actual,best)
    return True


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--seed',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--axis',choices=['fixed-upper','fixed-lower'],default='fixed-upper')
    ap.add_argument('--max-support',type=int,default=8)
    ap.add_argument('--global-mode',choices=['none','canonical','rref-high','rref-low'],default='canonical')
    ap.add_argument('--tiebreak',choices=['sparse','dense','output'],default='sparse')
    ap.add_argument('--slots',default='all')
    ap.add_argument('--emit',action='store_true')
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    with np.load(a.seed,allow_pickle=False) as z: words=np.array(z['angle_words'],dtype=np.int64)
    slots=list(range(15)) if a.slots=='all' else [int(x) for x in a.slots.split(',')]
    records=[]
    ledger=a.out/'experiments.jsonl'
    if ledger.exists():raise FileExistsError('Choose new output directory; ledger is immutable')
    for slot in slots:
        c,stat=compile_group(words,slot,a.axis,a.max_support,
                             None if a.global_mode=='none' else a.global_mode,a.tiebreak)
        delta=delta_table(words,slot)
        correctness=proof_hmr(c,delta,dirty_seed=7)
        rec=dict(**stat,**correctness,input_seed=a.seed.name,
                 sha256_seed=hashlib.sha256(a.seed.read_bytes()).hexdigest(),
                 official_kickmix=False,official_score=None)
        if a.emit:
            path=a.out/f'angle_k_{slot}.kmx'
            path.write_text('\n'.join(c.kmx_lines())+'\n')
            rec['kmx_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        with ledger.open('a') as f:f.write(json.dumps(rec,sort_keys=True)+'\n')
        records.append(rec)
        print(json.dumps({k:rec.get(k) for k in ('slot','CCX','CX','HMR','qubits','low_cost_gain','selectors_emitted')},sort_keys=True),flush=True)
    summary=dict(records=len(records),input=a.seed.name,axis=a.axis,
                 max_support=a.max_support,global_mode=a.global_mode,
                 tiebreak=a.tiebreak,CCX=sum(x['CCX'] for x in records),
                 CX=sum(x['CX'] for x in records),Q=max(x['qubits'] for x in records),
                 low_cost_gain=sum(x['low_cost_gain'] for x in records),
                 official_KickMix=False)
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('SUMMARY',json.dumps(summary))

if __name__=='__main__':main()
