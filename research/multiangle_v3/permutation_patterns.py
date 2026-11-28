#!/usr/bin/env python3
"""Noncontiguous 6-bit low-address partition for exact 7-bit J5 loader synthesis.

Permutation of which physical selection wires belong to low and high groups
changes 64-row GF(2) output basis factorization. No state semantics change.
The 6-low-bit cache is 57 fresh ANDs; group of five high bits split 3+2.
All changes are reversible and produce correct XOR for every legal address.
"""
from __future__ import annotations
import itertools,math
from collections import Counter
import numpy as np,sys
sys.path.insert(0,str(__import__('pathlib').Path(__file__).resolve().parents[1]/'gvqcc_multiform'))
from multi_angle_synthesis import Circuit,TARGETS,pair_flags,onehot,rank_output_basis,emit_fanout,word_masks,delta_table
from partition_patterns import convert_hmr,mobius


def select_bits(low_bits):
    low=tuple(sorted(int(x) for x in low_bits))
    if len(low)!=6 or len(set(low))!=6 or low[0]<0 or low[-1]>10:raise ValueError('need 6 distinct address wires q0..q10')
    high=tuple(i for i in range(11) if i not in low)
    return low,high


def low_mon_cache(c,low):
    cache=[None]*64
    for i in range(6):cache[1<<i]=low[i]
    for degree in range(2,7):
        for m in range(1,64):
            if m.bit_count()!=degree:continue
            highest=1<<(m.bit_length()-1)
            v=c.new()[0];c.emit('CCX',int(cache[m^highest]),low[highest.bit_length()-1],v)
            cache[m]=v
    return cache


def high_flags(c,high):
    a=onehot(c,high[:3]);b=c.new(4)
    pair_flags(c,*high[3:],b)
    return a,b


def table_for_lowset(words,slot,low_bits):
    low,high=select_bits(low_bits)
    masks=word_masks(delta_table(words,slot))
    result=[]
    for h in range(32):
        row=[]
        hb=sum(((h>>i)&1)<<high[i] for i in range(5))
        for l in range(64):
            addr=hb+sum(((l>>i)&1)<<low[i] for i in range(6))
            row.append(masks[addr] if addr < len(masks) else 0)
        result.append(row)
    return result


def estimate(words,slot,low_bits):
    groups=table_for_lowset(words,slot,low_bits)
    nactive=0; paid=0;highonly=0;out_terms=0
    for group in groups:
        coeff=mobius(group,6)
        masks,forms=rank_output_basis(coeff)
        factors=[(m,f) for m,f in zip(masks,forms) if m]
        if factors:nactive+=1
        out_terms+=len(factors)
        paid+=sum(f!=1 for m,f in factors)
        highonly+=sum(f==1 for m,f in factors)
    # Exactly counts the emitted ANDs: high flag per active block,
    # AND for every nonconstant low form, low cache and high flag prep.
    # Low cache=57; high3 onehot 12 CCX; high2 pair flags=4CCX.
    lowcache=57
    highcache=12
    # onehot 3 includes 4 pair-flags + 8 final ANDs = 12, plus high2 4.
    prep=lowcache+highcache+4
    static_hmr_ccx=prep+ nactive+paid
    assert static_hmr_ccx>=0
    return dict(total_ccx_after_hmr=static_hmr_ccx,nonconstant_products=paid,
                high_blocks=nactive,outputs=out_terms,high_only=highonly,prep=prep)


def compile_perm(words,slot,low_bits):
    low,high=select_bits(low_bits)
    c=Circuit();hiA,hiB=high_flags(c,high)
    cache=low_mon_cache(c,low)
    prefix=len(c.gates)
    hflag,active,tmp=c.new(3)
    assert c.alloc==127
    paid=0;terms=0
    for h,group in enumerate(table_for_lowset(words,slot,low)):
        masks,forms=rank_output_basis(mobius(group,6))
        factors=[(m,f) for m,f in zip(masks,forms) if m]
        if not factors:continue
        c.emit('CCX',hiA[h&7],hiB[h>>3],hflag)
        for mask,form in factors:
            if form==1:
                emit_fanout(c,hflag,mask)
            elif form.bit_count()==1:
                v=cache[form.bit_length()-1]
                c.emit('CCX',hflag,int(v),active)
                emit_fanout(c,active,mask)
                c.emit('CCX',hflag,int(v),active)
                paid+=1
            else:
                ops=[]
                for m in range(64):
                    if form>>m&1:
                        ops.append(('X',(tmp,)) if m==0 else ('CX',(int(cache[m]),tmp)))
                for op,q in ops:c.emit(op,*q)
                c.emit('CCX',hflag,tmp,active)
                emit_fanout(c,active,mask)
                c.emit('CCX',hflag,tmp,active)
                c.undo(ops)
                paid+=1
            terms+=1
        c.emit('CCX',hiA[h&7],hiB[h>>3],hflag)
    c.undo(tuple(c.gates[:prefix]))
    stat=dict(method='perm6-'+''.join(map(str,low)),slot=slot,low_selection=list(low),high_selection=list(high),
              prefix_len=prefix,qubits=c.alloc,CCX=int(c.counts['CCX']),CX=int(c.counts['CX']),
              X=int(c.counts['X']),output_terms=terms,paid_inner_products=paid)
    theoretical=estimate(words,slot,low)
    assert theoretical['total_ccx_after_hmr']*2 ==stat['CCX'],(theoretical,stat)
    return c,stat
