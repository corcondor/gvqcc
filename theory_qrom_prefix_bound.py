#!/usr/bin/env python3
"""Exact linear-span lower bound for the current ANGLE feature interface.

This certifies only reconstruction of the SAME 90-wire feature span from
address bits and the five conserved tags, without borrowing the other 35
output-data wires. It does not lower-bound a different whole-loader design.
Each CCX creates at most one new Boolean function modulo the previous span;
X/CX cannot enlarge that span. All truth tables are exact on 1220 addresses.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import time
import kickmix as km
from chemistry_joint_product_resynthesis import extract, TAGS
from chemistry_affine_span_resynthesis import parse_line


def rank(rows):
    basis={}
    for value in rows:
        while value:
            pivot=value.bit_length()-1
            if pivot in basis:value^=basis[pivot]
            else:
                basis[pivot]=value
                break
    return len(basis)


def analyze(path):
    circuit=km.Circuit.from_file(path);ex=extract(circuit)
    pool=set(ex['pool']);one=(1<<1220)-1;state=[0]*circuit.num_qubits
    for q in range(11):state[q]=sum(((a>>q)&1)<<a for a in range(1220))
    for q,(i,j) in zip(sorted(TAGS),[(0,1),(0,2),(1,2),(0,3),(1,3)]):
        state[q]=state[i]&state[j]
    # The first five CX expose the canonical conserved tags. Start directly
    # after them, with all other data wires irrelevant to the feature stage.
    first_reset=next(i for i,l in enumerate(ex['lines']) if parse_line(l)[0]=='R')
    initial=rank([one]+[state[q] for q in pool]);current=initial
    steps=[]
    for i in range(first_reset,ex['first']):
        gate,qs,condition=parse_line(ex['lines'][i])
        if condition is not None:raise AssertionError('Conditioned prefix gate')
        if gate=='CX':
            a,b=qs
            if b in pool and a not in pool:raise AssertionError('Borrowed data input')
            state[b]^=state[a]
        elif gate=='CCX':
            a,b,t=qs
            if not {a,b,t}.issubset(pool):raise AssertionError('Not a feature-only product')
            state[t]^=state[a]&state[b]
            after=rank([one]+[state[q] for q in pool])
            steps.append({'line_index':i,'rank_before':current,'rank_after':after})
            current=after
        elif gate=='X':state[qs[0]]^=one
        elif gate=='R':
            if state[qs[0]]:raise AssertionError('Resetting nonzero feature')
        else:raise AssertionError(gate)
    end=rank([one]+[state[q] for q in pool])
    assert end-initial==len(steps)==74
    assert all(r['rank_after']==r['rank_before']+1 for r in steps)
    return {'source':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'valid_addresses':1220,'initial_span_dimension':initial,'required_span_dimension':end,
            'ccx_lower_bound':end-initial,'actual_feature_ccx':len(steps),
            'all_74_products_increase_span_dimension':True,'rank_trace':steps}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--loaders',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    args=p.parse_args();t=time.monotonic()
    if args.report.exists():raise FileExistsError(args.report)
    rows=[analyze(args.loaders/f'angle_k_{k}.kmb') for k in range(1,15)]
    result={'status':'EXACT_SCOPED_LOWER_BOUND','loaders':rows,
            'scope':'Same 90-wire feature span, address bits and 5 conserved tags as initial resources; no borrowing the 35 output-data wires; X/CX/CCX feature computation.',
            'proof':'X/CX preserve the span of available Boolean functions and 1. A CCX adds at most one new product to this span. Exact truth-table rank grows from 17 to 91, so at least 74 CCX are required. Existing prefixes use 74.',
            'not_claimed':'Whole ANGLE optimality, optimality with changed feature interface, borrowing angle data, different table encoding, or cross-boundary fusion.',
            'seconds':time.monotonic()-t,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    args.report.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='loaders'},indent=2))


if __name__=='__main__':main()
