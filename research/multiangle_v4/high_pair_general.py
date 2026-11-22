#!/usr/bin/env python3
"""General high-cofactor basis exchanges, including unrelated high selectors.

For unrelated high block indices i,j, compute e_i XOR e_j using TWO CCX
into high flag, and erase its value by ONE HMR plus TWO conditional CZ:
    HMR high -> m;
    CZ hiA_i hiB_i if m;
    CZ hiA_j hiB_j if m.
The conditional phase is (-1)^{m(e_i+e_j)} and cancels the HMR phase.
This extends the cheap paired-high algorithm to ALL 190 pairs of 20 blocks.
A full all-address GF(2) simulator symbolically verifies every measurement
symbol and the exact output oracle; no native verifier is claimed.
"""
from __future__ import annotations
import argparse, math, json,sys
from pathlib import Path
from collections import Counter
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
BASE_CODE=ROOT/'gvqcc_multiform' if (ROOT/'gvqcc_multiform').exists() else ROOT
V3_CODE=ROOT/'gvqcc_multiform_v3' if (ROOT/'gvqcc_multiform_v3').exists() else ROOT/'multiangle_v3'
sys.path.insert(0,str(BASE_CODE))
sys.path.insert(0,str(V3_CODE))
sys.path.insert(0,str(ROOT/'gvqcc_multiform_v4' if (ROOT/'gvqcc_multiform_v4').exists() else Path(__file__).resolve().parent))
from multi_angle_synthesis import Circuit,delta_table,word_masks,rank_output_basis,emit_fanout,sha256,TARGETS,TAGS
from partition_patterns import high_flags,monomial_cache,mobius
from high_pair import low_paid,choose_pairs
from global_cofactor import discover_global
from hmr_patterns import MeasuredCircuit


def choose(rows:list[int],global_offset:str|None,mode:str):
    H=math.ceil(len(rows)/64)
    if global_offset:
        low,stat=discover_global(rows,6,global_offset)
    else:low=[0]*64;stat={}
    groups=[[int(v)^low[j] for j,v in enumerate(rows[64*h:64*h+64])]+[0]*max(0,64-len(rows[64*h:64*h+64])) for h in range(H)]
    costs=[low_paid(g) for g in groups]
    options=[]
    for i in range(H):
        for j in range(i+1,H):
            diff=[a^b for a,b in zip(groups[i],groups[j])]
            d=low_paid(diff)
            overhead=0 if ((i&7)==(j&7) or (i>>3)==(j>>3)) else 1
            gain=max(costs[i],costs[j])-d-overhead
            if gain>0:options.append((gain,i,j,d,costs[i],costs[j]))
    pairs=choose_pairs(options,mode)
    selected={h for pair in pairs for h in pair}
    pieces=[]
    for i,j in pairs:
        diff=[a^b for a,b in zip(groups[i],groups[j])]
        if costs[i]>=costs[j]:pieces.extend([((i,j),groups[j]),((i,),diff)])
        else:pieces.extend([((i,j),groups[i]),((j,),diff)])
    pieces.extend([((i,),groups[i]) for i in range(H) if i not in selected])
    predicted=sum(next(o[0] for o in options if o[1:3]==(i,j)) for i,j in pairs)
    return pieces,low,dict(global_stat=stat,pair_count=len(pairs),pairs=pairs,
                            matching_predicted_paid_gain=predicted,
                            total_high_pairs_examined=H*(H-1)//2,
                            positive_gain_pair_candidates=len(options),
                            cross_factor_pairs=sum(not ((i&7)==(j&7) or (i>>3)==(j>>3)) for i,j in pairs))


