#!/usr/bin/env python3
"""Independent textual-KMX verifier for 7-bit/J5 ANGLE XOR oracles.

Does NOT import any compiler module. It executes the serialized KMX gate
stream on all valid addresses as bitsets, seeded with arbitrary nonzero
dirty target registers and initial clean scratch. HMR outcomes are formal
independent symbols; each measurement's residual phase coefficient is
checked across ALL valid addresses, including multiple CZ corrections
on the same measurement outcome. Only certified operations are accepted.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
import numpy as np
MASKS=[11+8*j+b for j in range(5) for b in range(7)]
TAGS=[18,26,34,42,50]


def verify(path:Path,words:np.ndarray,slot:int,dirty_seed:int=23):
    N=len(words);whole=(1<<N)-1
    data=path.read_bytes();checksum=hashlib.sha256(data).hexdigest()
    state=[0]*128;init=[0]*128
    for q in range(11):state[q]=sum(((i>>q)&1)<<i for i in range(N))
    rng=np.random.default_rng(dirty_seed)
    for q in range(11,51):state[q]=int.from_bytes(rng.bytes((N+7)//8),'little') & whole
    init=state.copy()
    measured=0;multi=0;pending=None;cz_since=0
    counts=dict(CCX=0,CX=0,X=0,CZ=0,HMR=0,R=0)
    maxq=-1
    for ln,raw in enumerate(data.decode('utf-8').splitlines(),1):
        s=raw.strip()
        if not s:continue
        parts=s.split();op=parts[0]
        if op=='REGISTER':continue
        if op=='APPEND_TO_REGISTER':
            if len(parts)!=3:raise AssertionError(('bad declaration',ln,s))
            maxq=max(maxq,int(parts[1][1:]));continue
        qs=[]
        for t in parts[1:]:
            if t.startswith('q') and t[1:].isdigit():
                qs.append(int(t[1:]))
        if any(q>=128 or q<0 for q in qs):raise AssertionError(('bad qubit',ln,qs))
        if qs:maxq=max(maxq,*qs)
        if pending is not None and op!='CZ':
            if pending:raise AssertionError(('uncorrected phase',ln,measured,(pending&-pending).bit_length()-1))
            if cz_since>1:multi+=1
            pending=None;cz_since=0
        if op=='R':
            if len(qs)!=1 or state[qs[0]]:raise AssertionError(('dirty reset',ln,s))
        elif op=='X':
            if len(qs)!=1:raise AssertionError(('wrong X',ln))
            state[qs[0]] ^= whole
        elif op=='CX':
            if len(qs)!=2 or qs[0]==qs[1]:raise AssertionError(('wrong CX',ln))
            if 11<=qs[0]<=50:raise AssertionError(('dirty_target_used_as_control',ln,qs))
            state[qs[1]] ^= state[qs[0]]
        elif op=='CCX':
            if len(qs)!=3 or len(set(qs))!=3:raise AssertionError(('wrong CCX',ln))
            if any(11<=q<=50 for q in qs[:2]):raise AssertionError(('dirty_target_CCX_control',ln,qs))
            state[qs[2]] ^= state[qs[0]] & state[qs[1]]
        elif op=='HMR':
            if len(qs)!=1 or parts[-1]!='b0' or qs[0]<51:raise AssertionError(('wrong HMR',ln))
            pending=state[qs[0]]
            state[qs[0]]=0
            measured+=1
        elif op=='CZ':
            if len(qs)!=2 or parts[-2:]!=['if','b0'] or pending is None:raise AssertionError(('wrong conditioned CZ',ln))
            pending ^= state[qs[0]] & state[qs[1]]
            cz_since+=1
        else:raise AssertionError(('unknown operation',ln,s))
        counts[op]+=1
    if pending is not None:
        if pending:raise AssertionError(('uncorrected terminal phase',measured))
        if cz_since>1:multi+=1
    if maxq>=128:raise AssertionError(('width',maxq))
    d=np.array(words[:,5*slot:5*slot+5],dtype=np.uint8,copy=True)
    if slot:d ^= words[:,5*(slot-1):5*slot].astype(np.uint8)
    for bit,q in enumerate(MASKS):
        word,idx=divmod(bit,7)
        truth=sum(((int(d[a,word])>>idx)&1)<<a for a in range(N))
        if state[q]!=(init[q]^truth):raise AssertionError(('output error',q,bit,(state[q]^(init[q]^truth)&-(state[q]^(init[q]^truth))).bit_length()-1))
    for q in list(range(11))+TAGS:
        if state[q]!=init[q]:raise AssertionError(('changed selection or tag',q))
    for q in range(51, maxq+1):
        if state[q]:raise AssertionError(('dirty scratch',q))
    return dict(kmx_sha256=checksum,CCX=counts['CCX'],CX=counts['CX'],HMR=counts['HMR'],CZ=counts['CZ'],
                Q=maxq+1,phase_symbols_cancel=True,measurements_with_multiple_CZ=multi,
                all_legal_addresses_verified=N,dirty_seed=dirty_seed)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--kmx',type=Path,required=True)
    p.add_argument('--npz',type=Path,required=True)
    p.add_argument('--slot',type=int,required=True)
    args=p.parse_args()
    with np.load(args.npz,allow_pickle=False) as z:w=np.asarray(z['angle_words'],dtype=np.uint8)
    print(json.dumps(verify(args.kmx,w,args.slot),indent=2))
if __name__=='__main__':main()
