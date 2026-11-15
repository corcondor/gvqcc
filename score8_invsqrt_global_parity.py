#!/usr/bin/env python3
"""Minimax-dual-guided free parity features throughout the invsqrt tape.

Uses arbitrary affine parities of retained wires, not merely the single
intermediate values or two-wire parities tested in earlier experiments.
Computing such a parity in one of its participating wires and restoring it
uses CX/X only and adds neither qubits nor Toffoli gates.
"""
from __future__ import annotations
from collections import defaultdict
import json
from pathlib import Path
import sys

import numpy as np

import score_invsqrt_retire as R
import score8_invsqrt_global_feature as G
from score8_invsqrt_phase_quadratic import sample_values

STATE={}
ORIGINAL_OPT=G.opt


def opt(*args,**kwargs):
    result,res,active=ORIGINAL_OPT(*args,**kwargs)
    if args[3] is None and kwargs.get('full',True):
        B,e,t=args[:3];fixed=kwargs.get('fixed',())
        STATE.update(B=B,e=e,t=t,active=active,fixed=fixed)
    return result,res,active


def collect(lines,ops,xs,weights):
    one,values=sample_values(xs);seen=set();candidates=[];stack=[];nonlinear=0
    support=sorted(np.flatnonzero(abs(weights)>1e-10),key=lambda j:-abs(weights[j]));cutcount=0;solves=0;found=0
    def take(cut):
        nonlocal cutcount,solves,found
        cutcount+=1
        for count in sorted(set((len(support),min(24,len(support)),min(20,len(support))))):
            chosen=support[:count];target=sum(int(weights[i]>0)<<j for j,i in enumerate(chosen));mask=(1<<count)-1
            signals=[sum(((v>>int(i))&1)<<j for j,i in enumerate(chosen)) for v in values]
            for order in (list(range(46)),list(reversed(range(46)))):
                base=R.affine_basis([mask]+[signals[q] for q in order]);coeff=R.solve(base,target);solves+=1
                if coeff is None:continue
                found+=1;constant=coeff&1;wires=[q for j,q in enumerate(order) if coeff>>(j+1)&1]
                if not wires:continue
                v=one if constant else 0
                for q in wires:v^=values[q]
                if not v or v in seen:continue
                seen.add(v);corr=sum(float(weights[i]) for i in support if v>>int(i)&1)
                if abs(corr)<1e-9:continue
                candidates.append({'cut':cut,'wire':wires[0],'wires':wires,'constant':constant,'dual_correlation':corr,'value':v,'critical_constraints_fitted':count})
    take(0)
    for i,(op,qs) in enumerate(ops):
        if op=='PUSH_CONDITION':stack.append(values[:])
        elif op=='POP_CONDITION':assert values==stack.pop()
        else:R.advance(op,qs,values,one)
        if stack or op not in ('CCX','CSWAP','HMR'):continue
        nonlinear+=1
        if nonlinear%5==0:take(i+1)
    # Distinct critical-point solutions can behave very differently elsewhere.
    # Rank them by projection onto the weighted residual on all active rows.
    active=STATE['active'];fixed=STATE['fixed'];keep=[j for j in range(STATE['B'].shape[1]) if j not in {q for q,_ in fixed}]
    As=STATE['B'][active];weight=1/np.maximum(STATE['t'][active],1.)
    y=-STATE['e'][active].copy()
    for j,c in fixed:y-=As[:,j]*c
    A=np.asarray(As[:,keep],dtype=float)*weight[:,None];Q,_=np.linalg.qr(A,mode='reduced');y*=weight;residual=y-Q@(Q.T@y)
    for start in range(0,len(candidates),128):
        batch=candidates[start:start+128];V=np.asarray([G.unpack(c['value'],len(xs)) for c in batch],dtype=float)*weight[None,:]
        projected=V@Q;norm=np.maximum(np.sum(V*V,axis=1)-np.sum(projected*projected,axis=1),1e-12);score=(V@residual)**2/norm
        for c,s in zip(batch,score):c['ls_projection_score']=float(s)
    candidates.sort(key=lambda c:-c['ls_projection_score'])
    STATE.update(parity_cuts=cutcount,linear_systems=solves,solvable=found,unique_parities=len(seen))
    print(json.dumps({'parity_cuts':cutcount,'linear_systems':solves,'solvable_systems':found,'unique_parities':len(seen),'ranked':len(candidates)}),flush=True)
    return candidates,len(seen),len(support)


def full_features(lines,ops,candidates):
    at=defaultdict(list)
    for j,c in enumerate(candidates):at[c['cut']].append((j,c))
    one,values=R.initial_values();features={};stack=[]
    for i,(op,qs) in enumerate(ops):
        for j,c in at[i]:
            v=one if c['constant'] else 0
            for q in c['wires']:v^=values[q]
            features[j]=G.unpack(v>>1,G.MAX)
        if len(features)==len(candidates):break
        if op=='PUSH_CONDITION':stack.append(values[:])
        elif op=='POP_CONDITION':assert values==stack.pop()
        else:R.advance(op,qs,values,one)
    return features


if __name__=='__main__':
    G.opt=opt;G.collect=collect;G.full_features=full_features;G.main()
    out=Path(sys.argv[sys.argv.index('--out')+1])/'result.json';d=json.loads(out.read_text())
    d.update(parity_cuts=STATE['parity_cuts'],linear_systems=STATE['linear_systems'],solvable_systems=STATE['solvable'],unique_parities=STATE['unique_parities'])
    d['scope']='New generic phase on an arbitrary affine parity of live wires at every fifth unconditional nonlinear event. Critical inputs chosen by minimax LP dual weights, arbitrary parity solved by GF(2), alternate physical column orders, weighted residual ranking. Full legal domain for shortlisted fits. Named existing phases fixed to zero; no extra qubits or Toffoli required for parity compute/uncompute. Numerical ties below 1e-3 cost are not accepted gains.'
    out.write_text(json.dumps(d,indent=2)+'\n')
