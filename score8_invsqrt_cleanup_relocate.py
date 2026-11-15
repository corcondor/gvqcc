#!/usr/bin/env python3
"""Relocate complete measurement corrections onto a free Clifford basis.

Tests all unconditional nonlinear event boundaries after a measurement and
before its classical bit is overwritten. The target is the entire measured
phase function, not any single AND term of the old implementation.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import json
from pathlib import Path
import random
import time

import score_invsqrt_retire as R
from score4_invsqrt_block_cleanup import cleanup_records
from score8_invsqrt_phase_quadratic import PIN,PAID,shape,sample_values,sha,phase_value
from score8_invsqrt_cleanup_clifford import search


def basis_at(values,one):
    wires=[q for q,v in enumerate(values) if v not in (0,one)]
    fs=[one]+[values[q] for q in wires];ds=[()]+[(q,) for q in wires]
    for j,a in enumerate(wires):
        for b in wires[j+1:]:fs.append(values[a]&values[b]);ds.append((a,b))
    return R.affine_basis(fs),ds


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True);begin=time.monotonic()
    source=Path(__file__).with_name('score3_invsqrt_cache.kmx');assert sha(source)==PIN
    lines,ops=R.instructions(source);_,depth,_=shape(lines,ops);records,rejected=cleanup_records(lines,ops,depth)
    for r in records:r['removed_static_paid']=sum(ops[i][0] in PAID for i in r['remove_indices'])
    records=[r for r in records if r['removed_static_paid']];byfirst={r['index']:r for r in records}
    rng=random.Random(202611150804)
    xs=sorted(set(list(range(1,129))+[2**k+d for k in range(2,22) for d in range(-2,3)]+[rng.randrange(1,R.MAX_X+1) for _ in range(2048)]))
    one,values=sample_values(xs);targets={};stack=[];hits=[];cutcount=queries=0
    for i,(op,qs) in enumerate(ops):
        if i in byfirst:targets[i]=values[qs[0]]
        if op=='PUSH_CONDITION':stack.append(values[:])
        elif op=='POP_CONDITION':assert values==stack.pop()
        else:R.advance(op,qs,values,one)
        cut=i+1
        if stack or op not in ('CCX','CSWAP','HMR'):continue
        active=[j for j in targets if j<cut and (byfirst[j]['next_overwrite'] is None or cut<=byfirst[j]['next_overwrite'])]
        if not active:continue
        base,desc=basis_at(values,one);cutcount+=1
        for j in active:
            queries+=1;coeff=R.solve(base,targets[j])
            if coeff is not None:
                model=[desc[k] for k in range(len(desc)) if coeff>>k&1]
                hits.append({'first':j,'cut':cut,'model':model,'removed_static_paid':byfirst[j]['removed_static_paid']});targets.pop(j)
        if cutcount%200==0:print(json.dumps({'cuts':cutcount,'queries':queries,'hits':len(hits),'seconds':time.monotonic()-begin}),flush=True)
    report={'source_sha256':PIN,'sample_inputs':len(xs),'eligible_paid_lifetimes':len(records),'cuts':cutcount,'queries':queries,'sample_hits':hits,'scope':'Complete measured phase function as unrestricted quadratic polynomial at every depth-zero CCX, CSWAP, HMR boundary after its measurement and before guaranteed classical overwrite; excludes conditional-data routing.'}
    print(json.dumps({k:v for k,v in report.items() if k!='sample_hits'}),flush=True)
    full=[]
    if hits:
        one,values=R.initial_values();stack=[];targets={};atcut=defaultdict(list)
        for hit in hits:atcut[hit['cut']].append(hit)
        for i,(op,qs) in enumerate(ops):
            if i in byfirst:targets[i]=values[qs[0]]
            if op=='PUSH_CONDITION':stack.append(values[:])
            elif op=='POP_CONDITION':assert values==stack.pop()
            else:R.advance(op,qs,values,one)
            for hit in atcut[i+1]:
                actual=0
                for term in hit['model']:actual^=phase_value('Z',term,values,one)
                full.append({**hit,'result':'FULL_DOMAIN_MATCH' if actual==targets[hit['first']] else 'FULL_DOMAIN_MISMATCH'})
        # Separately verify the removed whole correction and every internal
        # measurement coefficient. Post-HMR model result in this helper is
        # irrelevant because the accepted model is at its reported later cut.
        one,values=R.initial_values();expected={h['first']:h for h in hits}
        cleanup=search(lines,ops,[r for r in records if r['index'] in expected],one,values,expected)
        phases={r['first']:r for r in cleanup}
        for row in full:
            p=phases[row['first']];row['cleanup_phase_valid']=p['correction_phase_equals_measured_value'] and p['all_internal_measurement_phase_coefficients_zero']
    report['full_results']=full
    accepted=[r for r in full if r['result']=='FULL_DOMAIN_MATCH' and r['cleanup_phase_valid']];report['accepted']=len(accepted)
    if accepted:
        remove=set(i for r in accepted for i in byfirst[r['first']]['remove_indices']);bycut=defaultdict(list)
        for r in accepted:bycut[r['cut']].append(r)
        new=[]
        for i,line in enumerate(lines):
            for hit in bycut[i]:
                new.append('PUSH_CONDITION if '+byfirst[hit['first']]['bit'])
                for term in hit['model']:new.append('NEG' if not term else ('Z' if len(term)==1 else 'CZ')+' '+' '.join('q'+str(q) for q in term))
                new.append('POP_CONDITION')
            if i not in remove:new.append(line)
        dest=a.out/'candidate.kmx';dest.write_text('\n'.join(new)+'\n');report.update(candidate=str(dest),candidate_sha256=sha(dest),static_paid_saved=sum(h['removed_static_paid'] for h in accepted))
    report['seconds']=time.monotonic()-begin;(a.out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('sample_hits','full_results')}),flush=True)


if __name__=='__main__':main()
