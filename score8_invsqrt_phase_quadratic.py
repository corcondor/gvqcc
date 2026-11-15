#!/usr/bin/env python3
"""Relational Clifford resynthesis of complete conditional phase blocks.

This is not an AND-window optimizer. A quantum-data identity block can have
an expensive phase polynomial; on the actual reachable input manifold that
whole phase may be expressible using only free Z/CZ gates. Internal HMR signs
are retained symbolically and must cancel. First screen on legal inputs, then
prove every proposed identity on the complete domain before emission.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import random
import re
import time

import score_invsqrt_retire as R

PIN = 'd431f212c7da02418429c2883dcdf4e3a90c9124ab2409c999efe0a5c7c037a8'
PHASE = {'Z','CZ','CCZ','NEG'}
DATA = {'X','CX','CCX','CSWAP','SWAP','HMR'}
PAID = {'CCX','CCZ','CSWAP'}


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def shape(lines, ops):
    stack=[]; blocks=[]; depth=[]; uses=defaultdict(list)
    for i, ((op,qs),line) in enumerate(zip(ops,lines)):
        depth.append(len(stack))
        for bit in set(re.findall(r'\bb\d+\b',line)): uses[bit].append(i)
        if op=='PUSH_CONDITION': stack.append(i)
        elif op=='POP_CONDITION':
            start=stack.pop()
            if not stack:
                paid=sum(ops[j][0] in PAID for j in range(start,i+1))
                if paid: blocks.append({'start':start,'end':i,'paid':paid})
    assert not stack
    return blocks,depth,uses


def symbols(lines,ops,item,depth,uses):
    """Only allow internal measurement versions which cannot escape a block."""
    a,b=item['start'],item['end']; outer=lines[a].split()[-1]
    versions={outer:None}; conditions=[]; terms=defaultdict(list)
    for j in range(a,b+1):
        op,qs=ops[j]; words=lines[j].split()
        if op not in PHASE|DATA|{'PUSH_CONDITION','POP_CONDITION'}:
            return None,'unsupported_'+op
        def variable(bit):
            if bit not in versions: versions[bit]='external_'+bit
            return versions[bit]
        if op=='PUSH_CONDITION':
            v=variable(words[-1]); conditions.append(set() if v is None else {v}); continue
        if op=='POP_CONDITION': conditions.pop(); continue
        monomial=set().union(*conditions) if conditions else set()
        if op=='HMR':
            bit=words[2]
            if bit==outer or depth[j]!=1 or ' if ' in lines[j]:return None,'conditional_or_self_HMR'
            for k in uses[bit]:
                if k<=j: continue
                wk=lines[k].split(); ok=ops[k][0]
                overwrite=((ok=='HMR' and wk[2]==bit) or (ok=='BIT_STORE0' and wk[1]==bit)) and depth[k]==0 and ' if ' not in lines[k]
                if overwrite: break
                if k>b:return None,'live_internal_outcome'
                if ok=='HMR' and wk[2]==bit: break
            v='measurement_'+str(j); versions[bit]=v;monomial.add(v)
        elif op in PHASE:
            if ' if ' in lines[j]:
                v=variable(words[-1])
                if v is not None:monomial.add(v)
        elif ' if ' in lines[j]:return None,'conditional_data'
        else:continue
        terms[tuple(sorted(monomial))].append(j)
    assert not conditions
    return {'outer':outer,'terms':dict(terms)},None


def phase_value(op,qs,values,one):
    v=one
    for q in qs:v&=values[q]
    return v


def quadratic(values,target,one):
    wires=[q for q,v in enumerate(values) if v not in (0,one)]
    features=[one]+[values[q] for q in wires]
    descriptions=[()] + [(q,) for q in wires]
    for i,a in enumerate(wires):
        for b in wires[i+1:]:
            features.append(values[a]&values[b]); descriptions.append((a,b))
    basis=R.affine_basis(features); coeff=R.solve(basis,target)
    if coeff is None:return None, len(basis)
    return [descriptions[j] for j in range(len(features)) if coeff>>j&1],len(basis)


def sample_values(xs):
    one=(1<<len(xs))-1
    values=[sum(((x>>q)&1)<<j for j,x in enumerate(xs)) for q in range(22)]+[0]*24
    return one,values


def simulate(lines,ops,selected,one,values,check=None):
    start={x['start']:x for x in selected}; end={x['end']:x for x in selected}
    event=defaultdict(list)
    for item in selected:
        for key,indices in item['symbolic']['terms'].items():
            for j in indices:event[j].append((item['start'],key))
    sums=defaultdict(int); entries={}; result=[];stack=[]
    for i,(op,qs) in enumerate(ops):
        if i in start:entries[i]=values[:]
        for a,key in event.get(i,[]):sums[a,key]^=phase_value(op,qs,values,one)
        if op=='PUSH_CONDITION':stack.append(values[:])
        elif op=='POP_CONDITION':
            old=stack.pop();assert values==old,(i, 'quantum nonidentity')
        else:R.advance(op,qs,values,one)
        if i in end:
            item=end[i];a=item['start']
            nonzero={key:sums[a,key] for key in item['symbolic']['terms'] if sums[a,key]}
            bad=[key for key in nonzero if any(v.startswith('measurement_') for v in key)]
            row={'start':a,'end':i,'paid':item['paid'],'nonzero_terms':len(nonzero)}
            if bad:row['result']='INTERNAL_MEASUREMENT_PHASE'
            else:
                models=[];rank=0
                for key,target in nonzero.items():
                    if check is None:
                        model,rk=quadratic(entries[a],target,one);rank=max(rank,rk)
                        if model is None:break
                    else:
                        source=next(m for m in check[a]['models'] if tuple(m['condition'])==key)
                        model=[tuple(v) for v in source['phase_monomials']]
                        actual=0
                        for monomial in model:actual^=phase_value('Z',monomial,entries[a],one)
                        if actual!=target:row['mismatch_x']=(actual^target).bit_length()-1; model=None; break
                    models.append({'condition':key,'phase_monomials':model})
                else:
                    row['result']='FULL_DOMAIN_MATCH' if check is not None else 'SAMPLE_MODEL'
                    row['models']=models
                if 'result' not in row:row['result']='NO_QUADRATIC_MODEL' if check is None else 'FULL_DOMAIN_MISMATCH'
                row['rank']=rank
            result.append(row);entries.pop(a)
    return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();begin=time.monotonic();args.out.mkdir(parents=True,exist_ok=True)
    source=Path(__file__).with_name('score3_invsqrt_cache.kmx');assert sha(source)==PIN
    lines,ops=R.instructions(source);blocks,depth,uses=shape(lines,ops)
    rejected=Counter();eligible=[]
    for item in blocks:
        sym,why=symbols(lines,ops,item,depth,uses)
        if sym is None:rejected[why]+=1
        else:eligible.append({**item,'symbolic':sym})
    rng=random.Random(202611150802)
    xs=sorted(set(list(range(1,257))+[2**k+d for k in range(2,22) for d in range(-3,4)]+[rng.randrange(1,R.MAX_X+1) for _ in range(4096)]))
    one,values=sample_values(xs)
    sampled=simulate(lines,ops,eligible,one,values)
    hits={row['start']:row for row in sampled if row['result']=='SAMPLE_MODEL'}
    print(json.dumps({'paid_blocks':len(blocks),'eligible':len(eligible),'rejected':dict(rejected),'sample_inputs':len(xs),'sample_counts':dict(Counter(x['result'] for x in sampled)),'sample_saved_paid':sum(x['paid'] for x in hits.values()),'seconds':time.monotonic()-begin}),flush=True)
    full=[]
    if hits:
        one,values=R.initial_values()
        full=simulate(lines,ops,[x for x in eligible if x['start'] in hits],one,values,hits)
    accepted=[x for x in full if x['result']=='FULL_DOMAIN_MATCH']
    report={'source_sha256':PIN,'paid_blocks':len(blocks),'eligible':len(eligible),'rejected':dict(rejected),'sample_input_count':len(xs),'sample_results':sampled,'full_results':full,'accepted':len(accepted),'full_domain_inputs':R.MAX_X if hits else 0,'seconds':time.monotonic()-begin,'scope':'whole conditional quantum-data identity blocks, all retained live entry wires, unrestricted quadratic Clifford phase; dead internal outcomes only; full domain for every accepted model'}
    if accepted:
        by_start={x['start']:x for x in accepted};new=[];i=0
        while i<len(lines):
            item=by_start.get(i)
            if item is None:new.append(lines[i]);i+=1;continue
            new.append(lines[i])
            for model in item['models']:
                for symbol in model['condition']:
                    assert symbol.startswith('external_');new.append('PUSH_CONDITION if '+symbol[len('external_'):])
                for monomial in model['phase_monomials']:
                    new.append(('NEG' if not monomial else ('Z' if len(monomial)==1 else 'CZ')+' '+' '.join('q'+str(q) for q in monomial)))
                new.extend('POP_CONDITION' for _ in model['condition'])
            new.append('POP_CONDITION');i=item['end']+1
        candidate=args.out/'candidate.kmx';candidate.write_text('\n'.join(new)+'\n')
        report.update(candidate_kmx=str(candidate),candidate_sha256=sha(candidate),static_paid_saved=sum(x['paid'] for x in accepted))
    (args.out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('sample_results','full_results')}),flush=True)


if __name__=='__main__':main()
