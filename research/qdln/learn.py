#!/usr/bin/env python3
"""Griffith-inspired differentiable selection over one-AND rank-2 features.

The continuous loss is only a proposal mechanism. The hard output must pass
exact GF(2) factorization + exhaustive truth-table verification, or it is
rejected. Torch training is not a substitute for quantum phase verification.
"""
from __future__ import annotations
import argparse
import json
import math
import random
from solver import anf,rank2_pool,coords,truth_product,Solution


def quad_truth(q,n=4):
    from itertools import combinations
    result=0
    for x in range(1<<n):
        bit=0
        for j,(i,k) in enumerate(combinations(range(n),2)):
            if q>>j&1:bit ^= ((x>>i)&1)&((x>>k)&1)
        result |= bit<<x
    return result


def train(tables,number_of_ands=2,epochs=800,restarts=8,seed=42):
    import torch
    n=4
    tables=list(map(int,tables))
    quads=[anf(t,n)[2] for t in tables]
    if any(anf(t,n)[3] for t in tables):
        raise ValueError("degree>2 target")
    pool=rank2_pool(n); qs=sorted(pool)
    truth=[quad_truth(q,n) for q in qs]
    X=torch.tensor([[(t>>i)&1 for t in truth] for i in range(16)],dtype=torch.float32)
    targets=torch.tensor([[(quad_truth(q,n)>>i)&1 for q in quads] for i in range(16)],dtype=torch.float32)
    torch.set_num_threads(1)
    rng=random.Random(seed)
    best=float("inf")
    for run in range(restarts):
        torch.manual_seed(rng.randrange(2**31))
        logits=torch.nn.Parameter(torch.randn(number_of_ands,len(qs))*.15)
        wiring=torch.nn.Parameter(torch.randn(len(quads),number_of_ands)*.1)
        optimizer=torch.optim.Adam([logits,wiring],lr=0.08)
        for step in range(epochs):
            selected=torch.softmax(logits,dim=1)
            hidden=X@selected.T
            outw=torch.sigmoid(wiring)
            prediction=(1-torch.prod(1-2*hidden[:,None,:]*outw[None,:,:],dim=2))/2
            data_loss=((prediction-targets)**2).mean()
            entropy=-(selected*selected.clamp_min(1e-9).log()).sum(1).mean()
            loss=data_loss + 0.025*(0.2+0.8*step/max(1,epochs-1))*entropy+0.002*outw.mean()
            optimizer.zero_grad();loss.backward();optimizer.step()
            if step%30!=0 and step!=epochs-1:continue
            best=min(best,float(data_loss.detach()))
            with torch.no_grad():
                chosen=[qs[j] for j in selected.argmax(dim=1).tolist()]
                coef=[coords(q,chosen) for q in quads]
                if any(c is None for c in coef):continue
                products=[pool[q] for q in chosen]
                affine=[]
                for t,c in zip(tables,coef):
                    pred=0
                    for j,(l,r) in enumerate(products):
                        if c>>j&1:pred^=truth_product(l,r,n)
                    b,a,q,h=anf(t^pred,n)
                    assert not q and not h
                    affine.append(a|(b<<n))
                solution=Solution(n,products,coef,affine,tables,0)
                assert solution.verify()
                return solution,{"status":"CERTIFIED_EXACT","steps":run*epochs+step+1,
                                 "soft_training_loss":float(data_loss),
                                 "products":len(products),"note":"GF(2) hard outputs verified on all 16 inputs"}
    return None,{"status":"NOT_CERTIFIED","best_soft_loss":best,
                 "note":"Failure to train is not a lower bound"}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--truths",required=True)
    p.add_argument("--ands",type=int,default=2)
    a=p.parse_args()
    solution,receipt=train(json.loads(a.truths),number_of_ands=a.ands)
    from dataclasses import asdict
    print(json.dumps({"training":receipt,"solution":asdict(solution) if solution else None},indent=2))


if __name__=="__main__":main()
