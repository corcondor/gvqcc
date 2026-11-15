#!/usr/bin/env python3
"""Use six-input restrictions to certify or prioritize extra live wires.

A seven-input program valid on the joint domain remains a valid four-AND
program when the extra bit is fixed. Thus a complete impossibility result on
either fixed-bit domain excludes that extra wire, without a seven-input scan.
"""
import json
import os
from pathlib import Path
import subprocess
import time

def main():
    base=Path(__file__).parent;root=json.loads((base/'score_invsqrt_joint_table.json').read_text())
    old=dict(root['rows']);extras=json.loads((base/'score_invsqrt_joint_live_probe.json').read_text())['extra_live_inputs']
    binary=Path(os.environ.get('SCORE2_ENUM_BINARY','/workspace/scratch/3815fb5fae06/score2_invsqrt_joint_fast'));records=[]
    for item in extras:
        q=item['extra_qubit'];parts=[[x&63 for x in item['encoded_patterns'] if x>>6==b] for b in (0,1)]
        b=max((0,1),key=lambda bit:len(parts[bit]));xs=sorted(parts[b])
        record={'extra_qubit':q,'patterns':len(item['encoded_patterns']),'chosen_value':b,'restricted_patterns':len(xs)}
        if len(xs)==47:
            record.update(status='EXCLUDED_BY_EXISTING_SIX_INPUT_LOWER_BOUND',reason='Fixing the extra bit retains all 47 original patterns')
        elif q==17:
            complete=base/'score2_invsqrt_extra17_complete.json'
            if complete.exists() and complete.stat().st_size:
                result=json.loads(complete.read_text())
                record.update(status=result['status'],result=result,source_result=complete.name,
                              excludes_extra_wire=result['status']=='NO_SOLUTION_IN_SEARCHED_FAMILY' and result['rank1_unresolved']==0)
            else:record.update(status='FULL_SEVEN_INPUT_ENUMERATION_RUNNING')
        else:
            n=6;rows=[[x,old[x]] for x in xs]
            vs=[(1<<len(rows))-1]+[sum(((x>>j)&1)<<i for i,(x,y) in enumerate(rows)) for j in range(n)]
            ts=[sum(((y>>j)&1)<<i for i,(x,y) in enumerate(rows)) for j in range(2)]
            table=base/f'score2_invsqrt_extra{q}_fixed{b}.txt';table.write_text(' '.join(map(str,[n]+vs+ts))+'\n')
            began=time.monotonic();proc=subprocess.run([str(binary),str(table),'all','60'],capture_output=True,text=True,timeout=75,check=True)
            result=json.loads(proc.stdout);record.update(status=result['status'],result=result,seconds=time.monotonic()-began,
                                                     restriction_table=table.name)
            record['excludes_extra_wire']=result['status']=='NO_SOLUTION_IN_SEARCHED_FAMILY' and result['rank1_unresolved']==0
        records.append(record);print(json.dumps(record),flush=True)
        (base/'score2_invsqrt_extra_restrictions.json').write_text(json.dumps({'status':'RUNNING' if len(records)<len(extras) else 'COMPLETE','scope':'one additional live wire at the fixed restoration cut; arbitrary combinations of several extra wires are not excluded','records':records},indent=2)+'\n')

if __name__=='__main__':main()
