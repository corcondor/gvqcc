#!/usr/bin/env python3
"""Extract two selected pairs of additional live wires on the entire domain."""
import json
from pathlib import Path
import numpy as np
import score_invsqrt_retire as r
from score_invsqrt_joint_synthesis import INPUTS,REPLACE_START

def main():
    base=Path(__file__).parent;lines,ops=r.instructions(base/'invsqrt_structural_e46.kmx');domain,values=r.initial_values();stack=[]
    for i,(op,qs) in enumerate(ops):
        if i==REPLACE_START:break
        if op=='PUSH_CONDITION':stack.append(values[:])
        elif op=='POP_CONDITION':before=stack.pop();assert before==values;values=before
        else:r.advance(op,qs,values,domain)
    def unpack(v):return np.unpackbits(np.frombuffer(v.to_bytes((r.MAX_X+8)//8,'little'),dtype=np.uint8),bitorder='little')[:r.MAX_X+1]
    pattern=np.zeros(r.MAX_X+1,dtype=np.uint8)
    for j,q in enumerate(INPUTS):pattern|=unpack(values[q])<<j
    original=json.loads((base/'score_invsqrt_joint_table.json').read_text());mapping=dict(original['rows'])
    for a,b in [(17,28),(17,16)]:
        extended=pattern|(unpack(values[a])<<6)|(unpack(values[b])<<7);xs=np.unique(extended[1:]).tolist()
        table={**original,'input_qubits':INPUTS+[a,b],'rows':[[x,mapping[x&63]] for x in xs],
               'reachable_patterns':len(xs),'extra_pair':[a,b],'all_legal_inputs':r.MAX_X}
        path=base/f'score2_invsqrt_pair{a}_{b}_table.json';path.write_text(json.dumps(table,indent=2)+'\n')
        print(json.dumps({'path':path.name,'reachable_patterns':len(xs)}),flush=True)

if __name__=='__main__':main()
