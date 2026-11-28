#!/usr/bin/env python3
"""Exact 7-bit ANGLE loader compiler with high-independent output factor extraction.

Mathematical operation: with F(h,l) in GF(2)^35 and N valid addresses,
choose a family of output parities alpha_i s.t. alpha_i . F(h,l) = f_i(l)
for every valid h,l. A GF(2) right inverse gives a low-only output vector
G(l), so F(h,l) = G(l) XOR [F(h,l) XOR G(l)].  The first term is applied
ONCE from low-monomial cache; the residual is synthesized per high block.

The high-independent spaces are exact nullspaces of (F_h-F_0), restricted
to ALL *valid* addresses. Proof applies to every high-block, including
partial last block. No physical error is introduced; words are unchanged.

HMR conversion and symbolic full-domain phase proofs use the existing v3
certificates, but this code creates new gate sequences, not peephole edits.
"""
from __future__ import annotations
import argparse,hashlib,json,math,sys
from pathlib import Path
from collections import Counter
from typing import Sequence
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
BASE_CODE=ROOT/'gvqcc_multiform' if (ROOT/'gvqcc_multiform').exists() else ROOT
V3_CODE=ROOT/'gvqcc_multiform_v3' if (ROOT/'gvqcc_multiform_v3').exists() else ROOT/'multiangle_v3'
sys.path.insert(0,str(BASE_CODE))
sys.path.insert(0,str(V3_CODE))
from multi_angle_synthesis import (Circuit,delta_table,word_masks,rank_output_basis,
                                    emit_fanout,TARGETS,sha256)
from partition_patterns import high_flags,monomial_cache,mobius,convert_hmr
from hmr_patterns import prove as prove_hmr

SIZES=(5,6)
MODES=('canonical','rref-high','rref-low','rref-best')
ALGORITHMS=tuple(f'global{L}-{mode}' for L in SIZES for mode in MODES)
MASK35=(1<<35)-1


def parity(mask:int,vector:int)->int:
    return (mask & vector).bit_count()&1


def kernel(vectors:Sequence[int],n:int=35)->list[int]:
    """Basis of all output parities constant across high blocks."""
    pivots={}
    for row in vectors:
        x=int(row)
        while x:
            p=x.bit_length()-1
            if p in pivots:x ^= pivots[p]
            else:pivots[p]=x;break
    solutions=[]
    for free in range(n):
        if free in pivots:continue
        v=1<<free
        # Pivot equations solved in increasing pivot order.
        for p in sorted(pivots):
            if parity(v,pivots[p]):v^=1<<p
        assert all(not parity(v,row) for row in pivots.values())
        solutions.append(v)
    return solutions


def independent_rows(rows:Sequence[int],order='high')->list[tuple[int,int]]:
    """RREF over GF(2): (output parity alpha, unique pivot bit).

    Two pivot priorities explore different legal right inverses, not
    different mathematical functions. All selected alpha rows independent.
    """
    mask=MASK35
    basis={}
    for row in rows:
        v=int(row)
        while v:
            p=v.bit_length()-1 if order=='high' else (v&-v).bit_length()-1
            if p in basis:v ^= basis[p]
            else:basis[p]=v;break
    for p in sorted(basis,reverse=(order=='high')):
        # remove the p coefficient from all OTHER basis rows
        for q in list(basis):
            if q!=p and (basis[q]>>p)&1:basis[q]^=basis[p]
    ans=sorted(((basis[p],p) for p in basis),key=lambda x:x[1])
    assert all(parity(a,1<<p)==1 and all(parity(a,1<<q)==0 for _,q in ans if q!=p)
               for a,p in ans)
    return ans


