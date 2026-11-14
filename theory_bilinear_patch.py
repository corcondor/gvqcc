#!/usr/bin/env python3
"""Apply exactly proved CPR templates under injective qubit renamings.

Only complete, unconditional CX/CCX instruction sequences are matched.
No condition-stack, classical, measurement or phase instruction is crossed.
All other KMB byte columns and registers are copied verbatim by the audited
column-splice writer. The original file is never overwritten.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import time

import dqi_ccx_peephole as shared
from dqi_ccx_input_factor import exact_polynomial_check
from theory_bilinear_verify import parse


def source_ordered_gf12(terms):
    out=[]
    for a,b,w in terms:
        masks=(a,b,w);prep=[];piv=[]
        for axis,mask in enumerate(masks):
            p=(mask&-mask).bit_length()-1;piv.append(axis*12+p)
            seq=[]
            for j in range(12):
                if j!=p and mask>>j&1:
                    qs=(axis*12+j,axis*12+p)
                    if axis==2:qs=qs[::-1]
                    seq.append(shared.Operation(0x21,qs))
            prep.append(seq);out.extend(seq)
        out.append(shared.Operation(0x31,tuple(piv)))
        out.extend(reversed(prep[2]));out.extend(prep[1]);out.extend(prep[0])
    return out


def wire_match(before,actual):
    mapping={};reverse={}
    for old,new in zip(before,actual):
        if old.opcode!=new.opcode or new.condition is not None or new.bit is not None:
            return None
        for q,r in zip(old.qubits,new.qubits):
            if q in mapping and mapping[q]!=r or r in reverse and reverse[r]!=q:
                return None
            mapping[q]=r;reverse[r]=q
    return mapping


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('input',type=Path)
    ap.add_argument('output',type=Path)
    ap.add_argument('--input-certificate',type=Path,required=True)
    ap.add_argument('--report',type=Path,required=True)
    ap.add_argument('--cached-profile',type=Path)
    args=ap.parse_args();root=Path(__file__).parent;start_time=time.monotonic()
    if args.output.exists() or args.input.resolve()==args.output.resolve():
        raise FileExistsError('Output must be a new candidate')
    old24=parse(root/'inverse_v2_actual_eea_product.kmx')
    new24=parse(root/'theory_bilinear_actual_cpr.kmx')
    cert=json.loads((root/'inverse_v2_actual_eea_product_certificate.json').read_text())
    # Both files have exactly the same explicit 12-CNOT conjugation layer.
    expected=[shared.Operation(0x21,(cert['input_left'][12+i],cert['input_left'][i])) for i in range(12)]
    assert old24[:12]==old24[-12:]==new24[:12]==new24[-12:]==expected
    c12=json.loads(args.input_certificate.read_text())['records'][0]
    templates=[('gf24_multiplication',old24[12:-12],new24[12:-12]),
               ('gf12_multiplication',source_ordered_gf12(c12['terms']),parse(root/'theory_bilinear_gf12_cpr.kmx'))]
    certificates={name:exact_polynomial_check(before,after) for name,before,after in templates}
    # The maps are accumulators, so reversed templates have the same map too.
    templates += [(name+'_reversed',list(reversed(before)),after) for name,before,after in templates[:]]
    for name,before,after in templates:
        if name not in certificates:certificates[name]=exact_polynomial_check(before,after)
    profile=(json.loads(args.cached_profile.read_text()) if args.cached_profile
             else shared.kp.profile(args.input,max_register_summaries=0))
    if profile['raw_kmb_sha256']!='e986d41663fa78ea2ed4ab0a47ebc4d99441ad1660b80e02872e7508cbce92a7':
        raise ValueError('This first study is pinned to the e986 baseline')
    # Cached profile is only an offset aid; hash the actual input independently.
    h=hashlib.sha256()
    with args.input.open('rb') as f:
        for block in iter(lambda:f.read(4<<20),b''):h.update(block)
    if h.hexdigest()!=profile['raw_kmb_sha256']:raise AssertionError('Actual input hash mismatch')
    circuit=shared.BinaryCircuit(args.input,profile)
    blocks=[];records=[];diagnostics=[]
    try:
        for name,before,after in templates:
            pattern=bytes(x.opcode for x in before);pos=0;candidates=0;matches=0
            while True:
                pos=circuit.opcodes.find(pattern,pos)
                if pos<0:break
                begin=pos;end=begin+len(before);pos+=1;candidates+=1
                actual=list(circuit.operations(begin,end))
                mapping=wire_match(before,actual)
                if mapping is None:continue
                if any(begin<e and end>b for b,e,_,_ in blocks):continue
                rewritten=[shared.Operation(x.opcode,tuple(mapping[q] for q in x.qubits)) for x in after]
                assert sum(x.is_ccx for x in actual)==sum(x.is_ccx for x in rewritten)
                blocks.append((begin,end,actual,rewritten));matches+=1
                records.append(dict(template=name,start=begin,end=end,removed_CX=len(before)-len(after),
                                    wire_mapping={str(q):r for q,r in mapping.items()}))
            diagnostics.append(dict(template=name,opcode_candidates=candidates,exact_matches=matches))
            print(json.dumps(diagnostics[-1]),flush=True)
        blocks.sort(key=lambda x:x[0]);records.sort(key=lambda x:x['start'])
        # Each matched segment contains no stack operation, and may have a fixed
        # inherited conjunction. Record its depth for review; the proof holds
        # independently for enabled=true and enabled=false.
        cursor=0;depth=0
        for rec in records:
            prefix=circuit.opcodes[cursor:rec['start']]
            depth+=prefix.count(b'\x81')-prefix.count(b'\x01')
            if depth<0:raise AssertionError('Negative inherited condition depth')
            rec['inherited_condition_stack_depth']=depth;cursor=rec['end']
        if not blocks:raise RuntimeError('No exact occurrence matched')
        shared.write_rewritten(circuit,args.output,blocks)
    finally:circuit.close()
    post=shared.kp.profile(args.output,max_register_summaries=0)
    removed=sum(x['removed_CX'] for x in records)
    assert profile['header']['num_ops']-post['header']['num_ops']==removed
    assert profile['header']['num_qubits']==post['header']['num_qubits']==889
    assert profile['header']['num_bits']==post['header']['num_bits']
    assert profile['raw_gate_families']['CX']['total']-post['raw_gate_families']['CX']['total']==removed
    for name,counts in profile['raw_gate_families'].items():
        if name!='CX':assert post['raw_gate_families'][name]==counts,(name,counts,post['raw_gate_families'][name])
    out=dict(status='BUILT_EXACT_TEMPLATE_REPLACEMENTS_FULL_VERIFIER_PENDING',
             input=str(args.input),output=str(args.output),input_sha256=profile['raw_kmb_sha256'],
             output_sha256=post['raw_kmb_sha256'],rewritten_blocks=len(blocks),removed_CX=removed,
             removed_CCX=0,Q=889,before_bytes=args.input.stat().st_size,after_bytes=args.output.stat().st_size,
             before_header=profile['header'],after_header=post['header'],
             template_certificates=certificates,discovery=diagnostics,blocks=records,
             unchanged='All registers; all non-CX raw gate counts; every non-replaced operation and its operands.',
             condition_rule='Each replacement is inside a constant condition stack; no explicit condition, measurement, classical or phase instruction occurs in a matched segment.',
             official_verification='Not run by this tool',elapsed_seconds=time.monotonic()-start_time)
    args.report.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ('blocks','before_header','after_header','template_certificates')},indent=2))


if __name__=='__main__':main()
