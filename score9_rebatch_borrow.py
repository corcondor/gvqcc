#!/usr/bin/env python3
"""Exact screen for low-address products borrowing the incoming angle data.

The same circuit must work on the forward and reverse reachable states.
We therefore retain both truth tables, rather than treating the incoming
words as address functions that are the same in the two directions.

This checks the entire span of L(low4)*incoming_bit, including arbitrary
linear combinations, modulo all pure-low and pure-high address functions.
It does not exclude higher-degree, high-address-controlled or staged uses
of the word data. It is a synthesis diagnostic, not a global lower bound.
"""
from __future__ import annotations
import argparse, hashlib, json, time
from pathlib import Path
import numpy as np


def packed(v):
    return int.from_bytes(np.packbits(np.asarray(v, dtype=np.uint8), bitorder='little').tobytes(), 'little')


def add(basis, value, expr=0):
    while value:
        p=value.bit_length()-1
        if p not in basis:
            basis[p]=(value,expr)
            return True,value,expr
        row,rep=basis[p]
        value^=row;expr^=rep
    return False,0,expr


def reduce(basis,value,expr=0):
    while value:
        p=value.bit_length()-1
        if p not in basis:return value,expr
        row,rep=basis[p];value^=row;expr^=rep
    return 0,expr


def selected(values,mask):
    v=0
    while mask:
        bit=mask&-mask;v^=values[bit.bit_length()-1];mask^=bit
    return v


def analyze(previous,current):
    n,J=previous.shape;addr=np.arange(n,dtype=np.uint64);one=(1<<n)-1
    # Complete free low and high truth-function spaces. Their implementation
    # cost and workspace are intentionally not assumed to be zero globally.
    low=[packed(((addr&15)&m)==m) for m in range(16)]
    high=[packed((addr>>4)==h) for h in range((n+15)//16)]
    free_basis={}
    for f in low+high:add(free_basis,f)
    before=[packed((previous[:,j]>>b)&1) for j in range(J) for b in range(8)]
    after=[packed((current[:,j]>>b)&1) for j in range(J) for b in range(8)]
    deltas=[a^b for a,b in zip(before,after)]
    controls=[(j,m) for j in range(8*J) for m in range(16)]
    p0=[before[j]&low[m] for j,m in controls]
    p1=[after[j]&low[m] for j,m in controls]
    relation_basis={};relations=[]
    for i,(a,b) in enumerate(zip(p0,p1)):
        independent,_,expr=add(relation_basis,a^b,1<<i)
        if not independent:relations.append(expr)
    # A relation in the branch-difference kernel yields a common function
    # on both inputs. Check each resulting identity independently in the
    # original pair of truth tables, before quotient-space elimination.
    common=[];new_basis=dict(free_basis);new_functions=[]
    for expression in relations:
        a=selected(p0,expression);b=selected(p1,expression)
        assert a==b
        common.append(a)
        independent,residual,_=add(new_basis,a)
        if independent:new_functions.append(residual)
    def quotient_rank(basis,values):
        b=dict(basis);initial=len(b)
        for v in values:add(b,v)
        return len(b)-initial
    before_rank=quotient_rank(free_basis,deltas)
    after_rank=quotient_rank(new_basis,deltas)
    witnesses=[]
    # A zero residual here is an exact representability result only. It
    # does not yet ensure a legal reversible output mutation/schedule.
    for bit,delta in enumerate(deltas):
        old,_=reduce(free_basis,delta);new,_=reduce(new_basis,delta)
        if old and not new:witnesses.append(bit)
    return dict(addresses=n,word_bits=8*J,low_forms_basis=16,
        data_product_generators=len(controls),free_address_function_rank=len(free_basis),
        forward_reverse_difference_rank=len(relation_basis),
        symmetric_product_kernel_dimension=len(relations),
        symmetric_functions_before_quotient_rank=len(new_basis),
        new_common_function_rank=len(new_basis)-len(free_basis),
        target_delta_rank_mod_address_functions=before_rank,
        target_delta_rank_after_borrowing=after_rank,
        target_span_dimension_gained=before_rank-after_rank,
        individual_newly_representable_output_bits=witnesses,
        all_kernel_identities_exact_on_both_directions=True,
        kernel_sha256=hashlib.sha256(('\n'.join(hex(x) for x in relations)).encode()).hexdigest(),
        new_function_sha256=hashlib.sha256(('\n'.join(hex(x) for x in new_functions)).encode()).hexdigest())


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--words',type=Path,required=True)
    p.add_argument('--batch-size',type=int,default=4)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():raise FileExistsError(a.out)
    started=time.monotonic();words=np.load(a.words,allow_pickle=False).astype(np.uint64)
    assert words.shape==(1220,75) and words.max()<256
    J=a.batch_size;K=(words.shape[1]+J-1)//J
    padded=np.pad(words,((0,0),(0,K*J-words.shape[1])))
    rows=[]
    for k in range(K):
        previous=padded[:,(k-1)*J:k*J] if k else np.zeros((len(words),J),np.uint64)
        current=padded[:,k*J:(k+1)*J]
        row=dict(k=k,**analyze(previous,current));rows.append(row)
        print(json.dumps({key:row[key] for key in ('k','new_common_function_rank','target_span_dimension_gained','individual_newly_representable_output_bits')}),flush=True)
    result=dict(status='EXACT_BOTH_DIRECTIONS_LOW_TIMES_DATA_SPAN_SCREEN',
        source=str(a.words),source_sha256=hashlib.sha256(a.words.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),J=J,rows=rows,
        scope='all products of arbitrary low4 functions and arbitrary linear combinations of incoming word bits; arbitrary XOR combinations; both reachable directions; modulo pure-low/pure-high functions',
        limitation='Does not cover products of two data-dependent forms, high-address coefficients, staged output changes, different feature spaces, or alternative angle words. Extra span is not a compiled gate saving.',
        circuits_written=False,official_verifier_run=False,seconds=time.monotonic()-started)
    a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}),flush=True)


if __name__=='__main__':main()
