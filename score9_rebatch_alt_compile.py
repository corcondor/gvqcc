#!/usr/bin/env python3
"""Compile care-domain J=4 loaders with arbitrary 4/7 or 5/6 input partition.

This emits genuine reversible XOR loaders, including measurement phase
corrections, then proves each circuit for all 1220 addresses, arbitrary output
values, and all measurement branches. It does not invoke the full score check.
"""
from __future__ import annotations
import argparse,hashlib,json,sys,time
from pathlib import Path
import numpy as np
sys.path.append('/workspace/scratch/7f542e06b7cf/kickmix_venv/lib/python3.12/site-packages')
import kickmix as km
from outcome_chem_j4_synthesize import factor_columns,packed,prove
from score9_rebatch_alt_partitions import ACTUAL_HASH,REPO,coefficients,deltas,mobius

def bits(mask):
    while mask:
        b=mask&-mask;yield b.bit_length()-1;mask^=b

def deposit(mask,variables):
    return sum(((mask>>i)&1)<<b for i,b in enumerate(variables))

def geometry(partition):
    low=list(bits(partition));high=[b for b in range(11) if b not in low]
    lm=[deposit(m,low) for m in range(1<<len(low))];lm=[m for m in lm if m<1220]
    hm=[deposit(m,high) for m in range(1<<len(high))];hm=[m for m in hm if m<1220]
    return low,high,lm,hm

def complete_nested_columns(columns,masks):
    """Complete columns whose known-row masks form a decreasing chain.

    Decisions only on already known row prefixes constrain future columns.
    On an unavoidable new independent column, a zero unknown suffix loses no
    future solution because later known prefixes are contained in this one.
    """
    independent=[];completed=[];last=-1
    for column,mask in zip(columns,masks):
        assert mask&last==mask;last=mask
        piv={}
        for vector in independent:
            value=vector&mask;full=vector
            while value:
                p=value.bit_length()-1
                if p in piv:
                    v,f=piv[p];value^=v;full^=f
                else:piv[p]=(value,full);break
        value=column&mask;full=0
        while value:
            p=value.bit_length()-1
            if p not in piv:break
            v,f=piv[p];value^=v;full^=f
        if value:
            full=column&mask;independent.append(full)
        assert (full^column)&mask==0
        completed.append(full)
    assert len(factor_columns(completed))==len(independent)
    return completed

def minimum_completion(columns,lm,hm):
    masks=[]
    for h in range(1,len(hm)):
        known=1
        while known<len(lm) and (hm[h]|lm[known])<1220:known+=1
        masks.append((1<<known)-2)
    return [0]+complete_nested_columns(columns[1:],masks)

def initial_terms(coeff,lm,hm,joint,completion=False):
    columns=[[0]+[sum(((int(coeff[h|l])>>o)&1)<<i for i,l in enumerate(lm) if i) for h in hm[1:]] for o in range(32)]
    original_ranks=[len(factor_columns(c)) for c in columns]
    if completion:columns=[minimum_completion(c,lm,hm) for c in columns]
    completion_ranks=[len(factor_columns(c)) for c in columns]
    terms=[];shared=[]
    if joint and (len(lm)-1)%2:
        full=[o for o,r in enumerate(completion_ranks) if r==len(lm)-1]
        for a,b in zip(full[::2],full[1::2]):
            ha=sum(((columns[a][h]>>1)&1)<<h for h in range(len(hm)))
            hb=sum(((columns[b][h]>>2)&1)<<h for h in range(len(hm)))
            for h in range(len(hm)):
                s=(((ha>>h)&1)<<1)^(((hb>>h)&1)<<2)
                columns[a][h]^=s;columns[b][h]^=s
            ranks=[len(factor_columns(columns[o])) for o in (a,b)]
            assert max(ranks)<=len(lm)-2
            # (l1+hb)(l2+ha) gives the shared cross term plus
            # separately linearizable low-low and high-high corrections.
            terms.append((2,hb,4,ha,(1<<a)|(1<<b)))
            shared.append(dict(outputs=[a,b],residual_ranks=ranks))
    for o,c in enumerate(columns):
        pairs=factor_columns(c)
        for at in range(0,len(pairs),2):
            a,h1=pairs[at]
            if at+1<len(pairs):
                b,h2=pairs[at+1];terms.append((a,h2,b,h1,1<<o))
            else:terms.append((a,0,0,h1,1<<o))
    return terms,dict(original_ranks=original_ranks,completion_ranks=completion_ranks,shared_pairs=shared)

