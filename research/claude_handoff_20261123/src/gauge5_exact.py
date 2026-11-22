#!/usr/bin/env python3
"""Exact five-dimensional FeMoCo ANGLE sign-gauge algebra.

Physical rule: shifting the first rotation word of a row by 64 negates
all 76 decoded components, preserving u*u^T and eigenvector projectors.
The 70 signed6 constraints are then restored using an AFFINE GF(2)
system on 74 intermediate signs. Four homogeneous freedoms remain.

This script does not itself establish Toffoli savings or KickMix acceptance.
"""
import argparse, hashlib, json
from pathlib import Path
import numpy as np


def geometry(edges):
    used={0}; refs=[]; slots=[]
    for k,(a,b) in enumerate(edges):
        a=int(a); b=int(b)
        assert (a in used) != (b in used)
        p,q=(a,b) if a in used else (b,a)
        later=set(edges[k+1:].flatten().tolist())
        pf=p in later; qf=q in later
        refs.append((p,q,pf,qf))
        if pf: slots.append((k,p))
        if qf: slots.append((k,q))
        used.add(q)
    assert len(used)==76 and len(slots)==74
    ix={v:i for i,v in enumerate(slots)}
    last={0:None}; expr=[]
    for k,(p,q,pf,qf) in enumerate(refs):
        incoming=(1<<ix[last[p]]) if last[p] in ix else 0
        x=((1<<ix[(k,p)]) if pf else 0)^incoming
        y=((1<<ix[(k,q)]) if qf else 0)^incoming
        expr.append((x,y))
        last[p]=(k,p);last[q]=(k,q)
    return refs,ix,expr


def affine_solution(mat, rhs):
    rows=[(int(v),int(r)) for v,r in zip(mat,rhs)]
    piv=[];i=0
    for bit in range(73,-1,-1):
        j=next((j for j in range(i,len(rows)) if rows[j][0]>>bit&1),None)
        if j is None:continue
        rows[i],rows[j]=rows[j],rows[i]
        v,b=rows[i]
        for j in range(len(rows)):
            if j!=i and rows[j][0]>>bit&1:
                a,t=rows[j];rows[j]=(a^v,t^b)
        piv.append(bit);i+=1
    if any(not v and b for v,b in rows[i:]):
        raise ValueError("No affine compensation exists")
    mask=sum(rows[j][1]<<p for j,p in enumerate(piv))
    assert all(((a&mask).bit_count()&1)==b for a,b in zip(mat,rhs))
    return mask,i


def decode(words,edges):
    n=len(words)
    v=np.zeros((n,76),dtype=np.float64);v[:,0]=1
    for k,(a,b) in enumerate(edges):
        a=int(a);b=int(b);theta=np.pi*words[:,k]/64.
        ca,sa=np.cos(theta),np.sin(theta)
        va,vb=v[:,a].copy(),v[:,b].copy()
        v[:,a]=ca*va-sa*vb;v[:,b]=sa*va+ca*vb
    return v


def transform(words, edges, selection):
    n=len(words); w=words.astype(np.uint8).copy()
    sigma=np.asarray(selection,dtype=np.uint8)
    assert w.shape==(n,75) and sigma.shape==(n,)
    residue=((w>>6)^(w>>5))&1
    assert np.array_equal(residue[:,5:],residue[:,:-5])
    refs,ix,expr=geometry(edges)
    cache={};masks=[]
    for row in range(n):
        f=[expr[k][int(w[row,k] in (32,96))] for k in range(75)]
        A=tuple(f[k]^f[k-5] for k in range(5,75))
        if A not in cache:cache[A]=affine_solution(A,[1]+[0]*69)
        m,rank=cache[A]
        assert rank==70, (row,rank)
        masks.append(m if sigma[row] else 0)
    w[:,0]^=sigma*64
    state=np.zeros((76,n),dtype=np.uint8)
    bits=np.array([[(m>>i)&1 for m in masks] for i in range(74)],dtype=np.uint8)
    for k,(p,q,pf,qf) in enumerate(refs):
        incoming=state[p]
        sp=bits[ix[(k,p)]] if pf else np.zeros(n,np.uint8)
        sq=bits[ix[(k,q)]] if qf else np.zeros(n,np.uint8)
        a=sp^incoming;b=sq^incoming
        old=w[:,k].astype(np.int16)
        w[:,k]=(np.where((a^b).astype(bool),-old,old)+64*a)&127
        state[p]=sp;state[q]=sq
    assert not np.any(state)
    resid=((w>>6)^(w>>5))&1
    assert np.array_equal(resid[:,5:],resid[:,:-5])
    return w, len(cache)


def synthetic_fixture(n=256):
    # This is explicitly SYNTHETIC, used to test the mathematical code on CI.
    edges=np.array([(0,i) for i in range(1,76)],dtype=np.int64)
    rng=np.random.default_rng(20261123)
    words=rng.integers(0,128,(n,75),dtype=np.uint8)
    words[(words&63)==32]^=1
    r=rng.integers(0,2,(n,5),dtype=np.uint8)
    for k in range(75):
        words[:,k]=(words[:,k]&63)|(((words[:,k]>>5)^r[:,k%5])<<6)
    return words,edges


def main():
    pa=argparse.ArgumentParser()
    pa.add_argument('--source',type=Path)
    pa.add_argument('--output',type=Path,required=True)
    pa.add_argument('--report',type=Path,required=True)
    pa.add_argument('--mode',choices=['zero_top_bit','all_flip','address_bit6'],default='zero_top_bit')
    pa.add_argument('--synthetic-rows',type=int,default=256)
    a=pa.parse_args()
    if a.source:
        with np.load(a.source,allow_pickle=False) as z:
            arrays={k:z[k].copy() for k in z.files}
        words=arrays['angle_words'].astype(np.uint8)
        edges=arrays['tree_edges'].astype(np.int64)
        kind='real_input'
    else:
        words,edges=synthetic_fixture(a.synthetic_rows)
        arrays={'angle_words':words,'tree_edges':edges}
        kind='synthetic_fixture_NOT_FE_MOCO'
    row=np.arange(len(words),dtype=np.uint16)
    sigma=({'zero_top_bit':(words[:,0]>>6)&1,
            'all_flip':np.ones(len(words),dtype=np.uint8),
            'address_bit6':(row>>6)&1})[a.mode].astype(np.uint8)
    out,count=transform(words,edges,sigma)
    expected=decode(words,edges)*(1-2*sigma.astype(np.int16))[:,None]
    error=float(np.max(np.abs(decode(out,edges)-expected)))
    assert error<1e-13
    arrays['angle_words']=out.astype(np.int64)
    a.output.parent.mkdir(exist_ok=True,parents=True)
    np.savez_compressed(a.output,**arrays)
    report={'input_kind':kind,'mode':a.mode,'rows':len(words),
       'affine_GF2_rank':70,'free_dimensions_per_row':5,
       'different_constraint_matrices':count,
       'changed_words':int(np.count_nonzero(out!=words)),
       'max_abs_vector_difference':error,
       'sha256_output':hashlib.sha256(a.output.read_bytes()).hexdigest(),
       'native_kickmix_verified':False,'score_improvement':None}
    a.report.parent.mkdir(exist_ok=True,parents=True)
    a.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
