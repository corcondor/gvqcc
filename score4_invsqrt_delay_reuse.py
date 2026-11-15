#!/usr/bin/env python3
"""Delay an HMR cleanup, retaining its value for a later AND target.

Only a dead classical outcome used exclusively by unconditional inline
Z/CZ/CCZ/NEG corrections is eligible. Its entire phase coefficient must equal
the measured value exactly. The measurement and those corrections can then be
deferred together. A later CCX consumes the held value, possibly with an affine
update, or uses it and performs one new correctly compensated HMR.
"""
from pathlib import Path
from bisect import bisect_left
from collections import defaultdict,Counter
import argparse,json,re,time,random
import score_invsqrt_retire as r
import score4_invsqrt_cache_route as route
from score4_invsqrt_affine_cache import affine_value,execute

def cleanup_records(lines,ops,depth):
    uses=defaultdict(list)
    for i,line in enumerate(lines):
        for bit in set(re.findall(r'\bb\d+\b',line)):uses[bit].append(i)
    result=[];rejected=Counter()
    for i,(op,qs) in enumerate(ops):
        if op!='HMR' or depth[i] or ' if ' in lines[i]:continue
        tokens=lines[i].split();bit=tokens[2];phases=[];bad=None;overwrite=None
        for j in uses[bit][bisect_left(uses[bit],i+1):]:
            words=lines[j].split();kind=words[0]
            if kind=='HMR' and words[2]==bit and not depth[j] and ' if ' not in lines[j]:overwrite=j;break
            if kind=='BIT_STORE0' and words[1]==bit and not depth[j] and ' if ' not in lines[j]:overwrite=j;break
            if kind in ('Z','CZ','CCZ','NEG') and depth[j]==0 and words[-2:]==['if',bit]:phases.append(j)
            else:bad=kind;break
        if bad:rejected[bad]+=1;continue
        result.append(dict(index=i,wire=qs[0],bit=bit,phase_indices=phases,next_overwrite=overwrite))
    return result,dict(rejected)

def capacity(record,ops,depth,refs,constant,ones):
    first=record['index'];holder=record['wire'];ignore=set(record.get('remove_indices',record['phase_indices']))
    def next_ref(q,t):
        k=bisect_left(refs[q],t)
        while k<len(refs[q]) and refs[q][k] in ignore:k+=1
        return refs[q][k] if k<len(refs[q]) else len(ops)
    def pick(t,exclude):
        best=None
        for q in range(46):
            if q==exclude or not(constant[t]>>q&1):continue
            end=next_ref(q,t)
            if end>t and (best is None or (end,q)>best):best=(end,q)
        return best
    until=next_ref(holder,first+1);hops=[];consumes=[]
    while until<len(ops):
        assert depth[until]==0
        if ops[until][0]=='CCX' and ' if ' not in source_lines[until] and ops[until][1][2]==holder:
            consumes.append(dict(last=until,holder=holder,hops=hops[:]))
        choice=pick(until,holder)
        if choice is None:break
        end,new=choice
        hops.append(dict(index=until,old=holder,new=new,old_constant=(ones[until]>>holder)&1,new_constant=(ones[until]>>new)&1))
        until,holder=end,new
    return dict(end_exclusive=until,hops=hops,consumes=consumes)

def plan_at(record,cap,last,ones,consume=None):
    hops=consume['hops'] if consume else [h for h in cap['hops'] if h['index']<=last]
    holder=hops[-1]['new'] if hops else record['wire']
    return dict(cleanup=record,first=record['index'],last=last,hops=hops,final_holder=holder,
                final_constant=(ones[last]>>holder)&1,consume=consume is not None)

def phase_value(kind,qs,values,one):
    if kind=='NEG':return one
    value=one
    for q in qs:value&=values[q]
    return value

