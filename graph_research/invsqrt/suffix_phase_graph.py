#!/usr/bin/env python3
"""Causal suffix phase reuse: index later singleton and pair predicates."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import random
import re
import numpy as np
from temporal_phase_graph import (MAX_X,SOURCE_SHA,DATA,gate,advance,columns,layout,
                                  capture_entries,make_edges,trace,solve,product)


def raw_features(w,mask):
    yield mask,()
    for i,a in enumerate(w):
        if a:
            yield a,(i,)
            for j,b in enumerate(w[:i]):
                if v:=a&b:yield v,(j,i)


def suffix_index(ops,v,mask,min_cut):
    """Store latest live top-level occurrence of each sampled quadratic edge."""
    w=v[:]; stack=[]; index={}
    for i,(op,qs) in enumerate(ops):
        if op=='PUSH_CONDITION': stack.append(w[:]);continue
        if op=='POP_CONDITION':
            assert stack.pop()==w,i
            continue
        if op not in DATA:continue
        old=w[:];advance(op,qs,w,mask)
        if stack or i<min_cut:continue
        changed=[j for j,a in enumerate(w) if a!=old[j]]
        if not index:
            for a,q in raw_features(w,mask):index[a]=(i,q)
        for j in changed:
            b=w[j]
            if not b:continue
            index[b]=(i,(j,))
            for k,a in enumerate(w):
                if k!=j and (r:=a&b):index[r]=(i,(j,k))
        index[mask]=(i,())
    return index


def eligible(hits,owner,unsupported):
    return [h for h in hits if owner[h['start']] is not None and owner[h['start']] not in unsupported]


def certify(lines,ops,results):
    """Full-domain bitset replay of just the selected insertion cuts."""
    owner,end,guards,unsupported=layout(lines,ops)
    n=MAX_X
    mask=(1<<n)-1
    initial=columns(np.arange(1,n+1,dtype=np.uint32))
    local_pushes={d['branch_start'] for d in results}
    outside_cuts={i for d in results for p in d['phases'] for i,_ in p['terms'] if i>=d['branch_end']}
    w=initial[:];stack=[];state={};outside={}
    for i,(op,qs) in enumerate(ops):
        if i in local_pushes:state[i]=w[:]
        if op=='PUSH_CONDITION':stack.append(w[:])
        elif op=='POP_CONDITION':assert stack.pop()==w,i
        else:advance(op,qs,w,mask)
        if i in outside_cuts: assert not stack;outside[i]=w[:]
    positives=[]; denied=[]
    for rec in results:
        t=trace(lines,ops,state[rec['branch_start']],mask,{'start':rec['removed']},owner,end,guards)
        if t is None:
            denied.append(dict(removed=rec['removed'],reason='bad full-domain data/observation trace'));continue
        snaps,debts,stop=t
        residual={k:f for k,(i,f) in debts.items()}
        for p in rec['phases']:
            origin=p['origin']; fx=0
            for i,qs in p['terms']:
                w1=outside[i] if i>=stop else snaps[i]
                fx^=product(w1,qs,mask)
            residual[origin]=residual.get(origin,0)^fx
        fails=[(k,(f&-f).bit_length()) for k,f in residual.items() if f]
        if fails:denied.append(dict(removed=rec['removed'],reason='phase mismatch',witnesses=fails))
        else:positives.append(rec)
    return positives,denied


def render(lines,rec):
    ops=list(map(gate,lines)); pre=defaultdict(list); post=defaultdict(list)
    push=rec['branch_start']; delete=rec['removed']; fresh=max(map(int,re.findall(r'\bb(\d+)\b','\n'.join(lines))))+1
    for k,phase in enumerate(rec['phases']):
        guard=f'b{fresh+k}'
        pre[push].append(f'BIT_STORE0 {guard}')
        origin=phase['origin']
        if origin==push:
            post[push].append(f'BIT_STORE1 {guard}')
        else:
            assert ops[origin][0]=='HMR'
            post[origin].append(f'BIT_INVERT {guard} if {lines[origin].split()[2]}')
        for i,qs in phase['terms']:
            opt={0:'NEG',1:'Z',2:'CZ'}[len(qs)]
            qstr=''.join(f' q{j}' for j in qs)
            post[i].append(f'{opt}{qstr} if {guard}')
    return '\n'.join(g for i,l in enumerate(lines) for g in pre[i]+([l] if i!=delete else [])+post[i])+'\n'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--prior-hits',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--samples',type=int,default=1552)
    p.add_argument('--suffix-pairs',action='store_true')
    args=p.parse_args()
    import kickmix as km
    assert hashlib.sha256(args.source.read_bytes()).hexdigest()==SOURCE_SHA
    circ=km.Circuit.from_file(args.source,format='kmb');lines=str(circ).splitlines();ops=list(map(gate,lines))
    rng=random.Random(141911)
    xs=np.array(sorted(set([*range(1,256),MAX_X,*[rng.randint(1,MAX_X) for _ in range(args.samples-256)]])),dtype=np.uint32)
    mask=(1<<len(xs))-1;v=columns(xs)
    owner,end,guards,unsupported=layout(lines,ops)
    hits=eligible(json.loads(args.prior_hits.read_text())['sample_hits'],owner,unsupported)
    entries=capture_entries(ops,v,mask,{owner[h['start']] for h in hits})
    index=suffix_index(ops,v,mask,min(end[owner[h['start']]] for h in hits))
    print('indexed',len(index),flush=True)
    positives=[]; records=[]
    for h in hits:
        push=owner[h['start']]; t=trace(lines,ops,entries[push],mask,h,owner,end,guards)
        if t is None:continue
        local,debts,stop=t; phases=[]; counters=defaultdict(int)
        for origin,(start,f) in sorted(debts.items(),key=lambda x:-x[1][0]):
            if (r:=index.get(f)) and r[0]>stop:
                phases.append(dict(origin=origin,terms=[r]));counters['single_suffix']+=1;continue
            # Try a suffix edge plus a local edge from one causal cut.
            found=False
            for i in [x for x in local if x>=start][-8:]:
                for val,q in raw_features(local[i],mask):
                    if (r:=index.get(f^val)) and r[0]>stop:
                        phases.append(dict(origin=origin,terms=[(i,q),r]));counters['mixed_two']+=1
                        found=True;break
                if found:break
            if found:continue
            basis,edges,_=make_edges(local,mask,start,12)
            c=solve(basis,f)
            if c is None:
                pair=None
                if args.suffix_pairs:
                    for a,e in index.items():
                        if e[0]<=stop:continue
                        r=index.get(a^f)
                        if r is not None and r[0]>stop:
                            pair=(e,r);break
                if pair is not None:
                    phases.append(dict(origin=origin,terms=list(pair)));counters['suffix_pair']+=1
                else:counters['unpaid']+=1
            else:
                phases.append(dict(origin=origin,terms=[e for j,e in enumerate(edges) if c>>j&1]));counters['local_span']+=1
        row=dict(removed=h['start'],branch_start=push,branch_end=stop,debts=len(debts),recovery=dict(counters))
        records.append(row)
        if len(phases)==len(debts):positives.append({**row,'phases':phases})
    print('sample passes',len(positives),'aggregates',dict(sum_counters(records)),flush=True)
    verified,denied=certify(lines,ops,positives) if positives else ([],[])
    print('full passes',len(verified),flush=True)
    if verified:
        best=min(verified,key=lambda a:sum(len(d['terms']) for d in a['phases']))
        text=render(lines,best);variant=km.Circuit(text)
        assert variant.num_qubits==circ.num_qubits
        assert variant.operation_statistics().num_toffoli_like==circ.operation_statistics().num_toffoli_like-1
        variant.to_file(args.out.parent/'suffix_candidate.kmb',format='kmb')
    args.out.write_text(json.dumps(dict(source_sha256=SOURCE_SHA,sample_count=len(xs),suffix_index=len(index),
        analyzed=len(records),sample_passes=len(positives),full_domain_passes=verified,full_domain_denied=denied,aggregate=dict(sum_counters(records)),records=records),indent=2)+'\n')


def sum_counters(records):
    d=defaultdict(int)
    for row in records:
        for k,v in row['recovery'].items():d[k]+=v
    return d

if __name__=='__main__':main()
