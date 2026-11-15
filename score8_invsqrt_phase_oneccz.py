#!/usr/bin/env python3
"""Replace a complete costly phase block by one CCZ plus Clifford phases.

Search f = q + a*b*L, where q is any quadratic form in all retained live
values, a,b are two retained wires, and L is an arbitrary retained parity.
The fit is on the complete phase, including internal measurement signs.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import itertools
import json
from pathlib import Path
import random
import time

import score_invsqrt_retire as R
from score8_invsqrt_phase_quadratic import PIN,PAID,shape,symbols,sample_values,sha,phase_value,quadratic


def extract(lines,ops,items,one,values):
    starts={x['start']:x for x in items};ends={x['end']:x for x in items};events=defaultdict(list);entry={};acc=defaultdict(int);stack=[];out=[]
    for x in items:
        for key,ids in x['symbolic']['terms'].items():
            for i in ids:events[i].append((x['start'],key))
    for i,(op,qs) in enumerate(ops):
        if i in starts:entry[i]=values[:]
        for a,key in events.get(i,[]):acc[a,key]^=phase_value(op,qs,values,one)
        if op=='PUSH_CONDITION':stack.append(values[:])
        elif op=='POP_CONDITION':assert values==stack.pop()
        else:R.advance(op,qs,values,one)
        if i in ends:
            x=ends[i];a=x['start'];terms={k:acc[a,k] for k in x['symbolic']['terms'] if acc[a,k]}
            if len(terms)==1 and not any(v.startswith('measurement_') for v in next(iter(terms))):
                key,target=next(iter(terms.items()));out.append((x,entry.pop(a),key,target))
    return out


def oneccz(values,target,one):
    wires=[q for q,v in enumerate(values) if v not in (0,one)]
    quad=[one]+[values[q] for q in wires]+[values[a]&values[b] for a,b in itertools.combinations(wires,2)]
    base=R.affine_basis(quad);pivots=sorted(base,reverse=True)
    def reduce(v):
        for p in pivots:
            if v>>p&1:v^=base[p][0]
        return v
    residual=reduce(target);cache={};queries=0
    if not residual:
        q,rank=quadratic(values,target,one);return {'pairs':[],'linear':[],'quadratic':q,'paid':0,'queries':0}
    for a,b in itertools.combinations(wires,2):
        js=[q for q in wires if q not in (a,b)];columns=[]
        for q in js:
            key=tuple(sorted((a,b,q)))
            if key not in cache:cache[key]=reduce(values[a]&values[b]&values[q])
            columns.append(cache[key])
        coeff=R.solve(R.affine_basis(columns),residual);queries+=1
        if coeff is not None:
            linear=[q for k,q in enumerate(js) if coeff>>k&1];v=0
            for q in linear:v^=values[q]
            quadmodel,rank=quadratic(values,target^(values[a]&values[b]&v),one);assert quadmodel is not None
            return {'pair':[a,b],'linear':linear,'quadratic':quadmodel,'paid':1,'queries':queries,'cached_cubic_terms':len(cache)}
    return {'status':'NO_MODEL_IN_SEARCHED_FAMILY','queries':queries,'cached_cubic_terms':len(cache),'quadratic_rank':len(base)}


def emit(model):
    out=[]
    for term in model['quadratic']:out.append('NEG' if not term else ('Z' if len(term)==1 else 'CZ')+' '+' '.join('q'+str(q) for q in term))
    if model['paid']:
        a,b=model['pair'];cs=model['linear'];assert cs and a not in cs and b not in cs;c=cs[0]
        out.extend('CX q'+str(q)+' q'+str(c) for q in cs[1:]);out.append(f'CCZ q{a} q{b} q{c}');out.extend('CX q'+str(q)+' q'+str(c) for q in reversed(cs[1:]))
    return out


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True);begin=time.monotonic()
    source=Path(__file__).with_name('score3_invsqrt_cache.kmx');assert sha(source)==PIN
    lines,ops=R.instructions(source);blocks,depth,uses=shape(lines,ops);items=[]
    for x in blocks:
        if x['paid']<=1:continue
        sym,why=symbols(lines,ops,x,depth,uses)
        if sym is not None:items.append({**x,'symbolic':sym})
    rng=random.Random(202611150805);xs=sorted(set(list(range(1,129))+[rng.randrange(1,R.MAX_X+1) for _ in range(4096)]))
    one,values=sample_values(xs);data=extract(lines,ops,items,one,values);rows=[]
    for item,values,key,target in data:
        st=time.monotonic();model=oneccz(values,target,one);row={'start':item['start'],'end':item['end'],'original_paid':item['paid'],'condition':key,'model':model,'seconds':time.monotonic()-st};rows.append(row)
        print(json.dumps({k:v for k,v in row.items() if k!='model'}|{'model_status':model.get('status','FOUND'),'queries':model['queries']}),flush=True)
        (a.out/'progress.json').write_text(json.dumps(rows,indent=2)+'\n')
    hits={r['start']:r for r in rows if 'paid' in r['model']};full=[]
    if hits:
        one,values=R.initial_values();data=extract(lines,ops,[x for x in items if x['start'] in hits],one,values)
        for item,values,key,target in data:
            row=hits[item['start']];m=row['model'];actual=0
            for term in m['quadratic']:actual^=phase_value('Z',term,values,one)
            if m['paid']:
                lin=0
                for q in m['linear']:lin^=values[q]
                actual^=values[m['pair'][0]]&values[m['pair'][1]]&lin
            full.append({**row,'result':'FULL_DOMAIN_MATCH' if actual==target else 'FULL_DOMAIN_MISMATCH'})
    report={'source_sha256':PIN,'sample_input_count':len(xs),'eligible_blocks':len(data),'sample_results':rows,'full_results':full,'seconds':time.monotonic()-begin,'scope':'Whole symbolic conditional phase, f = arbitrary quadratic + raw-wire pair times arbitrary linear parity; no arbitrary first two parity factors searched.'}
    accepted=[r for r in full if r['result']=='FULL_DOMAIN_MATCH'];report['accepted']=len(accepted)
    if accepted:
        bystart={r['start']:r for r in accepted};new=[];i=0
        while i<len(lines):
            hit=bystart.get(i)
            if hit is None:new.append(lines[i]);i+=1;continue
            new.append(lines[i])
            for sym in hit['condition']:
                assert sym.startswith('external_');new.append('PUSH_CONDITION if '+sym[len('external_'):])
            new.extend(emit(hit['model']));new.extend('POP_CONDITION' for _ in hit['condition']);new.append('POP_CONDITION');i=hit['end']+1
        dest=a.out/'candidate.kmx';dest.write_text('\n'.join(new)+'\n');report.update(candidate=str(dest),candidate_sha256=sha(dest),static_paid_saved=sum(r['original_paid']-r['model']['paid'] for r in accepted))
    (a.out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('sample_results','full_results')}),flush=True)


if __name__=='__main__':main()
