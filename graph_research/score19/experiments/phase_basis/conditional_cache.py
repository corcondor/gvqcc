#!/usr/bin/env python3
"""Find charged reductions by carrying an unconditional product into a later branch."""
import argparse
from bisect import bisect_left
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re

import numpy as np
import kickmix as km

from quadratic_phase import MAX_X, SOURCE_SHA, advance, columns, gate

def info(lines, ops):
    children = {}
    stack = []
    owner = []
    reference = [[] for _ in range(46)]
    for i, (op, qs) in enumerate(ops):
        owner.append(stack[0] if stack else None)
        if op=='PUSH_CONDITION':
            stack.append(i)
        reference_cut = stack[0] if stack else i
        for q in qs:
            if not reference[q] or reference[q][-1]!=reference_cut:
                reference[q].append(reference_cut)
        if op=='POP_CONDITION':
            children[stack.pop()]=i
    return children, owner, reference

def enumerate_sample(lines, ops, children, owner, reference, xs, distance):
    mask=(1<<len(xs))-1
    w=columns(xs)
    groups=defaultdict(list)
    target=[]
    const=[]
    states={}
    by_anchor=defaultdict(list)
    for i,(op,qs) in enumerate(ops):
        const.append(sum(1<<q for q,v in enumerate(w) if v in (0,mask)))
        if op=='CCX':
            a,b,q=qs
            z=w[a]&w[b]
            if z:
                if owner[i] is None:
                    groups[z].append((i,qs))
                else:
                    for p, before in groups[z]:
                        if i-p <= distance:
                            target.append((p,i))
                            by_anchor[p].append(i)
                    states[i]=w[:]
        if i in children:
            states[i]=w[:]
        if i in by_anchor:
            states[i]=w[:]
        advance(op,qs,w,mask)
    affected={q for p,i in target for q in range(p,children[owner[i]]+2)}
    w=columns(xs)
    for i,(op,qs) in enumerate(ops):
        if i in affected:
            states[i]=w[:]
        advance(op,qs,w,mask)
    return target,const,states,mask

def best_route(start, stop, reserved, const, states, ref, mask):
    def pick(at,exclude):
        choices=[]
        for q,uses in enumerate(ref):
            if q in exclude or not const[at]>>q&1:
                continue
            k=bisect_left(uses,at)
            until=uses[k] if k<len(uses) else len(const)
            if until>at:
                choices.append((until,q))
        return max(choices,default=(at,None))
    until,holder=pick(start,reserved)
    if holder is None:
        return None
    entry=(holder,int(bool(states[start][holder])))
    hops=[]
    while until < stop:
        end,new=pick(until,{holder})
        if new is None:
            return None
        hops.append((until,holder,new,int(bool(states[until][holder])),int(bool(states[until][new]))))
        until,holder=end,new
    return entry, hops, (holder,int(bool(states[stop][holder])))

def candidates(lines,ops,children,owner,refs, xs,distance):
    target,const,states,mask=enumerate_sample(lines,ops,children,owner,refs,xs,distance)
    plans=[]
    for p,i in target:
        begin=owner[i]
        stop=children[begin]+1
        a,b,t=ops[p][1]
        pred=states[p][a]&states[p][b]
        corrections=[]
        for q,v in enumerate(states[stop]):
            if v==pred:
                corrections.append((q,))
            for r,u in enumerate(states[stop][:q]):
                if v&u==pred:
                    corrections.append((q,r))
        if not corrections:
            continue
        for j in range(begin-1,p,-1):
            if owner[j] is not None or ops[j][0]=='POP_CONDITION':
                continue
            suitable=[(q,int(v!=pred)) for q,v in enumerate(states[j]) if v in (pred,pred^mask)]
            if not suitable:
                continue
            route=best_route(j,stop,{q for q,_ in suitable},const,states,refs,mask)
            if route:
                plans.append(dict(producer=p, consumer=i, branch_begin=begin, branch_end=stop,
                                  start=j, source=suitable[0], correction=corrections[0], route=route))
                break
        else:
            route=best_route(p,stop,{a,b,t},const,states,refs,mask)
            if route:
                plans.append(dict(producer=p, consumer=i, branch_begin=begin, branch_end=stop,
                                  start=p, source=None, correction=corrections[0], route=route))
    return plans,len(target)

