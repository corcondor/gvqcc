#!/usr/bin/env python3
"""Hoist complete HMR correction phases and resynthesize them as Z/CZ.

The measured value can be nonlinear in the individual current wire values,
yet quadratic in their joint reached-state manifold. A quadratic formula can
be corrected with Clifford phases immediately after the HMR, eliminating all
later paid cleanup for that classical outcome. Every internal HMR term must
cancel and all versions must be dead outside the deleted cleanup.
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
from score8_invsqrt_phase_quadratic import PIN,PAID,shape,quadratic,sample_values,sha,phase_value


def search(lines,ops,records,one,values,expected=None):
    events=defaultdict(list);starts={r['index']:r for r in records}; targets={}; models={};stack=[];sums=defaultdict(int)
    for r in records:
        for i in r['phase_indices']:events[i].append((r['index'],''))
        for monomial,ids in r['nonconstant_phase_terms'].items():
            for i in ids:events[i].append((r['index'],monomial))
    rows=[]
    for i,(op,qs) in enumerate(ops):
        for key,monomial in events.get(i,[]):sums[key,monomial]^=phase_value(op,qs,values,one)
        if i in starts:targets[i]=values[qs[0]]
        if op=='PUSH_CONDITION':stack.append(values[:])
        elif op=='POP_CONDITION':assert values==stack.pop()
        else:R.advance(op,qs,values,one)
        if i in starts:
            rec=starts[i]
            if expected is None:
                model,rank=quadratic(values,targets[i],one)
                row={'first':i,'removed_static_paid':rec['removed_static_paid'],'model':model,'rank':rank,'result':'SAMPLE_MODEL' if model is not None else 'NO_QUADRATIC_MODEL'}
            else:
                model=expected[i]['model'];actual=0
                for term in model:actual^=phase_value('Z',term,values,one)
                row={'first':i,'removed_static_paid':rec['removed_static_paid'],'model':model,'result':'FULL_DOMAIN_MATCH' if actual==targets[i] else 'FULL_DOMAIN_MISMATCH'}
            rows.append(row)
    for row in rows:
        i=row['first'];rec=starts[i]
        row['correction_phase_equals_measured_value']=sums[i,'']==targets[i]
        row['all_internal_measurement_phase_coefficients_zero']=all(sums[i,key]==0 for key in rec['nonconstant_phase_terms'])
        if not row['correction_phase_equals_measured_value'] or not row['all_internal_measurement_phase_coefficients_zero']:row['result']='CLEANUP_PHASE_FAILED'
    return rows


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True);begin=time.monotonic()
    source=Path(__file__).with_name('score3_invsqrt_cache.kmx');assert sha(source)==PIN
    lines,ops=R.instructions(source);_,depth,_=shape(lines,ops);records,rejected=cleanup_records(lines,ops,depth)
    for r in records:r['removed_static_paid']=sum(ops[i][0] in PAID for i in r['remove_indices'])
    records=[r for r in records if r['removed_static_paid']]
    rng=random.Random(202611150803)
    xs=sorted(set(list(range(1,257))+[2**k+d for k in range(2,22) for d in range(-3,4)]+[rng.randrange(1,R.MAX_X+1) for _ in range(4096)]))
    one,values=sample_values(xs);rows=search(lines,ops,records,one,values)
    hits={r['first']:r for r in rows if r['result']=='SAMPLE_MODEL'}
    print(json.dumps({'eligible_paid_lifetimes':len(records),'sample_inputs':len(xs),'sample_counts':dict(Counter(r['result'] for r in rows)),'seconds':time.monotonic()-begin}),flush=True)
    full=[]
    if hits:
        one,values=R.initial_values();full=search(lines,ops,[r for r in records if r['index'] in hits],one,values,hits)
    report={'source_sha256':PIN,'eligible_paid_lifetimes':len(records),'helper_rejections':rejected,'sample_input_count':len(xs),'sample_rows':rows,'full_rows':full,'scope':'Immediate post-HMR resynthesis of a complete correction lifetime as an arbitrary quadratic phase on retained wires. All measurement outcomes kept symbolically; all accepted equalities require all legal x.'}
    accepted=[r for r in full if r['result']=='FULL_DOMAIN_MATCH'];report['accepted']=len(accepted)
    if accepted:
        byfirst={r['first']:r for r in accepted};byrec={r['index']:r for r in records}
        remove=set(i for r in accepted for i in byrec[r['first']]['remove_indices']);new=[]
        for i,line in enumerate(lines):
            if i not in remove:new.append(line)
            if i in byfirst:
                new.append('PUSH_CONDITION if '+byrec[i]['bit'])
                for term in byfirst[i]['model']:
                    new.append('NEG' if not term else ('Z' if len(term)==1 else 'CZ')+' '+' '.join('q'+str(q) for q in term))
                new.append('POP_CONDITION')
        dest=args.out/'candidate.kmx';dest.write_text('\n'.join(new)+'\n');report.update(candidate=str(dest),candidate_sha256=sha(dest),removed_static_paid=sum(r['removed_static_paid'] for r in accepted))
    report['seconds']=time.monotonic()-begin;(args.out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('sample_rows','full_rows','helper_rejections')}),flush=True)


if __name__=='__main__':main()