def main():
    global source_lines
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
    p.add_argument('--source',type=Path,default=Path(__file__).with_name('score3_invsqrt_cache.kmx'))
    p.add_argument('--expected-sha256',default=route.PIN);p.add_argument('--allow-blocks',action='store_true');a=p.parse_args()
    if a.out.exists():raise FileExistsError(a.out)
    a.out.mkdir(parents=True);began=time.monotonic();base=Path(__file__).parent;source=a.source
    lines,ops,depth,refs,constant,ones,groups,ccx=route.profile(source,a.expected_sha256);source_lines=lines
    extractor=cleanup_records
    if a.allow_blocks:
        from score4_invsqrt_block_cleanup import cleanup_records as extractor
    records,rejected=extractor(lines,ops,depth);recmap={rec['index']:rec for rec in records}
    caps={rec['index']:capacity(rec,ops,depth,refs,constant,ones) for rec in records}
    correction_owners={j:rec['index'] for rec in records for j in rec['phase_indices']}
    nonconstant_owners=defaultdict(list)
    for rec in records:
        for monomial,indices in rec.get('nonconstant_phase_terms',{}).items():
            for j in indices:nonconstant_owners[j].append((rec['index'],monomial))
    rng=random.Random(2026111504);samples=list(range(1,129))
    for k in range(1,23):
        lo=1<<(k-1);hi=min((1<<k)-1,r.MAX_X)
        if lo<=hi:samples += [rng.randrange(lo,hi+1) for _ in range(12)]
    samples=list(dict.fromkeys(samples))
    while len(samples)<512:
        x=rng.randrange(1,r.MAX_X+1)
        if x not in samples:samples.append(x)
    domain=(1<<len(samples))-1;values=[sum(((x>>q)&1)<<j for j,x in enumerate(samples)) for q in range(22)]+[0]*24
    stack=[];held={};correction=defaultdict(int);nonconstant=defaultdict(int);active=[];hits=[];queries=0
    consume_at=defaultdict(list)
    for first,cap in caps.items():
        for consume in cap['consumes']:consume_at[consume['last']].append((first,consume))
    for i,(op,qs) in enumerate(ops):
        if i in correction_owners:correction[correction_owners[i]]^=phase_value(op,qs,values,domain)
        for owner in nonconstant_owners.get(i,[]):nonconstant[owner]^=phase_value(op,qs,values,domain)
        if op=='CCX' and depth[i]==0 and ' if ' not in lines[i]:
            active=[first for first in active if caps[first]['end_exclusive']>i]
            left,right,target=qs;product=values[left]&values[right]
            basis=r.affine_basis([domain]+[0 if q==target else v for q,v in enumerate(values)])
            tests=[(first,None) for first in active]+consume_at[i]
            for first,consume in tests:
                if not held[first]:continue
                queries+=1;coeff=r.solve(basis,product^held[first])
                if coeff is None:continue
                plan=plan_at(recmap[first],caps[first],i,ones,consume)
                holder=plan['final_holder']
                if coeff>>(holder+1)&1:
                    coeff^=1<<(holder+1)
                    if ones[i]>>holder&1:coeff^=1
                hits.append(dict(plan,affine_mask=coeff))
        if i in recmap:
            held[i]=values[qs[0]]
            if caps[i]['end_exclusive']>i+1:active.append(i)
        execute(op,qs,values,domain,stack)
    assert not stack
    before=len(hits);hits=[h for h in hits if correction[h['first']]==held[h['first']] and all(nonconstant[(h['first'],key)]==0 for key in h['cleanup'].get('nonconstant_phase_terms',{}))]
    hits.sort(key=lambda h:(not h['consume'],len(h['hops']),h['last']-h['first']))
    report=dict(status='DELAY_REUSE_BOUNDED_SAMPLE_COMPLETE',source_sha256=route.sha(source),
                eligible_cleanup_groups=len(records),rejected_classical_uses=rejected,pair_queries=queries,
                sample_hits_before_cleanup_proof=before,sample_hits=len(hits),samples=len(samples),
                sample_seconds=time.monotonic()-began,hits=hits,allow_blocks=a.allow_blocks,
                scope=('Full-lifetime inline corrections and closed conditional cleanup blocks with symbolically tracked internal measurements. ' if a.allow_blocks else 'Only full-lifetime inline Clifford/CCZ cleanup outcomes. ')+'Holder routes through existing constant slots; later product differs by an arbitrary affine function excluding its dirty target. Consume-in-target endpoints are permitted; no input-selective behavior.')
    (a.out/'profile.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='hits'},indent=2),flush=True)
    chosen=None;checks=[]
    # Check at most the first 20 distinct sample plans, each on the entire domain.
    for plan in hits[:20]:
        first,last=plan['first'],plan['last'];phase_ids=set(plan['cleanup']['phase_indices'])
        terms=plan['cleanup'].get('nonconstant_phase_terms',{});term_at=defaultdict(list);term_values=defaultdict(int)
        for key,indices in terms.items():
            for j in indices:term_at[j].append(key)
        limit=max({last}|phase_ids|set(term_at));domain,values=r.initial_values();stack=[];truth=None;phase=0;coeff=None
        for i,(op,qs) in enumerate(ops[:limit+1]):
            if i==first:truth=values[qs[0]]
            if i in phase_ids:phase^=phase_value(op,qs,values,domain)
            for key in term_at.get(i,[]):term_values[key]^=phase_value(op,qs,values,domain)
            if i==last:
                left,right,target=qs
                basis=r.affine_basis([domain]+[0 if q in (target,plan['final_holder']) else v for q,v in enumerate(values)])
                coeff=r.solve(basis,(values[left]&values[right])^truth)
            execute(op,qs,values,domain,stack)
        assert not stack
        phase_ok=truth==phase and all(v==0 for v in term_values.values())
        ok=coeff is not None and phase_ok
        checks.append(dict(first=first,last=last,affine_exists=coeff is not None,cleanup_phase_equal=truth==phase,internal_measurement_phase_terms_vanish=all(v==0 for v in term_values.values())))
        if ok:chosen=dict(plan,affine_mask=coeff);break
    report['exact_checks']=checks
    if chosen:
        first,last=chosen['first'],chosen['last'];linear=chosen['affine_mask'];holder=chosen['cleanup']['wire']
        fresh=max(map(int,re.findall(r'\bb(\d+)\b',source.read_text())))+1;remove_phases=set(chosen['cleanup'].get('remove_indices',chosen['cleanup']['phase_indices']))
        hopmap={h['index']:h for h in chosen['hops']};output=[];patches={};prefixes={}
        for i,line in enumerate(lines):
            emitted=[]
            if i in hopmap:
                h=hopmap[i];old,new=h['old'],h['new'];assert holder==old
                if h['new_constant']:emitted.append(f'X q{new}')
                emitted += [f'CX q{old} q{new}',f'CX q{new} q{old}']
                if h['old_constant']:emitted.append(f'X q{old}')
                holder=new;prefixes[i]=emitted[:]
            if i==first or i in remove_phases:pass
            elif i==last:
                left,right,target=ops[i][1]
                if chosen['consume']:
                    assert holder==target
                    if chosen['final_constant']^(linear&1):emitted.append(f'X q{target}')
                    emitted += [f'CX q{q} q{target}' for q in range(46) if linear>>(q+1)&1]
                else:
                    emitted.append(f'CX q{holder} q{target}')
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
        assert not stack;actual=values[:];truth=values[ops[first][1][0]];holder=chosen['cleanup']['wire']
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
            if i in hopmap:holder=hopmap[i]['new']
            if i in remove_phases and depth[i]>0:continue
            if i<last:
                assert actual[holder]==truth
                assert all(v==w for q,(v,w) in enumerate(zip(values,actual)) if q!=holder)
            else:assert values==actual
        assert not stack
        import kickmix as km
        old=km.Circuit(source.read_text());new=km.Circuit(kmx.read_text());kmb=a.out/'candidate.kmb';new.to_file(kmb,format='kmb')
        saved=int(old.operation_statistics().num_toffoli_like-new.operation_statistics().num_toffoli_like)
        assert new.num_qubits==old.num_qubits==46 and saved>=1
        rotations=lambda text:[l for l in text.splitlines() if l.split()[0].startswith('Z_POW') or l.split()[0].startswith('R')]
        assert rotations(source.read_text())==rotations(kmx.read_text())
        report.update(status='DELAYED_CLEANUP_REUSE_EXACT_PASS',selected=chosen,patches=patches,
                      candidate_kmx=str(kmx),candidate_kmb=str(kmb),candidate_sha256=route.sha(kmb),
                      qubits=46,removed_unconditional_ccx=1,removed_static_toffoli=saved,
                      static_toffoli_before=int(old.operation_statistics().num_toffoli_like),static_toffoli_after=int(new.operation_statistics().num_toffoli_like),
                      proof='The removed HMR outcome is read only by removed inline corrections or closed conditional correction blocks until its next unconditional overwrite. Internal measurement versions are dead outside the removed cleanup; every nonconstant measurement-monomial phase coefficient vanishes. The remaining phase predicate exactly equals the measured value on all 3133452 inputs, so the complete cleanup has zero phase for either outcome. Retaining its value, routing it, and consuming/releasing it at the later CCX preserves all other original values; any new HMR is exactly corrected.',
                      original_rotation_sequence_identical=True,full_official_run=False)
    report['seconds']=time.monotonic()-began;report['script_sha256']=route.sha(Path(__file__))
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('hits','patches')},indent=2),flush=True)

if __name__=='__main__':main()
