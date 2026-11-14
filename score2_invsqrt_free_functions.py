#!/usr/bin/env python3
"""Find free live-wire parities which are functions of the six local inputs.

This computes an exact intersection of two function spaces over all legal x:
the affine span of all retained live wires, and all functions constant on each
of the 47 fibers of the six-input table.
"""
import json
from pathlib import Path
import score_invsqrt_retire as r
from score_invsqrt_joint_synthesis import INPUTS,REPLACE_START

def main():
    base=Path(__file__).parent;lines,ops=r.instructions(base/'invsqrt_structural_e46.kmx')
    domain,values=r.initial_values();stack=[]
    for i,(op,qs) in enumerate(ops):
        if i==REPLACE_START:break
        if op=='PUSH_CONDITION':stack.append(values[:])
        elif op=='POP_CONDITION':before=stack.pop();assert before==values;values=before
        else:r.advance(op,qs,values,domain)
    rows=json.loads((base/'score_invsqrt_joint_table.json').read_text())['rows'];patterns=[x for x,y in rows]
    indicators=[]
    for pattern in patterns:
        mask=domain
        for j,q in enumerate(INPUTS):mask&=values[q] if pattern>>j&1 else domain^values[q]
        assert mask;indicators.append(mask)
    representatives=[mask.bit_length()-1 for mask in indicators]
    live=[q for q,v in enumerate(values) if v];columns=[domain]+[values[q] for q in live]
    def fiber_quotient(value):
        for mask,x in zip(indicators,representatives):
            if value>>x&1:value^=mask
        return value
    basis={};kernel=[]
    for j,column in enumerate(columns):
        s=fiber_quotient(column);c=1<<j
        while s:
            p=s.bit_length()-1
            if p not in basis:basis[p]=(s,c);break
            v,k=basis[p];s^=v;c^=k
        if not s:kernel.append(c)
    one=(1<<len(patterns))-1
    known=[one]+[sum(((x>>j)&1)<<i for i,x in enumerate(patterns)) for j in range(len(INPUTS))]
    found=[]
    for c in kernel:
        value=0
        for j,col in enumerate(columns):
            if c>>j&1:value^=col
        assert fiber_quotient(value)==0
        table=sum(((value>>x)&1)<<i for i,x in enumerate(representatives))
        if r.solve(r.affine_basis(known),table) is None:
            found.append({'constant':c&1,'qubits':[q for j,q in enumerate(live) if c>>(j+1)&1],
                          'function_on_47_patterns_hex':hex(table),'full_domain_check':'PASS'})
            known.append(table)
    report={'legal_inputs':r.MAX_X,'live_wires':len(live),'fiber_patterns':len(patterns),
            'fiber_residual_rank':len(basis),'intersection_dimension':len(kernel),
            'original_affine_function_dimension':7,'additional_free_functions':found,
            'scope':'all affine combinations of all retained live wires which depend only on the six local inputs; not arbitrary nonlinear uses of other wires'}
    (base/'score2_invsqrt_free_functions.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))

if __name__=='__main__':main()
