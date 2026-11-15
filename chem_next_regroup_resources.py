#!/usr/bin/env python3
"""Screen exact Hamiltonian-preserving ensemble regroupings with official costs.

Split each original ensemble's C columns into s equal pieces, duplicating its
B orbital vectors, then merge m old rho groups into each new group using block
diagonal W columns. This preserves the sum of squared operators and each
column L1 norm. Padding W/H2_I with zeros is also exact. New angle loaders
are NOT synthesized here; comparison assumes unchanged loader count as an
optimistic screening value rather than a verified improvement.
"""
import hashlib, importlib.util, json, math, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
MODEL=ROOT/'chem_next_official_costs_copy.py'
spec=importlib.util.spec_from_file_location('chem_next_costmodel',MODEL)
mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)

def metrics(r,b,c):
    model=mod.SpinFreeData_V1(R=r,B=b,C=c,N=76,chi=10,beta=8)
    oq=model.outer_state_prep_qubit_cost();iq=model.inner_state_prep_qubit_cost()
    q=oq['persistent']+iq['persistent']+40+max(oq['temporary'],iq['temporary'])
    heuristic=model.outer_state_prep()+model.inner_state_prep()+model.givens_rotations()
    return dict(R=r,B=b,C=c,Q=q,heuristic_T=heuristic,inner_temp=iq['temporary'],
                T_assuming_unchanged_loader=heuristic+8060,
                QT_ratio_assuming_unchanged_loader=q*(heuristic+8060)/(427*14722),
                loader_perpass_break_even=(427*14722/q-heuristic)/2)

def main():
    rows=[]
    for s in (1,2,4,11,22,44):
        for m in (1,2,4,8):
            row=metrics(8*s//m,143*m,44*m//s)
            row.update(construction='split_C_then_merge_rho',split=s,merge=m)
            rows.append(row)
    for b in range(143,257):
        for c in (44,45,48,64,88):
            row=metrics(8,b,c);row.update(construction='zero_padding');rows.append(row)
    rows.sort(key=lambda x:x['QT_ratio_assuming_unchanged_loader'])
    result=dict(status='NO_RESOURCE_GAIN_IN_SCREENED_EXACT_REGROUPINGS',
      model_sha256=hashlib.sha256(MODEL.read_bytes()).hexdigest(),
      model_source='Inzainos/quantum-circuit-compilation@4277c767440df9efb8a90860ae2ce47028e46ba9/verifiers/dfthcsos/scoreinfra/costs_prepare.py',
      baseline=metrics(8,143,44),configurations=len(rows),rows=rows,
      new_circuit_synthesized=False,official_full_verification=False,
      scope='Finite exact regrouping and zero-padding family; fixed-loader cost is an assumption, not a lower bound for arbitrary resynthesis.')
    out=ROOT/'chem_next_regroup_resources.json';out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'configurations':len(rows),'best':rows[:7]},indent=2))

if __name__=='__main__':main()
