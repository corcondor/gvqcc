#!/usr/bin/env python3
"""Focused regression for lifetime splits at classical conditions.

This validates the analysis decision that can otherwise produce an unsafe
aliasing suggestion: explicit/stack conditional resets must not free a wire.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import time
from test_scratch_audit import write_small_kmb

HERE=Path(__file__).resolve().parent
cases=[
 ('disjoint_after_R',[(0x11,[1],None,None),(0x12,[1],None,None),
                      (0x11,[2],None,None),(0x12,[2],None,None)],1,0),
 ('disjoint_after_HMR',[(0x11,[1],None,None),(0x50,[1],0,None),
                        (0x11,[2],None,None),(0x12,[2],None,None)],1,0),
 ('explicit_R_kept',[(0x11,[1],None,None),(0x92,[1],None,0),
                     (0x11,[2],None,None),(0x12,[1],None,None),(0x12,[2],None,None)],2,1),
 ('explicit_HMR_kept',[(0x11,[1],None,None),(0xd0,[1],0,1),
                       (0x11,[2],None,None),(0x12,[1],None,None),(0x12,[2],None,None)],2,1),
 ('stack_R_kept',[(0x11,[1],None,None),(0x81,[],None,0),(0x12,[1],None,None),
                  (0x01,[],None,None),(0x11,[2],None,None),
                  (0x12,[1],None,None),(0x12,[2],None,None)],2,1),
 ('nested_stack_HMR_kept',[(0x11,[1],None,None),(0x81,[],None,0),(0x81,[],None,1),
                         (0x50,[1],0,None),(0x01,[],None,None),(0x01,[],None,None),
                         (0x11,[2],None,None),(0x12,[1],None,None),(0x12,[2],None,None)],2,1),
]

def main():
    start=time.monotonic();result=[]
    with tempfile.TemporaryDirectory()as tmp:
        tmp=Path(tmp);exe=tmp/'audit'
        subprocess.run(['g++','-O3','-std=c++17',str(HERE/'theory_ancilla_lifetimes.cpp'),'-o',str(exe)],check=True)
        for name,ops,expected,conditionals in cases:
            path=tmp/(name+'.kmb');write_small_kmb(path,ops,num_qubits=3)
            r=json.loads(subprocess.check_output([str(exe),str(path),'1'],text=True))
            assert r['interval_chromatic_number']==expected,(name,r)
            assert r['conditional_resets_not_releasing']==conditionals,(name,r)
            result.append(dict(case=name,expected=expected,actual=r['interval_chromatic_number'],status='PASS'))
    baseline=HERE.parent/'dqi_inputs/821_ccx480_gauge128.kmb'
    h=hashlib.sha256()
    with baseline.open('rb')as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    assert h.hexdigest()=='e986d41663fa78ea2ed4ab0a47ebc4d99441ad1660b80e02872e7508cbce92a7'
    receipt=dict(status='PASS',cases=result,baseline_sha256=h.hexdigest(),
                 scanner_sha256=hashlib.sha256((HERE/'theory_ancilla_lifetimes.cpp').read_bytes()).hexdigest(),
                 elapsed_seconds=time.monotonic()-start)
    (HERE/'theory_ancilla_check_result.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))

if __name__=='__main__':main()
