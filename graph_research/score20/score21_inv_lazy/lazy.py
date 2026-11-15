"""Lazily compute a paid operation using causal classical outcome guards."""
import argparse
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from hashlib import sha256
import itertools
import json
from pathlib import Path
import re
import sys

import kickmix as km
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'highest_graph'/'phase_cone'))
from rewrite import (PIN,DOMAIN,PAID,DATA,PHASE,parse,initial_state,apply,product,
                     make_trace,quadratic_phase,tracks_for)

def event_group(events,track):
    scopes,_,writes,conditions=track
    out={}
    for site,pred,bit in events:
        keys={conditions[scope] for scope in scopes[site]}
        if bit:
            keys.add((bit,bisect_right(writes.get(bit,[]),site)))
        key=tuple(sorted(keys))
        leader,old=out.get(key,(site,0))
        out[key]=leader,old^pred
    return [(k,i,v) for k,(i,v) in out.items() if v]

def access(track,start,key):
    s,c,w,conds=track
    active={conds[q] for q in s[start]}
    result=[]
    for bit,version in key:
        refs=w.get(bit,[])
        if not version or version>len(refs):
            continue
        h=refs[version-1]
        if key is None:
            continue
        if (h<start and bisect_left(refs,start)==version and (bit,version) not in active and not s[h]):
            result.append((bit,version))
    return tuple(sorted(result))

def state_before(gates,trace,at,xs):
    return initial_state(xs) if not at else trace[at-1]

def find_cone(lines,gates,data,xs,track,start,span,counters,pair=None,approved=None):
    one=(1<<len(xs))-1
    scopes,closed,writes,conds=track
    g0=start
    edits={start}
    if pair is not None:
        edits.add(pair)
    last=max(edits)
    # An existing scope may be shared, but skip-only data paths must reunite
    # before that enclosing scope closes.
    base_scope=scopes[start]
    max_end=min(start+span,len(gates),closed[base_scope[-1]] if base_scope else len(gates))
    if approved is not None:
        max_end=approved['end']+1
    cur=list(state_before(gates,data,start,xs))
    events=[]
    states={}
    stacks=[]
    for i in range(start,max_end):
        before=state_before(gates,data,i,xs)
        after=data[i]
        op,qs,bit=gates[i]
        diff=0
        if i in edits:
            assert op in PAID
        elif op in DATA:
            if op=='HMR':
                diff=before[qs[0]]^cur[qs[0]]
                bit=lines[i].split()[2]
            assert op in ('CCX','CSWAP','X','CX','SWAP','HMR')
            apply(op,qs,cur,one)
        elif op=='R' and cur[qs[0]]:
            counters['reset']+=1
            return None
        elif op in PHASE or op=='NEG':
            diff=product(before,qs,one)^product(cur,qs,one)
        elif op=='Z_POW' and before[qs[0]]!=cur[qs[0]]:
            counters['rotation']+=1
            return None
        elif op=='PUSH_CONDITION':
            stacks.append((tuple(cur),before))
        elif op=='POP_CONDITION':
            entry,_=stacks.pop()
            if tuple(cur)!=entry:
                counters['join']+=1
                return None
        if diff:
            events.append((i,diff,bit))
        if diff or approved is not None:
            states[i]=tuple(cur)
        if i>=last and tuple(cur)==after and all(a==b for a,b in stacks):
            counters['converged']+=1
            terms=event_group(events,track)
            if approved is not None:
                ends=[]
                for key,site,pred in terms:
                    if any(tuple(k) in key for k in approved['run_on']):
                        continue
                    match=next((r for r in approved['corrections'] if tuple(map(tuple,r['guards']))==key),None)
                    if match is None:
                        return None
                    phases=0
                    for cut,label in match['terms']:
                        opcode,qs,_=parse(label)
                        if opcode=='PARITY_CCZ':
                            a,b,*tail=qs
                            value=0
                            for q in tail:
                                value^=states[cut][q]
                            phases^=states[cut][a]&states[cut][b]&value
                        else:
                            phases^=product(states[cut],qs,one)
                    if phases!=pred:
                        return None
                    ends.append(key)
                if len(ends)!=len(approved['corrections']):
                    return None
                return approved
            return i,terms,states,one
    counters['window']+=1
    return None

def minimal_guard(bad):
    pool=set(itertools.chain.from_iterable(bad))
    if not pool:
        return None
    for n in range(1,min(len(pool),3)+1):
        for mask in itertools.combinations(sorted(pool),n):
            if all(set(mask)&set(x) for x in bad):
                return mask
    return None

