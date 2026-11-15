#!/usr/bin/env python3
"""One saved AND plus an affine update; exact correction of its HMR phase.

Unlike exact-product hold chains, the later product may differ by any affine
function of retained live wires (excluding the dirty target). The cache routes
through known constant-zero/one slots. Search is bounded by existing free-slot
capacity, then every positive coefficient identity is proved on all legal x.
"""
from pathlib import Path
from bisect import bisect_left
import argparse,json,random,re,time
import score_invsqrt_retire as r
import score4_invsqrt_cache_route as route

def capacity(first,refs,constant,ones):
    def pick(t,exclude):
        best=None
        for q in range(46):
            if q==exclude or not(constant[t]>>q&1):continue
            k=bisect_left(refs[q],t);end=refs[q][k] if k<len(refs[q]) else len(constant)
            if end>t and (best is None or (end,q)>best):best=(end,q)
        return best
    choice=pick(first,None)
    if choice is None:return None
    until,holder=choice;plan=dict(first=first,initial_holder=holder,initial_constant=(ones[first]>>holder)&1,hops=[])
    while until<len(constant):
        choice=pick(until,holder)
        if choice is None:break
        end,new=choice;plan['hops'].append(dict(index=until,old=holder,new=new,old_constant=(ones[until]>>holder)&1,new_constant=(ones[until]>>new)&1))
        until,holder=end,new
    plan['end_exclusive']=until;return plan

def at_end(cap,last,ones):
    hops=[h for h in cap['hops'] if h['index']<=last];holder=hops[-1]['new'] if hops else cap['initial_holder']
    return dict(first=cap['first'],last=last,initial_holder=cap['initial_holder'],initial_constant=cap['initial_constant'],
                hops=hops,final_holder=holder,final_constant=(ones[last]>>holder)&1)

def affine_value(coeff,values,one):
    result=one if coeff&1 else 0
    for q in range(46):
        if coeff>>(q+1)&1:result^=values[q]
    return result

