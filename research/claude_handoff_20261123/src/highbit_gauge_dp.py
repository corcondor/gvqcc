#!/usr/bin/env python3
"""Exact high-bit-only Givens gauge via global tree dynamic programming.
At gates whose BOTH output wires are reused later (31 of 75), the common
frame sign is free; changing it toggles ONLY bit6 of this and successor words.
All low 6 bits of all 75 angles are unchanged, and the final state vectors
are exactly equal. This is a global discrete transform, not local CCX deletion.
"""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
from givens_gauge_global import proxy
from longtrain.physical_verify import Physical,decode

def graph(edges):
    seen={0};last={0:-1};src=[];children=[[] for _ in range(75)];free=[];slots=[]
    for k,(a,b) in enumerate(edges):
        a=int(a);b=int(b);parents=[x for x in (a,b) if x in seen];assert len(parents)==1
        p=parents[0];q=b if p==a else a
        i=last[p];src.append(i)
        if i>=0:children[i].append(k)
        after=edges[k+1:].flatten()
        f=(p in after) and (q in after)
        free.append(bool(f));
        if f:slots.append(k)
        last[p]=k;last[q]=k;seen.add(q)
    assert len(slots)==31,(len(slots),slots)
    assert max(map(len,children))<=2
    return src,children,np.array(free,dtype=bool),slots

def choose_target(w,mode):
    rows,n=w.shape;h=(w>>6)&1; b5=(w>>5)&1;target=np.zeros_like(h)
    if mode=='zero':pass
    elif mode=='ones':target[:]=1
    elif mode=='bit5':target[:]=b5
    elif mode=='previous_bit6':target[:,5:]=h[:,:-5]
    elif mode=='previous_bit5':target[:,5:]=b5[:,:-5]
    elif mode=='addr_low':
        inds=np.arange(rows,dtype=np.uint16)
        for k in range(n):target[:,k]=((inds>>(k%11))&1)
    elif mode=='addr_high':
        inds=np.arange(rows,dtype=np.uint16)
        for k in range(n):target[:,k]=((inds>>((k*3+8)%11))&1)
    elif mode=='bit5_prev6':target[:]=b5;target[:,5:]=h[:,:-5]
    else:raise ValueError(mode)
    return target

def solve(w,e,mode,weights=None):
    rows,n=w.shape;src,children,free,slots=graph(e)
    h=(w>>6)&1;target=choose_target(w,mode)
    if weights is None:weights=np.ones(n,dtype=np.int32)
    dp=np.zeros((n,2,rows),dtype=np.int32);best=np.zeros((n,2,rows),dtype=np.uint8)
    for k in range(n-1,-1,-1):
        opts=[0,1] if free[k] else [0]
        for inp in (0,1):
            costs=[]
            for out in opts:
                c=((h[:,k] ^ inp ^ out)^target[:,k]).astype(np.int32)*weights[k]
                for chi in children[k]:c=c+dp[chi,out]
                costs.append(c)
            costs=np.stack(costs);ix=costs.argmin(axis=0);dp[k,inp]=np.take_along_axis(costs,ix[None,:],axis=0)[0]
            best[k,inp]=np.array(opts,dtype=np.uint8)[ix]
    s=np.zeros((n,rows),dtype=np.uint8)
    for k in range(n):
        inp=s[src[k]] if src[k]>=0 else np.zeros(rows,dtype=np.uint8)
        s[k]=best[k,inp,np.arange(rows)]
    out=w.copy()
    for k in range(n):
        inp=s[src[k]] if src[k]>=0 else np.zeros(rows,dtype=np.uint8)
        out[:,k]^=((inp^s[k])<<6)
    assert np.array_equal(out&63,w&63)
    assert np.array_equal(s[np.logical_not(free)],np.zeros_like(s[np.logical_not(free)]))
    return out,dict(objective=int(dp[0,0].sum()),chosen_signs=int(s.sum()),free_gate_ids=slots,changed_highbits=int(np.count_nonzero(out!=w)),target_mode=mode)

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--data',required=True);p.add_argument('--out',required=True);p.add_argument('--modes',nargs='+',default=['zero','ones','bit5','previous_bit6','previous_bit5','addr_low','addr_high','bit5_prev6'])
    a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    with np.load(a.source) as z:base={k:np.array(z[k]) for k in z.files}
    raw=base['angle_words'].astype(np.uint8);edge=base['tree_edges'];model=Physical(a.data);m0=model.evaluate(base);v0=decode(raw,edge);p0=proxy(raw)
    report={'source_sha256':hashlib.sha256(Path(a.source).read_bytes()).hexdigest(),'base_proxy':sum(p0),'base_physics':m0,'program':'highbit-gauge-global-dp','modes':[],'official_KickMix_verified':False}
    for mode in a.modes:
        tic=time.monotonic();w,extra=solve(raw,edge,mode)
        maxdiff=float(np.max(np.abs(decode(w,edge)-v0)))
        assert maxdiff<1e-14
        cand=dict(base);cand['angle_words']=w.astype(np.int64)
        phy=model.evaluate(cand)
        assert abs(phy['lambda_eff']-m0['lambda_eff'])<1e-8 and abs(phy['error_2']-m0['error_2'])<1e-8
        path=out/(mode+'.npz');np.savez_compressed(path,**cand)
        pr=proxy(w)
        rec=dict(mode=mode,**extra,proxy=sum(pr),proxy_delta=sum(pr)-sum(p0),proxy_perbank=pr,modified_columns=int(np.count_nonzero(np.any(w!=raw,axis=0))),max_abs_decode_diff=maxdiff,physics=phy,file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),elapsed=time.monotonic()-tic)
        report['modes'].append(rec)
        print(mode,'changed_highbits',rec['changed_highbits'],'columns',rec['modified_columns'],'proxy',rec['proxy'],'delta',rec['proxy_delta'],'s',round(rec['elapsed'],2),flush=True)
    (out/'highbit_gauge_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()