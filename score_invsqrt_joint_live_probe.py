#!/usr/bin/env python3
"""Check restoration outputs against every retained live wire at the entry cut."""
import json
from pathlib import Path
import random
import time
import numpy as np
import score_invsqrt_retire as r
from score_invsqrt_joint_synthesis import CAPTURE_BEFORE,REPLACE_START,INPUTS

def main():
    base=Path(__file__).parent;lines,ops=r.instructions(base/'invsqrt_structural_e46.kmx')
    domain,vals=r.initial_values();stack=[]
    for i,(op,qs) in enumerate(ops):
        if i==CAPTURE_BEFORE:targets=[vals[19],vals[20]]
        if i==REPLACE_START:break
        if op=='PUSH_CONDITION':stack.append(vals[:])
        elif op=='POP_CONDITION':before=stack.pop();assert before==vals;vals=before
        else:r.advance(op,qs,vals,domain)
    assert not vals[19] and not vals[20]
    rng=random.Random(33591);samples=list(range(1,257))+[rng.randrange(1,r.MAX_X+1) for _ in range(768)]
    records=[]
    for target,value in zip((19,20),targets):
        trial=vals[:];trial[target]=value;began=time.monotonic()
        result=r.one_product(trial,target,domain,samples,2)
        record={'target':target,'retained_live_qubits':[q for q,v in enumerate(vals) if v],
                'identity':result,'seconds':time.monotonic()-began};records.append(record)
        print(json.dumps(record),flush=True)
    def unpack(value):
        return np.unpackbits(np.frombuffer(value.to_bytes((r.MAX_X+8)//8,'little'),dtype=np.uint8),bitorder='little')[:r.MAX_X+1]
    pattern=np.zeros(r.MAX_X+1,dtype=np.uint8)
    for j,q in enumerate(INPUTS):pattern|=unpack(vals[q])<<j
    extras=[]
    for q,value in enumerate(vals):
        if not value or q in INPUTS:continue
        rows=np.unique((pattern|(unpack(value)<<6))[1:]).tolist()
        extras.append({'extra_qubit':q,'joint_input_patterns':len(rows),'encoded_patterns':rows})
    extras.sort(key=lambda x:x['joint_input_patterns'])
    print(json.dumps({'extra_live_inputs':[{k:v for k,v in x.items() if k!='encoded_patterns'} for x in extras]}),flush=True)
    (base/'score_invsqrt_joint_live_probe.json').write_text(json.dumps({'legal_inputs':r.MAX_X,
        'scope':'all affine functions; additionally one product with left parity at most two wires, right parity unrestricted',
        'records':records,'extra_live_inputs':extras},indent=2)+'\n')

if __name__=='__main__':main()
