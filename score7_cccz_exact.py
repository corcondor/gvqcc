#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Exact Q(zeta_8) checks of CCCZ circuits from Nakanishi--Todo Fig. 1.

Primary source: arXiv:2410.00910v2, Fig. 1(a), (a'), (b), Table I.
The circuits are independently implemented gate by gate, not asserted from
the paper. All 16 data-basis columns and both measurement branches are checked
as linear operators, retaining their branch-global phases. This also checks a
coherent 15T relative-phase compute / 7T CCZ / inverse construction.

This is a research validation, NOT a competition circuit or score gain.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

ZERO=(0,0,0,0)
ONE=(1,0,0,0)

def add(a,b):return tuple(x+y for x,y in zip(a,b))
def neg(a):return tuple(-x for x in a)
def shift(a,k):
    r=[0]*4
    for j,x in enumerate(a):
        e=(j+k)%8
        r[e%4]+=x if e<4 else -x
    return tuple(r)
def mul(a,b):
    r=ZERO
    for j,x in enumerate(b):
        r=add(r,tuple(x*t for t in shift(a,j)))
    return r
def conjugate(a):
    r=ZERO
    for j,x in enumerate(a):r=add(r,shift((x,0,0,0),-j))
    return r

def simulate(gates,initial):
    # H is kept unnormalised. The final denominator is sqrt(2)^hcount.
    v=[ZERO]*32;v[initial]=ONE;hcount=0
    for g in gates:
        kind=g[0]
        if kind=='H':
            bit=1<<g[1];hcount+=1
            for i in range(32):
                if not i&bit:
                    a,b=v[i],v[i|bit]
                    v[i],v[i|bit]=add(a,b),add(a,neg(b))
        elif kind=='P':
            for i in range(32):
                if (i>>g[1])&1:v[i]=shift(v[i],g[2])
        elif kind=='CX':
            for i in range(32):
                if ((i>>g[1])&1) and not ((i>>g[2])&1):
                    j=i^(1<<g[2]);v[i],v[j]=v[j],v[i]
        else:raise ValueError(g)
    return v,hcount

def phase(k):return ('P',4,k)
def cx(q):return ('CX',q,4)
def figure_a():
    return [('H',4),phase(1),cx(3),phase(-1),cx(2),phase(1),cx(3),
            cx(1),phase(1),cx(0),phase(-1),cx(1),phase(1),('H',4)]
def figure_aprime():
    return [('H',4),phase(1),cx(3),phase(-1),cx(2),phase(1),cx(3),phase(-2),
            cx(1),phase(-1),cx(0),phase(1),cx(1),phase(-1),('H',4)]
def figure_b():
    return [('H',4),('CX',4,2),('CX',4,3),('P',2,-1),('P',3,-1),phase(1),
            ('CX',4,2),('CX',4,3),cx(3),cx(2),cx(1),cx(0),
            ('CX',4,0),('CX',4,1),('P',0,-1),('P',1,-1),phase(1),
            ('CX',4,0),('CX',4,1),('H',4)]
def correction(name,x,m):
    a,b,c,d=[(x>>j)&1 for j in range(4)]
    if name=='a':return m*(a*(1-b)+c*d)
    if name=='aprime':return m*a*(1-b)+(1-m)*c*d
    if name=='b':return m*((1-a)*(1-b)+c*d)
    raise ValueError(name)

def t_depth(gates):
    layers=[0]*5
    for g in gates:
        if g[0]=='P':layers[g[1]]+=bool(g[2]%2)
        elif g[0]=='CX':layers[g[1]]=layers[g[2]]=max(layers[g[1]],layers[g[2]])
    return max(layers)

def check_figure(name,gates,expected_depth,expected_cnot):
    branch_scalars=[None,None];checked=0
    for x in range(16):
        v,h=simulate(gates,x)
        assert h==2
        ideal_sign=-1 if x==15 else 1
        for m in (0,1):
            for y in range(16):
                amp=v[y+16*m]
                if correction(name,y,m)%2:amp=neg(amp)
                if x==y:
                    scalar=amp if ideal_sign==1 else neg(amp)
                    if branch_scalars[m] is None:branch_scalars[m]=scalar
                    assert scalar==branch_scalars[m],(name,x,m,scalar,branch_scalars)
                else:assert amp==ZERO,(name,x,y,m,amp)
                checked+=1
    assert all(mul(z,conjugate(z))==(2,0,0,0) for z in branch_scalars)
    t=sum(g[0]=='P' and bool(g[2]%2) for g in gates)
    cnot=sum(g[0]=='CX' for g in gates)
    assert t==6 and t_depth(gates)==expected_depth and cnot==expected_cnot
    feedback_cz=[1,1] if name=='aprime' else [0,2]
    return {'status':'PASS','data_qubits':4,'clean_ancillas':1,'measurement_branches':2,
            'exact_kraus_matrix_entries':checked,'t_count':t,'t_depth':t_depth(gates),
            'unconditional_cnot_count':cnot,'cnot_equivalent_including_cz_by_branch':
                [cnot+n for n in feedback_cz],
            'branch_scalar_numerators_in_basis_1_zeta_zeta2_zeta3':branch_scalars,
            'branch_scalar_denominator':2,'probability_each_branch':'1/2',
            'gates':gates,'correction_convention':'q0..q3 top-to-bottom; q4 ancilla; see correction()'}

def relative_ccx(a,b,t):
    return [('H',t),('P',t,1),('CX',b,t),('P',t,-1),('CX',a,t),
            ('P',t,1),('CX',b,t),('P',t,-1),('H',t)]
def inverse(gates):
    return [(g[0],g[1],-g[2]) if g[0]=='P' else g for g in reversed(gates)]
def seven_t_ccz(a,b,c):
    g=[('P',a,1),('P',b,1),('P',c,1)]
    for i,j in ((a,b),(a,c),(b,c)):g.extend([('CX',i,j),('P',j,-1),('CX',i,j)])
    g.extend([('CX',a,c),('CX',b,c),('P',c,1),('CX',b,c),('CX',a,c)])
    return g
def check_coherent():
    r=relative_ccx(0,1,4)
    gates=r+seven_t_ccz(4,2,3)+inverse(r)
    for x in range(16):
        v,h=simulate(gates,x)
        assert h==4
        for y in range(32):
            expected=((-4 if x==15 else 4),0,0,0) if y==x else ZERO
            assert v[y]==expected,(x,y,v[y],expected)
    t=sum(g[0]=='P' and bool(g[2]%2) for g in gates)
    assert t==15
    return {'status':'PASS','t_count':t,'clean_ancillas':1,'measurement_count':0,
            'exact_isometry_entries':16*32,'ancilla_restored_to_zero':True,'gates':gates}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,default=Path(__file__).with_suffix('.json'))
    args=ap.parse_args()
    figures={name:check_figure(name,gates,depth,cnot) for name,gates,depth,cnot in [
        ('a',figure_a(),6,6),('aprime',figure_aprime(),6,6),('b',figure_b(),2,12)]}
    result={'status':'PASS','source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'primary_source':'https://arxiv.org/abs/2410.00910v2',
        'proof_domain':'Integer arithmetic in Z[zeta_8], zeta_8^4=-1; explicit common denominator',
        'figures':figures,'coherent_15t':check_coherent(),
        'competition_artifact_changed':False,'competition_score_improvement':None}
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'figures':{k:{n:v[n] for n in ['t_count','t_depth','cnot_equivalent_including_cz_by_branch','exact_kraus_matrix_entries']} for k,v in figures.items()},
        'coherent_15t':{k:v for k,v in result['coherent_15t'].items() if k!='gates'}}))

if __name__=='__main__':main()
