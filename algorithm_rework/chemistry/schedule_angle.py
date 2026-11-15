#!/usr/bin/env python3
"""Reuse changing control parities and output fanout in ANGLE product blocks."""
from __future__ import annotations

import argparse
from collections import Counter, deque
import hashlib
import itertools
import json
import os
from pathlib import Path
import sys

import kickmix as km
import numpy as np

def bit_positions(mask):
    while mask:
        low = mask & -mask
        yield low.bit_length() - 1
        mask ^= low

def linear_gate(gate, wires, frame):
    if gate == 'CX':
        control, target = wires
        frame[target] ^= frame[control]
    else:
        assert gate == 'X'
        frame[wires[0]] ^= 1

def cnot(control, target):
    return f'CX q{control} q{target}'

def transform_sequences():
    """Exact shortest paths on ordered two-bit bases over GF(2)."""
    paths = {(1, 2): ()}
    todo = deque([(1, 2)])
    while todo:
        a, b = todo.popleft()
        for c, d, trans in [(a ^ b, b, (1, 0)), (a, b ^ a, (0, 1))]:
            if (c, d) not in paths:
                paths[c, d] = paths[a, b] + (trans,)
                todo.append((c, d))
    return paths

SEQUENCES = transform_sequences()

def affine_path(frame, data):
    """Synthesize a linear subspace action and return elimination gates."""
    mask = sum(1 << (q + 1) for q in data)
    rows = {q: frame[q] & mask for q in data}
    reduce = []
    for i, q in enumerate(data):
        bit = 1 << (q + 1)
        pivot = next(j for j in data[i:] if rows[j] & bit)
        if pivot != q:
            rows[pivot], rows[q] = rows[q], rows[pivot]
            reduce.extend(((pivot,q),(q,pivot),(pivot,q)))
        for other in data:
            if other != q and rows[other] & bit:
                rows[other] ^= rows[q]
                reduce.append((q, other))
    output = [cnot(u, v) for u, v in reversed(reduce)]
    for q in data:
        rest = frame[q] & ~mask
        if rest & 1:
            output.append(f'X q{q}')
        output.extend(cnot(i - 1, q) for i in bit_positions(rest & ~1))
    return output, reduce

def preimage_directions(terms, data, inverse_gates):
    indices={q:i for i,q in enumerate(data)}
    gates=[(1<<indices[s],1<<indices[t]) for s,t in inverse_gates]
    result=[]
    for a,b,w in terms:
        for src,dst in gates:
            if w & src: w^=dst
        assert w
        result.append((a,b,w))
    return result

def selector_pair(form_a, form_b, p, q):
    left = ((form_a >> (p+1)) & 1) | (((form_a >> (q+1)) & 1)<<1)
    right = ((form_b >> (p+1)) & 1) | (((form_b >> (q+1)) & 1)<<1)
    return left, right

def parity_transition(prev, new, pivots):
    """Plan a two-row basis change with all other rows immutable."""
    a,b = prev
    ca, cb = selector_pair(a,b,*pivots)
    from_key = {ca: (a,1), cb: (b,2), ca^cb: (a^b,3)}
    d,e = selector_pair(*new,*pivots)
    no1,k1 = from_key[d]
    no2,k2 = from_key[e]
    return SEQUENCES[k1,k2], new[0]^no1, new[1]^no2

def distance(plan):
    ops,a,b = plan
    return len(ops)+a.bit_count()+b.bit_count()

def emit_transition(plan,pivots):
    ops,a,b=plan
    result = [cnot(pivots[s],pivots[t]) for s,t in ops]
    for row, form in zip(pivots,(a,b)):
        if form & 1: result.append(f'X q{row}')
        result.extend(cnot(x-1,row) for x in bit_positions(form&~1))
    return result

def choose_groups(terms, pool):
    """Set cover by invertible projections on two physical control wires."""
    masks = {}
    for q in pool:
        a = sum(((left >> (q+1)) & 1) << i for i,(left,_,_) in enumerate(terms))
        b = sum(((right >> (q+1)) & 1) << i for i,(_,right,_) in enumerate(terms))
        if a or b:
            masks[q] = (a,b)
    pairs = []
    for p,q in itertools.combinations(masks,2):
        a,b = masks[p]
        c,d = masks[q]
        support = (a & d) ^ (b & c)
        if support:
            pairs.append((support,(p,q)))
    remaining = (1 << len(terms))-1
    while remaining:
        support,pivots = max(pairs,key=lambda x:(x[0] & remaining).bit_count())
        take = support & remaining
        assert take
        yield pivots,[terms[i] for i in bit_positions(take)]
        remaining ^= take

