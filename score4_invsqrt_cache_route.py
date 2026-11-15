#!/usr/bin/env python3
"""Route an exact repeated product through existing constant-zero/one slots.

The public ancestor's hold_pass.py already implements holder hopping. This
bounded application to submitted 684106 additionally permits constant-one slots
and excludes gate operands only when they are used, not for the whole chain.
Classical conditional blocks are indivisible reference barriers. No circuit
precision, HMR outcome, or legal input is modified for the search.
"""
from pathlib import Path
from collections import defaultdict,Counter
from bisect import bisect_left
import argparse,hashlib,json,re,time
import score_invsqrt_retire as r

PIN='d431f212c7da02418429c2883dcdf4e3a90c9124ab2409c999efe0a5c7c037a8'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def profile(source,expected_sha256=PIN):
    lines,ops=r.instructions(source);assert sha(source)==expected_sha256
    refs=[[] for _ in range(46)];stack=[];block_at=[];depth=[]
    for i,(op,qs) in enumerate(ops):
        depth.append(len(stack))
        if op=='PUSH_CONDITION':stack.append(i)
        effective=stack[0] if stack else i;block_at.append(effective)
        for q in qs:
            if not refs[q] or refs[q][-1]!=effective:refs[q].append(effective)
        if op=='POP_CONDITION':stack.pop()
    assert not stack
    domain,values=r.initial_values();groups=defaultdict(list);constant=[];ones=[];ccx=0
    for i,(op,qs) in enumerate(ops):
        zm=sum(1<<q for q,v in enumerate(values) if not v)
        om=sum(1<<q for q,v in enumerate(values) if v==domain)
        constant.append(zm|om);ones.append(om)
        if op=='CCX' and not stack and ' if ' not in lines[i]:
            ccx+=1;left,right,target=qs;truth=values[left]&values[right]
            if truth:
                digest=hashlib.sha256(truth.to_bytes((r.MAX_X+8)//8,'little')).hexdigest()
                groups[digest].append(dict(index=i,left=left,right=right,target=target))
        if op=='PUSH_CONDITION':stack.append(values[:])
        elif op=='POP_CONDITION':old=stack.pop();assert old==values;values=old
        else:r.advance(op,qs,values,domain)
    return lines,ops,depth,refs,constant,ones,groups,ccx

def plan_pair(first,last,depth,refs,constant,ones):
    def pick(t,exclude):
        choices=[]
        for q in range(46):
            if q==exclude or not(constant[t]>>q&1):continue
            k=bisect_left(refs[q],t);end=refs[q][k] if k<len(refs[q]) else len(depth)
            if end>t:choices.append((end,q))
        return max(choices) if choices else None
    choice=pick(first,None)
    if choice is None:return None,dict(reason='NO_START_SLOT',cut=first)
    until,holder=choice;start_holder=holder;hops=[]
    while until<=last:
        assert depth[until]==0
        choice=pick(until,holder)
        if choice is None:return None,dict(reason='NO_TRANSFER_SLOT',cut=until,holder=holder,constant_slots=constant[until])
        nxt,new=choice
        hops.append(dict(index=until,old=holder,new=new,old_constant=(ones[until]>>holder)&1,new_constant=(ones[until]>>new)&1))
        until,holder=nxt,new
    return dict(first=first,last=last,initial_holder=start_holder,initial_constant=(ones[first]>>start_holder)&1,
                final_holder=holder,final_constant=(ones[last]>>holder)&1,hops=hops),None

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
    p.add_argument('--source',type=Path,default=Path(__file__).with_name('score3_invsqrt_cache.kmx'))
    p.add_argument('--expected-sha256',default=PIN);a=p.parse_args()
    if a.out.exists():raise FileExistsError(a.out)
    a.out.mkdir(parents=True);base=Path(__file__).parent;source=a.source;began=time.monotonic()
    lines,ops,depth,refs,constant,ones,groups,ccx=profile(source,a.expected_sha256)
    plans=[];failures=[]
    for digest,rows in groups.items():
        for first,last in zip(rows,rows[1:]):
            plan,failure=plan_pair(first['index'],last['index'],depth,refs,constant,ones)
            if plan:plans.append(dict(plan,digest=digest,first_gate=first,last_gate=last))
            else:failures.append(dict(first=first['index'],last=last['index'],**failure))
    plans.sort(key=lambda p:(len(p['hops']),p['last']-p['first']))
    report=dict(status='BOUNDED_ROUTE_PROFILE_COMPLETE',source_sha256=sha(source),legal_inputs=r.MAX_X,
                unconditional_ccx=ccx,distinct_nonzero_products=len(groups),pairs_tested=len(plans)+len(failures),
                feasible_pairs=len(plans),plans=plans,failures=failures,profile_seconds=time.monotonic()-began,
                scope='Consecutive depth-zero equal-product CCX pairs; exact full-domain truth; existing constant-zero/one slots with transfers outside atomic conditional blocks; no whole-circuit optimality claim.')
    (a.out/'profile.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('plans','failures')},indent=2),flush=True)
    if plans:
        plan=plans[0];first,last=plan['first'],plan['last'];fresh=max(map(int,re.findall(r'\bb(\d+)\b',source.read_text())))+1
        hopmap={h['index']:h for h in plan['hops']};holder=plan['initial_holder'];output=[];patches={};prefixes={}
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
                if plan['initial_constant']:emitted.append(f'X q{holder}')
                emitted += [f'CCX q{left} q{right} q{holder}',f'CX q{holder} q{target}']
            elif i==last:
                left,right,target=ops[i][1]
                emitted += [f'CX q{holder} q{target}',f'HMR q{holder} b{fresh}',f'CZ q{left} q{right} if b{fresh}']
                if plan['final_constant']:emitted.append(f'X q{holder}')
            else:emitted.append(line)
            output+=emitted
            if emitted!=[line]:patches[i]=emitted
        kmx=a.out/'candidate.kmx';kmx.write_text('\n'.join(output)+'\n')
        # Only the bounded changed interval needs duplicate state evaluation.
        domain,values=r.initial_values();stack=[]
        for op,qs in ops[:first]:
            if op=='PUSH_CONDITION':stack.append(values[:])
            elif op=='POP_CONDITION':old=stack.pop();assert old==values;values=old
            else:r.advance(op,qs,values,domain)
        assert not stack;actual=values[:];truth=values[ops[first][1][0]]&values[ops[first][1][1]];holder=None
        for i in range(first,last+1):
            op,qs=ops[i]
            emitted=patches.get(i,[lines[i]])
            if op=='PUSH_CONDITION':
                for line in prefixes.get(i,[]):r.advance(line.split()[0],tuple(map(int,re.findall(r'\bq(\d+)\b',line))),actual,domain)
                stack.append((values[:],actual[:]))
            elif op=='POP_CONDITION':old,new=stack.pop();assert old==values and new==actual;values,actual=old,new
            else:
                r.advance(op,qs,values,domain)
                for line in emitted:
                    kind=line.split()[0];qubits=tuple(map(int,re.findall(r'\bq(\d+)\b',line)))
                    if i==last and kind=='HMR':assert actual[qubits[0]]==truth==actual[qs[0]]&actual[qs[1]]
                    r.advance(kind,qubits,actual,domain)
            if i==first:holder=plan['initial_holder']
            if i in hopmap:holder=hopmap[i]['new']
            if i<last:
                assert actual[holder]==truth
                assert all(v==w for q,(v,w) in enumerate(zip(values,actual)) if q!=holder)
            else:assert values==actual
        assert not stack
        import kickmix as km
        old=km.Circuit(source.read_text());new=km.Circuit(kmx.read_text());kmb=a.out/'candidate.kmb';new.to_file(kmb,format='kmb')
        assert new.num_qubits==old.num_qubits==46
        assert old.operation_statistics().num_toffoli_like-new.operation_statistics().num_toffoli_like==1
        rotations=lambda text:[l for l in text.splitlines() if l.split()[0].startswith('Z_POW') or l.split()[0].startswith('R')]
        assert rotations(source.read_text())==rotations(kmx.read_text())
        report.update(status='ROUTED_CACHE_CANDIDATE_EXACT_PASS',selected=plan,patches=patches,
                      candidate_kmx=str(kmx),candidate_kmb=str(kmb),candidate_sha256=sha(kmb),
                      qubits=46,removed_unconditional_ccx=1,static_toffoli_before=1550,static_toffoli_after=1549,
                      proof='All legal inputs: at every original operation all non-holder values agree, the holder equals the first product; original phase/measurement operands never reference the holder. The final product equals the holder so the new HMR phase is canceled by CZ for each outcome. Original conditional blocks retain their entry/exit identity.',
                      original_rotation_sequence_identical=True,full_official_run=False)
    report['seconds']=time.monotonic()-began;report['script_sha256']=sha(Path(__file__))
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('plans','failures','patches')},indent=2),flush=True)

if __name__=='__main__':main()