def discover_global(rows:Sequence[int],L:int,mode:str):
    """Return low-only output corrections and exact certificate.

    RREF mode: maximal high-invariant parity subspace. Canonical mode:
    five word upper-bit XOR parities, only if invariant on valid rows.
    """
    nl=1<<L;n=len(rows)
    if n<nl:raise ValueError('needs at least one complete low block')
    differences=[int(rows[a]^rows[a%nl]) for a in range(nl,n)]
    if mode=='canonical':
        alphas=[(3<<(7*j+5)) for j in range(5)]
        alphas=[a for a in alphas if all(parity(a,d)==0 for d in differences)]
        basis=independent_rows(alphas,'high')
    else:
        free=kernel(differences)
        basis=independent_rows(free,'low' if mode=='rref-low' else 'high')
    low=[]
    for i in range(nl):
        correction=0
        for a,p in basis:
            if parity(a,rows[i]):correction ^= 1<<p
        low.append(correction)
    # Exact full-care guarantee across all N valid addresses.
    for a,row in enumerate(rows):
        for alpha,pivot in basis:
            assert parity(alpha,row^low[a%nl])==0, (a,alpha,pivot)
    active=sum(any(parity(alpha,rows[i]) for i in range(nl)) for alpha,p in basis)
    return low,dict(invariant_dimension=len(basis), active_global_parities=active,
                    pivot_bits=[p for a,p in basis],
                    alpha_masks=[hex(a) for a,p in basis],
                    global_values_sha256=hashlib.sha256(b''.join(int(x).to_bytes(5,'little') for x in low)).hexdigest())


def factor_rank(rows:Sequence[int],L:int)->int:
    nl=1<<L
    return sum(len(rank_output_basis(mobius(list(rows[i:i+nl])+[0]*max(0,nl-len(rows[i:i+nl])),L))[0])
               for i in range(0,len(rows),nl))


def build_for_low(rows:list[int],L:int,low_values:list[int],stat:dict):
    c=Circuit()
    hiA,hiB,cut=high_flags(c,L)
    cache=monomial_cache(c,L)
    prefix=len(c.gates)
    high,active,low_tmp=c.new(3)
    nl=1<<L
    # The free high-independent component is applied once per loader.
    global_coeff=mobius(list(low_values),L)
    cx_global=0;x_global=0
    for m,out in enumerate(global_coeff):
        if not out:continue
        if m==0:
            for idx,q in enumerate(TARGETS):
                if (out>>idx)&1:c.emit('X',q);x_global+=1
        else:
            for idx,q in enumerate(TARGETS):
                if (out>>idx)&1:c.emit('CX',int(cache[m]),q);cx_global+=1
    terms=0;nontriv=0;active_high=0;perblock=[]
    for h in range(math.ceil(len(rows)/nl)):
        r=rows[h*nl:(h+1)*nl]
        residual=[int(v)^low_values[i] for i,v in enumerate(r)]
        coeff=mobius(residual+[0]*(nl-len(r)),L)
        outputs,forms=rank_output_basis(coeff)
        factors=[(mask,form) for mask,form in zip(outputs,forms) if mask]
        rank=len(factors);perblock.append(rank)
        if not factors:continue
        active_high+=1
        c.emit('CCX',hiA[h&((1<<cut)-1)],hiB[h>>cut],high)
        for mask,form in factors:
            if form==1:
                emit_fanout(c,high,mask)
            elif form.bit_count()==1:
                v=cache[form.bit_length()-1]
                c.emit('CCX',high,int(v),active)
                emit_fanout(c,active,mask)
                c.emit('CCX',high,int(v),active)
                nontriv+=1
            else:
                ops=[]
                for m in range(nl):
                    if form>>m&1:
                        ops.append(('X',(low_tmp,)) if m==0 else ('CX',(int(cache[m]),low_tmp)))
                for op,qs in ops:c.emit(op,*qs)
                c.emit('CCX',high,low_tmp,active)
                emit_fanout(c,active,mask)
                c.emit('CCX',high,low_tmp,active)
                c.undo(ops)
                nontriv+=1
            terms+=1
        c.emit('CCX',hiA[h&((1<<cut)-1)],hiB[h>>cut],high)
    c.undo(tuple(c.gates[:prefix]))
    assert tuple(c.gates[-prefix:])==tuple(reversed(c.gates[:prefix]))
    return c,dict(stat,slot=None,low_bits=L,prefix_len=prefix,qubits=c.alloc,
                  CCX=int(c.counts['CCX']),CX=int(c.counts['CX']),X=int(c.counts['X']),
                  low_global_cx=cx_global,low_global_x=x_global,
                  n_high_blocks=math.ceil(len(rows)/nl),active_high_blocks=active_high,
                  output_basis_terms=terms,nontrivial_high_low_products=nontriv,
                  residual_basis_ranks=perblock)


