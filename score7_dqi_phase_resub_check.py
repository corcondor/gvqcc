#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Positive and negative discovery controls; exact algebra checked separately."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import kickmix as km

def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--scanner',type=Path,required=True)
    ap.add_argument('--workspace',type=Path,required=True)
    ap.add_argument('--report',type=Path,required=True)
    args=ap.parse_args()
    args.workspace.mkdir(parents=True,exist_ok=False)
    prefix='R q3\nR q4\nCCX q0 q1 q3\nCCX q3 q2 q4\nHMR q3 b0\nCZ q0 q1 if b0\n'
    rows=[
        ('whole_cubic_literal',prefix+'CCZ q0 q1 q2\n','literal'),
        ('whole_cubic_xor',prefix+'CX q5 q4\nCCZ q0 q1 q2\n','affine'),
        ('quadratic','R q3\nCCX q0 q1 q3\nCCZ q0 q1 q2\n','quadratic'),
        ('dirty_negative','CCX q0 q1 q3\nCCZ q0 q1 q2\n',None),
        ('branch_literal','PUSH_CONDITION if b1\n'+prefix+'CCZ q0 q1 q2\nPOP_CONDITION\n','literal'),
        ('conditional_write_negative','R q3\nCCX q0 q1 q3 if b0\nCCZ q0 q1 q2\n',None),
    ]
    receipts=[]
    for name,text,kind in rows:
        source=args.workspace/(name+'.kmb')
        output=args.workspace/(name+'.json')
        km.Circuit(text).to_file(source,format='kmb')
        subprocess.run([str(args.scanner),str(source),str(output)],check=True,capture_output=True,text=True)
        result=json.loads(output.read_text())
        assert result['candidate_count']==int(kind is not None),(name,result)
        if kind is not None:
            assert result['candidates'][0]['kind']==kind,(name,result)
        receipts.append({'name':name,'input_sha256':sha(source),'expected_kind':kind,'result':result})
    # Complete diagonal Kraus-entry comparison, retaining the classical outcome.
    # The prefix creates t=abc, erases ab in X basis and corrects (-1)^(m ab).
    checked=0
    for a,b,c,d,reference,m in itertools.product((0,1),repeat=6):
        p=a*b;t=p*c
        common=(-1)**(m*p)*(-1)**(m*a*b)
        original=(a,b,c,d,reference,m,t^d,common*(-1)**(a*b*c))
        replaced=(a,b,c,d,reference,m,t^d,common*(-1)**((t^d)^d))
        assert original==replaced
        checked+=1
    dirty_counterexamples=sum((a*b*c)!=((dirty^(a*b))*c)
        for a,b,c,dirty in itertools.product((0,1),repeat=4))
    assert dirty_counterexamples==4
    result={'status':'PASS','source_sha256':sha(__file__),'scanner_binary_sha256':sha(args.scanner),
        'scanner_source_sha256':sha(Path(__file__).with_name('score7_dqi_phase_resub.cpp')),
        'exact_kraus_entries':checked,'dirty_counterexamples':dirty_counterexamples,
        'fixtures':receipts,'production_score_improvement':None}
    args.report.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='fixtures'}))

if __name__=='__main__':main()
