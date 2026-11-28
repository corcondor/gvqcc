#!/usr/bin/env python3
"""Exact high-address cofactor pairing, new multi-output KMX construction.

For distinct high selectors e_i,e_j and low output vector functions F_i,F_j:
   e_i F_i XOR e_j F_j
 = (e_i XOR e_j) F_i XOR e_j (F_i XOR F_j).
When high block indices i,j share the 3-bit or 2-bit one-hot factor,
(e_i XOR e_j) can be computed in ONE CCX using the XOR of the differing
one-hot factors, without an extra paid high-term. Rank(F_i XOR F_j) may
be smaller than rank(F_j); this is a real structural cost opportunity.

Disjoint pairs chosen by greedy, an exact weighted matching (NetworkX),
or a bounded randomized greedy. Selected candidates are emitted as X/CX/CCX,
then v3 HMR phase-correct cleanup. This is not a peephole pass; it replaces
per-high cofactor decomposition by a high-basis-change (an invertible GF2
linear transformation of the high-axis of the truth-table tensor).
"""
from __future__ import annotations
import argparse,math,random,sys,json
from pathlib import Path
from collections import Counter
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
BASE_CODE=ROOT/'gvqcc_multiform' if (ROOT/'gvqcc_multiform').exists() else ROOT
V3_CODE=ROOT/'gvqcc_multiform_v3' if (ROOT/'gvqcc_multiform_v3').exists() else ROOT/'multiangle_v3'
sys.path.insert(0,str(BASE_CODE))
sys.path.insert(0,str(V3_CODE))
from multi_angle_synthesis import Circuit,delta_table,word_masks,rank_output_basis,emit_fanout,sha256,TARGETS
from partition_patterns import high_flags,monomial_cache,mobius,convert_hmr
from hmr_patterns import prove as prove_hmr
from global_cofactor import discover_global
try: import networkx as nx
except ImportError: nx=None

STRATEGIES=('greedy','exact','reverse','random-1','random-2','random-3','random-4','greedy-paid','exact-paid','reverse-paid')


def low_rank(group:list[int])->int:
    return len(rank_output_basis(mobius(group,6))[0])


def low_paid(group:list[int])->int:
    outs,forms=rank_output_basis(mobius(group,6))
    return sum(f!=1 for f in forms)

def pair_options(groups,paid=False):
    r=[(low_paid(g) if paid else low_rank(g)) for g in groups]
    options=[]
    for i in range(len(groups)):
        for j in range(i+1,len(groups)):
            if not ((i&7)==(j&7) or (i>>3)==(j>>3)):
                continue
            diff=[a^b for a,b in zip(groups[i],groups[j])]
            d=low_paid(diff) if paid else low_rank(diff)
            gain=max(r[i]-d,r[j]-d)
            if gain>0: options.append((gain,i,j,d,r[i],r[j]))
    return r,options


def choose_pairs(options,mode):
    mode=mode.removesuffix('-paid')
    if mode=='exact':
        if nx is None:raise ImportError('networkx required for exact high-pair matching')
        G=nx.Graph()
        for gain,i,j,d,ri,rj in options:G.add_edge(i,j,weight=gain)
        edges=list(nx.algorithms.matching.max_weight_matching(G,maxcardinality=False,weight='weight'))
        pairs=[(min(i,j),max(i,j)) for i,j in edges]
        if len(set(x for pair in pairs for x in pair))!=2*len(pairs):raise AssertionError('overlapping matching')
        return sorted(pairs)
    opts=list(options)
    if mode.startswith('random-'):
        rng=random.Random(int(mode.split('-')[1]));rng.shuffle(opts)
        opts.sort(key=lambda x:(-x[0],rng.random()))
    else:
        opts.sort(key=lambda x:(-x[0],(x[1],x[2]) if mode=='greedy' else (-x[1],-x[2])))
    used=set();pairs=[]
    for gain,i,j,d,ri,rj in opts:
        if i in used or j in used:continue
        used.update((i,j));pairs.append((i,j))
    return sorted(pairs)


def high_selector(c,hiA,hiB,high,tmp,ids):
    """Compute one selector into fresh high, return *uncompute ops*.

    Single high index: CCX(A_i,B_i,high).
    Paired selectors with one equal coordinate: XOR the other one-hot
    factor into tmp, single CCX to high, then reset tmp. On inverse
    regenerate the same selector in tmp before inverse CCX.
    """
    if len(ids)==1:
        h=ids[0];op=('CCX',(hiA[h&7],hiB[h>>3],high));c.emit(*op[0:1],*op[1]);return [op]
    if len(ids)!=2:raise ValueError(ids)
    i,j=ids
    if (i&7)==(j&7):controls=(hiB[i>>3],hiB[j>>3]);fixed=hiA[i&7]
    elif (i>>3)==(j>>3):controls=(hiA[i&7],hiA[j&7]);fixed=hiB[i>>3]
    else:raise AssertionError('paired indices share neither high flag')
    for q in controls:c.emit('CX',q,tmp)
    c.emit('CCX',fixed,tmp,high)
    for q in reversed(controls):c.emit('CX',q,tmp)
    return [('CX',(controls[0],tmp)),('CX',(controls[1],tmp)),
            ('CCX',(fixed,tmp,high)),('CX',(controls[1],tmp)),('CX',(controls[0],tmp))]


