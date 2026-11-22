#!/usr/bin/env python3
"""Globally optimal signed-frame Givens tree re-encoding for additive 7-bit angle costs.
Unlike coordinate-wise local rewrites, this is exact dynamic programming across
all 75 Givens gates; 74 intermediate-frame binary variables per address.
The transformed table has exactly the same decoded vectors.
"""
from __future__ import annotations
import argparse,hashlib,json,time,sys
from pathlib import Path
import numpy as np
from longtrain.physical_verify import Physical,decode
from givens_gauge_global import tree_info,new_word,popcount7,proxy

def successors(edges):
    info,slots=tree_info(edges)
    succ=[]
    for k,(p,q,_,_) in enumerate(info):
        sp=next((i for i in range(k+1,len(info)) if p in edges[i]),-1)
        sq=next((i for i in range(k+1,len(info)) if q in edges[i]),-1)
        succ.append((sp,sq))
    return info,succ

def weight_function(w,mode,k,rows):
    W=w.astype(np.int16)
    b6=(W>>6)&1;b5=(W>>5)&1;b4=(W>>4)&1
    if mode=='min_value':return W
    if mode=='min_hamming':return popcount7(w).astype(np.int16)*128+W
    if mode=='min_signed6':return ((b6^b5)*32+b6*4+b5*2)*128+W
    if mode=='bitplane_6':return b6*128+W//3
    if mode=='low3_priority':return (W&7)*200+W
    if mode=='bank_weighted':
        factor=10 if (k//5) in {0,1,5,7,11} else 2
        return ((b6*16+b5*4+b4)*factor)*128+W
    if mode.startswith('affine_'):
        bit=int(mode.rsplit('_',1)[1]);mask=(np.arange(rows,dtype=np.uint16)>>bit)&1
        return ((b6!=mask)*128+(b5!=mask)*16)+(W&31)
    if mode=='coset_id':return ((W+16)&127)*2+W//20
    raise ValueError(mode)

def solve(words,edges,mode):
    n=words.shape[0];info,succ=successors(edges)
    dp=np.zeros((75,2,n),dtype=np.int32)
    pick=np.zeros((75,2,n),dtype=np.uint8)
    combos={}
    for k in range(74,-1,-1):
        p,q,pfree,qfree=info[k]
        sp,sq=succ[k]
        config=[(a,b) for a in ([0,1] if sp>=0 else [0]) for b in ([0,1] if sq>=0 else [0])]
        combos[k]=config
        for incoming in (0,1):
            arrivals=np.full(n,incoming,dtype=np.uint8)
            all_cost=[]
            for a,b in config:
                pp=np.full(n,a,dtype=np.uint8);qq=np.full(n,b,dtype=np.uint8)
                w=new_word(words[:,k],arrivals,pp,qq)
                c=weight_function(w,mode,k,n).astype(np.int32)
                if sp>=0:c+=dp[sp,a]
                if sq>=0:c+=dp[sq,b]
                all_cost.append(c)
            stacked=np.stack(all_cost)
            win=stacked.argmin(axis=0)
            dp[k,incoming]=np.take_along_axis(stacked,win[None,:],axis=0)[0]
            pick[k,incoming]=win
    out=np.empty_like(words,dtype=np.uint8)
    incoming=np.full((75,n),2,dtype=np.uint8);incoming[0]=0
    ix=np.arange(n)
    for k in range(75):
        state=incoming[k]
        assert np.all(state<2),('incoming missing',k)
        win=pick[k,state,ix]
        conf=combos[k]
        pstate=np.choose(win,[a for a,b in conf]).astype('uint8')
        qstate=np.choose(win,[b for a,b in conf]).astype('uint8')
        out[:,k]=new_word(words[:,k],state,pstate,qstate)
        sp,sq=succ[k]
        if sp>=0:incoming[sp]=pstate
        if sq>=0:incoming[sq]=qstate
    return out,int(dp[0,0].sum())

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--data',required=True);ap.add_argument('--out',required=True);ap.add_argument('--modes',nargs='+',default=['min_value','min_hamming','min_signed6','bitplane_6','low3_priority','bank_weighted','affine_0','affine_4','affine_9','coset_id'])
    a=ap.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    with np.load(a.source) as z:base={k:np.array(z[k]) for k in z.files}
    words=base['angle_words'].astype(np.uint8);edge=base['tree_edges'];v0=decode(words,edge)
    pb=Physical(a.data);origin=pb.evaluate(base);p0=proxy(words)
    report={'source':a.source,'source_sha256':hashlib.sha256(Path(a.source).read_bytes()).hexdigest(),'baseline_proxy':sum(p0),'physical_source':origin,'successors':successors(edge)[1],'modes':[],'official_KickMix_executed':False}
    for mode in a.modes:
        tic=time.monotonic();output,objective=solve(words,edge,mode)
        maxdiff=float(np.max(np.abs(decode(output,edge)-v0)))
        assert maxdiff<1e-14,(mode,maxdiff)
        d=dict(base);d['angle_words']=output.astype('int64')
        phy=pb.evaluate(d)
        assert abs(phy['lambda_eff']-origin['lambda_eff'])<1e-8
        assert abs(phy['error_1']-origin['error_1'])<1e-8
        assert abs(phy['error_2']-origin['error_2'])<1e-8
        fout=out/(mode+'.npz');np.savez_compressed(fout,**d)
        proxies=proxy(output)
        rec={'mode':mode,'objective':objective,'modified_words':int(np.count_nonzero(words!=output)),'modified_columns':int(np.count_nonzero(np.any(words!=output,axis=0))),'max_abs_decode_diff':maxdiff,'proxy':sum(proxies),'proxy_by_bank':proxies,'proxy_delta':sum(proxies)-sum(p0),'error_1':phy['error_1'],'error_2':phy['error_2'],'lambda_eff':phy['lambda_eff'],'sha256':hashlib.sha256(fout.read_bytes()).hexdigest(),'file':fout.name,'seconds':round(time.monotonic()-tic,3)}
        report['modes'].append(rec)
        print('DP',mode,'changed',rec['modified_words'],'proxy',rec['proxy'],'delta',rec['proxy_delta'],'error',maxdiff,'s',rec['seconds'],flush=True)
    (out/'dp_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()