def schedule_products(terms, pool, data):
    lines=[]
    for pivots,group in choose_groups(terms,pool):
        orig=tuple(1<<(q+1) for q in pivots)
        control=orig
        while group:
            t=max(range(len(data)),key=lambda i:sum((w>>i)&1 for _,_,w in group))
            mask=1<<t
            yes=[term for term in group if term[2]&mask]
            group=[term for term in group if not term[2]&mask]
            last=mask
            while yes:
                best_key=None
                for i,(a,b,w) in enumerate(yes):
                    for new in ((a,b),(b,a)):
                        plan=parity_transition(control,new,pivots)
                        cost=(last^w).bit_count()+distance(plan)
                        if best_key is None or cost<best_key:
                            best_key=cost
                            best=(i,new,w,plan)
                i,new,w,plan=best
                yes.pop(i)
                lines.extend(emit_transition(plan,pivots))
                lines.extend(cnot(data[t],data[j]) for j in bit_positions(last^w))
                lines.append(f'CCX q{pivots[0]} q{pivots[1]} q{data[t]}')
                control,last=new,w
            lines.extend(cnot(data[t],data[j]) for j in bit_positions(last^mask))
        lines.extend(emit_transition(parity_transition(control,orig,pivots),pivots))
    return lines

def get_frame(parsed, data, n):
    """Exact affine-plus-control-product on all arbitrary input bits."""
    entry = [1 << (q+1) for q in range(n)]
    frame = entry[:]
    data_index = {q:i for i,q in enumerate(data)}
    pool = set(range(n))-set(data)
    directions={q:1<<i for i,q in enumerate(data)}
    output_masks={}
    for i,(g,w,_c) in reversed(list(enumerate(parsed))):
        if g=='CX' and w[0] in data_index and w[1] in data_index:
            directions[w[0]] ^= directions[w[1]]
        elif g=='CCX':
            output_masks[i]=directions[w[2]]
    terms=[]
    for i,(g,w,c) in enumerate(parsed):
        assert c is None
        if g=='CCX':
            assert w[0] in pool and w[1] in pool
            a,b=sorted([frame[w[0]],frame[w[1]]])
            terms.append((a,b,output_masks[i]))
        else:
            linear_gate(g,w,frame)
    return frame,terms

def rewrite(circuit, parse_line, data):
    n=int(circuit.num_qubits)
    lines=str(circuit).splitlines()
    parsed=list(map(parse_line,lines))
    pool=sorted(set(range(n))-set(data))
    s=0
    new=[]
    artifacts=[]
    for i,(g,w,c) in enumerate(parsed+[('END',(),None)]):
        if c is None and (
            g=='X' or (g=='CX' and not(w[0] in data and w[1] in pool))
            or (g=='CCX' and w[2] in data and w[0] in pool and w[1] in pool)
        ):
            continue
        block=parsed[s:i]
        if any(g=='CCX' for g,_,_ in block):
            frame,terms=get_frame(block,data,n)
            affine,inverse=affine_path(frame,data)
            restore,_=affine_path(frame,pool)
            candidates=[
                schedule_products(preimage_directions(terms,data,inverse),pool,data)+affine+restore
            ]
            if not restore:
                candidates.append(affine+schedule_products(terms,pool,data))
            candidate=min(candidates,key=len)
            fresh_frame,fresh_terms=get_frame(list(map(parse_line,candidate)),data,n)
            assert frame==fresh_frame and Counter(terms)==Counter(fresh_terms)
            artifacts.append({'original_lines':i-s,'compiled_lines':len(candidate),'CCX':len(terms),'start':s,'end':i})
            new.extend(candidate if len(candidate)<i-s else lines[s:i])
        else:
            new.extend(lines[s:i])
        if i<len(lines):
            new.append(lines[i])
        s=i+1
    return km.Circuit('\n'.join(new)+'\n'),artifacts

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',required=True,type=Path)
    parser.add_argument('--source',required=True,type=Path)
    parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args()
    sys.path.insert(0,str(args.repo))
    from chemistry_affine_span_resynthesis import parse_line
    from chemistry_joint_product_resynthesis import DATA
    args.out.mkdir(parents=True,exist_ok=False)
    receipt=[]
    for k in range(15):
        f=args.source/f'angle_k_{k}.kmb'
        circuit=km.Circuit.from_file(f)
        out,records=rewrite(circuit,parse_line,DATA)
        assert out.num_qubits==circuit.num_qubits
        assert out.operation_statistics().num_toffoli_like==circuit.operation_statistics().num_toffoli_like
        dest=args.out/f.name
        out.to_file(dest,format='kmb')
        row={'batch':k,'num_qubits':int(out.num_qubits),
             'original_ops':len(circuit),'ops':len(out),'toffoli':int(out.operation_statistics().num_toffoli_like),
             'blocks':records,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}
        print(json.dumps(row),flush=True)
        receipt.append(row)
    (args.out/'submission.npz').write_bytes((args.source/'submission.npz').read_bytes())
    out={'batches':receipt,
         'original_ops':sum(x['original_ops'] for x in receipt),
         'candidate_ops':sum(x['ops'] for x in receipt),
         'toffoli_per_pass':sum(x['toffoli'] for x in receipt),
         'proof':'gatewise identity outside rewritten blocks; each replaced block has identical affine map and vector-valued product list on arbitrary entry bits.'}
    (args.out/'operation_receipt.json').write_text(json.dumps(out,indent=2)+'\n')
    print({k:v for k,v in out.items() if k!='batches'},flush=True)

if __name__=='__main__':
    main()
