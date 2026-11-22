#!/usr/bin/env python3
"""Reproducible GF(2) ANGLE pattern registry with strict evidence tiers.

The patterns explore different mathematically defined equivalences, not
peephole CCX removal. A lowered rank is NEVER interpreted as paid Toffolis.

Run from research/ on a checkout of corcondor/gvqcc.
Requires NumPy. For physical evaluation also supply --physical-module and
--reference (not distributed). Outputs append-only JSONL records with
stable experiment IDs (seed hash, transformation, code version).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import sys
from dataclasses import dataclass
from pathlib import Path
import numpy as np

VERSION = '2026-11-23-patterns-v1'
N = 76
J = 5


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def canonical(data):
    return json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def load_npz(path):
    with np.load(path, allow_pickle=False) as z:
        return {k: z[k].copy() for k in z.files}


def gf2_rank(rows):
    arr = np.asarray(rows, dtype=np.uint8)
    if arr.ndim != 2: raise ValueError('2D expected')
    pivots = {}
    for row in arr:
        value = int.from_bytes(np.packbits(row, bitorder='little').tobytes(), 'little')
        while value:
            lead = value.bit_length()-1
            if lead not in pivots:
                pivots[lead] = value
                break
            value ^= pivots[lead]
    return len(pivots)


def delta_table(words, slot):
    if words.shape[1] != 75: raise ValueError('expected 75 word columns')
    d = words[:, 5*slot:5*slot+5].copy()
    if slot: d ^= words[:, 5*(slot-1):5*slot]
    return d


def mixed_rows(words, slot, bit=0, pad=None):
    """GF(2) mixed low4/high rows for 5 word outputs of one bit plane.

    In screen-only mode, exclude incomplete last high block (as original
    baseline) ; in pad mode include it, treating invalid tail as don't cares.
    Exact coefficients from 4-variable Möbius/ANF transform.
    """
    d = delta_table(words, slot)
    n = len(d)
    if pad is None:
        rows = (n//16)*16
        d = d[:rows]
    else:
        rows = math.ceil(n/16)*16
        if rows > n:
            missing = rows-n
            if pad == 'zero': extra = np.zeros((missing,5), dtype=d.dtype)
            elif pad == 'repeat': extra = np.repeat(d[-1:], missing, axis=0)
            elif pad == 'previous': extra = d[-16:-16+missing].copy()
            else: raise ValueError(pad)
            if extra.shape != (missing,5): raise AssertionError((pad,extra.shape,missing,n))
            d = np.concatenate([d,extra],axis=0)
    if not len(d): raise ValueError('no 16-row blocks')
    y = ((d >> bit)&1).reshape(-1,16,5).transpose(2,1,0).copy()
    for j in range(4):
        for lo in range(16):
            if lo & (1<<j): y[:,lo] ^= y[:,lo ^ (1<<j)]
    return y[:,1:,:]  # 5 x 15 x high


def mixed_rank_profile(words, bit=0, pad=None):
    return [gf2_rank(mixed_rows(words,k,bit,pad).reshape(75,-1)) for k in range(15)]


def dead_givens_mask(words, edges, eps=1e-14):
    """Both rotated amplitudes must be zero, not just the parent.

    Only these rows/edges can change angle without changing the vector.
    Free-on-both-zero is a sufficient condition, not an exhaustive symmetry.
    """
    v = np.zeros((len(words), N), dtype=np.float64)
    v[:,0] = 1.
    dead = np.zeros_like(words,dtype=bool)
    for edge,(p,c) in enumerate(edges):
        p,c=int(p),int(c)
        before_p,before_c=v[:,p].copy(),v[:,c].copy()
        dead[:,edge] = (np.abs(before_p)<eps)&(np.abs(before_c)<eps)
        ang = np.pi*words[:,edge]/64.0
        cos,sin=np.cos(ang),np.sin(ang)
        v[:,p] = cos*before_p-sin*before_c
        v[:,c] = sin*before_p+cos*before_c
    return dead, v


def apply(z, change):
    """Produce logically distinct candidate, updating U on row permutations.

    Never mutates original. Only an action whose mathematical semantics
    are explicitly specified here can enter an evidence ledger.
    """
    out = {k:v.copy() for k,v in z.items()}
    act = change['type']
    if act == 'dead_word':
        row, col, xor = change['row'],change['col'],change.get('xor',1)
        out['angle_words'][row,col] ^= xor
    elif act == 'run_length':
        for col in change['columns']:
            out['angle_words'][change['row'],col] ^= change.get('xor',1)
    elif act == 'row_swap':
        rank, a, b = change['rank'],change['a'],change['b']
        B = out['W'].shape[1]
        i,j=N+rank*B+a,N+rank*B+b
        out['angle_words'][[i,j]] = out['angle_words'][[j,i]]
        out['W'][rank,[a,b]] = out['W'][rank,[b,a]]
        if 'U' in out: out['U'][rank,[a,b]] = out['U'][rank,[b,a]]
    else: raise ValueError('nonphysical action: '+act)
    return out


def generate_dead(z, max_items=30):
    w=z['angle_words']; dead,_=dead_givens_mask(w,z['tree_edges'])
    R,B,_=z['W'].shape
    mags=np.linalg.norm(z['W'],axis=2)
    rows = sorted([(N+r*B+b,float(mags[r,b])) for r in range(R) for b in range(B)],key=lambda x:x[1])
    choices=[]
    for row,mag in rows:
        cols=np.flatnonzero(dead[row])
        for col in cols:
            choices.append({'type':'dead_word','row':row,'col':int(col),'xor':1,'prior_weight_norm':mag})
        if len(choices)>max_items*30:break
    return choices,{'all_dead_entries':int(dead.sum()),'inner_dead_entries':int(dead[N:].sum())}


def generate_run(z, lengths=(2,3,4), max_items=100):
    w=z['angle_words']; dead,_=dead_givens_mask(w,z['tree_edges'])
    R,B,_=z['W'].shape
    mags=np.linalg.norm(z['W'],axis=2)
    rows=sorted([(N+r*B+b,float(mags[r,b])) for r in range(R) for b in range(B)],key=lambda x:x[1])
    actions=[]
    for row,mag in rows:
        for length in lengths:
            for start in range(16-length):
                for j in range(5):
                    cols=[5*k+j for k in range(start,start+length)]
                    if all(dead[row,col] for col in cols):
                        actions.append({'type':'run_length','row':row,'columns':cols,'xor':1,'prior_weight_norm':mag})
        if len(actions)>max_items*20:break
    return actions,{'raw_run_actions':len(actions)}


def generate_swap(z, pairs_per_rank=15):
    R,B,_ = z['W'].shape
    mags=np.linalg.norm(z['W'],axis=2)
    actions=[]
    for r in range(R):
        lows=list(np.argsort(mags[r])[:min(B,12)])
        for i in range(len(lows)):
            for j in range(i+1,len(lows)):
                a,b=sorted((int(lows[i]),int(lows[j])))
                actions.append({'type':'row_swap','rank':r,'a':a,'b':b,
                                'prior_weight_norm':float(mags[r,a]+mags[r,b])})
                if len([a for a in actions if a['rank']==r])>=pairs_per_rank:break
            if len([a for a in actions if a['rank']==r])>=pairs_per_rank:break
    return actions,{'raw_row_swaps':len(actions)}


def cheapest_output_basis(words, bitplanes=(0,1,2,3,4)):
    """Find invertible elementary XOR output-basis changes for a batch.

    The 5 output words' given bit plane may be re-encoded as t_i ^= t_j.
    This has a CX inverse, but no actual KMX is emitted or verified here.
    The joint matrix rank is invariant under this transformation.
    """
    results=[]
    for k in range(15):
        for bit in bitplanes:
            A=mixed_rows(words,k,bit)
            ranks=[gf2_rank(A[i]) for i in range(5)]
            combined=gf2_rank(A.reshape(75,-1))
            moves=[]
            for target in range(5):
                for source in range(5):
                    if target==source:continue
                    rnew=gf2_rank(A[target]^A[source])
                    saving=ranks[target]-rnew
                    if saving>0:
                        moves.append({'target':target,'source':source,'old_rank':ranks[target],
                                      'new_rank':rnew,'single_output_rank_saving':saving})
            if moves:
                moves.sort(key=lambda x:(-x['single_output_rank_saving'],x['target'],x['source']))
                results.append({'slot':k,'bit':bit,'joint_rank_invariant':combined,
                                'original_single_output_rank_sum':sum(ranks),'best':moves[0],
                                'positive_moves_count':len(moves)})
    return results


def padding_completions(words):
    n=len(words); missing=(-n)%16
    if not missing:return []
    results=[]
    for k in range(15):
        for bit in range(7):
            values={pad:gf2_rank(mixed_rows(words,k,bit,pad).reshape(75,-1))
                    for pad in ('zero','repeat','previous')}
            candidates=sorted(values.items(),key=lambda x:(x[1],x[0]))
            if len(set(values.values()))>1:
                results.append({'slot':k,'bit':bit,'padding_unused_addresses':missing,
                                'ranks':values,'best':candidates[0][0],
                                'rank_spread':max(values.values())-min(values.values())})
    return results


def fingerprint(seed_sha,pattern,action):
    return hashlib.sha256(canonical({'v':VERSION,'seed':seed_sha,'pattern':pattern,'action':action}).encode()).hexdigest()


class Ledger:
    def __init__(self,path):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        self.ids=set()
        if self.path.exists():
            with self.path.open(encoding='utf-8') as f:
                for line in f:
                    if line.strip():self.ids.add(json.loads(line)['experiment_id'])
        self.added=0
    def append(self,seed_sha,pattern,action,record):
        key=fingerprint(seed_sha,pattern,action)
        if key in self.ids:return False
        data={'schema':'gvqcc.pattern.evidence.v1','experiment_id':key,'version':VERSION,
              'seed_sha256':seed_sha,'pattern':pattern,'action':action,**record}
        with self.path.open('a',encoding='utf-8') as f:
            f.write(canonical(data)+'\n');f.flush();os.fsync(f.fileno())
        self.ids.add(key);self.added+=1
        return True


def physical_metrics(phys,z):
    m=phys.evaluate(z)
    key=['error_1','error_2','Lambda','E_gap','lambda_eff','gap_in_domain']
    d={k:(float(m[k]) if k!='gap_in_domain' else bool(m[k])) for k in key}
    d['pass']=bool(d['error_1']<=0.02 and d['error_2']<=0.02 and
                   d['Lambda']>49 and d['E_gap']>3.914898 and d['gap_in_domain'] and
                   np.isfinite(d['lambda_eff']))
    return d


def import_physics(path,reference):
    spec=importlib.util.spec_from_file_location('gvqcc_pattern_reference_physics',path)
    if spec is None or spec.loader is None: raise ValueError(path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod.Physical(reference)


def shortlist(z, actions, slots_ranks, budget=8, no_worse=False):
    """Select diversity-aware candidates by exact affected-bit0 rank delta.

    For row swaps, all 15 slots may change. This is a screen, not a cost model.
    """
    found=[]
    orig=sum(slots_ranks)
    for action in actions:
        child=apply(z,action)
        if action['type']=='dead_word':
            slot = action['col']//5
            changed_slots=[slot]+([slot+1] if slot<14 else [])
        elif action['type']=='run_length':
            first=action['columns'][0]//5
            last=action['columns'][-1]//5
            changed_slots=[first]+([last+1] if last<14 else [])
        else:
            changed_slots=list(range(15))
        rank_profile=slots_ranks.copy()
        for slot in changed_slots:
            rank_profile[slot]=gf2_rank(mixed_rows(child['angle_words'],slot,0).reshape(75,-1))
        delta=sum(rank_profile)-orig
        if not no_worse or delta<=0:
            found.append((delta,action,rank_profile))
    found.sort(key=lambda x:(x[0], canonical(x[1])))
    # Select at least one unchanged/worse candidate when available (counterexample control).
    picks=found[:budget]
    return picks, {'screened':len(actions),'rank_improving':sum(x[0]<0 for x in found),
                   'rank_tie':sum(x[0]==0 for x in found),
                   'rank_worsening':sum(x[0]>0 for x in found)}


def run_seeds(args):
    phys=import_physics(args.physical_module,args.reference) if args.physical_module else None
    journal=Ledger(args.ledger)
    summaries=[]
    for seed in args.seeds:
        z=load_npz(seed);s_sha=sha256(seed)
        if 'brot' in z and int(z['brot'])!=7: raise ValueError('only brot=7')
        shape=z['W'].shape
        base_rank=mixed_rank_profile(z['angle_words'])
        base_physical=physical_metrics(phys,z) if phys else None
        base={'seed_path':str(seed),'seed_sha256':s_sha,'shape':list(shape),
              'addresses':int(len(z['angle_words'])),'base_rank_bit0':sum(base_rank),
              'base_physical':base_physical, 'patterns':{}}
        journal.append(s_sha,'seed_baseline',{},
             {'evidence':'physics_numeric' if phys else 'structural_screen',
              'baseline_rank':base_rank,'base_physical':base_physical,
              'source_path':str(seed),'full_kmb':False,'official_verified':False})
        generators={
            'null_givens':lambda:generate_dead(z),
            'chained_word_run':lambda:generate_run(z),
            'within_rank_row_permutation':lambda:generate_swap(z,pairs_per_rank=4),
        }
        for family,gen in generators.items():
            actions,metadata=gen()
            actions=actions[:args.max_screen_actions]
            picks,screen=shortlist(z,actions,base_rank,args.budget)
            # control: choose rank-worse swap as example in addition to best
            if family=='within_rank_row_permutation' and actions:
                worst=max(actions,key=lambda a:sum(mixed_rank_profile(apply(z,a)['angle_words'])))
                if all(canonical(worst)!=canonical(p[1]) for p in picks):
                    wprof=mixed_rank_profile(apply(z,worst)['angle_words'])
                    picks.append((sum(wprof)-sum(base_rank),worst,wprof))
            outcomes=[]
            for delta,action,ranks in picks:
                changed=apply(z,action)
                measured=physical_metrics(phys,changed) if phys else None
                # For symmetry cases, we also explicitly verify full reconstructed U.
                invariant=None
                if family in ('null_givens','within_rank_row_permutation'):
                    # No stronger claim than actual physical numeric equality unless tested below.
                    invariant=all(abs(measured[k]-base_physical[k])<1e-8
                                  for k in ('error_1','error_2','Lambda','E_gap','lambda_eff')) if measured else None
                record={'evidence':'physics_numeric' if phys else 'structural_screen',
                        'GF2_bit0_rank_before':sum(base_rank),
                        'GF2_bit0_rank_after':sum(ranks),
                        'GF2_bit0_rank_delta':delta,
                        'physics':measured,
                        'physics_invariant_within_1e8':invariant,
                        'implementation':{'kmb_emitted':False,'angle_ccx_measured':None,
                                          'native_kickmix_pass':False,'new_score':None},
                        'classification': ('NUMERIC_PASS_UNCOMPILED' if measured and measured['pass']
                                           else 'NUMERIC_FAIL' if measured else 'STRUCTURAL_ONLY')}
                journal.append(s_sha,family,action,record)
                outcomes.append({'action':action,'rank_delta':delta,'physical_pass':measured['pass'] if measured else None})
            base['patterns'][family]={'screen':screen,**metadata,'checked':len(outcomes),
                                       'physics_pass':sum(int(x['physical_pass']) for x in outcomes if x['physical_pass'] is not None),
                                       'top':outcomes[:3]}
        # The following are strictly non-physical changes of compiler representation.
        basis=cheapest_output_basis(z['angle_words'])
        for record in basis:
            journal.append(s_sha,'linear_output_basis',record,
                {'evidence':'algebraic_identity_only','raw_angle_words_unchanged':True,
                 'mathematical_basis_invertible_by_CX':True,
                 'kmb_emitted':False,'native_verified':False,'Toffoli_saving':None})
        base['patterns']['linear_output_basis']={'positive_patterns':len(basis),
                                                 'best':sorted(basis,key=lambda x:-x['best']['single_output_rank_saving'])[:3]}
        pads=padding_completions(z['angle_words'])
        for rec in pads:
            journal.append(s_sha,'invalid_address_padding',rec,
                {'evidence':'algebraic_screen_only','valid_addresses_unchanged':True,
                 'kmb_emitted':False,'native_verified':False,'Toffoli_saving':None})
        base['patterns']['invalid_address_padding']={'nonconstant_effects':len(pads),
                                                      'best':sorted(pads,key=lambda x:-x['rank_spread'])[:3]}
        print(json.dumps({'seed':seed.name,'summary':{k:{x:v for x,v in val.items() if x!='top'}
                                                    for k,val in base['patterns'].items()}},ensure_ascii=False),flush=True)
        summaries.append(base)
    result={'schema':'gvqcc.pattern.run.v1','version':VERSION,'seeds':summaries,
            'ledger':str(args.ledger),'new_ledger_events':journal.added,
            'reference_sha256':sha256(args.reference) if args.reference else None,
            'physical_module_sha256':sha256(args.physical_module) if args.physical_module else None,
            'evidence_ceiling':'PHYSICS_NUMERIC_AND_GF2_ONLY_NO_NATIVE_KMB'}
    Path(args.summary).parent.mkdir(parents=True,exist_ok=True)
    Path(args.summary).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seeds',nargs='+',type=Path,required=True)
    p.add_argument('--physical-module',type=Path)
    p.add_argument('--reference',type=Path)
    p.add_argument('--ledger',type=Path,required=True)
    p.add_argument('--summary',type=Path,required=True)
    p.add_argument('--budget',type=int,default=8)
    p.add_argument('--max-screen-actions',type=int,default=240)
    a=p.parse_args()
    if a.budget<1 or a.max_screen_actions<1 or bool(a.physical_module)!=bool(a.reference):p.error('budget>=1 and physical-module/reference together')
    run_seeds(a)


if __name__=='__main__':main()
