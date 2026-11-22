#!/usr/bin/env python3
"""Cross-axis high-cofactor basis compiler (heuristic, with rank-priced selectors).

G=M F for M in GL(H,2), H<=20 high address states. Corresponding output
selectors are columns of M^{-1}. Any selector is a Boolean 8x3 onehot matrix,
so its GF(2) matrix rank r is the exact minimum count of rank-one bilinear
terms, each implementable by one CCX from XORs of the precomputed high A/B
flags. For r>1 we keep the high selector inverse CCX; for r=1 replace the
inverse with HMR and a conditional CZ. Low products and prefix are HMR-clean.

This is constructive, produces exact KMX and full all-address phase proof.
Weighted greedy picks the cofactor basis using an independent low cost only,
so optimization of high-selector ranks is HEURISTIC (not an exact global
optimum). No general claim about multiplicative complexity is made.
"""
from __future__ import annotations
import argparse,hashlib,json,math,sys
from collections import Counter
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
for d in ('gvqcc_multiform','gvqcc_multiform_v3','gvqcc_multiform_v4','gvqcc_multiform_v5'):
 sys.path.insert(0,str(ROOT/d))
from multi_angle_synthesis import Circuit,TARGETS,delta_table,word_masks,rank_output_basis,emit_fanout
from partition_patterns import high_flags,monomial_cache,mobius
from global_cofactor import discover_global
from hmr_patterns import MeasuredCircuit
from high_group_basis import cf_cost,emit_low_basis
from screen_global_axis import greedy_basis,high_selector_rank
from high_pair_general import full_domain_prove
from independent_kmx_verifier import verify as independent_verify


def factor_selector(mask:int)->list[tuple[int,int]]:
    """Return r outer products a*b for an 8x3 GF(2) indicator matrix.

    Construct column basis of 3 columns. The column representation over the
    chosen basis determines the right factor. Rank is exactly minimal under
    bilinear rank-one selector semantics.
    """
    cols=[(mask>>(8*j))&255 for j in range(3)]
    basis=[]
    def combination(mask):
        value = 0
        for i, item in enumerate(basis):
            if (mask >> i) & 1:
                value ^= item
        return value
    for col in cols:
        if col and all(combination(subset) != col for subset in range(1 << len(basis))):
            basis.append(col)
    right=[]
    for col in cols:
        options = [subset for subset in range(1 << len(basis)) if combination(subset) == col]
        if len(options)!=1:raise AssertionError(('no_unique_expansion',col,basis))
        right.append(options[0])
    factors=[]
    for i,a in enumerate(basis):
        b=sum(((right[j]>>i)&1)<<j for j in range(3))
        factors.append((a,b))
    assert len(factors)==high_selector_rank(mask)
    reconstructed=0
    for a,b in factors:
        for j in range(3):
            if b>>j&1:reconstructed^=int(a)<<(8*j)
    assert reconstructed == mask
    return factors


def emit_high(c:Circuit,factors:list[tuple[int,int]],hiA,hiB,high,active,tmp):
    start=len(c.gates)
    for a,b in factors:
        for idx in range(8):
            if a>>idx&1:c.emit('CX',hiA[idx],active)
        for idx in range(3):
            if b>>idx&1:c.emit('CX',hiB[idx],tmp)
        c.emit('CCX',active,tmp,high)
        for idx in reversed(range(3)):
            if b>>idx&1:c.emit('CX',hiB[idx],tmp)
        for idx in reversed(range(8)):
            if a>>idx&1:c.emit('CX',hiA[idx],active)
    return list(c.gates[start:])


def custom_convert(c:Circuit,stat:dict,skip_high_inverse:set[int],high:int,active:int):
    """Conservative HMR: only uncompute of a rank1 high flag is measured;
    rank>=2 flags retain classical reversible inverse. All low AND inverses
    and cached-prefix inverses are measured with their matched CZ correction.
    """
    gates=c.gates;prefix=stat['prefix_len'];marked={}
    for i,(op,q) in enumerate(gates):
        if op!='CCX' or q[-1]!=active:continue
        j=i+1
        while j<len(gates) and gates[j][0]=='CX' and gates[j][1][0]==active and gates[j][1][1] in TARGETS:j+=1
        if j>i+1 and j<len(gates) and gates[j]==(op,q):marked[j]=q
    for i,(op,q) in enumerate(gates):
        if op=='CCX' and q[-1]==high and i not in skip_high_inverse:
            # Mark just rank1 selector inverse, not its forward.
            # Caller records eligible inversion indices in stat explicitly.
            if i in stat['eligible_rank1_inverse_indices']:marked[i]=q
    for i in range(len(gates)-prefix,len(gates)):
        op,q=gates[i]
        if op=='CCX':
            if i in marked:raise AssertionError('prefix inverse overlap')
            marked[i]=q
    ops=[]
    for i,(op,q) in enumerate(gates):
        if i in marked:
            a,b,t=q
            ops.append(('HMR',(t,),0));ops.append(('CZ',(a,b),0))
        else:ops.append((op,q,None))
    h=MeasuredCircuit(c.alloc,ops)
    stat2={k:v for k,v in stat.items() if k not in ('eligible_rank1_inverse_indices',)}
    stat2.update(CCX=int(h.counts['CCX']),CX=int(h.counts['CX']),X=int(h.counts['X']),
                 HMR=int(h.counts['HMR']),CZ=int(h.counts['CZ']),
                 bypass_rank2plus_inverse_CCX=len(skip_high_inverse))
    return h,stat2


