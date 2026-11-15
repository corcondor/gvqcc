#!/usr/bin/env python3
"""Independent value evaluation of positive controls and pinned-result replay."""
import json
import os
from pathlib import Path
import subprocess
import score_invsqrt_retire as r

def eval_program(model,path):
    raw=list(map(int,path.read_text().split()));n=raw[0];one=raw[1];values=raw[2:n+2];expected=raw[n+2:]
    for gate in model['gates']:
        a=b=0
        for j in gate['left']:a^=values[j]
        for j in gate['right']:b^=values[j]
        values.append(a&b)
    outputs=[]
    for mask in model['output_coefficient_masks']:
        value=one if mask&1 else 0
        for j,v in enumerate(values):
            if mask>>(j+1)&1:value^=v
        outputs.append(value)
    assert outputs==expected

def main():
    base=Path(__file__).parent
    for prefix,table in [('fast','score_invsqrt_joint_positive_control.txt'),('three','score2_invsqrt_three_positive.txt')]:
        eval_program(json.loads((base/f'score2_invsqrt_{prefix}_positive.json').read_text()),base/table)
    old=json.loads((base/'score_invsqrt_joint_enum_all.json').read_text());new=json.loads((base/'score2_invsqrt_fast_six_audit.json').read_text())
    for key in ['status','first_gates_completed','first_gates_total','second_gates_tried','rank1_unresolved']:assert old[key]==new[key]
    raw=list(map(int,(base/'score2_invsqrt_global_oneand_round0.txt').read_text().split()));nw,ncuts,nt=raw[:3]
    words=lambda v:[v>>(64*j)&((1<<64)-1) for j in range(nw)]
    number=lambda ws:sum(v<<(64*j) for j,v in enumerate(ws))
    one=number(raw[3:3+nw]);p=3+nw+nt*(2+nw);cut,zeros=raw[p:p+2];p+=2
    sig=[number(raw[p+q*nw:p+(q+1)*nw]) for q in range(46)]
    basis=r.affine_basis([one]+sig);pair=None
    for a in range(46):
        for b in range(a):
            if r.solve(basis,sig[a]&sig[b]) is None:pair=(a,b);break
        if pair:break
    assert pair;target=sig[pair[0]]&sig[pair[1]]
    packed=[nw,1,1]+words(one)+[-1,-1]+words(target)+[cut,zeros]
    for value in sig:packed+=words(value)
    control=base/'score2_invsqrt_oneand_positive.txt';control.write_text(' '.join(map(str,packed))+'\n')
    binary=os.environ.get('SCORE2_ONEAND_BINARY','/workspace/scratch/3815fb5fae06/score2_invsqrt_relocate_oneand')
    proc=subprocess.run([binary,str(control)],capture_output=True,text=True,check=True)
    model=json.loads(proc.stdout);assert model['status']=='SAMPLE_MODEL'
    _,ops=r.instructions(base/'invsqrt_structural_e46.kmx');domain,values=r.initial_values();stack=[]
    for op,qs in ops[:cut]:
        if op=='PUSH_CONDITION':stack.append(values[:])
        elif op=='POP_CONDITION':before=stack.pop();assert before==values;values=before
        else:r.advance(op,qs,values,domain)
    assert not stack
    def expr(mask):
        v=0
        for q in range(46):
            if mask>>q&1:v^=values[q]
        return v
    linear=model['affine_mask_constant_then_qubits'];actual=(expr(model['left_mask'])&expr(model['right_mask']))^expr(linear>>1)^(domain if linear&1 else 0)
    assert actual==values[pair[0]]&values[pair[1]]
    model.update(full_domain_positive_control='PASS',legal_inputs=r.MAX_X,reference_product_qubits=list(pair))
    (base/'score2_invsqrt_oneand_positive.json').write_text(json.dumps(model,indent=2)+'\n')
    report={'status':'PASS','fast_six_input_replay_matches_prior_complete_enumeration':True,
            'fast_four_AND_positive_control':'PASS','five_AND_three_output_positive_control':'PASS',
            'relocated_one_AND_positive_control_all_legal_inputs':'PASS','legal_inputs':r.MAX_X,
            'note':'Positive controls test the implementation; they are not improved benchmark candidates.'}
    (base/'score2_invsqrt_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

if __name__=='__main__':main()
