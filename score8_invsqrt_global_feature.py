#!/usr/bin/env python3
"""Direct official-cost search for a new generic phase on any tape value.

Unlike fixed local XOR/AND optimization, this allows changed approximation
and a new phase predicate anywhere outside a classically controlled block.
The incumbent arithmetic is retained. Minimax dual constraints rank all
observed intermediate values; coarse LP upper bounds screen candidates, then
the complete input domain separates any promising fit.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from fractions import Fraction
import json
import math
from pathlib import Path
import time

import numpy as np
from scipy.optimize import linprog

import score_invsqrt_retire as R
from score8_invsqrt_phase_quadratic import PIN,sha,sample_values
from score8_invsqrt_sparse_phase import load,matvec,MAX,SCALE,ROOT


def opt(B,e,t,new,active,maxiter=25,full=True,fixed=()):
    C=B if new is None else np.column_stack((B,new));n=len(C);r=C.shape[1];obj=np.zeros(r+1);obj[-1]=-1
    bounds=[(-1e6,1e6)]*r+[(None,None)]
    for index,value in fixed:bounds[index]=(value,value)
    active=np.unique(active)
    for it in range(maxiter):
        a=np.asarray(C[active],dtype=float)
        res=linprog(obj,A_ub=np.column_stack((np.vstack((a,-a)),np.ones(2*len(active)))),b_ub=np.r_[t[active]-e[active],t[active]+e[active]],bounds=bounds,method='highs',options={'dual_feasibility_tolerance':1e-8,'primal_feasibility_tolerance':1e-8})
        if not res.success:return {'status':'FAILED','message':res.message},None,None
        if not full:
            return {'status':'COARSE_BOUND','upper_margin_turns':float(res.x[-1])*SCALE,'coeff_scaled':res.x[:-1].tolist()},res,active
        err=e+matvec(C,res.x[:-1]);m=t-abs(err);mn=float(m.min());gap=float(res.x[-1]-mn)
        row={'status':'CONVERGED' if gap<1e-7 else 'ITERATING','min_margin_turns':mn*SCALE,'gap_turns':gap*SCALE,'iterations':it+1,'max_error_ratio':float(np.max(abs(err)/t)),'coeff_scaled':res.x[:-1].tolist()}
        if gap<1e-7:return row,res,active
        active=np.unique(np.r_[active,np.argpartition(m,128)[:128]])
    return row,res,active


def unpack(value,n):return np.unpackbits(np.frombuffer(value.to_bytes((n+7)//8,'little'),dtype=np.uint8),bitorder='little')[:n]


def collect(lines,ops,xs,weights):
    one,values=sample_values(xs);seen=set();candidates=[];stack=[]
    support=[(int(i),float(w)) for i,w in enumerate(weights) if abs(w)>1e-10]
    def take(cut,q):
        v=values[q]
        if not v or v in seen:return
        seen.add(v);correlation=sum(w for i,w in support if v>>i&1)
        if abs(correlation)>1e-9:candidates.append({'cut':cut,'wire':q,'dual_correlation':correlation,'value':v})
    for q in range(22):take(0,q)
    for i,(op,qs) in enumerate(ops):
        if op=='PUSH_CONDITION':stack.append(values[:])
        elif op=='POP_CONDITION':assert values==stack.pop()
        else:R.advance(op,qs,values,one)
        if stack:continue
        if op in ('X','CX','CCX'):take(i+1,qs[-1])
        elif op in ('SWAP','CSWAP'):
            for q in qs[-2:]:take(i+1,q)
    candidates.sort(key=lambda c:-abs(c['dual_correlation']))
    return candidates,len(seen),len(support)


def full_features(lines,ops,candidates):
    at=defaultdict(list)
    for j,c in enumerate(candidates):at[c['cut']].append((j,c['wire']))
    one,values=R.initial_values();features={};stack=[]
    for i,(op,qs) in enumerate(ops):
        for j,q in at[i]:features[j]=unpack(values[q]>>1,MAX)
        if len(features)==len(candidates):break
        if op=='PUSH_CONDITION':stack.append(values[:])
        elif op=='POP_CONDITION':assert values==stack.pop()
        else:R.advance(op,qs,values,one)
    return features


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--limit',type=int,default=600);ap.add_argument('--full-limit',type=int,default=30);ap.add_argument('--drop',type=int,nargs='*',default=[]);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True);begin=time.monotonic()
    source=ROOT/'score3_invsqrt_cache.kmx';assert sha(source)==PIN;lines,ops=R.instructions(source)
    B,e,t,desc=load(ROOT.parent/'invsqrt_structural_work');margin=t-abs(e);initial=np.unique(np.r_[np.arange(2048),np.linspace(0,MAX-1,2048,dtype=int),np.argpartition(margin,1024)[:1024]])
    fixed=[(j,-float(Fraction(desc[j]['half_turns'])/2)/SCALE) for j in a.drop]
    incumbent,_,_=opt(B,e,t,None,initial)
    baseline,res,active=opt(B,e,t,None,initial,fixed=fixed);dual=res.ineqlin.marginals;weights=dual[:len(active)]-dual[len(active):]
    candidates,total,support=collect(lines,ops,(active+1).tolist(),weights)
    baseline_rot=33*(.56*math.log2(33/(math.pi*incumbent['min_margin_turns']))+5.3)/4
    nrot=34-len(a.drop)
    threshold=nrot/(math.pi*2**((4*baseline_rot/nrot-5.3)/.56))
    # Every coarse constraint is a legal input constraint, so its optimum is
    # an upper bound on the same bounded fit's complete-domain margin.
    tight=np.argsort(margin[active])[:512];nonzero=np.flatnonzero(abs(weights)>1e-10)
    coarse=np.unique(np.r_[tight,nonzero,np.linspace(0,len(active)-1,256,dtype=int)])
    BB=B[active][coarse];ee=e[active][coarse];tt=t[active][coarse];ca=np.arange(len(coarse))
    rows=[];promising=[]
    for j,c in enumerate(candidates[:a.limit]):
        v=unpack(c['value'],len(active))[coarse];fit,_,_=opt(BB,ee,tt,v,ca,full=False,fixed=fixed)
        row={k:v for k,v in c.items() if k!='value'};row.update(fit=fit,candidate_rank=j)
        rows.append(row)
        if fit.get('upper_margin_turns',-math.inf)>threshold:promising.append(row)
        if (j+1)%100==0:print(json.dumps({'coarse_trials':j+1,'potential_improvement':len(promising),'seconds':time.monotonic()-begin}),flush=True)
    promising.sort(key=lambda c:-c['fit']['upper_margin_turns']);selected=promising[:a.full_limit]
    print(json.dumps({'unique_tape_values':total,'nonzero_dual_candidates':len(candidates),'dual_support':support,'baseline_margin_turns':baseline['min_margin_turns'],'profit_margin_threshold_turns':threshold,'coarse_trials':len(rows),'promising':len(promising),'selected_full_domain':len(selected),'seconds':time.monotonic()-begin}),flush=True)
    full=[]
    if selected:
        features=full_features(lines,ops,selected)
        for j,c in enumerate(selected):
            fit,_,_=opt(B,e,t,features[j],active,fixed=fixed);row={**c,'full_fit':fit}
            m=fit.get('min_margin_turns',0)
            if m>0:row['predicted_cost']=46*(1478.7506100300882+.25+nrot*(.56*math.log2(nrot/(math.pi*m))+5.3)/4)
            full.append(row);print(json.dumps({'rank':j,'cut':c['cut'],'wire':c['wire'],'margin':m,'cost':row.get('predicted_cost'),'seconds':time.monotonic()-begin}),flush=True)
    report={'source_sha256':PIN,'incumbent_fit':incumbent,'baseline_fit':baseline,'dropped_generic_indices':a.drop,'new_generic_rotation_count':nrot,'unique_tape_values':total,'dual_support':support,'nonzero_dual_candidates':len(candidates),'coarse_trials':len(rows),'coarse_rows':rows,'profit_margin_threshold_turns':threshold,'full_results':full,'improving_candidates':[r for r in full if r.get('predicted_cost',math.inf)<78673.55534364567-1e-3],'minimum_cost_difference_for_candidate':1e-3,'seconds':time.monotonic()-begin,'scope':'One new generic rotation on an actually generated intermediate wire value, all unconditional tape locations; dual-ranked bounded subset, all 3133452 inputs for shortlisted fits; existing33angles refit within +-1e-5turns, named removals fixed exactly zero. No new arithmetic or qubits assumed. Predicted changes below 1e-3 cost are numerical ties, not accepted gains.'}
    (a.out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'improving_count':len(report['improving_candidates']),'seconds':report['seconds']}),flush=True)


if __name__=='__main__':main()
