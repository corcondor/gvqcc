#!/usr/bin/env python3
"""Bounded search for one-CCX idle-wire packing into disjoint exponent flags.

Seek g in the affine spans at BOTH endpoints with g=q on f2 OR f3.
Then q'=q XOR g can be packed into (f2 XOR q', f3 XOR q') and measured;
q' equals the packed flags' AND. One CCX restores it at the end, followed
by the endpoint expression for g. This is nonlinear encoding, not deletion.
"""
from __future__ import annotations
import argparse,json,re,time,hashlib,bisect
from pathlib import Path
import score_invsqrt_retire as r


def xor_columns(columns,coefficients):
    result=0
    while coefficients:
        bit=coefficients&-coefficients
        result^=columns[bit.bit_length()-1]
        coefficients^=bit
    return result


def expression(coefficients,wires):
    return dict(constant=coefficients&1,wires=[q for j,q in enumerate(wires) if coefficients>>(j+1)&1])


def search(entry,exit_state,target,domain):
    if entry[target]!=exit_state[target]:raise AssertionError('Target changed across idle interval')
    if entry[24]!=exit_state[24] or entry[25]!=exit_state[25]:return dict(status='FLAGS_CHANGED')
    if entry[24]&entry[25]:return dict(status='FLAGS_NOT_DISJOINT')
    wires=[q for q in range(46) if q!=target]
    left=[domain]+[entry[q] for q in wires]
    right=[domain]+[exit_state[q] for q in wires]
    right_basis=r.affine_basis(right)
    quotient_basis={};intersection=[];left_expressions=[]
    for j,function in enumerate(left):
        value=function
        for pivot in sorted(right_basis,reverse=True):
            if value>>pivot&1:value^=right_basis[pivot][0]
        selection=1<<j
        while value:
            pivot=value.bit_length()-1
            if pivot not in quotient_basis:
                quotient_basis[pivot]=(value,selection);break
            row,combination=quotient_basis[pivot];value^=row;selection^=combination
        if not value:
            common=xor_columns(left,selection)
            intersection.append(common);left_expressions.append(selection)
    restricted=entry[24]|entry[25]
    coefficients=r.solve(r.affine_basis([value&restricted for value in intersection]),entry[target]&restricted)
    result=dict(status='NO_AFFINE_SHARED_CORRECTION',intersection_generators=len(intersection),restricted_inputs=restricted.bit_count())
    if coefficients is None:return result
    g=xor_columns(intersection,coefficients)
    in_expression=xor_columns(left_expressions,coefficients)
    out_expression=r.solve(right_basis,g)
    assert out_expression is not None and xor_columns(left,in_expression)==xor_columns(right,out_expression)==g
    transformed=entry[target]^g
    assert transformed==((entry[24]^transformed)&(entry[25]^transformed))
    return dict(result,status='EXACT_PACK_FOUND',entry=expression(in_expression,wires),exit=expression(out_expression,wires),
                additional_ccx=1,full_domain_identities_verified=r.MAX_X)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--max-cases',type=int,default=24);a=ap.parse_args()
    if a.out.exists():raise FileExistsError(a.out)
    began=time.monotonic();path=Path(__file__).with_name('invsqrt_structural_e46.kmx');lines,ops=r.instructions(path)
    peaks=json.loads(path.with_name('score_invsqrt_retire.json').read_text())['positions_with_all46_nonzero']
    # Explicitly exclude the614 peaks already covered by the concrete h0 pack.
    remaining_peaks=[p for p in peaks if not 1635<=p<3428]
    refs=[[] for _ in range(46)];depth=[0];d=0
    for i,(op,qs) in enumerate(ops):
        for q in qs:refs[q].append(i)
        if op=='PUSH_CONDITION':d+=1
        elif op=='POP_CONDITION':d-=1
        depth.append(d)
    candidates=[]
    for q,uses in enumerate(refs):
        if q in (22,23,24,25):continue
        for last,next_use in zip(uses,uses[1:]):
            for begin,end in ((632,7626),(8396,23634)):
                start=max(last+1,begin);stop=min(next_use,end)
                while start<stop and depth[start]:start+=1
                while stop>start and depth[stop]:stop-=1
                if start>=stop:continue
                covered=remaining_peaks[bisect.bisect_left(remaining_peaks,start):bisect.bisect_left(remaining_peaks,stop)]
                if covered:candidates.append(dict(q=q,start=start,end=stop,covered=covered))
    candidates.sort(key=lambda x:(-len(x['covered']),-(x['end']-x['start'])))
    selected=[];uncovered=set(remaining_peaks)
    while candidates and len(selected)<min(8,a.max_cases):
        best=max(candidates,key=lambda x:len(uncovered.intersection(x['covered'])))
        if not uncovered.intersection(best['covered']):break
        selected.append(best);uncovered.difference_update(best['covered']);candidates.remove(best)
    selected+=candidates[:max(0,a.max_cases-len(selected))]
    cuts=set(v for item in selected for v in (item['start'],item['end']));snapshots={}
    domain,values=r.initial_values();stack=[]
    for i,(op,qs) in enumerate(ops):
        if i in cuts:snapshots[i]=values[:]
        if op=='PUSH_CONDITION':stack.append(values[:])
        elif op=='POP_CONDITION':old=stack.pop();assert old==values;values=old
        else:r.advance(op,qs,values,domain)
    if len(ops) in cuts:snapshots[len(ops)]=values[:]
    print(json.dumps(dict(candidates=len(candidates)+len(selected),selected=len(selected),snapshots=len(snapshots),profile_seconds=time.monotonic()-began)),flush=True)
    rows=[]
    for item in selected:
        t=time.monotonic();entry=snapshots[item['start']];out=snapshots[item['end']]
        result=search(entry,out,item['q'],domain) if entry[item['q']] else dict(status='ALREADY_ZERO')
        row=dict(item,**result,seconds=time.monotonic()-t);rows.append(row)
        print(json.dumps({k:v for k,v in row.items() if k!='covered'}),flush=True)
    accepted=[row for row in rows if row['status']=='EXACT_PACK_FOUND']
    record=dict(status='BOUNDED_PANEL_COMPLETE',source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                full_domain_inputs=r.MAX_X,scope='Affine correction common to both endpoints; nonlinear packing into idle disjoint q24/q25; at most24 selected idle intervals; no Q45 lower-bound claim',
                candidates_tested=len(rows),accepted=len(accepted),rows=rows,seconds=time.monotonic()-began,
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    a.out.write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({k:v for k,v in record.items() if k!='rows'},indent=2),flush=True)


if __name__=='__main__':main()
