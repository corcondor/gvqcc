#!/usr/bin/env python3
"""New exact J5/7bit ANGLE constructions using per-high-block Boolean coordinates.

Unlike a cosmetic gate deletion, each 16-row low-address function is
re-expanded over alternative affine input coordinates (shifts and shears),
then a basis/ANF representation is chosen by its actual high-controlled
AND count. The low coordinate change is compiled back into a polynomial
of the original low address wires, with all temporary CNOT/X undone.

The four modes implement genuinely different search spaces:
  block-hybrid: existing ANF vs independent output-mask GF(2) basis per block;
  low-shift: 16 low-coordinate translations, polynomial re-expression;
  low-shear: 12 elementary GL(4,2) shears + identity, no translations;
  affine-mix: translations + shears and per-block basis option.

Optionally HMR-cleans (a) output ANDs, (b) high flag, and (c) all prepared
low/high one-hot or monomial flags with exact conditional CZ corrections.
"""
from __future__ import annotations
import hashlib,json,sys
from collections import Counter
from functools import lru_cache
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'gvqcc_multiform'))
from multi_angle_synthesis import (Circuit,TARGETS,onehot,monomial_cache,word_masks,
                                    mobius_low_anf,rank_output_basis,delta_table,emit_fanout)
from hmr_patterns import MeasuredCircuit

METHODS=('block-hybrid','low-shift','low-shear','affine-mix')


def gf2_poly_mul(a:int,b:int)->int:
    out=0
    while a:
        bit=a&-a;aa=bit.bit_length()-1;a^=bit
        bb=b
        while bb:
            bit2=bb&-bb;ii=bit2.bit_length()-1;bb^=bit2
            out ^= 1 << (aa|ii)
    return out


def transform_maps(shear:tuple[int,int]|None, shift:int):
    """y_i=x_i xor x_j (for one shear), then y_i xor shift_i."""
    # The elementary shear is self-inverse: x=T^-1(y xor shift).
    map_y_to_x=[]
    for y in range(16):
        x=y^shift
        if shear is not None:
            i,j=shear
            if (x>>j)&1:x ^= 1<<i
        map_y_to_x.append(x)
    # Variable y_i as Boolean polynomial in original x_i, x_j.
    yi=[]
    for i in range(4):
        p=1 << (1<<i)
        if shear is not None and i==shear[0]:p ^= 1<<(1<<shear[1])
        if shift>>i&1:p ^= 1
        yi.append(p)
    forms=[]
    for mask in range(16):
        p=1 # constant function
        for i in range(4):
            if mask>>i&1:p=gf2_poly_mul(p,yi[i])
        forms.append(p)
    assert len(set(map_y_to_x))==16
    # Confirm each mapped monomial equals product(y_i) on x in 0..15.
    for m in range(16):
        for x in range(16):
            y=x
            if shear is not None:
                i,j=shear
                if y>>j&1:y^=1<<i
            y ^= shift
            expected=int((y&m)==m)
            actual=(sum((forms[m]>>z&1)*int((x&z)==z) for z in range(16)))&1
            if actual!=expected:raise AssertionError(('incorrect inverse transform',m,x))
    return map_y_to_x,forms


@lru_cache(maxsize=32)
def transform_catalog(method:str):
    shears=[None]+[(i,j) for i in range(4) for j in range(4) if i!=j]
    if method=='block-hybrid':pairs=[(None,0)]
    elif method=='low-shift':pairs=[(None,s) for s in range(16)]
    elif method=='low-shear':pairs=[(sh,0) for sh in shears]
    elif method=='affine-mix':pairs=[(sh,s) for sh in shears for s in range(16)]
    else:raise ValueError(method)
    return [(sh,s,*transform_maps(sh,s)) for sh,s in pairs]


def factor_cost(factors:list[tuple[int,int]]):
    paid=sum(poly!=1 for mask,poly in factors if mask)
    # CNOT work to form low nonlinear polynomial and fanout targets.
    extra=sum(mask.bit_count()+2*((poly.bit_count()) if poly and poly & (poly-1) else 0)
              for mask,poly in factors if mask)
    return paid,extra,len(factors)


def chosen_factorization(rows:list[int],method:str,catalog):
    candidates=[]
    original=mobius_low_anf(rows)
    if method in ('block-hybrid','affine-mix'):
        basis,forms=rank_output_basis(original)
        candidate=[(mask,poly) for mask,poly in zip(basis,forms) if mask]
        candidates.append((factor_cost(candidate),'basis',candidate))
    for shear,shift,inv,forms in catalog:
        output=mobius_low_anf([rows[x] for x in inv])
        candidate=[(mask,forms[m]) for m,mask in enumerate(output) if mask]
        candidates.append((factor_cost(candidate),f'shear={shear};shift={shift}',candidate))
    candidates.sort(key=lambda x:(x[0],x[1]))
    return candidates[0][1],candidates[0][2],candidates[0][0]


