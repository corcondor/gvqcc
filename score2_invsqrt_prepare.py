#!/usr/bin/env python3
"""Regenerate the joint v9/v10/v11 table and its five-AND positive control."""
import json
from pathlib import Path
import score_invsqrt_retire as r
from score_invsqrt_joint_synthesis import REPLACE_START

def main():
    base=Path(__file__).parent;_,ops=r.instructions(base/'invsqrt_structural_e46.kmx');domain,values=r.initial_values();stack=[]
    for i,(op,qs) in enumerate(ops):
        if i==7572:targets=[values[19],values[20],values[44]]
        if i==REPLACE_START:break
        if op=='PUSH_CONDITION':stack.append(values[:])
        elif op=='POP_CONDITION':before=stack.pop();assert before==values;values=before
        else:r.advance(op,qs,values,domain)
    assert targets[2]==values[9]^targets[1]^(values[34]&targets[1])
    original=json.loads((base/'score_invsqrt_joint_table.json').read_text())
    rows=[[x,y|((((x>>1)&1)^((y>>1)&1)^(((x>>2)&1)&((y>>1)&1)))<<2)] for x,y in original['rows']]
    table={**original,'output_qubits':[19,20,44],'rows':rows,'original_joint_AND_count':6,
           'additional_target_full_domain_identity':'v11=s12 XOR v10 XOR s13*v10; verified for every legal x'}
    (base/'score2_invsqrt_joint_three_table.json').write_text(json.dumps(table,indent=2)+'\n')
    vectors=[(1<<len(rows))-1]+[sum(((x>>j)&1)<<i for i,(x,y) in enumerate(rows)) for j in range(6)]
    ts=[sum(((y>>j)&1)<<i for i,(x,y) in enumerate(rows)) for j in range(3)]
    (base/'score2_invsqrt_joint_three_table.txt').write_text(' '.join(map(str,[6]+vectors+ts))+'\n')
    x=vectors[1:];g0=x[0]&x[1];g1=x[2]&x[3]
    control=[(x[4]^g0)&(x[5]^g1),(x[0]^g0)&(x[1]^g1),(x[2]^g0)&(x[3]^g1)]
    (base/'score2_invsqrt_three_positive.txt').write_text(' '.join(map(str,[6]+vectors+control))+'\n')
    print('Regenerated the three-output table with a full-domain identity check and a synthetic five-AND control.')

if __name__=='__main__':main()
