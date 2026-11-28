#!/usr/bin/env python3
"""Independently certify routed DQI kernels as exact arbitrary-state maps.

The checker uses full Boolean ANF; it does not use Polytof to verify Polytof.
The old physical EEA block and every candidate are evaluated on the same
formal input variables. All gates are CX/CCX, hence there is no hidden phase.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import time

from dqi_ccx_peephole import Operation
from dqi_ccx_input_factor import exact_polynomial_check


def parse(path, mapping=None):
    result = []
    for line in path.read_text().splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        parts = line.split()
        op = {'CX': 0x21, 'CCX': 0x31}[parts[0]]
        qs = tuple(int(s[1:]) for s in parts[1:])
        if mapping is not None:
            qs = tuple(mapping[q] for q in qs)
        result.append(Operation(op, qs))
    return result


def standard(terms, n):
    result = []
    for a, b, c in terms:
        pivot = [(x & -x).bit_length()-1 for x in (a,b,c)]
        prepare = []
        for ax, x in enumerate((a,b,c)):
            for i in range(n):
                if i != pivot[ax] and x >> i & 1:
                    pair = (ax*n+i, ax*n+pivot[ax])
                    if ax == 2:
                        pair = pair[::-1]
                    prepare.append(Operation(0x21,pair))
        result.extend(prepare)
        result.append(Operation(0x31, tuple(ax*n+pivot[ax] for ax in range(3))))
        result.extend(reversed(prepare))
    return result


def write_kmx(path, operations):
    path.write_text(''.join(('CX' if x.opcode==0x21 else 'CCX')+' '+
                           ' '.join(f'q{q}' for q in x.qubits)+'\n' for x in operations))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--run-dir',type=Path,required=True)
    ap.add_argument('--repo-dir',type=Path,default=Path(__file__).parent)
    ap.add_argument('--output-dir',type=Path,help='Keep reproduced kernels and proof separate from source files')
    args=ap.parse_args();r=args.run_dir;repo=args.repo_dir
    dest=args.output_dir or repo;dest.mkdir(parents=True,exist_ok=True)
    start=time.monotonic()
    cert=json.loads((repo/'inverse_v2_actual_eea_product_certificate.json').read_text())
    wires=cert['input_left']+cert['input_right']+cert['output_qubits_in_field_order']
    to_local={q:i for i,q in enumerate(wires)}
    actual=parse(repo/'inverse_v2_actual_eea_product.kmx',to_local)
    cases=[]
    candidates=[]
    for name in ('gf24_actual_cpr_local','gf24_actual_cpr1024_local','gf24_actual_symmetric_cpr1024_local'):
        path=r/(name+'.kmx')
        ops=parse(path)
        if 'symmetric' in name:
            conjugation=[Operation(0x21,(12+i,i)) for i in range(12)]
            ops=conjugation+ops+conjugation
        proof=exact_polynomial_check(actual,ops)
        counts=Counter(x.opcode for x in ops)
        assert counts[0x31]==99
        case=dict(name=name,CX=counts[0x21],CCX=counts[0x31],proof=proof,source_sha256=digest(path))
        cases.append(case);candidates.append((counts[0x21],ops,case))
    _,best,record=min(candidates,key=lambda x:x[0])
    physical=[Operation(x.opcode,tuple(wires[q] for q in x.qubits)) for x in best]
    target=dest/'theory_bilinear_actual_cpr.kmx'
    write_kmx(target,physical)
    proof=exact_polynomial_check(parse(repo/'inverse_v2_actual_eea_product.kmx'),parse(target))
    c12=json.loads((r/'input_certificate.json').read_text())['records'][0]
    old12=standard(c12['terms'],12)
    tests12=[]
    for name in ('gf12_cpr_local','gf12_cpr1024_local'):
        ops=parse(r/(name+'.kmx'));p12=exact_polynomial_check(old12,ops)
        counts=Counter(x.opcode for x in ops)
        assert counts[0x31]==42
        tests12.append(dict(name=name,CX=counts[0x21],CCX=counts[0x31],proof=p12))
    write_kmx(dest/'theory_bilinear_gf12_cpr.kmx',parse(r/'gf12_cpr1024_local.kmx'))
    out=dict(status='PASS_EXACT_ARBITRARY_ACCUMULATOR_AND_PHASE',actual_block_cases=cases,
             chosen=dict(name=record['name'],before_CX=6122,after_CX=record['CX'],CCX=99,
                         removed_CX=6122-record['CX'],reduction_percent=100*(6122-record['CX'])/6122,
                         output_path=str(target),output_sha256=digest(target),proof=proof),
             gf12=dict(before_CX=sum(x.opcode==0x21 for x in old12),CCX=42,cases=tests12),
             elapsed_seconds=time.monotonic()-start,
             scope='Exact standalone block identity. Q and Toffoli unchanged; no Kaggle score improvement claimed.')
    (dest/'theory_bilinear_cpr_verification.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))


if __name__=='__main__':main()