def synthesize_affine(words:np.ndarray,slot:int,method:str):
    if method not in METHODS:raise ValueError(method)
    delta=delta_table(words,slot)
    rows=word_masks(delta)
    catalog=transform_catalog(method)
    c=Circuit()
    hi3=onehot(c,(4,5,6))
    hi4=onehot(c,(7,8,9,10))
    low=monomial_cache(c)
    prefix=len(c.gates)
    if prefix!=79:raise AssertionError(('unexpected precompute',prefix))
    high,active,low_tmp=c.new(3)
    terms=0
    winner=Counter()
    active_high_blocks=0
    for h in range((len(rows)+15)//16):
        group=rows[16*h:16*h+16]
        padded=group+[0]*(16-len(group))
        name,factors,_=chosen_factorization(padded,method,catalog)
        winner[name]+=1
        if not factors:continue
        active_high_blocks+=1
        c.emit('CCX',hi3[h&7],hi4[h>>3],high)
        for mask,form in factors:
            if form==1:
                emit_fanout(c,high,mask)
            elif form.bit_count()==1 and form!=1:
                mono=form.bit_length()-1
                c.emit('CCX',high,int(low[mono]),active)
                emit_fanout(c,active,mask)
                c.emit('CCX',high,int(low[mono]),active)
            else:
                ops=[]
                for mono in range(16):
                    if form>>mono&1:
                        ops.append(('X',(low_tmp,)) if mono==0 else ('CX',(int(low[mono]),low_tmp)))
                for op,qs in ops:c.emit(op,*qs)
                c.emit('CCX',high,low_tmp,active)
                emit_fanout(c,active,mask)
                c.emit('CCX',high,low_tmp,active)
                c.undo(ops)
            terms+=1
        c.emit('CCX',hi3[h&7],hi4[h>>3],high)
    c.undo(tuple(c.gates[:prefix]))
    assert tuple(c.gates[-prefix:])==tuple(reversed(c.gates[:prefix]))
    return c,dict(method=method,slot=slot,qubits=c.alloc,CCX=c.counts['CCX'],
                  CX=c.counts['CX'],X=c.counts['X'],output_terms=terms,
                  active_high_blocks=active_high_blocks,chosen_bases=dict(winner),
                  candidates_considered=len(catalog))


def hmr_from_reversible(original:Circuit,stat:dict,grade:str):
    """Certified structure-based conversion for 79-gate common precompute."""
    if grade not in ('active','active-high','all-clean'):raise ValueError(grade)
    prefix=79
    high,active=original.alloc-3,original.alloc-2
    gates=original.gates
    assert list(gates[:prefix])==list(reversed(gates[-prefix:]))
    marked={}
    for i,(op,q) in enumerate(gates):
        if op!='CCX' or q[2]!=active:continue
        j=i+1
        while j<len(gates) and gates[j][0]=='CX' and gates[j][1][0]==active and gates[j][1][1] in TARGETS:
            j+=1
        if j>i+1 and j<len(gates) and gates[j]==(op,q):marked[j]=q
    active_count=len(marked)
    if grade in ('active-high','all-clean'):
        positions=[i for i,(op,q) in enumerate(gates) if op=='CCX' and q[2]==high]
        assert len(positions)%2==0
        for i,j in zip(positions[::2],positions[1::2]):
            assert gates[i]==gates[j]
            marked[j]=gates[j][1]
    high_count=len(marked)-active_count
    if grade=='all-clean':
        for i in range(len(gates)-prefix,len(gates)):
            op,q=gates[i]
            if op=='CCX':
                assert i not in marked and q[2]>=51
                marked[i]=q
    pre_count=len(marked)-active_count-high_count
    ops=[]
    for i,(op,q) in enumerate(gates):
        if i in marked:
            assert op=='CCX'
            a,b,t=q
            ops.extend([('HMR',(t,),0),('CZ',(a,b),0)])
        else:ops.append((op,q,None))
    c=MeasuredCircuit(original.alloc,ops)
    stat={**stat,'method':stat['method']+'--hmr-'+grade,
          'CCX':int(c.counts['CCX']),'HMR':int(c.counts['HMR']),
          'conditional_CZ':int(c.counts['CZ']),
          'HMR_active':active_count,'HMR_high':high_count,'HMR_precomp':pre_count}
    assert stat['HMR']==stat['conditional_CZ']
    return c,stat
