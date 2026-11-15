#!/usr/bin/env python3
"""Resynthesize measured phase differences from a time-expanded XOR hypergraph.

A vertex is a causal insertion cut carrying a quantum wire value. A labeled
hyperedge is the phase predicate 1, q, or q*r at one insertion cut. Edges can
be selected at several different cuts, preserving the classical observation
for each parity equation. This search covers singleton controlled windows;
all sample hits are hypotheses, not certifications.
"""
from pathlib import Path
from collections import defaultdict
import argparse
import hashlib
import json
import random
import re
import numpy as np

DATA={'X','CX','CCX','SWAP','CSWAP','R','HMR'}
SIGN={'Z','CZ','CCZ','NEG'}
MAX_X=3133452
SOURCE_SHA='684106f101730ca193627229920a0501bef9ea10ccfb34aa453fcf63edadb50a'
PAID={'CCX','CSWAP'}


def columns(xs):
    bits=np.packbits(((xs[None,:]>>np.arange(22,dtype=np.uint32)[:,None])&1).astype(np.uint8), axis=1,bitorder='little')
    return [int.from_bytes(a.tobytes(),'little') for a in bits]+[0]*24


def gate(line):
    return line.split()[0],tuple(map(int,re.findall(r'\bq(\d+)\b',line)))


def advance(op,qs,w,m):
    if op=='X': (a,)=qs; w[a]^=m
    elif op=='CX': a,b=qs; w[b]^=w[a]
    elif op=='CCX': a,b,c=qs; w[c]^=w[a]&w[b]
    elif op=='SWAP': a,b=qs; w[a],w[b]=w[b],w[a]
    elif op=='CSWAP': a,b,c=qs; d=w[a]&(w[b]^w[c]);w[b]^=d;w[c]^=d
    elif op in {'R','HMR'}: (a,)=qs;w[a]=0


def product(w,qs,m):
    for q in qs: m &= w[q]
    return m


def layout(lines,ops):
    stack=[]; owner=[]; end={}; last={}; guards={}; unsupported=set()
    for i,(l,(op,qs)) in enumerate(zip(lines,ops)):
        owner.append(stack[-1] if stack else None)
        if op=='PUSH_CONDITION':
            if stack: unsupported.add(stack[0])
            stack.append(i);last[i]={}
        elif op=='POP_CONDITION': end[stack.pop()]=i
        elif stack and op=='HMR': last[stack[-1]][l.split()[2]]=i
        elif stack and op.startswith('BIT_'): unsupported.add(stack[0])
        elif stack and op in SIGN and ' if ' in l:
            b=l.split()[-1]; guards[i]=last[stack[-1]].get(b)
    assert not stack
    return owner,end,guards,unsupported


def capture_entries(ops,vals,mask,pushes):
    stack=[]; states={}; w=vals[:]
    for i,(op,qs) in enumerate(ops):
        if i in pushes:states[i]=w[:]
        if op=='PUSH_CONDITION':stack.append(w[:])
        elif op=='POP_CONDITION': assert stack.pop()==w, i
        elif op=='R': assert not w[qs[0]],i
        else:advance(op,qs,w,mask)
    assert not stack
    return states


def trace(lines,ops,initial,mask,r,owner,end,guards):
    push=owner[r['start']]; stop=end[push]; skip=r['start']
    w=initial[:];mod=w[:]; states={}; debts=defaultdict(int); starts={}
    for i in range(push+1,stop):
        op,qs=ops[i]
        if op=='HMR':
            k=i; starts[k]=i
            debts[k]^=w[qs[0]]^mod[qs[0]]
        elif op in SIGN:
            delta=product(w,qs,mask)^product(mod,qs,mask)
            if delta:
                if ' if ' in lines[i]:
                    k=guards.get(i)
                    if k is None: return None
                else:k=push; starts[k]=push
                debts[k]^=delta
        elif op=='Z_POW' and product(w,qs,mask)!=product(mod,qs,mask):return None
        elif op=='R' and (w[qs[0]] or mod[qs[0]]):return None
        if op in DATA:
            assert ' if ' not in lines[i]
            advance(op,qs,w,mask)
            if i!=skip:advance(op,qs,mod,mask)
        if i>=skip and (op in DATA or i==stop-1):states[i]=mod[:]
    if w!=mod or w!=initial:return None
    return states,{key:(starts[key],f) for key,f in debts.items() if f},stop


