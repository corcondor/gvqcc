#!/usr/bin/env python3
"""Independent text-KMX proof allowing linear scratch updates between HMR and CZ.
The measurement phase coefficient p_m is carried symbolically until the
next HMR; each conditional CZ adds control_A*control_B to p_m.
All valid addresses and arbitrary dirty targets are checked in parallel.
This parser does NOT import the emitter or compiled function implementations.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
import numpy as np
TARGETS=[11+8*w+b for w in range(5) for b in range(7)]
TAGS=[18,26,34,42,50]

def independent_verify(path, words, slot, dirty_seed=1997):
    n=len(words);ones=(1<<n)-1;state=[0]*128
    for q in range(11):state[q]=sum(((a>>q)&1)<<a for a in range(n))
    rng=np.random.default_rng(dirty_seed)
    for q in range(11,51):state[q]=int.from_bytes(rng.bytes((n+7)//8),'little')&ones
    start=state.copy();pending=None;maxq=-1;meas=0;multicz=0;czcount=0
    counts={name:0 for name in ['X','CX','CCX','CZ','HMR','R']}
    for ln,s in enumerate(path.read_text().splitlines(),1):
        p=s.split();
        if not p:continue
        op=p[0]
        if op=='REGISTER':continue
        if op=='APPEND_TO_REGISTER':maxq=max(maxq,int(p[1][1:]));continue
        qs=[int(t[1:]) for t in p[1:] if t.startswith('q') and t[1:].isdigit()]
        if any(q>=128 or q<0 for q in qs):raise AssertionError(('invalid_qubit',ln,qs))
        if qs:maxq=max(maxq,*qs)
        if op=='R':
            if len(qs)!=1 or state[qs[0]]:raise AssertionError(('dirty_R',ln))
        elif op=='X':
            if len(qs)!=1:raise AssertionError(('bad_X',ln))
            state[qs[0]]^=ones
        elif op=='CX':
            if len(qs)!=2 or qs[0] in TARGETS or qs[0] in TAGS:raise AssertionError(('bad_CX',ln))
            state[qs[1]]^=state[qs[0]]
        elif op=='CCX':
            if len(qs)!=3 or qs[0] in TARGETS or qs[1] in TARGETS or qs[0] in TAGS or qs[1] in TAGS:raise AssertionError(('bad_CCX',ln))
            state[qs[2]]^=state[qs[0]]&state[qs[1]]
        elif op=='HMR':
            if len(qs)!=1 or p[-1]!='b0' or qs[0]<51:raise AssertionError(('bad_HMR',ln))
            if pending is not None:
                if pending:raise AssertionError(('uncorrected_previous_HMR',ln,meas))
                if czcount>1:multicz+=1
            pending=state[qs[0]];state[qs[0]]=0;czcount=0;meas+=1
        elif op=='CZ':
            if len(qs)!=2 or p[-2:]!=['if','b0'] or pending is None:raise AssertionError(('bad_CZ',ln))
            if qs[0] in TARGETS or qs[1] in TARGETS:raise AssertionError(('dirty_CZ',ln))
            pending^=state[qs[0]]&state[qs[1]];czcount+=1
        else:raise AssertionError(('unsupported',ln,s))
        counts[op]+=1
    if pending is not None:
        if pending:raise AssertionError(('uncorrected_last_phase',meas))
        if czcount>1:multicz+=1
    d=np.array(words[:,slot*5:slot*5+5],dtype=np.uint8,copy=True)
    if slot:d^=words[:,slot*5-5:slot*5].astype(np.uint8)
    for j in range(5):
        for b in range(7):
            q=11+8*j+b
            expect=sum(((int(d[a,j])>>b)&1)<<a for a in range(n))
            if state[q]!=(start[q]^expect):raise AssertionError(('bad_word',slot,j,b))
    for q in list(range(11))+TAGS:
        if state[q]!=start[q]:raise AssertionError(('tag_or_address_changed',q))
    for q in range(51,maxq+1):
        if state[q]:raise AssertionError(('unclean_scratch',q))
    return dict(Q=maxq+1,CCX=counts['CCX'],CX=counts['CX'],HMR=counts['HMR'],CZ=counts['CZ'],
                independent_addresses=n,dirty_target_XOR_pass=True,phase_symbols_cancel=True,
                clean_scratch=True,multi_CZ_events=multicz,
                kmx_sha256=hashlib.sha256(path.read_bytes()).hexdigest())

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--kmx',type=Path,required=True);p.add_argument('--npz',type=Path,required=True);p.add_argument('--slot',type=int,required=True)
    a=p.parse_args();
    with np.load(a.npz) as z:words=np.asarray(z['angle_words'])
    print(json.dumps(independent_verify(a.kmx,words,a.slot),indent=2))