def compile_global(words:np.ndarray,slot:int,algorithm:str):
    if algorithm not in ALGORITHMS:raise ValueError(algorithm)
    header,mode=algorithm.split('-',1)
    L=int(header[6:])
    rows=word_masks(delta_table(words,slot))
    modes=[mode] if mode!='rref-best' else ['rref-high','rref-low','canonical']
    results=[]
    for variant in modes:
        low,stat=discover_global(rows,L,variant)
        c,stat=build_for_low(rows,L,low,stat)
        stat.update(method=algorithm,slot=slot,variant=variant,
                    original_basis_rank_total=factor_rank(rows,L),
                    residual_basis_rank_total=sum(stat['residual_basis_ranks']),
                    actual_ccx_before_hmr=stat['CCX'])
        h,hs=convert_hmr(c,stat)
        results.append((h,hs))
    results.sort(key=lambda x:(x[1]['CCX'],x[1]['CX'],x[1]['X']))
    return results[0]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seed',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--methods',nargs='+',choices=ALGORITHMS,default=list(ALGORITHMS))
    p.add_argument('--emit',action='store_true')
    args=p.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    ledger=args.out/'experiments.jsonl'
    if ledger.exists():raise FileExistsError('append-only output path')
    with np.load(args.seed,allow_pickle=False) as z:words=np.array(z['angle_words'],np.int64)
    recs=[]
    for alg in args.methods:
        for k in range(15):
            c,stat=compile_global(words,k,alg)
            proof=prove_hmr(c,delta_table(words,k),dirty_seed=7)
            rec=dict(schema='gvqcc.globalcofactor.v1',source=args.seed.name,
                     source_sha256=sha256(args.seed),algorithm=alg,**stat,**proof,
                     native_kickmix_full_verifier=False,official_score=None)
            if args.emit:
                dest=args.out/'kmx'/alg/f'angle_k_{k}.kmx'
                dest.parent.mkdir(parents=True,exist_ok=True)
                dest.write_text('\n'.join(c.kmx_lines())+'\n')
                rec['kmx_sha256']=sha256(dest)
            with ledger.open('a') as f:f.write(json.dumps(rec,sort_keys=True)+'\n')
            recs.append(rec)
            print(json.dumps({q:rec.get(q) for q in ('algorithm','slot','CCX','qubits','CX','active_global_parities','original_basis_rank_total','residual_basis_rank_total')}),flush=True)
    summary=dict(scope='NEW ACTUAL KMX BUILT SYMBOLICALLY PROVED; NO OFFICIAL NATIVE VERIFIER',
                 source=args.seed.name,methods=args.methods,n=len(recs),
                 by_method=[dict(method=alg,CCX=sum(x['CCX'] for x in recs if x['algorithm']==alg),
                                 CX=sum(x['CX'] for x in recs if x['algorithm']==alg),
                                 Q=max(x['qubits'] for x in recs if x['algorithm']==alg),
                                 measured=sum(x['HMR'] for x in recs if x['algorithm']==alg),
                                 global_rank_savings=sum(x['original_basis_rank_total']-x['residual_basis_rank_total'] for x in recs if x['algorithm']==alg))
                           for alg in args.methods])
    (args.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
if __name__=='__main__':main()
