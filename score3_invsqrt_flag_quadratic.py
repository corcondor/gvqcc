#!/usr/bin/env python3
"""Three bounded quadratic-correction probes for nonlinear flag packing."""
from pathlib import Path
import json,hashlib,time
import score_invsqrt_retire as r
from score3_invsqrt_flag_pack_scan import xor_columns


CASES=[(36,15023,17277),(30,15029,17296),(6,15029,17295)]


def common_basis(entry,exit_state,target,domain):
    wires=[q for q in range(46) if q!=target]
    left=[domain]+[entry[q] for q in wires];right=[domain]+[exit_state[q] for q in wires]
    rb=r.affine_basis(right);qb={};functions=[domain];entry_coeff=[1];exit_coeff=[1];fb=r.affine_basis(functions)
    for j,f in enumerate(left):
        v=f
        for pivot in sorted(rb,reverse=True):
            if v>>pivot&1:v^=rb[pivot][0]
        c=1<<j
        while v:
            p=v.bit_length()-1
            if p not in qb:qb[p]=(v,c);break
            row,co=qb[p];v^=row;c^=co
        if not v:
            g=xor_columns(left,c)
            if r.solve(fb,g) is None:
                functions.append(g);entry_coeff.append(c);exit_coeff.append(r.solve(rb,g));fb=r.affine_basis(functions)
    return wires,functions,entry_coeff,exit_coeff


def product_polynomial(a,b):
    terms=set()
    for i in range(a.bit_length()):
        if not a>>i&1:continue
        for j in range(b.bit_length()):
            if b>>j&1:
                term=(1<<i)|(1<<j)
                if term in terms:terms.remove(term)
                else:terms.add(term)
    return terms


def main():
    start=time.monotonic();source=Path(__file__).with_name('invsqrt_structural_e46.kmx');_,ops=r.instructions(source)
    cuts={cut for q,a,b in CASES for cut in (a,b)};states={};domain,values=r.initial_values();stack=[]
    for i,(op,qs) in enumerate(ops):
        if i in cuts:states[i]=values[:]
        if op=='PUSH_CONDITION':stack.append(values[:])
        elif op=='POP_CONDITION':old=stack.pop();assert old==values;values=old
        else:r.advance(op,qs,values,domain)
    rows=[]
    for target,a,b in CASES:
        entry,exit_state=states[a],states[b]
        assert entry[target]==exit_state[target] and entry[24]==exit_state[24] and entry[25]==exit_state[25]
        assert not(entry[24]&entry[25])
        wires,functions,incoef,outcoef=common_basis(entry,exit_state,target,domain)
        restriction=entry[24]|entry[25]
        linear=[f&restriction for f in functions]
        pairs=[(i,j) for i in range(1,len(functions)) for j in range(i+1,len(functions))]
        features=linear+[linear[i]&linear[j] for i,j in pairs]
        basis=r.affine_basis(features);solution=r.solve(basis,entry[target]&restriction)
        row=dict(target=target,start=a,end=b,common_affine_rank=len(functions),restricted_inputs=restriction.bit_count(),
                 quadratic_features=len(features),restricted_rank=len(basis),status='NO_QUADRATIC_SHARED_CORRECTION')
        if solution is not None:
            polynomial=set();constant=bool(solution&1)
            for i in range(1,len(functions)):
                if solution>>i&1:polynomial.add(1<<(i-1))
            for k,(i,j) in enumerate(pairs,len(functions)):
                if solution>>k&1:polynomial.add((1<<(i-1))|(1<<(j-1)))
            products=[]
            while True:
                edges=[term for term in polynomial if term.bit_count()==2]
                if not edges:break
                edge=min(edges);u=edge&-edge;v=edge^u;left,right=u,v
                for term in edges:
                    if term==edge:continue
                    if term&u:right^=term^u
                    if term&v:left^=term^v
                products.append((left,right));polynomial.symmetric_difference_update(product_polynomial(left,right))
            assert all(term.bit_count()==1 for term in polynomial)
            remainder=0
            for term in polynomial:remainder^=term
            g=domain if constant else 0
            g^=xor_columns(functions[1:],remainder)
            for left,right in products:g^=xor_columns(functions[1:],left)&xor_columns(functions[1:],right)
            assert not((entry[target]^g)&restriction)
            h=entry[target]^g;assert h==((entry[24]^h)&(entry[25]^h))
            row.update(status='EXACT_QUADRATIC_PACK_FOUND',products=len(products),additional_ccx=2*len(products)+1,
                       constant=constant,remainder_hex=hex(remainder),product_forms_hex=[[hex(x),hex(y)] for x,y in products],
                       wires=wires,entry_coordinates_hex=[hex(c) for c in incoef],exit_coordinates_hex=[hex(c) for c in outcoef],
                       identity_inputs_verified=r.MAX_X)
        rows.append(row);print(json.dumps(row),flush=True)
    report=dict(status='THREE_SCOPED_PROBES_COMPLETE',cases=rows,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                scope='Quadratic polynomial of the affine intersection of endpoint functions; scoped constructive packing test, not a Q45 impossibility proof',
                seconds=time.monotonic()-start,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    Path(__file__).with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