def verify_and_build(lines,ops,plans):
    xs=np.arange(1,MAX_X+1,dtype=np.uint32)
    mask=(1<<len(xs))-1
    baseline=columns(xs)
    selected_cuts={q for plan in plans for q in (plan['producer'],plan['start'],plan['consumer'],plan['branch_end'],*(v[0] for v in plan['route'][1]))}
    states={}
    for i,(op,qs) in enumerate(ops):
        if i in selected_cuts:
            states[i]=baseline[:]
        advance(op,qs,baseline,mask)
    last=-1
    inserts={}
    replacements={}
    fresh=max(int(x) for l in lines for x in re.findall(r'\bb(\d+)\b',l))+1
    results=[]
    for plan in sorted(plans,key=lambda r:r['branch_end']):
        p,i,j,stop=(plan[k] for k in ('producer','consumer','start','branch_end'))
        if j<=last:
            continue
        initial,hops,final=plan['route']
        h,k=initial
        a,b,t=ops[p][1]
        pred=states[p][a]&states[p][b]
        c,d,target=ops[i][1]
        if pred!=states[i][c]&states[i][d] or states[j][h]!=(mask if k else 0):
            continue
        corr=mask
        for q in plan['correction']:
            corr &= states[stop][q]
        if corr!=pred or final[0] in plan['correction']:
            continue
        if plan['source'] is not None:
            q, inverted=plan['source']
            if states[j][q] != pred^(mask if inverted else 0):
                continue
        if any(states[l][old]!=(mask if old_k else 0) or states[l][new]!=(mask if new_k else 0)
               for l,old,new,old_k,new_k in hops):
            continue
        actual=states[j][:]
        original=states[j][:]
        local_inserts={}
        local_repl={}
        work=[]
        if k:
            work.append(f'X q{h}')
        if plan['source'] is None:
            assert j==p
            local_repl[j]=work+[f'CCX q{a} q{b} q{h}',f'CX q{h} q{t}']
        else:
            q,inverted=plan['source']
            work += [f'CX q{q} q{h}']
            if inverted:
                work.append(f'X q{h}')
            local_inserts[j]=work
        for pos,old,new,old_k,new_k in hops:
            work=([f'X q{new}'] if new_k else [])+[f'CX q{old} q{new}',f'CX q{new} q{old}']
            if old_k:
                work += [f'X q{old}']
            assert pos not in local_inserts
            local_inserts[pos]=work
        h_end,k_end=final
        local_repl[i]=[f'CX q{h_end} q{target}']
        tag=f'b{fresh}'
        name='CZ' if len(plan['correction'])==2 else 'Z'
        coords=' '.join(f'q{q}' for q in plan['correction'])
        assert stop not in local_inserts
        local_inserts[stop]=[f'HMR q{h_end} {tag}',f'{name} {coords} if {tag}']+([f'X q{h_end}'] if k_end else [])
        active=h
        hop_at={v[0]:v[2] for v in hops}
        for l in range(j,stop+1):
            for op,qs in map(gate,local_inserts.get(l,[])):
                advance(op,qs,actual,mask)
            if l in hop_at:
                active=hop_at[l]
            if l==stop:
                assert actual==original
                break
            op,qs=ops[l]
            if l not in local_repl:
                assert (l==j and not local_inserts.get(l)) or active not in qs
                advance(op,qs,actual,mask)
            else:
                for newop,newqs in map(gate,local_repl[l]):
                    advance(newop,newqs,actual,mask)
            advance(op,qs,original,mask)
            assert all(value==target for q,(value,target) in enumerate(zip(actual,original)) if q!=active)
            assert actual[active]==pred
        inserts.update(local_inserts)
        replacements.update(local_repl)
        results.append(plan)
        last=stop
        fresh+=1
    if not results:
        return None,[]
    result=[]
    for i,l in enumerate(lines):
        result.extend(inserts.get(i,[]))
        result.extend(replacements.get(i,[l]))
    return '\n'.join(result)+'\n',results

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path, required=True)
    p.add_argument('--output',type=Path, required=True)
    p.add_argument('--distance',type=int,default=600)
    args=p.parse_args()
    assert hashlib.sha256(args.source.read_bytes()).hexdigest()==SOURCE_SHA
    lines=str(km.Circuit.from_file(args.source,format='kmb')).splitlines()
    ops=list(map(gate,lines))
    info0=info(lines,ops)
    rng=np.random.default_rng(668)
    xs=np.unique(np.r_[np.arange(1,500),rng.integers(1,MAX_X+1,2500),MAX_X]).astype(np.uint32)
    plans,pairs=candidates(lines,ops,*info0,xs,args.distance)
    print('matching pairs',pairs,'feasible routes',len(plans),flush=True)
    data=dict(source=SOURCE_SHA, sample_pairs=pairs, sample_routes=plans, legal_inputs=MAX_X)
    if plans:
        kmx, matches = verify_and_build(lines,ops,plans)
        data['selected']=matches
        if matches:
            c=km.Circuit(kmx)
            assert c.num_qubits==46 and c.operation_statistics().num_toffoli_like==1550-len(matches)
            kmb=args.output.with_suffix('.kmb')
            c.to_file(kmb,format='kmb')
            data['candidate_sha']=hashlib.sha256(kmb.read_bytes()).hexdigest()
            print('candidate',len(matches),data['candidate_sha'],flush=True)
    args.output.write_text(json.dumps(data,indent=2)+'\n')

if __name__=='__main__':
    main()