def compile_pairs(words,slot,mode='greedy',global_offset=None):
    if mode not in STRATEGIES:raise ValueError(mode)
    rows=word_masks(delta_table(words,slot));H=math.ceil(len(rows)/64)
    low_values=[0]*64
    global_stat={}
    if global_offset:
        low_values,global_stat=discover_global(rows,6,global_offset)
    groups=[[(int(v)^low_values[j]) for j,v in enumerate(rows[i*64:(i+1)*64])]+[0]*max(0,64-len(rows[i*64:(i+1)*64])) for i in range(H)]
    ranks,options=pair_options(groups,paid=mode.endswith('-paid'))
    pairs=choose_pairs(options,mode)
    used={v for pair in pairs for v in pair}
    pieces=[]
    for i,j in pairs:
        d=[a^b for a,b in zip(groups[i],groups[j])]
        rd=low_paid(d) if mode.endswith('-paid') else low_rank(d)
        # The i+j cofactor is chosen for one high coordinate and the
        # difference cofactor is assigned to the other. Preserve exactness.
        if ranks[i]>=ranks[j]:
            pieces.extend([((i,j),groups[j]),((i,),d)])
            assert ranks[i]-rd>0
        else:
            pieces.extend([((i,j),groups[i]),((j,),d)])
            assert ranks[j]-rd>0
    pieces.extend([((h,),groups[h]) for h in range(H) if h not in used])
    c=Circuit();hiA,hiB,_=high_flags(c,6);cache=monomial_cache(c,6)
    prefix=len(c.gates);high,active,tmp=c.new(3)
    global_coeff=mobius(low_values,6)
    for m,mask in enumerate(global_coeff):
        if not mask:continue
        if m==0:
            for idx,q in enumerate(TARGETS):
                if mask>>idx&1:c.emit('X',q)
        else:
            for idx,q in enumerate(TARGETS):
                if mask>>idx&1:c.emit('CX',int(cache[m]),q)
    terms=0; paid=0;high_cnt=0
    for sel,group in pieces:
        outputs,forms=rank_output_basis(mobius(group,6))
        factors=[(mask,form) for mask,form in zip(outputs,forms) if mask]
        if not factors:continue
        high_cnt+=1
        inverse=high_selector(c,hiA,hiB,high,tmp,sel)
        for mask,form in factors:
            if form==1:
                emit_fanout(c,high,mask)
            elif form.bit_count()==1:
                v=cache[form.bit_length()-1]
                c.emit('CCX',high,int(v),active)
                emit_fanout(c,active,mask)
                c.emit('CCX',high,int(v),active)
                paid+=1
            else:
                ops=[]
                for m in range(64):
                    if form>>m&1:
                        ops.append(('X',(tmp,)) if m==0 else ('CX',(int(cache[m]),tmp)))
                for op,qs in ops:c.emit(op,*qs)
                c.emit('CCX',high,tmp,active)
                emit_fanout(c,active,mask)
                c.emit('CCX',high,tmp,active)
                c.undo(ops)
                paid+=1
            terms+=1
        c.undo(inverse)
    c.undo(tuple(c.gates[:prefix]))
    assert tuple(c.gates[-prefix:])==tuple(reversed(c.gates[:prefix]))
    score=0
    for i,j in pairs:
        score+=max(ranks[i],ranks[j])-(low_paid([a^b for a,b in zip(groups[i],groups[j])]) if mode.endswith('-paid') else low_rank([a^b for a,b in zip(groups[i],groups[j])]))
    stat=dict(method='pair6-'+mode,slot=slot,prefix_len=prefix,
              qubits=c.alloc,CCX=int(c.counts['CCX']),CX=int(c.counts['CX']),
              X=int(c.counts['X']),pairs=pairs,pair_count=len(pairs),
              predicted_rank_gain=score,origin_rank_sum=sum(ranks),
              paid_products=paid,output_basis_terms=terms,
              active_high_blocks=high_cnt,global_offset=global_offset,**global_stat)
    h,hs=convert_hmr(c,stat)
    return h,hs


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seed',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--modes',nargs='+',choices=STRATEGIES,default=list(STRATEGIES))
    p.add_argument('--emit',action='store_true')
    p.add_argument('--global-offset',choices=['canonical','rref-high','rref-low'],default=None)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    f=a.out/'experiments.jsonl'
    if f.exists():raise FileExistsError('append-only output')
    with np.load(a.seed,allow_pickle=False) as z:w=np.array(z['angle_words'],np.int64)
    records=[]
    for mode in a.modes:
        for k in range(15):
            c,st=compile_pairs(w,k,mode,a.global_offset)
            proof=prove_hmr(c,delta_table(w,k),7)
            rec=dict(schema='gvqcc.pair6.v1',source=a.seed.name,
                     source_sha256=sha256(a.seed),**st,**proof,
                     native_KickMix_full_verifier=False,score_status='NO_SCORE')
            if a.emit:
                out=a.out/'kmx'/mode/f'angle_k_{k}.kmx'
                out.parent.mkdir(parents=True,exist_ok=True)
                out.write_text('\n'.join(c.kmx_lines())+'\n')
                rec['kmx_sha256']=sha256(out)
            records.append(rec)
            with f.open('a') as g:g.write(json.dumps(rec,sort_keys=True)+'\n')
            print(json.dumps({x:rec.get(x) for x in ('method','slot','CCX','qubits','pair_count','predicted_rank_gain')}),flush=True)
    summary=dict(source=a.seed.name,scope='actual KMX, full symbolic proof, no official verifier',
                 patterns=len(a.modes),circuits=len(records),methods=[dict(method=m,
                     CCX=sum(r['CCX'] for r in records if r['method']=='pair6-'+m+'--hmr-all-clean'),
                     Q=max(r['qubits'] for r in records if r['method']=='pair6-'+m+'--hmr-all-clean'),
                     pairs=sum(r['pair_count'] for r in records if r['method']=='pair6-'+m+'--hmr-all-clean'),
                     rank_gain=sum(r['predicted_rank_gain'] for r in records if r['method']=='pair6-'+m+'--hmr-all-clean')) for m in a.modes])
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
if __name__=='__main__':main()