def compile_global20(words,slot,support=3,global_mode='canonical',criterion='pure'):
    if global_mode not in (None,'canonical'):
        raise ValueError(global_mode)
    rows=word_masks(delta_table(words,slot)); H=math.ceil(len(rows)/64)
    meta=greedy_basis(rows,global_mode,support,criterion)
    low,_=discover_global(rows,6,global_mode) if global_mode else ([0]*64,{})
    groups=[[int(v)^low[j] for j,v in enumerate(rows[i*64:(i+1)*64])]+[0]*(64-len(rows[i*64:(i+1)*64])) for i in range(H)]
    masks=[int(x,16) for x in meta['chosen_high_cofactor_masks']]
    selectors=[int(x,16) for x in meta['inverse_selector_masks']]
    assert len(masks)==H
    # Recompose F_i from new cofactor vector G_j and inverse selectors.
    coefs=[]
    for i,mask in enumerate(masks):
        group=[0]*64
        for h in range(H):
            if mask>>h&1:group=[a^b for a,b in zip(group,groups[h])]
        coefs.append(mobius(group,6))
    decoded=[]
    for h in range(H):
        co=[0]*64
        for j in range(H):
            if selectors[j]>>h&1:co=[a^b for a,b in zip(co,coefs[j])]
        assert co == mobius(groups[h],6)
    c=Circuit();hiA,hiB,_=high_flags(c,6);cache=monomial_cache(c,6)
    prefix=len(c.gates);high,active,tmp=c.new(3)
    for mon,out in enumerate(mobius(low,6)):
        if not out:continue
        for idx,q in enumerate(TARGETS):
            if out>>idx&1:
                if mon==0:c.emit('X',q)
                else:c.emit('CX',int(cache[mon]),q)
    eligible=[];skipped=set();rank_hist=Counter();emitted=0
    for sel,coeff in zip(selectors,coefs):
        weight,_,_=cf_cost(coeff)
        if weight==0:continue
        factors=factor_selector(sel)
        rank=len(factors)
        rank_hist[rank]+=1
        forward=emit_high(c,factors,hiA,hiB,high,active,tmp)
        emit_low_basis(c,cache,high,active,tmp,coeff)
        start=len(c.gates)
        c.undo(forward)
        inverse_indices=[i for i in range(start,len(c.gates)) if c.gates[i][0]=='CCX' and c.gates[i][1][-1]==high]
        assert len(inverse_indices)==rank
        if rank==1:eligible.extend(inverse_indices)
        else:skipped.update(inverse_indices)
        emitted+=1
    c.undo(tuple(c.gates[:prefix]))
    assert tuple(c.gates[-prefix:])==tuple(reversed(c.gates[:prefix]))
    stat=dict(slot=slot,method=f'cross20-support{support}-{global_mode}-{criterion}',
              qubits=c.alloc,prefix_len=prefix,high_selector_rank_hist=dict(rank_hist),
              selectors_emitted=emitted,eligible_rank1_inverse_indices=eligible,
              low_products=sum(cf_cost(coeff)[1] for coeff in coefs),
              base_high_cost=meta['base_cost'],
              theoretical_selector_rank_lower=sum(rank_hist[k]*k for k in rank_hist),
              screen_est_conservative=meta['cost_est_conservative'],
              screen_est_relaxed=meta['cost_est_relaxed'],
              source_cofactor_masks=meta['chosen_high_cofactor_masks'],
              output_selector_masks=meta['inverse_selector_masks'])
    h,stat2=custom_convert(c,stat,skipped,high,active)
    return h,stat2


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seed',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    p.add_argument('--slots',default='all')
    p.add_argument('--max-support',type=int,default=3)
    p.add_argument('--global-mode',choices=['canonical','none'],default='canonical')
    p.add_argument('--criterion',choices=['pure','support'],default='pure')
    p.add_argument('--emit',action='store_true')
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    with np.load(a.seed,allow_pickle=False) as z:words=np.array(z['angle_words'],np.int64)
    slots=list(range(15)) if a.slots=='all' else [int(x) for x in a.slots.split(',')]
    records=[]
    for k in slots:
        c,stat=compile_global20(words,k,a.max_support,None if a.global_mode=='none' else a.global_mode,a.criterion)
        proof=full_domain_prove(c,delta_table(words,k))
        rec=dict(**stat,**proof,input=a.seed.name,
                 input_sha256=hashlib.sha256(a.seed.read_bytes()).hexdigest(),
                 official_verified=False,official_score=None)
        if a.emit:
            path=a.out/f'angle_k_{k}.kmx'
            path.write_text('\n'.join(c.kmx_lines())+'\n')
            rec['kmx_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        records.append(rec)
        with (a.out/'experiments.jsonl').open('a') as f:f.write(json.dumps(rec,sort_keys=True)+'\n')
        print(json.dumps({key:rec.get(key) for key in ('slot','CCX','CX','HMR','qubits','high_selector_rank_hist')}),flush=True)
    summary=dict(input=a.seed.name,slots=len(records),CCX=sum(x['CCX'] for x in records),
                 CX=sum(x['CX'] for x in records),max_Q=max(x['qubits'] for x in records),
                 max_support=a.max_support,criterion=a.criterion,global_mode=a.global_mode,
                 schema='gvqcc.cross20.actual-kmx.v1',verification='all addresses symbolic, not official KickMix')
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('SUMMARY',json.dumps(summary),flush=True)
if __name__=='__main__':main()