def full_domain_prove(c:MeasuredCircuit,delta:np.ndarray,seed=7):
    """Bitparallel all-address proof with multiple CZ for one HMR bit."""
    n=len(delta);ones=(1<<n)-1
    initial=[0]*c.num_qubits
    for q in range(11):initial[q]=sum(((a>>q)&1)<<a for a in range(n))
    rng=np.random.default_rng(seed)
    for q in range(11,51):initial[q]=int.from_bytes(rng.bytes((n+7)//8),'little')&ones
    current=initial.copy();phase=None;number=0;multi=0;cz_since=0
    for op,q,flag in c.operations:
        if op!='CZ' and phase is not None:
            if phase:raise AssertionError(('uncancelled_measurement',number-1,(phase&-phase).bit_length()-1))
            if cz_since>1:multi+=1
            phase=None;cz_since=0
        if op=='X':current[q[0]]^=ones
        elif op=='CX':current[q[1]]^=current[q[0]]
        elif op=='CCX':current[q[2]]^=current[q[0]]&current[q[1]]
        elif op=='HMR':
            assert q[0]>=51
            phase=current[q[0]]
            current[q[0]]=0
            number+=1
        elif op=='CZ':
            if phase is None:raise AssertionError('orphan conditional CZ')
            phase^=current[q[0]]&current[q[1]]
            cz_since+=1
        else:raise AssertionError(op)
    if phase is not None:
        if phase:raise AssertionError('trailing uncompensated measurement')
        if cz_since>1:multi+=1
    targets=word_masks(delta)
    for t,q in enumerate(TARGETS):
        required=sum(((mask>>t)&1)<<i for i,mask in enumerate(targets))
        if current[q]!=(initial[q]^required):raise AssertionError(('wrong_output',t,q))
    for q in list(range(11))+list(TAGS):
        if current[q]!=initial[q]:raise AssertionError(('public qubit changed',q))
    for q in range(51,c.num_qubits):
        if current[q]:raise AssertionError(('dirty_scratch',q))
    return dict(all_valid_addresses=True,all_HMR_symbols_cancel=True,
                scratch_clean=True,tags_unchanged=True,dirty_target_XOR=True,
                independently_checked_measurements=number,multi_CZ_measurements=multi)


def compile_general(words:np.ndarray,slot:int,mode='exact',global_offset='canonical'):
    rows=word_masks(delta_table(words,slot))
    pieces,low_values,info=choose(rows,global_offset,mode)
    c=Circuit();hiA,hiB,_=high_flags(c,6);cache=monomial_cache(c,6)
    prefix=len(c.gates)
    high,active,tmp=c.new(3)
    specials={} # id gate -> (emit HMR, list of monomial CZ corrections)
    special_forward=set()
    for mon,mask in enumerate(mobius(low_values,6)):
        if not mask:continue
        for idx,q in enumerate(TARGETS):
            if mask>>idx&1:
                if mon==0:c.emit('X',q)
                else:c.emit('CX',int(cache[mon]),q)
    n_global=sum(bool(x) for x in low_values)
    num=0;cross=0;paired=0
    for ids,group in pieces:
        outputs,forms=rank_output_basis(mobius(group,6))
        factors=[(mask,form) for mask,form in zip(outputs,forms) if mask]
        if not factors:continue
        controls=[(hiA[h&7],hiB[h>>3]) for h in ids]
        start=len(c.gates)
        if len(ids)==1:
            a,b=controls[0];c.emit('CCX',a,b,high)
            selector_kind='single'
        elif len(ids)==2 and (ids[0]&7)==(ids[1]&7):
            b1,b2=hiB[ids[0]>>3],hiB[ids[1]>>3]
            c.emit('CX',b1,tmp);c.emit('CX',b2,tmp)
            c.emit('CCX',hiA[ids[0]&7],tmp,high)
            c.emit('CX',b2,tmp);c.emit('CX',b1,tmp)
            selector_kind='cheap'
        elif len(ids)==2 and (ids[0]>>3)==(ids[1]>>3):
            a1,a2=hiA[ids[0]&7],hiA[ids[1]&7]
            c.emit('CX',a1,tmp);c.emit('CX',a2,tmp)
            c.emit('CCX',hiB[ids[0]>>3],tmp,high)
            c.emit('CX',a2,tmp);c.emit('CX',a1,tmp)
            selector_kind='cheap'
        else:
            for a,b in controls:c.emit('CCX',a,b,high)
            selector_kind='general';cross+=1
            special_forward.update((start,start+1))
        forward=list(c.gates[start:])
        for mask,form in factors:
            if form==1:emit_fanout(c,high,mask)
            elif form.bit_count()==1:
                q=cache[form.bit_length()-1]
                c.emit('CCX',high,int(q),active)
                emit_fanout(c,active,mask)
                c.emit('CCX',high,int(q),active)
            else:
                ops=[]
                for mon in range(64):
                    if form>>mon&1:
                        ops.append(('X',(tmp,)) if mon==0 else ('CX',(int(cache[mon]),tmp)))
                for op,qs in ops:c.emit(op,*qs)
                c.emit('CCX',high,tmp,active)
                emit_fanout(c,active,mask)
                c.emit('CCX',high,tmp,active)
                c.undo(ops)
            num+=1
        # Schedule a general-pair inverse as a single HMR + two conditional
        # CZs, replacing TWO inverse CCX; all other high selectors have
        # exactly one inverse CCX and are handled by the existing marker.
        if selector_kind=='general':
            before=len(c.gates)
            c.undo(forward)
            inv=list(range(before,before+len(forward)))
            assert len(inv)==2
            specials[inv[0]]=(high,controls)
            specials[inv[1]]=(None,None)
        else:c.undo(forward)
    c.undo(tuple(c.gates[:prefix]))
    # First mark inverse CCX of active products (must be followed only by
    # target CX fanout before its exact twin inverse).
    markers={}
    for i,(op,q) in enumerate(c.gates):
        if op!='CCX' or q[-1]!=active:continue
        j=i+1
        while j<len(c.gates) and c.gates[j][0]=='CX' and c.gates[j][1][0]==active and c.gates[j][1][1] in TARGETS:j+=1
        if j>i+1 and j<len(c.gates) and c.gates[j]==(op,q):markers[j]=[q[:2]]
    # Marker high inverse for singleton and cheap-pair selectors, skipping
    # general high-pair inverses already represented in 'specials'.
    highindices=[i for i,(op,q) in enumerate(c.gates) if op=='CCX' and q[-1]==high and i not in specials and i not in special_forward]
    assert len(highindices)%2==0
    for i,j in zip(highindices[::2],highindices[1::2]):
        if c.gates[i]!=c.gates[j]:raise AssertionError(('high_pair_mismatch',i,j))
        markers[j]=[c.gates[j][1][:2]]
    for i in range(len(c.gates)-prefix,len(c.gates)):
        op,q=c.gates[i]
        if op=='CCX':markers[i]=[q[:2]]
    ops=[]
    for i,(op,q) in enumerate(c.gates):
        if i in specials:
            t,controls=specials[i]
            if t is not None:
                ops.append(('HMR',(t,),0))
                for a,b in controls:ops.append(('CZ',(a,b),0))
            continue
        if i in markers:
            t=q[-1];ops.append(('HMR',(t,),0))
            for a,b in markers[i]:ops.append(('CZ',(a,b),0))
        else:ops.append((op,q,None))
    h=MeasuredCircuit(c.alloc,ops)
    stat=dict(method='general6-'+mode,slot=slot,qubits=c.alloc,
        CCX=int(h.counts['CCX']),CX=int(h.counts['CX']),X=int(h.counts['X']),
        HMR=int(h.counts['HMR']),conditional_CZ=int(h.counts['CZ']),
        global_offset=global_offset,global_nonzero_low_addresses=n_global,
        general_selector_count=cross,output_basis_terms=num,
        **info)
    return h,stat


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seed',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--modes',nargs='+',choices=['greedy','exact','reverse'],default=['greedy','exact','reverse'])
    p.add_argument('--global-offset',choices=['canonical','rref-high','rref-low'],default='canonical')
    p.add_argument('--emit',action='store_true')
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    f=a.out/'experiments.jsonl'
    if f.exists():raise FileExistsError('append-only')
    with np.load(a.seed,allow_pickle=False) as z:w=np.asarray(z['angle_words'],np.int64)
    rows=[]
    for mode in a.modes:
        for k in range(15):
            c,stat=compile_general(w,k,mode,a.global_offset)
            proof=full_domain_prove(c,delta_table(w,k),seed=7)
            rec=dict(schema='gvqcc.generalpair.v1',source=a.seed.name,
                     source_sha256=sha256(a.seed),**stat,**proof,
                     official_score=None,official_full_verifier=False)
            if a.emit:
                dest=a.out/'kmx'/mode/f'angle_k_{k}.kmx'
                dest.parent.mkdir(parents=True,exist_ok=True)
                dest.write_text('\n'.join(c.kmx_lines())+'\n');rec['kmx_sha256']=sha256(dest)
            with f.open('a') as stream:stream.write(json.dumps(rec,sort_keys=True)+'\n')
            rows.append(rec)
            print(json.dumps({v:rec.get(v) for v in ('method','slot','CCX','qubits','general_selector_count','multi_CZ_measurements')}),flush=True)
    report=dict(source=a.seed.name,n=len(rows),group=[dict(method=m,CCX=sum(x['CCX'] for x in rows if x['method']=='general6-'+m),
                   general_selectors=sum(x['general_selector_count'] for x in rows if x['method']=='general6-'+m),
                   Q=max(x['qubits'] for x in rows if x['method']=='general6-'+m)) for m in a.modes])
    (a.out/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
