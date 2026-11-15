#!/usr/bin/env python3
"""Find exact affine predicates at other cuts for whole phase-feature relocation.

All candidate predicate identities are verified on every legal input. Cuts
inside conditional blocks and inside a feature's own compute/erase gadget are
excluded. Moving a phase on the same Boolean predicate can delete its separate
endpoint compute/phase/erase gadget without altering the coherent phase map.
"""
import json
from pathlib import Path
import random
import time
import score_invsqrt_retire as r

PANEL=[dict(name='feature_j0',start=8075,phase=8085,end=8098,old_ANDs=1),
       dict(name='feature_j1',start=8136,phase=8143,end=8151,old_ANDs=1),
       dict(name='feature_j2',start=8189,phase=8195,end=8203,old_ANDs=2),
       dict(name='feature_j7',start=8204,phase=8205,end=8210,old_ANDs=1),
       dict(name='feature_j3',start=8247,phase=8250,end=8256,old_ANDs=1),
       dict(name='feature_j6',start=8257,phase=8259,end=8265,old_ANDs=2),
       dict(name='feature_j4',start=8293,phase=8301,end=8313,old_ANDs=2),
       dict(name='feature_j5',start=8314,phase=8317,end=8325,old_ANDs=2)]

def main():
    began=time.monotonic();base=Path(__file__).parent;lines,ops=r.instructions(base/'invsqrt_structural_e46.kmx')
    domain,values=r.initial_values();stack=[];targets={};by_phase={x['phase']:x for x in PANEL}
    for i,(op,qs) in enumerate(ops):
        if i in by_phase:
            assert op=='Z_POW' and qs==(21,);targets[by_phase[i]['name']]=values[21]
        if op=='PUSH_CONDITION':stack.append(values[:])
        elif op=='POP_CONDITION':before=stack.pop();assert before==values;values=before
        else:r.advance(op,qs,values,domain)
        if i>max(by_phase):break
    rng=random.Random(502734);samples=list(range(1,4097))+[rng.randrange(1,r.MAX_X+1) for _ in range(512)]
    signatures=[sum(((x>>j)&1)<<i for i,x in enumerate(samples)) for j in range(22)]+[0]*24
    ts={key:sum(((v>>x)&1)<<i for i,x in enumerate(samples)) for key,v in targets.items()}
    sample_domain=(1<<len(samples))-1;domain,values=r.initial_values();stack=[];sample_stack=[]
    found={};queries=0;refinements=[];cuts=0
    for i,(op,qs) in enumerate(ops):
        if op=='PUSH_CONDITION':stack.append(values[:]);sample_stack.append(signatures[:])
        elif op=='POP_CONDITION':before=stack.pop();sb=sample_stack.pop();assert before==values and sb==signatures;values=before;signatures=sb
        else:r.advance(op,qs,values,domain);r.advance(op,qs,signatures,sample_domain)
        if stack or op not in ('CCX','CSWAP','HMR'):continue
        cut=i+1;cuts+=1
        while True:
            basis=r.affine_basis([sample_domain]+signatures);retry=False
            for item in PANEL:
                name=item['name']
                if name in found or item['start']<=cut<=item['end']:continue
                queries+=1;coeff=r.solve(basis,ts[name])
                if coeff is None:continue
                value=domain if coeff&1 else 0
                for q in range(46):
                    if coeff>>(q+1)&1:value^=values[q]
                difference=value^targets[name]
                if difference:
                    x=(difference&-difference).bit_length()-1;bit=1<<len(samples)
                    for q in range(46):signatures[q]|=((values[q]>>x)&1)*bit
                    for key,target in targets.items():ts[key]|=((target>>x)&1)*bit
                    sample_domain|=bit;samples.append(x);refinements.append({'cut':cut,'target':name,'input':x});retry=True;break
                found[name]={'target':name,'insert_after_line':cut,'constant':coeff&1,
                             'parity_qubits':[q for q in range(46) if coeff>>(q+1)&1],
                             'remove_start_zero_based':item['start'],'remove_end_exclusive':item['end'],
                             'original_rotation':lines[item['phase']],'ANDs_saved':item['old_ANDs'],
                             'full_domain_predicate_check':'PASS'}
                print(json.dumps({'FOUND':found[name]}),flush=True)
            if not retry:break
        if cuts%500==0:print(json.dumps({'cuts':cuts,'found':len(found),'queries':queries,'seconds':time.monotonic()-began}),flush=True)
    report={'status':'COMPLETE','legal_inputs':r.MAX_X,'phase_predicates':len(PANEL),'eligible_cuts':cuts,
            'affine_queries':queries,'sample_rows_final':len(samples),'counterexample_refinements':refinements,
            'predicate_support_sizes':{k:v.bit_count() for k,v in targets.items()},
            'matches':list(found.values()),'elapsed_seconds':time.monotonic()-began}
    (base/'score2_invsqrt_phase_relocation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='counterexample_refinements'}))

if __name__=='__main__':main()
