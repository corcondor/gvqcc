#!/usr/bin/env python3
"""Prepare exact enumerator inputs and reproducible algebraic witnesses."""
import json
from pathlib import Path

def packed(rows,n):
    values=[(1<<len(rows))-1]+[sum(((x>>j)&1)<<i for i,(x,y) in enumerate(rows)) for j in range(n)]
    targets=[sum(((y>>j)&1)<<i for i,(x,y) in enumerate(rows)) for j in range(2)]
    return values,targets

def main():
    base=Path(__file__).parent;table=json.loads((base/'score_invsqrt_joint_table.json').read_text())
    values,targets=packed(table['rows'],6)
    (base/'score_invsqrt_joint_table.txt').write_text(' '.join(map(str,[6]+values+targets))+'\n')
    extra=next(x for x in json.loads((base/'score_invsqrt_joint_live_probe.json').read_text())['extra_live_inputs'] if x['extra_qubit']==17)
    old=dict(table['rows']);rows=[[x,old[x&63]] for x in extra['encoded_patterns']]
    t7={**table,'input_qubits':table['input_qubits']+[17],'rows':rows,'reachable_patterns':len(rows)}
    (base/'score_invsqrt_joint_extra17_table.json').write_text(json.dumps(t7,indent=2)+'\n')
    v7,y7=packed(rows,7)
    (base/'score_invsqrt_joint_extra17_table.txt').write_text(' '.join(map(str,[7]+v7+y7))+'\n')
    x=values[1:];g0=x[0]&x[1];g1=x[2]&x[3]
    positive=[(x[4]^g0)&(x[5]^g1),(x[0]^g0)&(x[1]^g1)]
    (base/'score_invsqrt_joint_positive_control.txt').write_text(' '.join(map(str,[6]+values+positive))+'\n')
    known={'gates':[{'left':[0,2,3,4,5],'right':[0,1,2,3,5]},
                   {'left':[1,3],'right':[0,2,4,6]},
                   {'left':[1,2,7],'right':[3,4,5,6]},
                   {'left':[0,1,3,4,7],'right':[0,3,4,5,6,7,8]},
                   {'left':[2,7],'right':[1,2,3,4,5,6,7,8,9]}],
           'outputs':[{'constant':0,'terms':[1,2,4,5,6,7,8,9]},
                      {'constant':0,'terms':[1,2,4,5,6,8,9,10]}],
           'status':'VERIFIED','rows':len(table['rows']),
           'source':'Current e46 restoration block, algebraic transcript of five CCX gates','candidate':False}
    for inp,out in table['rows']:
        vs=[inp>>j&1 for j in range(6)]
        for gate in known['gates']:vs.append((sum(vs[j] for j in gate['left'])&1)&(sum(vs[j] for j in gate['right'])&1))
        actual=sum((o['constant']^(sum(vs[j] for j in o['terms'])&1))<<j for j,o in enumerate(known['outputs']))
        assert actual==out
    (base/'score_invsqrt_joint_known_five.json').write_text(json.dumps(known,indent=2)+'\n')
    print('Prepared 47-pattern and 63-pattern tables, four-AND positive control, and current five-AND witness.')

if __name__=='__main__':main()
