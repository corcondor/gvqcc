#!/usr/bin/env python3
"""Progressive *certified-structure* HMR cleanup for existing ANGLE compilers.

This is NOT a generic peephole rule. Each replacement is restricted to a
known freshly-computed AND ancilla and an intact pair of controls. HMR
measurement kickback is cancelled by conditional CZ on the same controls.
We retain every target-XOR CX and all unmeasured precomputation.

Phases are proved symbolically, independently for EVERY measurement outcome:
for each HMR, the measured bit function t(a) must equal a_control(a)&b_control(a)
on every legitimate address; conditional CZ cancels the contribution.
Does not require sampling all 2^N measurement outcome strings.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
import numpy as np
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'gvqcc_multiform'))
from multi_angle_synthesis import synthesize as base_synthesize, delta_table, TARGETS, TAGS, word_masks, sha256

BASES=('split-minterm','split-anf','split-basis')
GRADES=('active','active-high','all-clean')
ALGORITHMS=tuple(f'{b}--hmr-{g}' for b in BASES for g in GRADES)


class MeasuredCircuit:
    def __init__(self,num_qubits,operations):
        self.num_qubits=num_qubits
        self.operations=tuple(operations) # (op, qubits, flag)
        self.counts=Counter(op for op,_,_ in self.operations)

    def kmx_lines(self):
        for q in range(11):yield f'APPEND_TO_REGISTER q{q} r0'
        yield 'REGISTER r0 "selection"'
        for q in range(11,51):yield f'APPEND_TO_REGISTER q{q} r1'
        yield 'REGISTER r1 "target"'
        for q in range(51,self.num_qubits):yield f'R q{q}'
        for op,qs,flag in self.operations:
            name=op+' '+' '.join(f'q{q}' for q in qs)
            if op=='HMR':name+=' b0'
            if op=='CZ':name+=' if b0'
            yield name


def compile_hmr(words:np.ndarray,slot:int,algorithm:str):
    if algorithm not in ALGORITHMS:raise ValueError(algorithm)
    base,grade=algorithm.split('--hmr-')
    original,counts=base_synthesize(words,slot,base)
    gates=original.gates
    if base=='split-basis':
        high=original.alloc-3
        active=original.alloc-2
        prefix=79
    elif base=='split-anf':
        high=original.alloc-2
        active=original.alloc-1
        prefix=79
    else:
        high=original.alloc-2
        active=original.alloc-1
        prefix=108
    assert list(gates[:prefix])==list(reversed(gates[-prefix:]))
    assert all(op in ('CX','X','CCX') for op,_ in gates)
    assert all(q[-1]>=51 for op,q in gates[-prefix:] if op=='CCX')

    marked={} # original gate index -> [a,b,t]
    # Family I: active = high_condition AND low_form, its CX fanout,
    # then an inverse CCX. All targets are borrowed dirty XOR targets.
    for i,(op,qs) in enumerate(gates):
        if op!='CCX' or qs[2]!=active:continue
        j=i+1
        while j<len(gates) and gates[j][0]=='CX' and gates[j][1][0]==active and gates[j][1][1] in TARGETS:
            j+=1
        if j>i+1 and j<len(gates) and gates[j]==(op,qs):
            marked[j]=qs
    active_count=len(marked)
    if grade in ('active-high','all-clean'):
        # Family II: each nonzero high block has a high3*high4 flag,
        # reused for many active products and then reversed once.
        indices=[i for i,(op,q) in enumerate(gates) if op=='CCX' and q[2]==high]
        if len(indices)%2:raise AssertionError('high-flags must come in matched pairs')
        for i,j in zip(indices[::2],indices[1::2]):
            if gates[i]!=gates[j]:raise AssertionError('high control changed')
            marked[j]=gates[j][1]
    high_count=len(marked)-active_count
    if grade=='all-clean':
        # Family III: the prefix is a reversible bank of fresh AND flags,
        # and the exact inverse suffix restores each after all uses.
        for i in range(len(gates)-prefix,len(gates)):
            op,q=gates[i]
            if op=='CCX':
                if i in marked:raise AssertionError('overlapping uncompute')
                marked[i]=q
    pre_count=len(marked)-active_count-high_count
    if not marked:raise AssertionError('no eligible clean ANDs found')
    ops=[]
    for i,(op,qs) in enumerate(gates):
        if i in marked:
            a,b,t=marked[i]
            ops.append(('HMR',(t,),0))
            ops.append(('CZ',(a,b),0))
        else:
            ops.append((op,qs,None))
    if not all(g[0]=='CCX' for i,g in enumerate(gates) if i in marked):raise AssertionError
    circuit=MeasuredCircuit(original.alloc,ops)
    report=dict(method=algorithm,slot=slot,qubits=original.alloc,
                CCX=int(circuit.counts['CCX']),CX=int(circuit.counts['CX']),
                X=int(circuit.counts['X']),HMR=int(circuit.counts['HMR']),
                conditional_CZ=int(circuit.counts['CZ']),
                baseline_CCX=int(counts.get('CCX',0)),
                saving_CCX=int(counts.get('CCX',0)-circuit.counts['CCX']),
                HMR_active=active_count,HMR_high=high_count,HMR_precomp=pre_count)
    assert report['saving_CCX']==report['HMR']==report['conditional_CZ']
    return circuit,report


def prove(circuit:MeasuredCircuit,delta:np.ndarray,dirty_seed=7):
    """All valid addresses in one bitparallel run; HMR phase certificate.

    HMR measurement result is a fresh independent symbol m_i. The resulting
    phase polynomial coefficient for m_i is value_of_t XOR (a&b). By
    checking each coefficient ==0 over ALL addresses, we check *every*
    measurement outcome combination without enumerating 2^HMR cases.
    """
    n=len(delta);care=(1<<n)-1
    initial=[0]*circuit.num_qubits
    for q in range(11):initial[q]=sum(((a>>q)&1)<<a for a in range(n))
    rng=np.random.default_rng(dirty_seed)
    for q in range(11,51):initial[q]=int.from_bytes(rng.bytes((n+7)//8),'little')&care
    state=initial.copy();measurements=0
    pending=None
    for op,q,flag in circuit.operations:
        if pending is not None and op!='CZ':
            raise AssertionError(('missing immediate phase correction',op,q))
        if op=='X':state[q[0]]^=care
        elif op=='CX':
            if q[0] in range(11,51):raise AssertionError('dirty target control')
            state[q[1]]^=state[q[0]]
        elif op=='CCX':
            if q[0] in range(11,51) or q[1] in range(11,51):raise AssertionError('dirty CCX control')
            state[q[2]]^=state[q[0]]&state[q[1]]
        elif op=='HMR':
            if q[0]<51:raise AssertionError('measured public wire')
            pending=state[q[0]] # symbolic coefficient of fresh measurement outcome
            state[q[0]]=0
        elif op=='CZ':
            if pending is None:raise AssertionError('orphan CZ')
            residual=pending^(state[q[0]]&state[q[1]])
            if residual:raise AssertionError(('uncorrected phase',measurements,(residual&-residual).bit_length()-1))
            pending=None;measurements+=1
        else:raise AssertionError('unexpected opcode')
    if pending is not None:raise AssertionError('uncorrected final HMR')
    target_masks=word_masks(delta)
    for i,q in enumerate(TARGETS):
        expected=sum(((target_masks[a]>>i)&1)<<a for a in range(n))
        if state[q]!=(initial[q]^expected):raise AssertionError(('wrong output',i,q))
    for q in list(range(11))+list(TAGS):
        if state[q]!=initial[q]:raise AssertionError(('address/tag changed',q))
    for q in range(51,circuit.num_qubits):
        if state[q]:raise AssertionError(('scratch not reset',q))
    return dict(all_valid_addresses=True,arbitrary_dirty_targets=True,
                all_HMR_phase_symbols_cancel=True,independent_measurements=measurements,
                scratch_clean=True,tags_unchanged=True,verified_addresses=n)


def experiment(args):
    args.out.mkdir(parents=True,exist_ok=True)
    script_hash=sha256(Path(__file__))
    ledger=args.out/'experiments.jsonl'
    if ledger.exists():raise FileExistsError('append only: choose new output path')
    totals={}; records=[]
    for source in args.seeds:
        with np.load(source,allow_pickle=False) as z:words=np.array(z['angle_words'],np.int64)
        source_hash=sha256(source)
        for method in args.methods:
            totals[(source.name,method)]=dict(source=source.name,method=method,Q_peak=0,CCX=0,CX=0,X=0,HMR=0,conditional_CZ=0,slots=0)
            for slot in range(15):
                c,stat=compile_hmr(words,slot,method)
                proof=prove(c,delta_table(words,slot),args.dirty_seed)
                key=hashlib.sha256(f'{script_hash}|{source_hash}|{method}|{slot}'.encode()).hexdigest()
                rec=dict(schema='gvqcc.multiangle.hmr.v1',experiment_id=key,
                         source_sha256=source_hash,script_sha256=script_hash,
                         source=source.name,**stat,**proof,
                         official_KickMix_pass=False,score_status='NO_NEW_SCORE')
                if args.emit and slot in (0,1,14):
                    path=args.out/(source.stem+'__'+method+'__k'+str(slot)+'.kmx')
                    path.write_text('\n'.join(c.kmx_lines())+'\n')
                    rec['kmx_sha256']=sha256(path)
                with ledger.open('a') as f:f.write(json.dumps(rec,sort_keys=True)+'\n')
                records.append(rec)
                bucket=totals[(source.name,method)]
                bucket['Q_peak']=max(bucket['Q_peak'],stat['qubits']);bucket['slots']+=1
                for field in ('CCX','CX','X','HMR','conditional_CZ'):bucket[field]+=stat[field]
            print(json.dumps(totals[(source.name,method)]),flush=True)
    summ=dict(schema='gvqcc.multiangle.hmr.summary.v1',script_sha256=script_hash,
              records=len(records),groups=list(totals.values()),
              proof='every address; arbitrary dirty target bits; each HMR phase symbol cancels',
              scope='native KickMix for real generated KMX NOT run; no score')
    (args.out/'summary.json').write_text(json.dumps(summ,indent=2)+'\n')
    return summ


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seeds',nargs='+',required=True,type=Path)
    p.add_argument('--methods',nargs='+',choices=ALGORITHMS,default=list(ALGORITHMS))
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--emit',action='store_true')
    p.add_argument('--dirty-seed',type=int,default=7)
    args=p.parse_args()
    experiment(args)

if __name__=='__main__':main()
