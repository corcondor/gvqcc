#!/usr/bin/env python3
"""Independent degree-two interpolation check for the routed DQI kernel.

Does not import the production ANF checker or Polytof. First certifies the
bilinear accumulator gate structure, then evaluates zero, every singleton,
and every pair of arbitrary input bits. These evaluations uniquely determine
every coefficient of a Boolean polynomial of degree at most two.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path


def parse(path,group):
    gates=[]
    for number,line in enumerate(path.read_text().splitlines(),1):
        if not line.strip() or line.startswith('#'):continue
        fields=line.split();op=fields[0]
        if op not in {'CX','CCX'}:raise AssertionError((number,op))
        args=tuple(int(x[1:]) for x in fields[1:] if x.startswith('q'))
        assert len(fields)==len(args)+1
        assert len(args)==(2 if op=='CX' else 3)
        assert len(set(args))==len(args)
        if op=='CX':assert group[args[0]]==group[args[1]]
        else:assert {group[args[0]],group[args[1]]}=={0,1} and group[args[2]]==2
        gates.append((op,args))
    return gates


def evaluate(gates,initial):
    values=dict(initial)
    for op,q in gates:
        if op=='CX':values[q[1]]^=values[q[0]]
        else:values[q[2]]^=values[q[0]]&values[q[1]]
    return values


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo-dir',type=Path,default=Path(__file__).parent)
    p.add_argument('--report',type=Path,required=True)
    args=p.parse_args();root=args.repo_dir
    cert=json.loads((root/'inverse_v2_actual_eea_product_certificate.json').read_text())
    groups=[cert['input_left'],cert['input_right'],cert['output_qubits_in_field_order']]
    wires=sum(groups,[]);assert len(wires)==len(set(wires))==72
    group={q:g for g,qs in enumerate(groups) for q in qs}
    old=root/'inverse_v2_actual_eea_product.kmx';new=root/'theory_bilinear_actual_cpr.kmx'
    before=parse(old,group);after=parse(new,group)
    cases=[0]+[1<<i for i in range(72)]+[(1<<i)|(1<<j) for i,j in itertools.combinations(range(72),2)]
    initial={q:sum(((c>>i)&1)<<j for j,c in enumerate(cases)) for i,q in enumerate(wires)}
    assert evaluate(before,initial)==evaluate(after,initial)
    result={'status':'PASS_INDEPENDENT_EXACT_DEGREE_TWO_INTERPOLATION',
            'arbitrary_input_bits':72,'coefficient_determining_inputs':len(cases),
            'degree_bound_proved_by_gate_structure':2,
            'cnot_rule':'Both operands stay inside one of the two input or one output registers.',
            'ccx_rule':'One control in each input register, target in output register; all operands distinct.',
            'proof':'Input registers remain linear in their own original variables. Output registers remain degree<=2. Evaluations at 0,e_i,e_i+e_j uniquely determine every Boolean ANF coefficient of degree<=2. All 72 output polynomials agree, so the maps agree for all2^72 inputs, arbitrary superpositions and entanglement. Both gate sets are positive permutation matrices, so no relative phase is introduced.',
            'before_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),
            'after_sha256':hashlib.sha256(new.read_bytes()).hexdigest(),
            'before_CX':sum(op=='CX' for op,_ in before),'after_CX':sum(op=='CX' for op,_ in after),
            'before_CCX':sum(op=='CCX' for op,_ in before),'after_CCX':sum(op=='CCX' for op,_ in after),
            'scope':'Standalone72-wireblock; fullKMBplacement and official scoring are separate checks.'}
    if args.report.exists():raise FileExistsError(args.report)
    args.report.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
