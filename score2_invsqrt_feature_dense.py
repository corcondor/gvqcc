#!/usr/bin/env python3
"""Full parity search in a local control/held-difference space, with all live RHS wires."""
import json
from pathlib import Path
import random
import time
import score_invsqrt_retire as r

PANEL=[dict(name='feature_j2',start=8189,phase=8195,end=8203,left_wires=[22,23,24,25,7,34,19,20,44,43]),
       dict(name='feature_j6',start=8257,phase=8259,end=8265,left_wires=[22,23,24,25,7,40,19,20,44,9]),
       dict(name='feature_j4',start=8293,phase=8301,end=8313,left_wires=[22,23,24,25,7,8,19,20,41,40]),
       dict(name='feature_j5',start=8314,phase=8317,end=8325,left_wires=[22,23,24,25,7,41,19,20,8,40])]

def dense_product(vals,target,domain,samples,left_wires):
    eligible=[q for q in range(46) if q!=target and vals[q]]
    sig=[sum(((vals[q]>>x)&1)<<j for j,x in enumerate(samples)) for q in eligible]
    ts=sum(((vals[target]>>x)&1)<<j for j,x in enumerate(samples));one=(1<<len(samples))-1
    affine=[one]+sig;lefts=[eligible.index(q) for q in left_wires if q in eligible]
    def full_linear(c):
        value=domain if c&1 else 0
        for j,q in enumerate(eligible):
            if c>>(j+1)&1:value^=vals[q]
        return value
    checks=0
    for leftmask in range(1,1<<len(lefts)):
        left=[lefts[j] for j in range(len(lefts)) if leftmask>>j&1];a=0;av=0
        for j in left:a^=sig[j];av^=vals[eligible[j]]
        signatures=affine+[a&s for s in sig];target_sig=ts;width=len(samples)
        for refine in range(len(signatures)+1):
            coeff=r.solve(r.affine_basis(signatures),target_sig)
            if coeff is None:break
            lin=coeff&((1<<len(affine))-1);right=coeff>>len(affine);bv=0
            for j,q in enumerate(eligible):
                if right>>j&1:bv^=vals[q]
            value=full_linear(lin)^(av&bv);difference=value^vals[target];checks+=1
            if not difference:return {'and_count':1,'constant':lin&1,'linear':[q for j,q in enumerate(eligible) if lin>>(j+1)&1],
                'left':[eligible[j] for j in left],'right':[q for j,q in enumerate(eligible) if right>>j&1],
                'full_domain_candidate_checks':checks,'refinements':refine}
            x=(difference&-difference).bit_length()-1;bits=[(vals[q]>>x)&1 for q in eligible];abit=sum(bits[j] for j in left)&1
            fb=[1]+bits+[abit*b for b in bits];signatures=[s|(b<<width) for s,b in zip(signatures,fb)]
            target_sig|=((vals[target]>>x)&1)<<width;width+=1
    return None

def states():
    base=Path(__file__).parent;lines,ops=r.instructions(base/'invsqrt_structural_e46.kmx');domain,values=r.initial_values();stack=[]
    panel=[dict(x) for x in PANEL];starts={x['start']:x for x in panel};phases={x['phase']:x for x in panel}
    for i,(op,qs) in enumerate(ops):
        if i in starts:starts[i]['entry']=values[:];assert not values[21]
        if i in phases:
            item=phases[i];assert op=='Z_POW' and qs==(21,);trial=item['entry'][:];trial[21]=values[21]
            yield item,trial,domain
        if op=='PUSH_CONDITION':stack.append(values[:])
        elif op=='POP_CONDITION':before=stack.pop();assert before==values;values=before
        else:r.advance(op,qs,values,domain)
        if i>max(phases):break

def main():
    base=Path(__file__).parent;rng=random.Random(41983);samples=list(range(1,129))+[rng.randrange(1,r.MAX_X+1) for _ in range(512)]
    records=[]
    for item,trial,domain in states():
        began=time.monotonic();identity=dense_product(trial,21,domain,samples,item['left_wires'])
        record={k:v for k,v in item.items() if k!='entry'}|{'identity':identity,'seconds':time.monotonic()-began}
        records.append(record);print(json.dumps(record),flush=True)
        (base/'score2_invsqrt_feature_dense.json').write_text(json.dumps({'legal_inputs':r.MAX_X,'scope':'left parity arbitrary over the 10 stated control and held-difference wires; right parity and affine remainder use every retained live wire','records':records},indent=2)+'\n')

if __name__=='__main__':main()
