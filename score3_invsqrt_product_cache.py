#!/usr/bin/env python3
"""Profile exact repeated CCX products, and cache one in a genuinely idle clean wire.

For a dirty original target t, CX(t,c); CCX(a,b,t); CX(t,c) copies a*b
to an initially zero cache c without an extra CCX. Later equal products can
use CX(c,t). At the last use HMR(c), followed by CZ(a,b) conditioned on its
fresh result, removes the cache with exact phase repayment. Original gates
must not reference c anywhere in the interval, including phase-only gates.
"""
from pathlib import Path
from collections import defaultdict
from bisect import bisect_left
import argparse,hashlib,json,re,time
import score_invsqrt_retire as r


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise FileExistsError(a.out)
    a.out.mkdir(parents=True);began=time.monotonic();base=Path(__file__).parent
    source=base/'invsqrt_structural_e46.kmx';lines,ops=r.instructions(source)
    domain,values=r.initial_values();stack=[];groups=defaultdict(list);masks=[];depth=[]
    refs=[[] for _ in range(46)];ccx=0
    for i,(op,qs) in enumerate(ops):
        masks.append(sum(1<<q for q,v in enumerate(values) if not v));depth.append(len(stack))
        for q in qs:refs[q].append(i)
        if op=='CCX' and not stack and ' if ' not in lines[i]:
            ccx+=1;left,right,target=qs;truth=values[left]&values[right]
            digest=hashlib.sha256(truth.to_bytes((r.MAX_X+8)//8,'little')).hexdigest()
            groups[digest].append(dict(index=i,left=left,right=right,target=target,nonzero=bool(truth)))
        if op=='PUSH_CONDITION':stack.append(values[:])
        elif op=='POP_CONDITION':before=stack.pop();assert before==values;values=before
        else:r.advance(op,qs,values,domain)
    assert not stack
    repeated=[(digest,rows) for digest,rows in groups.items() if len(rows)>1 and rows[0]['nonzero']]
    natural=[];packed=[]
    for digest,rows in repeated:
        for lo in range(len(rows)-1):
            first=rows[lo]['index']
            for q in range(46):
                if not(masks[first]>>q&1):continue
                k=bisect_left(refs[q],first);end=refs[q][k] if k<len(refs[q]) else len(ops)
                uses=[row for row in rows[lo:] if row['index']<end]
                if len(uses)>=2:
                    natural.append(dict(kind='NATURAL_CLEAN_IDLE_WIRE',cache=q,uses=uses,
                                        saved_ccx=len(uses)-1,added_ccx=0,net_saved_ccx=len(uses)-1,
                                        first=first,last=uses[-1]['index'],digest=digest))
        uses=[row for row in rows if 1635<=row['index']<3428]
        if len(uses)>=2:
            packed.append(dict(kind='H0_PACKED_CACHE',cache=0,uses=uses,saved_ccx=len(uses)-1,
                               added_ccx=2,net_saved_ccx=len(uses)-3,
                               first=uses[0]['index'],last=uses[-1]['index'],digest=digest))
    natural.sort(key=lambda x:(-x['net_saved_ccx'],x['last']-x['first'],x['cache']))
    packed.sort(key=lambda x:(-x['net_saved_ccx'],x['last']-x['first']))
    report=dict(status='EXACT_PRODUCT_CACHE_PROFILE_COMPLETE',source_sha256=sha(source),
                legal_inputs=r.MAX_X,unconditional_ccx=ccx,distinct_products=len(groups),
                repeated_nonzero_product_groups=len(repeated),natural_candidates=len(natural),
                natural_top=natural[:20],h0_repeated_products=packed,
                seconds=time.monotonic()-began,
                scope='Full valid-input product equality at depth-zero CCX. Cache must be zero at entry and entirely unreferenced by every original instruction through final use. Only one cache plan is built; no global optimality claim.')
    if natural:
        plan=natural[0];q=plan['cache'];uses={row['index'] for row in plan['uses']};first=plan['first'];last=plan['last']
        fresh=max(map(int,re.findall(r'\bb(\d+)\b',source.read_text())))+1
        output=[]
        for i,line in enumerate(lines):
            if i==first:
                target=ops[i][1][2];output += [f'CX q{target} q{q}',line,f'CX q{target} q{q}']
            elif i in uses:output.append(f'CX q{q} q{ops[i][1][2]}')
            else:output.append(line)
            if i==last:
                left,right,_=ops[i][1]
                output += [f'HMR q{q} b{fresh}',f'CZ q{left} q{right} if b{fresh}']
        # Exact gatewise data equality and the only new phase predicate.
        domain,values=r.initial_values();cached=values[:];stack=[];truth=None;checked=0
        for i,(op,qs) in enumerate(ops):
            if i==first:
                assert cached[q]==0 and values[q]==0
                left,right,target=qs;truth=values[left]&values[right]
                cached[q]^=cached[target];r.advance(op,qs,cached,domain);cached[q]^=cached[target]
                r.advance(op,qs,values,domain);assert cached[q]==truth
            elif i in uses:
                left,right,target=qs;assert values[left]&values[right]==truth
                cached[target]^=cached[q];r.advance(op,qs,values,domain);checked+=1
            elif op=='PUSH_CONDITION':stack.append((values[:],cached[:]))
            elif op=='POP_CONDITION':
                old,new=stack.pop();assert old==values and new==cached;values,cached=old,new
            else:r.advance(op,qs,values,domain);r.advance(op,qs,cached,domain)
            if i==last:
                left,right,_=qs;assert cached[q]==cached[left]&cached[right]
                cached[q]=0
            assert all(v==w for j,(v,w) in enumerate(zip(values,cached)) if j!=q)
            if not(first<=i<last):assert values==cached
        assert not stack and checked==plan['saved_ccx']
        kmx=a.out/'candidate.kmx';kmx.write_text('\n'.join(output)+'\n')
        import kickmix as km
        original=km.Circuit(source.read_text());candidate=km.Circuit(kmx.read_text())
        kmb=a.out/'candidate.kmb';candidate.to_file(kmb,format='kmb')
        removed=int(original.operation_statistics().num_toffoli_like-candidate.operation_statistics().num_toffoli_like)
        assert removed==plan['saved_ccx'] and candidate.num_qubits==original.num_qubits==46
        report.update(status='EXACT_PRODUCT_CACHE_CANDIDATE_PASS',plan=plan,
                      candidate_kmx=str(kmx),candidate_kmb=str(kmb),candidate_sha256=sha(kmb),
                      candidate_qubits=46,removed_unconditional_ccx=removed,
                      proof=dict(all_3133452_inputs_gatewise_equal_except_idle_cache=True,
                                 original_measurement_predicates_unchanged=True,
                                 fresh_measurement_phase='cache = final_original_control_a AND final_original_control_b; HMR sign canceled by conditioned CZ',
                                 all_measurement_branches=True,full_official_run=False))
    report['script_sha256']=sha(Path(__file__));report['seconds']=time.monotonic()-began
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':main()
