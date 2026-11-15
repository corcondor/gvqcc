#!/usr/bin/env python3
"""Extract a whole, measurement-aware cleanup whose outer HMR can be delayed.

This is an analysis helper for score4_invsqrt_delay_reuse.py --allow-blocks.
Internal measurement outcomes are symbolic independent variables. Every
nonconstant monomial coefficient must vanish on the entire input domain before
any accepted rewrite. Internal classical writes must be dead outside the
removed cleanup until an unconditional overwrite.
"""
from bisect import bisect_left
from collections import defaultdict,Counter
import re

PHASE={'Z','CZ','CCZ','NEG'}
ALLOWED=PHASE|{'X','CX','CCX','SWAP','CSWAP','HMR','PUSH_CONDITION','POP_CONDITION'}

def cleanup_records(lines,ops,depth):
    uses=defaultdict(list);ends={};stack=[]
    for i,line in enumerate(lines):
        for bit in set(re.findall(r'\bb\d+\b',line)):uses[bit].append(i)
        kind=ops[i][0]
        if kind=='PUSH_CONDITION':stack.append(i)
        elif kind=='POP_CONDITION':ends[stack.pop()]=i
    result=[];rejected=Counter()
    for first,(kind,qs) in enumerate(ops):
        if kind!='HMR' or depth[first] or ' if ' in lines[first]:continue
        bit=lines[first].split()[2];removed=set();blocks=[];inline=[];bad=None;overwrite=None
        for j in uses[bit][bisect_left(uses[bit],first+1):]:
            if j in removed:continue
            words=lines[j].split();kind=words[0]
            if kind=='HMR' and words[2]==bit and not depth[j] and ' if ' not in lines[j]:overwrite=j;break
            if kind=='BIT_STORE0' and words[1]==bit and not depth[j] and ' if ' not in lines[j]:overwrite=j;break
            if kind in PHASE and not depth[j] and words[-2:]==['if',bit]:removed.add(j);inline.append(j)
            elif kind=='PUSH_CONDITION' and not depth[j] and words==['PUSH_CONDITION','if',bit]:
                end=ends[j];blocks.append((j,end));removed.update(range(j,end+1))
            else:bad='outer_use_'+kind;break
        if bad:rejected[bad]+=1;continue
        for j in sorted(removed):
            kind,qubits=ops[j];words=lines[j].split()
            if kind not in ALLOWED:bad='unsupported_'+kind;break
            if kind=='HMR':
                target_bit=words[2]
                if target_bit==bit or depth[j]!=1 or ' if ' in lines[j]:bad='conditional_or_self_measurement';break
                # This particular assigned version must be dead outside the
                # entire removed set before a guaranteed assignment.
                for k in uses[target_bit][bisect_left(uses[target_bit],j+1):]:
                    wk=lines[k].split();kk=wk[0]
                    guaranteed=(kk=='HMR' and wk[2]==target_bit and not depth[k] and ' if ' not in lines[k]) or (kk=='BIT_STORE0' and wk[1]==target_bit and not depth[k] and ' if ' not in lines[k])
                    if guaranteed:break
                    if k not in removed:bad='live_internal_measurement';break
                    if kk=='HMR' and wk[2]==target_bit:break
                if bad:break
            elif kind not in PHASE|{'PUSH_CONDITION','POP_CONDITION'} and ' if ' in lines[j]:bad='conditional_data_gate';break
        if bad:rejected[bad]+=1;continue
        # Evaluate the classical condition polynomial with outer bit fixed to
        # one. Internal HMRs occur directly in that outer block and receive fresh
        # independent symbols. Their signs are included as phase events.
        versions={bit:None};terms=defaultdict(list);conditions=[];previous=first
        def variable(name):
            if name not in versions:versions[name]='external_'+name
            return versions[name]
        def current():return set().union(*conditions) if conditions else set()
        for j in sorted(removed):
            # A classical bit reused between separated removed blocks denotes a
            # new independent value. Never cancel two different assignments by
            # accidentally giving them the same external-variable name.
            for k in range(previous+1,j):
                words=lines[k].split();kind=words[0]
                if kind=='HMR':versions[words[2]]='external_after_'+str(k)
                elif kind in ('BIT_STORE0','BIT_INVERT'):versions[words[1]]='external_after_'+str(k)
            previous=j
            kind,qubits=ops[j];words=lines[j].split()
            if kind=='PUSH_CONDITION':
                assert words[:2]==['PUSH_CONDITION','if'] and len(words)==3
                v=variable(words[2]);conditions.append(set() if v is None else {v});continue
            if kind=='POP_CONDITION':conditions.pop();continue
            monomial=current()
            if kind=='HMR':
                v='measurement_'+str(j);versions[words[2]]=v;monomial.add(v)
            elif kind in PHASE:
                if ' if ' in lines[j]:
                    assert words[-2]=='if';v=variable(words[-1])
                    if v is not None:monomial.add(v)
            else:continue
            terms[','.join(sorted(monomial))].append(j)
        assert not conditions
        result.append(dict(index=first,wire=qs[0],bit=bit,phase_indices=terms.get('',[]),
                           nonconstant_phase_terms={k:v for k,v in terms.items() if k},
                           remove_indices=sorted(removed),blocks=blocks,next_overwrite=overwrite,
                           internal_measurement_versions_dead_outside_cleanup=True))
    return result,dict(rejected)
