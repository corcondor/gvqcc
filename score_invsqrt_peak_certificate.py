#!/usr/bin/env python3
"""Generate an exact, small witness against a 45-coordinate affine encoding."""
import hashlib
import json
from pathlib import Path
import score_invsqrt_retire as r

def main():
    base=Path(__file__).parent;path=base/'invsqrt_structural_e46.kmx'
    lines,ops=r.instructions(path);stop=2388
    assert lines[stop-1]=='CCX q26 q27 q45'
    domain,values=r.initial_values();stack=[]
    for op,qs in ops[:stop]:
        if op=='PUSH_CONDITION':stack.append(values[:])
        elif op=='POP_CONDITION':before=stack.pop();assert before==values;values=before
        else:r.advance(op,qs,values,domain)
    assert not stack
    columns=[domain]+values;basis=r.affine_basis(columns)
    assert len(basis)==47
    xs=sorted(basis)
    rows=[sum(((column>>x)&1)<<j for j,column in enumerate(columns)) for x in xs]
    assert len(r.affine_basis(rows))==47
    report={'status':'PASS','baseline_kmx_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'after_line':stop,'instruction':lines[stop-1],
            'claim':'constant plus all 46 live wire functions have rank 47 on legal inputs',
            'scope':'rules out 45-coordinate affine encoding at this cut, not nonlinear encoding or arithmetic redesign',
            'witness_inputs':xs,'rows_constant_then_q0_to_q45_hex':[hex(x) for x in rows],
            'rank':47,'all_witness_inputs_legal':all(1<=x<=r.MAX_X for x in xs)}
    (base/'score_invsqrt_peak_certificate.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if not isinstance(v,list)}))

if __name__=='__main__':main()