def trial(lines,gates,data,xs,track,start,span,counters,pair=None):
    details=find_cone(lines,gates,data,xs,track,start,span,counters,pair=pair)
    if details is None:
        return None
    end,events,states,one=details
    unguarded=[]
    candidates=[]
    for key,site,pred in events:
        idx=access(track,start,key)
        if idx:
            candidates.append((key,site,pred,idx))
        else:
            unguarded.append((key,site,pred))
    if not candidates:
        return None
    layers=track[0]
    corrections=[]
    def cover(key,site,pred):
        # To retain exactly what existing classical scopes make available, the
        # phase restoration is computed at its actual observable location.
        match=quadratic_phase(pred,[(site,states[site])],one)
        if match is None:
            return None
        return dict(guards=key,site=site,terms=match)
    for key,site,pred in unguarded:
        c=cover(key,site,pred)
        if c is None:
            counters['unconditional_debt']+=1
            return None
        corrections.append(c)
    bad=[]
    for key,site,pred,k in candidates:
        c=cover(key,site,pred)
        if c is not None:
            corrections.append(c)
        else:
            bad.append(k)
    guard=minimal_guard(bad)
    # If full removal would work, use the smallest causal guard instead of
    # claiming conditional savings for an unrelated event.
    if guard is None:
        if bad:
            counters['no_common_guard']+=1
            return None
        guard=candidates[0][3][:1]
    for bit,v in guard:
        i=track[2][bit][v-1]
        if gates[i][0]!='HMR':
            counters['unsupported_initial_guard']+=1
            return None
    corrections=[c for c in corrections if not any(k in c['guards'] for k in guard)]
    if any(len(k)!=len(set(k)) for k,_,_ in events):
        return None
    return dict(start=start,end=end,run_on=guard,corrections=corrections,
                tagged_events=len(candidates),computing_gate=lines[start],pair=pair)

def compile_program(lines,gates,track,selected):
    before=defaultdict(list)
    after=defaultdict(list)
    count=max(int(i) for l in lines for i in re.findall(r'\bb(\d+)\b',l))+1
    for row in selected:
        i=row['start']
        skip=f'b{count}';run=f'b{count+1}';count+=2
        before[i]+=[f'BIT_STORE0 {skip}',f'BIT_INVERT {skip}']
        for bit,_ in row['run_on']:
            before[i]+=[f'PUSH_CONDITION if {bit}',f'BIT_STORE0 {skip}','POP_CONDITION']
        before[i]+=[f'BIT_STORE0 {run}',f'BIT_INVERT {run} if {skip}',f'BIT_INVERT {run}',
                    f'PUSH_CONDITION if {run}']
        after[i].append('POP_CONDITION')
        pair=row['pair']
        if pair is not None:
            before[pair].append(f'PUSH_CONDITION if {run}')
            after[pair].append('POP_CONDITION')
        for cor in row['corrections']:
            for site,term in cor['terms']:
                existing=set(track[3][k] for k in track[0][site])
                missing=set(map(tuple,cor['guards']))-existing
                extra=[]
                for bit,ver in sorted(missing):
                    windows=track[2][bit]
                    assert bisect_right(windows,site)==ver
                    extra.append(bit)
                after[site]+=[f'PUSH_CONDITION if {skip}']
                for b in extra:
                    after[site]+=[f'PUSH_CONDITION if {b}']
                after[site].append(term)
                after[site]+=['POP_CONDITION']*(1+len(extra))
    out=[]
    for i,l in enumerate(lines):
        out+=before[i]
        out.append(l)
        out+=after[i]
    return '\n'.join(out)+'\n'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--span',type=int,default=650)
    p.add_argument('--pairs',type=int,default=0)
    args=p.parse_args()
    assert sha256(args.source.read_bytes()).hexdigest()==PIN
    lines=str(km.Circuit.from_file(args.source,format='kmb')).splitlines()
    gates=list(map(parse,lines))
    rng=np.random.default_rng(94314)
    xs=np.unique(np.r_[np.arange(1,1200),rng.integers(1,DOMAIN+1,2100),DOMAIN]).astype(np.uint32)
    sample=list(make_trace(gates,xs))
    track=tracks_for(gates,lines)
    counters=Counter()
    hits=[]
    paid=[i for i,(op,_,_) in enumerate(gates) if op in PAID]
    for x,i in enumerate(paid):
        pairs=[None] if not args.pairs else [j for j in paid[x+1:x+1+args.pairs]
                    if track[0][i]==track[0][j] and j-i<300]
        for pair in pairs:
            found=trial(lines,gates,sample,xs,track,i,args.span,counters,pair)
            if found is not None:
                hits.append(found)
                print('sample candidate',i,pair,[k[0] for k in found['run_on']],len(found['corrections']),flush=True)
    print('counts',counters,'hits',len(hits),flush=True)
    valid=[]
    if hits:
        whole=np.arange(1,DOMAIN+1,dtype=np.uint32)
        needed={i for r in hits for i in range(r['start']-1,r['end']+1)}
        full={i:st for i,st in enumerate(make_trace(gates,whole)) if i in needed}
        for h in hits:
            v=find_cone(lines,gates,full,whole,track,h['start'],args.span,Counter(),pair=h['pair'],approved=h)
            if v is not None:
                print('full candidate',h['start'],len(h['run_on']),flush=True)
                valid.append(h)
    selected=[]
    for h in sorted(valid,key=lambda p:p['end']):
        if not selected or h['start']>selected[-1]['end']:
            selected.append(h)
    out=dict(source=PIN,samples=len(xs),counts=counters,proposals=hits,validated=valid,selected=selected)
    if selected:
        k=km.Circuit(compile_program(lines,gates,track,selected))
        assert k.num_qubits==46 and k.operation_statistics().num_toffoli_like==1550
        path=args.out.with_suffix('.kmb')
        k.to_file(path,format='kmb')
        out['candidate_sha']=sha256(path.read_bytes()).hexdigest()
    args.out.write_text(json.dumps(out,indent=2)+'\n')

if __name__=='__main__':
    main()
