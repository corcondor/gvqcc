#!/usr/bin/env python3
"""Find idle-wire retirement intervals and certify a one-product reconstruction.

This is a nonlinear lifetime search, distinct from single-gate affine deletion.
All positive identities are checked on every legal x. An accepted retirement
would X-measure the idle wire, reuse the zero wire, reconstruct its value, and
repay the measurement sign with conditioned Z on the restored value.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import re
import time
import numpy as np

MAX_X=3133452
PIN='e46d90c36d1beb3ce7731a3e0b5c3659b3cda7f5f290b73c6c34513d96c005b6'


def instructions(path):
    lines=path.read_text().splitlines()
    return lines,[(l.split()[0],tuple(map(int,re.findall(r'\bq(\d+)\b',l)))) for l in lines]


def initial_values():
    xs=np.arange(MAX_X+1,dtype=np.uint32);domain=((1<<(MAX_X+1))-1)^1
    vals=[int.from_bytes(np.packbits(((xs>>j)&1).astype(np.uint8),bitorder='little').tobytes(),'little')&domain for j in range(22)]+[0]*24
    return domain,vals


def advance(op,qs,vals,domain):
    if op=='X':q,=qs;vals[q]^=domain
    elif op=='CX':a,t=qs;vals[t]^=vals[a]
    elif op=='CCX':a,b,t=qs;vals[t]^=vals[a]&vals[b]
    elif op=='CSWAP':c,a,b=qs;d=vals[c]&(vals[a]^vals[b]);vals[a]^=d;vals[b]^=d
    elif op=='SWAP':a,b=qs;vals[a],vals[b]=vals[b],vals[a]
    elif op=='HMR':q,=qs;vals[q]=0


def scan(lines,ops):
    domain,vals=initial_values();stack=[];depth=[0];masks=[]
    refs=[[] for _ in vals];peak=[]
    for i,(op,qs) in enumerate(ops):
        masks.append(sum(1<<q for q,v in enumerate(vals) if v))
        for q in qs:refs[q].append(i)
        if op=='PUSH_CONDITION':stack.append(vals[:])
        elif op=='POP_CONDITION':before=stack.pop();assert vals==before;vals=before
        else:advance(op,qs,vals,domain)
        depth.append(len(stack))
        if all(vals):peak.append(i+1)
    masks.append(sum(1<<q for q,v in enumerate(vals) if v))
    intervals=[]
    for q,uses in enumerate(refs):
        for a,b in zip(uses,uses[1:]):
            start=a+1
            while start<b and depth[start]:start+=1
            end=b
            while end>start and depth[end]:end-=1
            if end<=start or not (masks[start]>>q&1):continue
            covered=[p for p in peak if start<=p<end]
            if covered:intervals.append({'q':q,'start':start,'end':end,'covered':covered,'span':end-start})
    return masks,depth,peak,intervals


def affine_basis(signatures):
    basis={}
    for j,s in enumerate(signatures):
        c=1<<j
        while s:
            p=s.bit_length()-1
            if p not in basis:basis[p]=(s,c);break
            t,d=basis[p];s^=t;c^=d
    return basis


def solve(basis,s):
    c=0
    while s:
        p=s.bit_length()-1
        if p not in basis:return None
        t,d=basis[p];s^=t;c^=d
    return c


def one_product(vals,target,domain,samples,max_left=2):
    eligible=[q for q in range(46) if q!=target and vals[q]]
    sig=[sum(((vals[q]>>x)&1)<<j for j,x in enumerate(samples)) for q in eligible]
    ts=sum(((vals[target]>>x)&1)<<j for j,x in enumerate(samples));one=(1<<len(samples))-1
    affine=[one]+sig
    base=affine_basis(affine);hit=solve(base,ts)
    def full_affine(c):
        v=domain if c&1 else 0
        for j,q in enumerate(eligible):
            if c>>(j+1)&1:v^=vals[q]
        return v
    if hit is not None and full_affine(hit)==vals[target]:
        return {'and_count':0,'constant':hit&1,'linear':[q for j,q in enumerate(eligible) if hit>>(j+1)&1]}
    # Exact coefficient search for B and the affine remainder for each A.
    lefts=[(j,) for j in range(len(eligible))]
    if max_left>=2:lefts += [(i,j) for i in range(len(eligible)) for j in range(i+1,len(eligible))]
    checks=0
    for left in lefts:
        a=0
        for j in left:a^=sig[j]
        features=affine+[a&s for s in sig]
        signatures=features;target_sig=ts;width=len(samples)
        for refine in range(len(features)+1):
            c=solve(affine_basis(signatures),target_sig)
            if c is None:break
            lin=c&((1<<len(affine))-1);right=c>>len(affine)
            av=0;bv=0
            for j in left:av^=vals[eligible[j]]
            for j,q in enumerate(eligible):
                if right>>j&1:bv^=vals[q]
            value=full_affine(lin)^(av&bv);checks+=1
            difference=value^vals[target]
            if not difference:
                return {'and_count':1,'constant':lin&1,'linear':[q for j,q in enumerate(eligible) if lin>>(j+1)&1],
                        'left':[eligible[j] for j in left],'right':[q for j,q in enumerate(eligible) if right>>j&1],
                        'full_domain_candidate_checks':checks,'refinements':refine}
            x=(difference&-difference).bit_length()-1
            bits=[(vals[q]>>x)&1 for q in eligible];abit=0
            for j in left:abit^=bits[j]
            fb=[1]+bits+[abit*b for b in bits]
            signatures=[s|(bit<<width) for s,bit in zip(signatures,fb)]
            target_sig|=((vals[target]>>x)&1)<<width;width+=1
    return None


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--kmx',type=Path,default=Path(__file__).parent/'invsqrt_structural_e46.kmx')
    ap.add_argument('--out',type=Path,required=True);ap.add_argument('--max-candidates',type=int,default=24)
    ap.add_argument('--left-terms',type=int,default=2);args=ap.parse_args();began=time.monotonic()
    lines,ops=instructions(args.kmx);masks,depth,peaks,intervals=scan(lines,ops)
    peakset=set(peaks);selected=[];remaining=set(peaks)
    candidates=sorted(intervals,key=lambda x:(-len(x['covered']),-x['span']))
    # A small diverse panel of intervals that can cover the entire width-46 frontier.
    while remaining and candidates and len(selected)<args.max_candidates:
        best=max(candidates,key=lambda x:len(set(x['covered'])&remaining))
        if not (set(best['covered'])&remaining):break
        selected.append(best);remaining.difference_update(best['covered']);candidates.remove(best)
    for item in candidates:
        if len(selected)>=args.max_candidates:break
        if any(item['q']==x['q'] and item['start']>=x['start'] and item['end']<=x['end'] for x in selected):continue
        selected.append(item)
    print(json.dumps({'width46_positions':len(peaks),'candidate_idle_intervals':len(intervals),'screening':len(selected),
                      'uncovered_by_greedy_panel':len(remaining),'panel':[{k:v for k,v in x.items() if k!='covered'} for x in selected]}),flush=True)
    by_end={}
    for x in selected:by_end.setdefault(x['end'],[]).append(x)
    domain,vals=initial_values();stack=[];rng=random.Random(20261115061)
    samples=list(range(1,129))+[2**k+d for k in range(3,22) for d in range(-2,3)]+[rng.randrange(1,MAX_X+1) for _ in range(512)]
    results=[]
    for i,(op,qs) in enumerate(ops):
        for item in by_end.get(i,[]):
            t=time.monotonic();identity=one_product(vals,item['q'],domain,samples,args.left_terms)
            record={**item,'identity':identity,'seconds':time.monotonic()-t};results.append(record)
            print(json.dumps({k:v for k,v in record.items() if k!='covered'}),flush=True)
        if op=='PUSH_CONDITION':stack.append(vals[:])
        elif op=='POP_CONDITION':before=stack.pop();assert vals==before;vals=before
        else:advance(op,qs,vals,domain)
    accepted=[x for x in results if x['identity'] is not None];covered=set(p for x in accepted for p in x['covered'])
    report={'status':'COMPLETE','baseline_kmx_sha256':hashlib.sha256(args.kmx.read_bytes()).hexdigest(),
            'valid_inputs':MAX_X,'positions_with_all46_nonzero':peaks,'candidate_intervals':len(intervals),
            'tested':results,'accepted':len(accepted),'uncovered_width46_positions':len(peakset-covered),
            'elapsed_seconds':time.monotonic()-began}
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('positions_with_all46_nonzero','tested')}))


if __name__=='__main__':main()