def execute(op,qs,values,domain,stack):
    if op=='PUSH_CONDITION':stack.append(values[:])
    elif op=='POP_CONDITION':old=stack.pop();assert old==values;values[:]=old
    else:r.advance(op,qs,values,domain)

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
    p.add_argument('--source',type=Path,default=Path(__file__).with_name('score3_invsqrt_cache.kmx'))
    p.add_argument('--expected-sha256',default=route.PIN);a=p.parse_args()
    if a.out.exists():raise FileExistsError(a.out)
    a.out.mkdir(parents=True);began=time.monotonic();base=Path(__file__).parent;source=a.source
    lines,ops,depth,refs,constant,ones,groups,ccx=route.profile(source,a.expected_sha256)
    gates=[i for i,(op,_) in enumerate(ops) if op=='CCX' and depth[i]==0 and ' if ' not in lines[i]]
    caps={i:cap for i in gates if (cap:=capacity(i,refs,constant,ones)) is not None}
    rng=random.Random(2026111504);samples=list(range(1,129))
    for k in range(1,23):
        lo=1<<(k-1);hi=min((1<<k)-1,r.MAX_X)
        if lo<=hi:samples += [rng.randrange(lo,hi+1) for _ in range(12)]
    samples=list(dict.fromkeys(samples))
    while len(samples)<512:
        x=rng.randrange(1,r.MAX_X+1)
        if x not in samples:samples.append(x)
    domain=(1<<len(samples))-1;values=[sum(((x>>q)&1)<<j for j,x in enumerate(samples)) for q in range(22)]+[0]*24
    stack=[];active=[];hits=[];queries=0
    for i,(op,qs) in enumerate(ops):
        if i in gates:
            active=[row for row in active if caps[row[0]]['end_exclusive']>i]
            left,right,target=qs;product=values[left]&values[right]
            basis=r.affine_basis([domain]+[0 if q==target else v for q,v in enumerate(values)])
            for first,oldproduct in active:
                queries+=1;coeff=r.solve(basis,product^oldproduct)
                if coeff is not None:
                    # Constant holder rows are redundant; force coefficient masks
                    # to avoid whichever holder this particular plan uses.
                    plan=at_end(caps[first],i,ones);holder=plan['final_holder']
                    if coeff>>(holder+1)&1:
                        coeff^=1<<(holder+1)
                        if ones[i]>>holder&1:coeff^=1
                    hits.append(dict(plan,affine_mask=coeff))
            if i in caps:active.append((i,product))
        execute(op,qs,values,domain,stack)
    assert not stack
    hits.sort(key=lambda p:(len(p['hops']),p['last']-p['first']))
    report=dict(status='BOUNDED_AFFINE_CACHE_SAMPLE_SEARCH_COMPLETE',source_sha256=route.sha(source),
                ccx=ccx,start_gates_with_capacity=len(caps),pair_queries=queries,samples=len(samples),sample_hits=len(hits),
                sample_seconds=time.monotonic()-began,hits=hits,
                scope='Consecutive or nonconsecutive unconditional CCX; a holder can route through existing constant slots. Later product XOR old product is affine in all current wire values except the dirty target. Original conditional blocks are atomic for holder routing.')
    (a.out/'profile.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='hits'},indent=2),flush=True)
    chosen=None;checks=[]
    if hits:
        # Full-domain simulation once, retaining only earlier products referenced
        # by sample hits. At each later cut solve the complete affine space exactly.
        wanted={h['first'] for h in hits};later={h['last'] for h in hits};stored={}
        bylast={i:[h for h in hits if h['last']==i] for i in later}
        domain,values=r.initial_values();stack=[]
        for i,(op,qs) in enumerate(ops):
            if i in wanted:stored[i]=values[qs[0]]&values[qs[1]]
            if i in later:
                left,right,target=qs;product=values[left]&values[right]
                basis=r.affine_basis([domain]+[0 if q==target else v for q,v in enumerate(values)])
                for plan in bylast[i]:
                    coeff=r.solve(basis,product^stored[plan['first']]);checks.append(dict(first=plan['first'],last=i,exists=coeff is not None))
                    if coeff is None:continue
                    holder=plan['final_holder']
                    if coeff>>(holder+1)&1:
                        coeff^=1<<(holder+1)
                        if ones[i]>>holder&1:coeff^=1
                    assert not(coeff>>(target+1)&1) and not(coeff>>(holder+1)&1)
                    assert affine_value(coeff,values,domain)==product^stored[plan['first']]
                    chosen=dict(plan,affine_mask=coeff);break
                if chosen:break
            execute(op,qs,values,domain,stack)
        assert not chosen or not stack
    report['exact_checks']=checks
    if chosen:
        first,last=chosen['first'],chosen['last'];linear=chosen['affine_mask'];holder=chosen['initial_holder']
        fresh=max(map(int,re.findall(r'\bb(\d+)\b',source.read_text())))+1
        hopmap={h['index']:h for h in chosen['hops']};patches={};prefixes={};output=[]
        for i,line in enumerate(lines):
            emitted=[]
            if i in hopmap:
                h=hopmap[i];old,new=h['old'],h['new'];assert holder==old
                if h['new_constant']:emitted.append(f'X q{new}')
                emitted += [f'CX q{old} q{new}',f'CX q{new} q{old}']
                if h['old_constant']:emitted.append(f'X q{old}')
                holder=new;prefixes[i]=emitted[:]
            if i==first:
                left,right,target=ops[i][1]
                if chosen['initial_constant']:emitted.append(f'X q{holder}')
                emitted += [f'CCX q{left} q{right} q{holder}',f'CX q{holder} q{target}']
            elif i==last:
                left,right,target=ops[i][1];emitted.append(f'CX q{holder} q{target}')
                if linear&1:emitted.append(f'X q{target}')
                emitted += [f'CX q{q} q{target}' for q in range(46) if linear>>(q+1)&1]
                emitted += [f'HMR q{holder} b{fresh}',f'CZ q{left} q{right} if b{fresh}']
                emitted += [f'Z q{q} if b{fresh}' for q in range(46) if linear>>(q+1)&1]
                if linear&1:emitted += [f'X q{left}',f'Z q{left} if b{fresh}',f'X q{left}',f'Z q{left} if b{fresh}']
                if chosen['final_constant']:emitted.append(f'X q{holder}')
            else:emitted.append(line)
            output+=emitted
            if emitted!=[line]:patches[i]=emitted
        kmx=a.out/'candidate.kmx';kmx.write_text('\n'.join(output)+'\n')
        domain,values=r.initial_values();stack=[]
        for op,qs in ops[:first]:execute(op,qs,values,domain,stack)
        assert not stack;actual=values[:];truth=values[ops[first][1][0]]&values[ops[first][1][1]];holder=None
        for i in range(first,last+1):
            op,qs=ops[i];emitted=patches.get(i,[lines[i]])
            if op=='PUSH_CONDITION':
                for line in prefixes.get(i,[]):r.advance(line.split()[0],tuple(map(int,re.findall(r'\bq(\d+)\b',line))),actual,domain)
                stack.append((values[:],actual[:]))
            elif op=='POP_CONDITION':old,new=stack.pop();assert old==values and new==actual;values,actual=old,new
            else:
                r.advance(op,qs,values,domain)
                for line in emitted:
                    kind=line.split()[0];qubits=tuple(map(int,re.findall(r'\bq(\d+)\b',line)))
                    if i==last and kind=='HMR':assert actual[qubits[0]]==truth==(actual[qs[0]]&actual[qs[1]])^affine_value(linear,actual,domain)
                    r.advance(kind,qubits,actual,domain)
            if i==first:holder=chosen['initial_holder']
            if i in hopmap:holder=hopmap[i]['new']
            if i<last:
                assert actual[holder]==truth
                assert all(v==w for q,(v,w) in enumerate(zip(values,actual)) if q!=holder)
            else:assert values==actual
        assert not stack
        import kickmix as km
        old=km.Circuit(source.read_text());new=km.Circuit(kmx.read_text());kmb=a.out/'candidate.kmb';new.to_file(kmb,format='kmb')
        assert new.num_qubits==old.num_qubits==46 and old.operation_statistics().num_toffoli_like-new.operation_statistics().num_toffoli_like==1
        rotations=lambda text:[l for l in text.splitlines() if l.split()[0].startswith('Z_POW') or l.split()[0].startswith('R')]
        assert rotations(source.read_text())==rotations(kmx.read_text())
        report.update(status='AFFINE_CACHE_CANDIDATE_EXACT_PASS',selected=chosen,patches=patches,
                      candidate_kmx=str(kmx),candidate_kmb=str(kmb),candidate_sha256=route.sha(kmb),
                      qubits=46,removed_unconditional_ccx=1,static_toffoli_before=1550,static_toffoli_after=1549,
                      proof='All legal inputs: later product = old product XOR affine(retained wires). The affine remainder excludes dirty target and holder. Every original phase and measurement sees the same values. The final HMR sign is canceled by CZ(controls) and Z(affine terms), including explicit constant phase, for both outcomes.',
                      original_rotation_sequence_identical=True,full_official_run=False)
    report['seconds']=time.monotonic()-began;report['script_sha256']=route.sha(Path(__file__))
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('hits','patches')},indent=2),flush=True)

if __name__=='__main__':main()
