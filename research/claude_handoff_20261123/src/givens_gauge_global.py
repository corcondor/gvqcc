#!/usr/bin/env python3
"""Exact Givens-tree sign-frame gauge, changing QUANTIZED angle words globally.
The factors U/W/H2 and target physics stay invariant. Each gate adds a NEW wire.
At each gate independent signs may be assigned to outputs only while reused later.
This creates 74 free sign slots per row for the given FeMoCo tree.
Every output vector is verified against the original decoder, not merely assumed.
"""
from __future__ import annotations
from pathlib import Path
import argparse,hashlib,json,collections,time
import numpy as np
from longtrain.physical_verify import Physical,decode
import sys
sys.path.insert(0,str(Path(__file__).parent/'axis_old'/'src'))
from chemistry_j_scheduler import delta_for,multiout_perbit_ranks

def tree_info(edges):
    seen={0};infos=[];slots=[]
    for k,(a,b) in enumerate(edges):
        a=int(a);b=int(b)
        parents=[x for x in (a,b) if x in seen]
        assert len(parents)==1,(k,a,b,seen)
        p=parents[0];q=b if a==p else a
        later=edges[k+1:].flatten()
        pf=p in later; qf=q in later
        infos.append((p,q,pf,qf))
        slots.extend([(k,x) for x,f in ((p,pf),(q,qf)) if f])
        seen.update((p,q))
    assert len(seen)==76
    return infos,slots

# signs are Boolean 1 if the signed 'frame' is negative.
def new_word(word,incoming,after_p,after_q):
    a=np.bitwise_xor(after_p,incoming)
    b=np.bitwise_xor(after_q,incoming)
    flip=np.bitwise_xor(a,b).astype(bool)
    out=np.where(flip,-word,word)+64*a.astype(np.int16)
    return np.bitwise_and(out,127).astype(np.uint8)

def popcount7(x):
    # np.bitwise_count if numpy>=2.0; compatibility table
    return np.take(_POPCOUNT, np.asarray(x,dtype=np.uint8))
_POPCOUNT=np.array([int(x).bit_count() for x in range(128)],dtype=np.uint8)

def generate(words,edges,mode='fold_value',seed=42):
    n=len(words);infos,slots=tree_info(edges)
    rng=np.random.default_rng(seed)
    state=np.zeros((76,n),dtype=np.uint8)
    out=np.empty_like(words,dtype=np.uint8)
    trace=[]
    for k,(p,q,free_p,free_q) in enumerate(infos):
        inp=state[p]
        choices=[]
        for bp in ([0,1] if free_p else [0]):
            for bq in ([0,1] if free_q else [0]):
                pp=np.full(n,bp,dtype=np.uint8);qq=np.full(n,bq,dtype=np.uint8)
                cand=new_word(words[:,k],inp,pp,qq)
                if mode=='fold_value': score=cand.astype(np.int16)
                elif mode=='fold_popcount': score=popcount7(cand).astype(np.int16)*128+cand.astype(np.int16)
                elif mode=='fold_xor5':
                    target=out[:,k-5] if k>=5 else np.zeros(n,dtype=np.uint8)
                    score=popcount7(cand^target).astype(np.int16)*128+cand.astype(np.int16)
                elif mode=='fold_xor1':
                    target=out[:,k-1] if k>=1 else np.zeros(n,dtype=np.uint8)
                    score=popcount7(cand^target).astype(np.int16)*128+cand.astype(np.int16)
                elif mode=='fold_signed6':
                    score=((cand>>6)^(cand>>5)).astype(np.int16)*128+cand.astype(np.int16)
                elif mode=='random':score=rng.integers(0,2**14,size=n,dtype=np.int16)
                elif mode=='global_lowrank':
                    # global low-complexity sign functions: constant/linear address pattern
                    mask=(np.arange(n,dtype=np.uint16) >> ((k*13+seed)%11))&1
                    score=(bp^mask).astype(np.int16)*128+(bq^mask).astype(np.int16)*128+cand.astype(np.int16)//10
                else:raise ValueError(mode)
                choices.append((score, pp,qq,cand))
        scores=np.stack([s for s,_,_,_ in choices])
        idx=scores.argmin(axis=0)
        selection=np.arange(n)
        out[:,k]=np.stack([c for _,_,_,c in choices])[idx,selection]
        state[p]=np.stack([pp for _,pp,_,_ in choices])[idx,selection]
        state[q]=np.stack([qq for _,_,qq,_ in choices])[idx,selection]
        trace.append({'gate':k,'free_slots':int(free_p)+int(free_q),'edited_rows':int(np.count_nonzero(out[:,k]!=words[:,k])),'highest_bit_fraction':float(np.mean(out[:,k]>=64))})
    assert not np.any(state)
    return out,trace

def proxy(words,ks=None):
    sched=list(range(75)); ks=range(15) if ks is None else ks
    per=[int(sum(multiout_perbit_ranks(delta_for(sched,words,5,k),4))) for k in ks]
    return per

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--data',required=True);p.add_argument('--out',required=True);p.add_argument('--modes',nargs='+',default=['fold_value','fold_popcount','fold_xor5','fold_xor1','fold_signed6','global_lowrank','random']);p.add_argument('--seed',type=int,default=42)
    a=p.parse_args();out=Path(a.out);out.mkdir(exist_ok=True,parents=True)
    with np.load(a.source) as z:orig={k:np.array(z[k]) for k in z.files}
    phys=Physical(a.data);raw=orig['angle_words'].astype('uint8');edge=orig['tree_edges'];base=phys.evaluate(orig)
    v0=decode(raw,edge)
    before=proxy(raw);report={'source':str(a.source),'source_sha256':hashlib.sha256(Path(a.source).read_bytes()).hexdigest(),'baseline_proxy_sum':sum(before),'baseline_proxy_perbank':before,'free_sign_slots':len(tree_info(edge)[1]),'baseline_physics':base,'gauge_results':[],'official_KickMix_executed':False}
    for mode in a.modes:
        tic=time.monotonic()
        changed,trace=generate(raw,edge,mode,seed=a.seed)
        v1=decode(changed,edge)
        maxdiff=float(np.max(np.abs(v0-v1)))
        assert maxdiff<3e-14, (mode,maxdiff)
        d=dict(orig);d['angle_words']=changed.astype(np.int64)
        met=phys.evaluate(d)
        assert abs(met['lambda_eff']-base['lambda_eff'])<1e-7
        assert abs(met['error_1']-base['error_1'])<1e-8
        assert abs(met['error_2']-base['error_2'])<1e-7
        dest=out/(mode+'.npz');np.savez_compressed(dest,**d)
        r=proxy(changed)
        record={'mode':mode,'angle_words_changed':int(np.count_nonzero(changed!=raw)),'angle_columns_changed':int(np.sum(np.any(changed!=raw,axis=0))),'proxy_sum':sum(r),'proxy_by_bank':r,'delta_proxy':sum(r)-sum(before),'max_abs_decode_diff':maxdiff,'lambda_eff':met['lambda_eff'],'error_1':met['error_1'],'error_2':met['error_2'],'file':dest.name,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'time_s':time.monotonic()-tic,'gate_trace':trace}
        report['gauge_results'].append(record)
        print('MODE',mode,'modified',record['angle_words_changed'],'columns',record['angle_columns_changed'],'proxy',sum(r),'baseline',sum(before),'max_error',maxdiff,'seconds',round(record['time_s'],1),flush=True)
    (out/'landscape_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('BEST',sorted([(r['proxy_sum'],r['mode']) for r in report['gauge_results']]))
if __name__=='__main__':main()