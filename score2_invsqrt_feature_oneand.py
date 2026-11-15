#!/usr/bin/env python3
"""Resynthesize whole two-AND phase features with every current live value."""
import json
from pathlib import Path
import random
import time
import score_invsqrt_retire as r

def main():
    base=Path(__file__).parent;lines,ops=r.instructions(base/'invsqrt_structural_e46.kmx')
    # Zero-based compute start, index of the rotation, final cleanup endpoint.
    panel=[dict(name='feature_j2',start=8189,phase=8195,end=8203),
           dict(name='feature_j6',start=8257,phase=8259,end=8265),
           dict(name='feature_j4',start=8293,phase=8301,end=8313),
           dict(name='feature_j5',start=8314,phase=8317,end=8325)]
    starts={x['start']:x for x in panel};phases={x['phase']:x for x in panel}
    domain,values=r.initial_values();stack=[];rng=random.Random(19451)
    samples=list(range(1,257))+[rng.randrange(1,r.MAX_X+1) for _ in range(768)];records=[]
    for i,(op,qs) in enumerate(ops):
        if i in starts:
            starts[i]['entry']=values[:];assert values[21]==0
        if i in phases:
            item=phases[i];assert op=='Z_POW' and qs==(21,)
            trial=item['entry'][:];trial[21]=values[21];began=time.monotonic()
            identity=r.one_product(trial,21,domain,samples,2)
            records.append({k:v for k,v in item.items() if k!='entry'}|{'identity':identity,'seconds':time.monotonic()-began,
                'free_live_inputs':[q for q,v in enumerate(item['entry']) if v]})
            print(json.dumps(records[-1]),flush=True)
        if op=='PUSH_CONDITION':stack.append(values[:])
        elif op=='POP_CONDITION':before=stack.pop();assert before==values;values=before
        else:r.advance(op,qs,values,domain)
        if i>max(phases):break
    (base/'score2_invsqrt_feature_oneand.json').write_text(json.dumps({'legal_inputs':r.MAX_X,'scope':'whole phase feature replacement; one AND with at most two terms in left parity and arbitrary right parity and affine remainder','records':records},indent=2)+'\n')

if __name__=='__main__':main()
