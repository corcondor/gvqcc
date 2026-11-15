#!/usr/bin/env python3
"""Find exact production occurrences of the old inverse-phase fixed kernel."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from collections import Counter

def audit(kmb, baseline_profile, report, mark_path, repo):
    sys.path.insert(0,str(repo))
    import dqi_ccx_peephole as binary
    import kmb_profile
    from outcome_inverse65_template_scan import match

    with kmb.open('rb') as stream:
        digest=hashlib.file_digest(stream,'sha256').hexdigest()
    profile=json.loads(baseline_profile.read_text())
    assert profile['raw_kmb_sha256']==digest
    compiled=kmb_profile.profile(mark_path,max_register_summaries=0)
    mark=binary.BinaryCircuit(mark_path,compiled)
    try:
        ops=list(mark.operations(0,len(mark.opcodes)))
        opcode=mark.opcodes
    finally:
        mark.close()
    tape=binary.BinaryCircuit(kmb,profile)
    matched=[]
    opcode_hits=0
    try:
        pos=0
        while True:
            start=tape.opcodes.find(opcode,pos)
            if start<0:break
            pos=start+1
            opcode_hits+=1
            qe=tape.operations(start,start+len(ops))
            m=match(ops,qe)
            if m is None:continue
            q,c=m
            scratch={k:v for k,v in q.items() if k>=19}
            matched.append(dict(start=start,end=start+len(ops),
                                source=[q[i] for i in range(12)],
                                helpers=[scratch[i] for i in sorted(scratch)],
                                classical_bits=[c[i] for i in sorted(c)]))
    finally:
        tape.close()
    output=dict(status='EXACT_FIXED_INVERSE_PHASE_TEMPLATE_MATCH',
                sha256=digest,whole_DQI_Q=profile['header']['num_qubits'],
                template_sha256=compiled['raw_kmb_sha256'],template_instructions=len(ops),
                opcode_matches=opcode_hits, exact_matches=len(matched),
                old_helper_max_index_histogram=dict(Counter(max(m['helpers']) for m in matched)),
                matches=matched,whole_DQI_emitted=False)
    report.write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({k:v for k,v in output.items() if k!='matches'},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--circuit',type=Path,required=True)
    p.add_argument('--profile',type=Path,required=True)
    p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    audit(a.circuit,a.profile,a.out,a.reference,a.repo)
