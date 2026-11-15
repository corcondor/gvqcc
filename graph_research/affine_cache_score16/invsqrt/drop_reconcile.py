#!/usr/bin/env python3
"""Drop one paid operation from a coherent window and rebuild via output affine span."""
from measure_linear import MAX_X, SOURCE_SHA, columns, affine_basis, solve, advance
from pathlib import Path
import argparse, hashlib, json, re, random, time
import numpy as np

COHERENT = {'X','CX','CCX','SWAP','CSWAP'}
NONLINEAR = {'CCX','CSWAP'}

def analyse(lines, values, d, only=None):
    qs_pat=re.compile(r'\bq(\d+)\b')
    branch=[]
    active=[]
    hits=[]
    count=0
    snapshots={}
    for i,line in enumerate(lines):
        op=line.split()[0]
        qs=tuple(map(int,qs_pat.findall(line)))
        if op not in COHERENT:active.clear()
        if op=='PUSH_CONDITION':
            branch.append(values[:])
        elif op=='POP_CONDITION':
            assert branch.pop()==values
        elif op in COHERENT|{'HMR'}:
            is_paid=op in NONLINEAR
            assert ' if ' not in line
            for rec in active:
                advance(op,qs,rec['changed'],d)
            if is_paid and (only is None or i in only):
                active.append(dict(start=i,changed=values[:],depth=len(branch)))
            advance(op,qs,values,d)
            if is_paid:
                if len(active)>9:active.pop(0)
                for rec in active[:-1]:
                    if only is not None and i not in only[rec['start']]:continue
                    count+=1
                    old=[d,*values]
                    new=[d,*rec['changed']]
                    basis=affine_basis(new)
                    if all(solve(basis,v) is not None for v in old) and len(affine_basis(old))==len(basis):
                        start=rec['start']
                        hits.append(dict(start=start,end=i,depth=rec['depth'],rank=len(basis)))
                        if only is not None:snapshots[(start,i)]=(old,new,basis)
        elif op=='R':assert values[qs[0]]==0
    return hits,count,snapshots

def unit_row_ops(rows):
    # XOR row operations on an augmented basis to obtain fixed canonical frame.
    a=list(rows)
    n=len(a)
    ops=[]
    for j in range(n):
        pivot=j
        while ((a[pivot]>>j)&1)==0:pivot+=1
        if pivot!=j:
            assert j!=0 and pivot!=0
            a[j],a[pivot]=a[pivot],a[j]
            ops.append(f'SWAP q{j-1} q{pivot-1}')
        for i in range(1,n):
            if i!=j and ((a[i]>>j)&1):
                a[i]^=a[j]
                ops.append(f'X q{i-1}' if j==0 else f'CX q{j-1} q{i-1}')
    assert a==[1<<i for i in range(n)]
    return ops

def encode_common(old,new,basis):
    # Both old and new span the same subspace. Complete symbolic coefficient rows
    # to invertible matrices by introducing nullspace coordinates also zero on
    # the audited reachable domain.
    del basis
    pivots=affine_basis(old)
    desc=[v[0] for key,v in sorted(pivots.items(),reverse=True)]
    # Row 0 is the all-ones constant and must stay fixed. Use it explicitly.
    support=[old[0]]
    b1=affine_basis(support)
    for v in desc:
        if solve(b1,v) is None:
            support.append(v)
            b1=affine_basis(support)
    assert len(support)==len(pivots)
    def lift(vs):
        coeffs=[solve(b1,v) for v in vs]
        dep=[]
        independent=affine_basis([])
        for i,c in enumerate(coeffs):
            if solve(independent,c) is None:
                independent=affine_basis([v for v,_ in independent.values()]+[c])
            else:dep.append(i)
        for k,i in enumerate(dep):
            coeffs[i]^=1<<(len(support)+k)
        assert coeffs[0]==1
        return unit_row_ops(coeffs)
    return lift(new)+lift(old)[::-1]

def main():
    import kickmix as km
    p=argparse.ArgumentParser()
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    assert hashlib.sha256(args.source.read_bytes()).hexdigest()==SOURCE_SHA
    c=km.Circuit.from_file(args.source,format='kmb')
    lines=str(c).splitlines()
    rng=random.Random(9222)
    xs=np.array(sorted(set([1,2,3,MAX_X]+[2**j+d for j in range(1,22) for d in (-1,0,1)]+[rng.randint(1,MAX_X) for i in range(1414)])),dtype=np.uint32)
    hits,count,_=analyse(lines,columns(xs),(1<<len(xs))-1)
    print('sample',len(hits),count,hits[:120],flush=True)
    valid=[]
    if hits:
        only={}
        for h in hits:only.setdefault(h['start'],set()).add(h['end'])
        domain=(1<<MAX_X)-1
        valid,_,snapshots=analyse(lines,columns(np.arange(1,MAX_X+1,dtype=np.uint32)),domain,only)
        for rec in valid:
            start,end=rec['start'],rec['end']
            old,new,b=snapshots[(start,end)]
            built=encode_common(old,new,b)
            actual=new[1:].copy()
            for l in built:
                advance(l.split()[0],tuple(map(int,re.findall(r'\bq(\d+)\b',l))),actual,domain)
            assert actual==old[1:]
            rec['following_gates']=built
        print('valid',valid,flush=True)
        valid.sort(key=lambda rec:len(rec['following_gates']))
        if valid:
            r=valid[0];st,ed=r['start'],r['end']
            text='\n'.join(lines[:st]+lines[st+1:ed+1]+r['following_gates']+lines[ed+1:])+'\n'
            rebuilt=km.Circuit(text)
            assert rebuilt.num_qubits==c.num_qubits
            rebuilt.to_file(args.out/'drop_candidate.kmb',format='kmb')
            (args.out/'drop_candidate.kmx').write_text(text)
    (args.out/'drop_reconcile.json').write_text(json.dumps(dict(source_sha=SOURCE_SHA,windows=count,sample_hits=hits,certified=valid),indent=2)+'\n')

if __name__=='__main__':main()
