"""Materialize a phase-only product on the first live requesting branch."""
import argparse
from bisect import bisect_right
from collections import Counter, defaultdict
from fractions import Fraction
from hashlib import sha256
from itertools import product as bits_product
import json
from pathlib import Path
import re

import kickmix as km
import numpy as np

from lazy import PIN, DOMAIN, PAID, DATA, PHASE, parse, make_trace, tracks_for
COMBINED='f3427a64809c228189dfc4edc412f03a0bc5e29153d524b4e0d235433c6bcba3'

def requests(gates,track):
    scopes,_,writes,conditions=track
    refs=[[] for _ in range(46)]
    for site,(op,qs,_) in enumerate(gates):
        for q in qs:
            refs[q].append(site)
    candidates=[]
    for i,(op,qs,_) in enumerate(gates):
        if op!='CCX' or scopes[i]:
            continue
        a,b,q=qs
        clauses={}
        final=None
        for j in refs[q][bisect_right(refs[q],i):]:
            op,qs,inline=gates[j]
            if op=='HMR' and not scopes[j]:
                final=j
                break
            readonly=(op=='CX' and qs[0]==q) or (op=='CCX' and q in qs[:2]) or (
                op=='CSWAP' and qs[0]==q)
            if op not in PHASE|{'Z_POW'} and not readonly:
                break
            guard=set(conditions[s] for s in scopes[j])
            if inline:
                guard.add((inline,bisect_right(writes.get(inline,[]),j)))
            if not guard:
                break
            if any(set(need)<=guard for need in clauses):
                # A previously encountered broader request has already
                # materialized the product whenever this event can execute.
                continue
            # Only independent direct HMR bits, with their own version valid.
            if any(not v or v>len(writes[k]) or gates[writes[k][v-1]][0]!='HMR' or
                   scopes[writes[k][v-1]] for k,v in guard):
                break
            clauses.setdefault(tuple(sorted(guard)),j)
        if final is None or not clauses:
            continue
        mask=sorted(set(u for c in clauses for u in c))
        if len(mask)>11:
            continue
        active=0
        for choice in bits_product((False,True),repeat=len(mask)):
            mapping=dict(zip(mask,choice))
            active+=any(all(mapping[q] for q in c) for c in clauses)
        cost=Fraction(active,1<<len(mask))
        if cost<1:
            candidates.append(dict(start=i,end=final,controls=(a,b),target=q,
                                   requests=[(s,list(c)) for c,s in clauses.items()],
                                   exact_expected_saving=str(1-cost)))
    return candidates

def screen(plans,trace):
    out=[]
    for p in plans:
        i=p['start'];a,b=p['controls'];q=p['target']
        base=trace[i-1]
        if base[q]:
            continue
        target_product=base[a]&base[b]
        cuts=[s-1 for s,c in p['requests']]+[p['end']]
        if all(trace[j][a]&trace[j][b]==target_product for j in cuts):
            out.append(p)
    return out

def emit(lines,gates,track,plans):
    before=defaultdict(list)
    after=defaultdict(list)
    removed=set()
    fresh=max(int(k) for l in lines for k in re.findall(r'\bb(\d+)\b',l))+1
    for p in plans:
        i,j=p['start'],p['end']
        a,b=p['controls']
        gate=lines[i]
        have=f'b{fresh}';need=f'b{fresh+1}';fresh+=2
        before[i].append(f'BIT_STORE0 {have}')
        removed.add(i)
        for s,conditions in p['requests']:
            active=set(track[3][z] for z in track[0][s])
            extra=set(map(tuple,conditions))-active
            for bit,_ in sorted(extra):
                before[s].append(f'PUSH_CONDITION if {bit}')
            before[s]+=[f'BIT_STORE0 {need}',f'BIT_INVERT {need} if {have}',
                        f'BIT_INVERT {need}',f'PUSH_CONDITION if {need}',
                        gate,f'BIT_INVERT {have}','POP_CONDITION']
            before[s]+=['POP_CONDITION']*len(extra)
        measure=lines[j].split()[2]
        after[j]+=[f'BIT_STORE0 {need}',f'BIT_INVERT {need} if {have}',
                   f'BIT_INVERT {need}',f'PUSH_CONDITION if {need}',
                   f'CZ q{a} q{b} if {measure}','POP_CONDITION']
    stitched=[]
    for i,line in enumerate(lines):
        stitched+=before[i]
        if i not in removed:
            stitched.append(line)
        stitched+=after[i]
    return chr(10).join(stitched)+chr(10)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    src=sha256(args.source.read_bytes()).hexdigest()
    assert src in (PIN,COMBINED)
    lines=str(km.Circuit.from_file(args.source,format='kmb')).splitlines()
    gates=list(map(parse,lines))
    tr=tracks_for(gates,lines)
    plans=requests(gates,tr)
    full=np.arange(1,DOMAIN+1,dtype=np.uint32)
    rng=np.random.default_rng(143522)
    small=np.unique(np.r_[np.arange(1,1100),rng.integers(1,DOMAIN+1,2600),DOMAIN]).astype(np.uint32)
    exact=screen(plans,list(make_trace(gates,small)))
    print('plans',len(plans),'sample',len(exact),flush=True)
    needed={cut for r in exact for cut in [r['start']-1,r['end'],*[i-1 for i,_ in r['requests']]]}
    # The combined source introduces a data-restoring conditional phase block.
    audit={j:state for j,state in enumerate(make_trace(gates,full)) if j in needed}
    exact=screen(exact,audit)
    selected=[]
    for r in sorted(exact,key=lambda r:-Fraction(r['exact_expected_saving'])):
        # A requested product uses the two unmodified original control wires
        # at every new site, and candidate lifetimes cannot modify those.
        conflict=any(max(r['start'],p['start'])<=min(r['end'],p['end']) and
                     (r['target']==p['target'] or r['target'] in p['controls'] or
                      p['target'] in r['controls']) for p in selected)
        if not conflict:
            selected.append(r)
    out=dict(source=src,candidates=len(plans),exact=exact,selected=selected)
    if selected:
        q=km.Circuit(emit(lines,gates,tr,selected))
        assert q.num_qubits==46
        file=args.out.with_suffix('.kmb')
        q.to_file(file,format='kmb')
        out['candidate_sha']=sha256(file.read_bytes()).hexdigest()
        out['expected_saving_vs_source']=str(sum(Fraction(r['exact_expected_saving']) for r in selected))
        out['static_toffoli_like']=q.operation_statistics().num_toffoli_like
    args.out.write_text(json.dumps(out,indent=2)+chr(10))
    print({k:v for k,v in out.items() if k!='exact'},flush=True)

if __name__=='__main__':
    main()
