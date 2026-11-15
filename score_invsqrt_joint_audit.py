#!/usr/bin/env python3
"""Evaluate the synthesis positive control and the current five-AND witness."""
import json
from pathlib import Path

def evaluate(gates,values):
    values=list(values)
    for gate in gates:
        a=b=0
        for j in gate['left']:a^=values[j]
        for j in gate['right']:b^=values[j]
        values.append(a&b)
    return values

def main():
    base=Path(__file__).parent
    table=json.loads((base/'score_invsqrt_joint_table.json').read_text())
    current=json.loads((base/'score_invsqrt_joint_known_five.json').read_text())
    for x,y in table['rows']:
        values=evaluate(current['gates'],[x>>j&1 for j in range(6)])
        outputs=[o['constant']^(sum(values[j] for j in o['terms'])&1) for o in current['outputs']]
        assert outputs[0]+2*outputs[1]==y
    control=json.loads((base/'score_invsqrt_joint_positive_control.json').read_text())
    packed=list(map(int,(base/'score_invsqrt_joint_positive_control.txt').read_text().split()))
    n=packed[0];one=packed[1];inputs=packed[2:n+2];expected=packed[n+2:]
    values=evaluate(control['gates'],inputs)
    outputs=[]
    for mask in control['output_coefficient_masks']:
        out=one if mask&1 else 0
        for j,value in enumerate(values):
            if mask>>(j+1)&1:out^=value
        outputs.append(out)
    assert outputs==expected
    changed=outputs[:];changed[0]^=1
    assert changed!=expected
    report={'status':'PASS','algorithm':'independent Python bit-vector evaluation',
            'all_table_rows':len(table['rows']),'positive_control_gates':len(control['gates']),
            'positive_control_output_match':True,'deliberately_changed_output_detected':True,
            'known_five_AND_current_block_match':True}
    (base/'score_invsqrt_joint_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))

if __name__=='__main__':main()
