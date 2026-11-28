#!/usr/bin/env python3
"""Nonlocal 75-angle signed gauge with exact signed6 15-bank invariant.
Solve 70 GF(2) constraints on 74 intermediate frame variables for EACH row.
Nullity=4, hence 16 globally different orbit choices per legal address.
RBC, W/H2 and final state vectors remain exactly equal.
The original bit6^bit5 residue repeats at stride five; the new residue
is forced to repeat at the same stride, preserving the 10/15 low-rank structure.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
from signed6_constraint_rank import vectors,nullspace
from givens_gauge_global import tree_info,new_word,popcount7,proxy
from longtrain.physical_verify import Physical,decode

def bases(w,edges):
    n=len(w);ex,slots=vectors(edges)
    result=np.empty((n,4),dtype=object);ranks=np.zeros(n,dtype=np.int32)
    for row in range(n):
        masks=[ex[k][int(w[row,k] in (32,96))] for k in range(75)]
        rows=[masks[k]^masks[k-5] for k in range(5,75)]
        ns,rank=nullspace(rows,len(slots))
        assert rank<=70 and len(ns)>=4,(row,rank,len(ns))
        result[row,:]=ns[:4];ranks[row]=rank
    return result,slots

def make_words(w,edges,base,slots,selection):
    n=len(w);indices={v:i for i,v in enumerate(slots)}
    masks=[0]*n
    for row in range(n):
        mask=0
        for bit in range(4):
            if (selection[row]>>bit)&1:mask^=int(base[row,bit])
        masks[row]=mask
    signs=np.empty((len(slots),n),dtype=np.uint8)
    for si in range(len(slots)):
        signs[si]=np.fromiter(((int(m)>>si)&1 for m in masks),dtype=np.uint8,count=n)
    info,_=tree_info(edges);state=np.zeros((76,n),dtype=np.uint8);out=np.empty_like(w)
    for k,(p,q,pf,qf) in enumerate(info):
        incoming=state[p]
        gp=signs[indices[(k,p)]] if pf else np.zeros(n,dtype=np.uint8)
        gq=signs[indices[(k,q)]] if qf else np.zeros(n,dtype=np.uint8)
        out[:,k]=new_word(w[:,k],incoming,gp,gq)
        state[p]=gp;state[q]=gq
    assert not np.any(state)
    r_old=((w>>6)^(w>>5))&1;r_new=((out>>6)^(out>>5))&1
    assert np.array_equal(r_new[:,5:],r_new[:,:-5]),'signed6 stride-five property violated'
    assert np.array_equal(r_old[:,5:],r_old[:,:-5]),'source signed6 broken'
    return out

def choices(n,mode,seed=2):
    row=np.arange(n,dtype=np.uint16);rng=np.random.default_rng(seed)
    if mode.startswith('fixed_'):return np.full(n,int(mode.split('_')[1]),dtype=np.uint8)
    if mode=='addr_4bit':return (row&15).astype(np.uint8)
    if mode=='addr_gray':return ((row^(row>>1))&15).astype(np.uint8)
    if mode=='addr_high':return ((row>>7)&15).astype(np.uint8)
    if mode=='addr_middle':return ((row>>3)&15).astype(np.uint8)
    if mode=='addr_parity':return ((row*7^(row>>2))&15).astype(np.uint8)
    if mode=='random':return rng.integers(0,16,n,dtype=np.uint8)
    raise ValueError(mode)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--data',required=True);ap.add_argument('--out',required=True);ap.add_argument('--modes',nargs='+',default=[]);a=ap.parse_args()
    out=Path(a.out);out.mkdir(exist_ok=True,parents=True)
    with np.load(a.source) as z:d={k:np.array(z[k]) for k in z.files}
    w=d['angle_words'].astype(np.uint8);edges=d['tree_edges'];phys=Physical(a.data)
    before=phys.evaluate(d);v0=decode(w,edges);p0=proxy(w)
    t0=time.monotonic();bs,slots=bases(w,edges);print('NULLSPACE rows',len(w),'dim',bs.shape[1],'seconds',round(time.monotonic()-t0,2),flush=True)
    all_modes=a.modes or [f'fixed_{i}' for i in range(16)]+['addr_4bit','addr_gray','addr_high','addr_middle','addr_parity','random']
    results=[];best=[]
    for mode in all_modes:
        t=time.monotonic();s=choices(len(w),mode);new=make_words(w,edges,bs,slots,s)
        rank=proxy(new)
        rec={'mode':mode,'selected_nonzero_rows':int(np.count_nonzero(s)),'modified_words':int(np.count_nonzero(w!=new)),'modified_columns':int(np.count_nonzero(np.any(w!=new,axis=0))),'proxy':int(sum(rank)),'proxy_perbank':rank,'proxy_delta':int(sum(rank)-sum(p0)),'candidate_SHA256':hashlib.sha256(new.tobytes()).hexdigest(),'elapsed':round(time.monotonic()-t,2)}
        results.append(rec)
        print('CANDIDATE',mode,'changed',rec['modified_words'],'proxy',rec['proxy'],'delta',rec['proxy_delta'],'time',rec['elapsed'],flush=True)
    results.sort(key=lambda r:r['proxy'])
    for rec in results[:8]:
        s=choices(len(w),rec['mode']);new=make_words(w,edges,bs,slots,s)
        maxdiff=float(np.max(np.abs(decode(new,edges)-v0)))
        assert maxdiff<1e-14
        cand=dict(d);cand['angle_words']=new.astype(np.int64)
        pp=phys.evaluate(cand)
        assert abs(pp['lambda_eff']-before['lambda_eff'])<1e-8 and abs(pp['error_2']-before['error_2'])<1e-8
        fp=out/f"signed6_{rec['mode']}.npz";np.savez_compressed(fp,**cand)
        rec.update(phys=pp,max_abs_decode_diff=maxdiff,file=fp.name,sha256=hashlib.sha256(fp.read_bytes()).hexdigest())
        best.append(rec)
    report={'algorithm':'70 signed6 constraints on 74 free Givens intermediate signs; at least four dimensions for every address','source_sha256':hashlib.sha256(Path(a.source).read_bytes()).hexdigest(),'source_physics':before,'proxy_baseline':sum(p0),'all_variants':results,'candidates_exact':best,'native_KickMix_checked':False}
    (out/'coset_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('BEST',[(r['mode'],r['proxy'],r['modified_words']) for r in best],flush=True)
if __name__=='__main__':main()