def synthesize(delta,partition,joint=True,completion=False):
    low,high,lm,hm=geometry(partition);nl,nh=len(lm),len(hm)
    coeff=coefficients(delta);terms,stats=initial_terms(coeff,lm,hm,joint,completion)
    lines=[]
    for q in range(11):lines.append(f'APPEND_TO_REGISTER q{q} r0')
    lines.append('REGISTER r0 "selection"')
    for j in range(4):
        for b in range(8):lines.append(f'APPEND_TO_REGISTER q{11+8*j+b} r{j+1}')
        lines.append(f'REGISTER r{j+1} "word_{j}"')
        lines.append(f'CX q{17+8*j} q{18+8*j}')
    cursor=43;nodes=[]
    def bank(n,variables):
        nonlocal cursor
        wires={1<<b:q for b,q in enumerate(variables)}
        for mask in range(1,n):
            if mask in wires:continue
            unit=mask&-mask;a,b=wires[unit],wires[mask^unit]
            wires[mask]=cursor;nodes.append((a,b,cursor))
            lines.extend((f'R q{cursor}',f'CCX q{a} q{b} q{cursor}'));cursor+=1
        return wires
    hi=bank(nh,high);lo=bank(nl,low);c1,c2=cursor,cursor+1
    assert c2<128
    lines.extend((f'R q{c1}',f'R q{c2}'))
    def form(l,h,target):
        return [f'CX q{lo[m]} q{target}' for m in bits(l)]+[f'CX q{hi[m]} q{target}' for m in bits(h)]
    address=np.arange(1220,dtype=np.uint16)
    lt=[((address&m)==m).astype(np.uint8) for m in lm]
    ht=[((address&m)==m).astype(np.uint8) for m in hm]
    def evaluate(l,h):
        value=np.zeros(1220,dtype=np.uint8)
        for m in bits(l):value^=lt[m]
        for m in bits(h):value^=ht[m]
        return value
    coded=delta.astype(np.uint32);coded^=(coded&64)<<1
    residual=sum(coded[:,j]<<(8*j) for j in range(4))
    for la,ha,lb,hb,outputs in terms:
        a,b=form(la,ha,c1),form(lb,hb,c2)
        out=list(bits(outputs));target=11+out[0]
        fan=[f'CX q{target} q{11+o}' for o in out[1:]]
        lines+=fan+a+b+[f'CCX q{c1} q{c2} q{target}']+list(reversed(b))+list(reversed(a))+list(reversed(fan))
        residual^=(evaluate(la,ha)&evaluate(lb,hb)).astype(np.uint32)*np.uint32(outputs)
    table=np.zeros(2048,dtype=np.uint32);table[:1220]=residual
    correction=mobius(table);correction[1220:]=0
    allowed=set(lm)|set(hm)
    assert all(not correction[m] for m in range(1220) if m not in allowed),'nonseparable residual'
    lookup={m:lo[i] for i,m in enumerate(lm) if i}
    lookup.update({m:hi[i] for i,m in enumerate(hm) if i})
    for mask,wires in enumerate(correction[:1220]):
        for o in bits(int(wires)):
            lines.append(f'CX q{lookup[mask]} q{11+o}' if mask else f'X q{11+o}')
    for a,b,target in reversed(nodes):lines.extend((f'HMR q{target} b0',f'CZ q{a} q{b} if b0'))
    for j in range(4):lines.append(f'CX q{17+8*j} q{18+8*j}')
    circuit=km.Circuit('\n'.join(lines)+'\n');count=int(circuit.operation_statistics().num_toffoli_like)
    assert count==len(nodes)+len(terms) and circuit.num_qubits<=128
    stats.update(partition=partition,low_bits=low,high_bits=high,nlo=nl,nhi=nh,bank_ccx=len(nodes),core_ccx=len(terms),ccx=count,qubits=circuit.num_qubits)
    return circuit,stats

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,default=Path('/workspace/scratch/3815fb5fae06/score9_rebatch_alt'))
    p.add_argument('--batches',type=int,nargs='+',default=[0,5,18])
    p.add_argument('--partition',type=int)
    p.add_argument('--no-joint',action='store_true')
    p.add_argument('--completion',action='store_true')
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);start=time.monotonic();all_delta=deltas();rows=[]
    chosen=None
    if a.partition is None:
        method=('completion_paired' if a.no_joint else 'completion_joint') if a.completion else ('paired' if a.no_joint else 'joint_full')
        chosen=json.loads((a.out/'partitions.json').read_text())['best'][method]['rows']
    for k in a.batches:
        partition=a.partition if a.partition is not None else chosen[k]['partition']
        circuit,row=synthesize(all_delta[k],partition,not a.no_joint,a.completion)
        row.update(batch=k,proof=prove(circuit,all_delta[k]))
        dest=a.out/f'alt_angle_k_{k}.kmb';circuit.to_file(dest,format='kmb')
        row['file']=str(dest);row['sha256']=hashlib.sha256(dest.read_bytes()).hexdigest();rows.append(row)
        print(json.dumps({key:row[key] for key in ('batch','partition','low_bits','ccx','qubits','proof')}),flush=True)
    result=dict(status='COMPILED_EXACT_ARBITRARY_TARGET_XOR',actual_words_sha256=ACTUAL_HASH,rows=rows,seconds=time.monotonic()-start,
                official_full_verifier_run=False,source_modified=False,joint_shared_products=not a.no_joint,care_aware_completion=a.completion)
    (a.out/'compiled.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
