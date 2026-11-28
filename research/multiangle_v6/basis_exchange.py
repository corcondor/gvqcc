#!/usr/bin/env python3
"""Exact-cost local GL(H,2) row exchanges for the rank-r-HMR emitter.

Given a cofactor basis G and selectors b such that F=sum b_j G_j,
replace G_j <- G_j+G_k and b_k <- b_k+b_j. This preserves F exactly.
The measured high selector costs rank_GF2(8x3(b_j)), and low cofactor
costs the actual chosen multi-output low-ANF emitter product count.
Greedy pair swaps improve the *coupled exact emitted CCX count*; not
an optimum over all reversible circuits or GL(20,2).
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.extend([str(ROOT/('gvqcc_multiform' if (ROOT/'gvqcc_multiform').exists() else '.')),str(ROOT/('gvqcc_multiform_v5' if (ROOT/'gvqcc_multiform_v5').exists() else 'multiangle_v5'))])
from high_group_basis import cf_cost
from screen_global_axis import high_selector_rank


def xorcoefs(a,b):
    return tuple(x^y for x,y in zip(a,b))


def cost(coef,sel):
    if not any(coef):return 0
    return cf_cost(coef)[1]+high_selector_rank(sel)


def verify_transform(masks,selectors,coefs,n):
    if len(masks)!=n or len(selectors)!=n or len(coefs)!=n:raise ValueError('dimension mismatch')
    for old in range(n):
        v=0
        for j in range(n):
            if selectors[j]>>old&1:v^=masks[j]
        if v!=(1<<old):raise AssertionError(('noninvertible_transform',old,v))
    return True


def optimize(masks,selectors,coefs,max_steps=120):
    masks=list(masks);selectors=list(selectors);coefs=[tuple(x) for x in coefs]
    n=len(masks)
    verify_transform(masks,selectors,coefs,n)
    weights=[cost(g,b) for g,b in zip(coefs,selectors)]
    original=sum(weights);history=[];scans=0
    for step in range(max_steps):
        best_delta=0;best=None
        for j in range(n):
            for k in range(n):
                if j==k:continue
                scans+=1
                nextcoef=xorcoefs(coefs[j],coefs[k])
                nextsel=selectors[k]^selectors[j]
                new_j=cost(nextcoef,selectors[j]);new_k=cost(coefs[k],nextsel)
                delta=new_j+new_k-weights[j]-weights[k]
                if delta<best_delta:
                    best_delta=delta;best=(j,k,nextcoef,nextsel,new_j,new_k)
        if best is None:break
        j,k,nc,ns,nj,nk=best
        old=weights[j]+weights[k]
        masks[j]^=masks[k]
        coefs[j]=nc
        selectors[k]=ns
        weights[j]=nj;weights[k]=nk
        history.append(dict(iteration=step,j=j,k=k,saving=-best_delta,
                            old_pair=old,new_pair=nj+nk,total=sum(weights)))
        verify_transform(masks,selectors,coefs,n)
    if sum(weights)>original:raise AssertionError('cost increased')
    return masks,selectors,coefs,dict(previous_cost=original,cost=sum(weights),
                                     savings=original-sum(weights),steps=len(history),
                                     candidate_evaluations=scans,history=history)