def make_edges(states,mask,start,max_cuts):
    cuts=sorted(i for i in states if i>=start)
    # Important cuts first: earliest available, final common state, and
    # geometrically separated intermediate states. Nearby state terms repeat.
    if len(cuts)>max_cuts:
        indices=np.linspace(0,len(cuts)-1,max_cuts).round().astype(int)
        cuts=[cuts[j] for j in indices]
    done=set(); basis={}; edges=[]
    for i in cuts:
        unique={}; vals=states[i]
        for q,v in enumerate(vals):
            if v and v!=mask:unique.setdefault(v,q)
        vv=list(unique.items())
        feats=[(mask,())]+[(v,(q,)) for v,q in vv]
        feats.extend((v&w,(q,p)) for j,(v,q) in enumerate(vv) for w,p in vv[:j])
        for value,qs in feats:
            if not value or value in done:continue
            done.add(value); reduced=value; coeff=0
            while reduced:
                pivot=reduced.bit_length()-1
                if pivot not in basis:
                    k=len(edges);edges.append((i,qs));basis[pivot]=reduced,coeff^(1<<k);break
                t,c=basis[pivot]; reduced^=t;coeff^=c
    return basis,edges,len(cuts)


def solve(basis,v):
    coeff=0
    while v:
        key=v.bit_length()-1
        if key not in basis:return None
        x,c=basis[key];v^=x;coeff^=c
    return coeff


def search(lines,ops,vals,mask,hits,max_cuts):
    owner,end,guards,unsupported=layout(lines,ops)
    hits=[h for h in hits if (push:=owner[h['start']]) is not None and push not in unsupported]
    states=capture_entries(ops,vals,mask,{owner[h['start']] for h in hits})
    report=[]; positives=[]
    for h in hits:
        push=owner[h['start']]
        t=trace(lines,ops,states[push],mask,h,owner,end,guards)
        if t is None:continue
        snapshots,debts,stop=t
        ans=[]; measurements=[]
        for k,(start,f) in sorted(debts.items(),key=lambda x:-x[1][0]):
            basis,edges,cuts=make_edges(snapshots,mask,start,max_cuts)
            c=solve(basis,f)
            measurements.append(dict(origin=k,rank=len(basis),cuts=cuts,spanned=c is not None))
            if c is None:break
            ans.append(dict(origin=k,terms=[e for j,e in enumerate(edges) if c>>j&1]))
        rec=dict(removed=h['start'],branch_start=push,branch_end=stop,debt_count=len(debts),visited=measurements)
        if len(ans)==len(debts):
            rec['phases']=ans;positives.append(rec)
        report.append(rec)
    return report,positives


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--prior-hits',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--samples',type=int,default=4096)
    p.add_argument('--max-cuts',type=int,default=12)
    args=p.parse_args()
    import kickmix as km
    assert hashlib.sha256(args.source.read_bytes()).hexdigest()==SOURCE_SHA
    c=km.Circuit.from_file(args.source,format='kmb');lines=str(c).splitlines();ops=list(map(gate,lines))
    rng=random.Random(141911)
    xs=np.array(sorted(set([*range(1,256),MAX_X,*[rng.randint(1,MAX_X) for _ in range(args.samples-256)]])),dtype=np.uint32)
    mask=(1<<len(xs))-1
    hits=json.loads(args.prior_hits.read_text())['sample_hits']
    report,positive=search(lines,ops,columns(xs),mask,hits,args.max_cuts)
    out=dict(source_sha256=SOURCE_SHA,sample_count=len(xs),max_cuts=args.max_cuts,prior_hits=len(hits),analyzed=len(report),sample_passes=len(positive),results=report)
    args.out.write_text(json.dumps(out,indent=2)+'\n')
    print({k:v for k,v in out.items() if k!='results'},flush=True)
    print([(r['removed'],sum(len(q['terms']) for q in r['phases'])) for r in positive],flush=True)

if __name__=='__main__':main()
