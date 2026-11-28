#!/usr/bin/env python3
"""ANGLE global address repartition 3/5/6 low bits with multi-output GF(2) basis.

Unlike a cost proxy, returns concrete reversible X/CX/CCX KMX. The low6
variant fits 127Q by constructing 57 reusable low monomials and combining
its 64-low-row × 35-output table into <=35 independent output masks per
high block. This changes the *algorithmic* basis size (not a local peephole).
HMR versions clean only proven fresh scratch, with conditional CZ restoring
all measurement branches.
"""
from __future__ import annotations
import math
from collections import Counter
import numpy as np,sys
sys.path.insert(0,str(__import__('pathlib').Path(__file__).resolve().parents[1]/'gvqcc_multiform'))
from multi_angle_synthesis import (Circuit, TARGETS, TAGS,onehot,pair_flags,
                                    word_masks,delta_table,emit_fanout,rank_output_basis)
from hmr_patterns import MeasuredCircuit

LOW_BITS=(3,5,6)
METHODS=tuple(f'partition{l}-{type_}' for l in LOW_BITS for type_ in ('anf','basis'))


def monomial_cache(c:Circuit, lowbits:int):
    wire=[None]*(1<<lowbits)
    for i in range(lowbits):wire[1<<i]=i
    for degree in range(2,lowbits+1):
        for m in range(1,1<<lowbits):
            if m.bit_count()!=degree:continue
            pivot=1<<(m.bit_length()-1)
            v=c.new()[0]
            c.emit('CCX',int(wire[m^pivot]),pivot.bit_length()-1,v)
            wire[m]=v
    return wire


def mobius(values:list[int],L:int):
    out=values.copy()
    assert len(out)==1<<L
    for bit in range(L):
        for i in range(1<<L):
            if i&(1<<bit):out[i]^=out[i^(1<<bit)]
    return out


def high_flags(c:Circuit,L:int):
    if L==3:
        a=onehot(c,(3,4,5,6))
        b=onehot(c,(7,8,9,10))
        return a,b,4
    if L==5:
        a=onehot(c,(5,6,7))
        b=onehot(c,(8,9,10))
        return a,b,3
    if L==6:
        a=onehot(c,(6,7,8))
        b=c.new(4)
        pair_flags(c,9,10,b)
        return a,b,3
    raise ValueError(L)


def compile_partition(words,slot:int,method:str):
    if method not in METHODS:raise ValueError(method)
    L=int(method[len('partition')]);type_=method.split('-')[-1]
    delta=delta_table(words,slot)
    rows=word_masks(delta)
    c=Circuit()
    hiA,hiB,cut=high_flags(c,L)
    cache=monomial_cache(c,L)
    prefix=len(c.gates)
    high,active,low_tmp=c.new(3)
    num_low=1<<L
    group_count=math.ceil(len(rows)/num_low)
    terms=0;nontriv=0
    for h in range(group_count):
        group=rows[h*num_low:(h+1)*num_low]
        coeff=mobius(group+[0]*(num_low-len(group)),L)
        if type_=='anf':
            factors=[(mask,1<<m) for m,mask in enumerate(coeff) if mask]
        else:
            outputs,forms=rank_output_basis(coeff)
            factors=[(mask,form) for mask,form in zip(outputs,forms) if mask]
        if not factors:continue
        c.emit('CCX',hiA[h&((1<<cut)-1)],hiB[h>>cut],high)
        for mask,form in factors:
            if form==1:
                emit_fanout(c,high,mask)
            elif form.bit_count()==1:
                v=cache[form.bit_length()-1]
                c.emit('CCX',high,int(v),active)
                emit_fanout(c,active,mask)
                c.emit('CCX',high,int(v),active)
                nontriv+=1
            else:
                ops=[]
                for m in range(num_low):
                    if form>>m&1:
                        ops.append(('X',(low_tmp,)) if m==0 else ('CX',(int(cache[m]),low_tmp)))
                for op,q in ops:c.emit(op,*q)
                c.emit('CCX',high,low_tmp,active)
                emit_fanout(c,active,mask)
                c.emit('CCX',high,low_tmp,active)
                c.undo(ops)
                nontriv+=1
            terms+=1
        c.emit('CCX',hiA[h&((1<<cut)-1)],hiB[h>>cut],high)
    c.undo(tuple(c.gates[:prefix]))
    assert tuple(c.gates[-prefix:])==tuple(reversed(c.gates[:prefix]))
    return c,dict(method=method,slot=slot,qubits=c.alloc,CCX=int(c.counts['CCX']),
       CX=int(c.counts['CX']),X=int(c.counts['X']), low_bits=L,
       n_high_blocks=group_count, active_high_blocks=sum(1 for _ in [h for h in range(group_count)]),
       output_basis_terms=terms,nontrivial_high_low_products=nontriv,
       prefix_len=prefix)


def convert_hmr(original,stat,grade='all-clean'):
    if grade not in ('active','all-clean'):raise ValueError(grade)
    gates=original.gates;prefix=stat['prefix_len'];high=original.alloc-3;active=original.alloc-2
    assert list(gates[:prefix])==list(reversed(gates[-prefix:]))
    marked={}
    for i,(op,q) in enumerate(gates):
        if op!='CCX' or q[-1]!=active:continue
        j=i+1
        while j<len(gates) and gates[j][0]=='CX' and gates[j][1][0]==active and gates[j][1][1] in TARGETS:j+=1
        if j>i+1 and j<len(gates) and gates[j]==(op,q):marked[j]=q
    nactive=len(marked)
    if grade=='all-clean':
        indices=[i for i,(op,q) in enumerate(gates) if op=='CCX' and q[-1]==high]
        assert len(indices)%2==0
        for i,j in zip(indices[::2],indices[1::2]):
            assert gates[i]==gates[j]
            marked[j]=gates[j][1]
        for i in range(len(gates)-prefix,len(gates)):
            op,q=gates[i]
            if op=='CCX':
                assert i not in marked and q[-1]>=51
                marked[i]=q
    ops=[]
    for i,(op,q) in enumerate(gates):
        if i in marked:
            assert op=='CCX'
            a,b,t=q
            ops.append(('HMR',(t,),0));ops.append(('CZ',(a,b),0))
        else:ops.append((op,q,None))
    c=MeasuredCircuit(original.alloc,ops)
    new=dict(stat, method=stat['method']+'--hmr-'+grade,
             CCX=int(c.counts['CCX']),HMR=int(c.counts['HMR']),
             conditional_CZ=int(c.counts['CZ']),HMR_active=nactive,
             HMR_high_and_precomp=int(c.counts['HMR'])-nactive)
    return c,new
