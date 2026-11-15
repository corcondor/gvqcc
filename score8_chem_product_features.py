#!/usr/bin/env python3
"""Find sparse masks in adjacent existing-product spans (no added CCX)."""
from pathlib import Path
import hashlib,itertools,json,time
import kickmix as km
import numpy as np
from score8_chem_shared_features import basis,expression,SOURCE,TABLE
from chemistry_joint_product_resynthesis import extract
from chemistry_dontcare_v4_prune import basis_state,mutate,affine_value
from chemistry_reachable_exact_proof import pack

def represented(mask,items):
    value=0
    while mask:
        bit=(mask&-mask).bit_length()-1;mask^=1<<bit;value^=items[bit]
    return value

def intersection(left,right):
    # Carry the original right-space truth through quotient elimination.
    quotient={};shared=[]
    for value,_ in right.values():
        full=value
        for bit,(a,_) in sorted(left.items(),reverse=True):
            if value>>bit&1:value^=a
        while value:
            bit=value.bit_length()-1
            if bit in quotient:
                v,f=quotient[bit];value^=v;full^=f
            else:quotient[bit]=(value,full);break
        if not value:shared.append(full)
    return basis([(v,1<<i) for i,v in enumerate(shared)])

def main():
    started=time.monotonic();data=dict(np.load(TABLE));words=data['angle_words'].astype(np.uint64);ones=(1<<1220)-1
    abits=[pack((np.arange(1220,dtype=np.uint64)>>b)&1) for b in range(11)]
    features={};report={};candidates=[]
    for k in range(1,15):
        circuit=km.Circuit.from_file(SOURCE/f'angle_k_{k}.kmb');ex=extract(circuit)
        state=basis_state(circuit,words[:,5*(k-1):5*k],abits)
        for line in ex['lines'][:ex['first']]:mutate(state,line,ones)
        values=[ones]+[state[q] if q in ex['pool'] else 0 for q in range(circuit.num_qubits)]
        values += [affine_value(a,state,ones)&affine_value(b,state,ones) for a,b,_ in ex['terms']]
        ba=basis([(v,1<<i) for i,v in enumerate(values)])
        features[k]=(ba,values)
        report[k]=dict(batch=k,qubits=circuit.num_qubits,products=len(ex['terms']),rank=len(ba),first=ex['first'],last=ex['last'],
            values_hex=list(map(hex,values)),basis={str(p):[hex(v),hex(e)] for p,(v,e) in ba.items()})
    stats=[]
    for k in range(1,15):
        ba,_=features[k];bb,_=features[k+1] if k<14 else features[k]
        common=intersection(ba,bb) if k<14 else ba
        found=set()
        # Exact one- and two-address masks, including pairs in different groups.
        units=[]
        for a in range(80,1220):
            v=1<<a
            if expression(v,common) is not None:found.add(v);units.append(a)
        # Equal quotient syndromes characterize two-address codewords.
        buckets={}
        for a in range(80,1220):
            value=1<<a
            for bit,(v,_) in sorted(common.items(),reverse=True):
                if value>>bit&1:value^=v
            buckets.setdefault(value,[]).append(a)
        pairs=0
        for addresses in buckets.values():
            for a,b in itertools.combinations(addresses,2):found.add((1<<a)|(1<<b));pairs+=1
        # Reduced sparse common basis plus pair combinations, up to 15 rows.
        vectors=[v for v,_ in common.values()]
        for v in vectors:
            if not(v&((1<<80)-1)) and 0<v.bit_count()<16:found.add(v)
        for a,b in itertools.combinations(vectors,2):
            v=a^b
            if not(v&((1<<80)-1)) and 0<v.bit_count()<16:found.add(v)
        hist={}
        for v in sorted(found,key=lambda x:(x.bit_count(),x)):
            ea,eb=expression(v,ba),expression(v,bb);assert ea is not None and eb is not None
            addresses=[a for a in range(1220) if v>>a&1];hist[str(len(addresses))]=hist.get(str(len(addresses)),0)+1
            candidates.append(dict(batch=k,addresses=addresses,current_expression=hex(ea),next_expression=hex(eb) if k<14 else None))
        row=dict(batch=k,rank_current=len(ba),common_rank=len(common),unit_masks=len(units),pair_masks=pairs,
            sparse_mask_histogram=hist,total=len(found));stats.append(row);print(json.dumps(row),flush=True)
    out=dict(status='EXISTING_PRODUCT_FEATURE_SPANS_EXTRACTED',table=str(TABLE),source=str(SOURCE),features=report,
        candidates=candidates,statistics=stats,total_candidates=len(candidates),seconds=time.monotonic()-started)
    Path(__file__).with_suffix('.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(dict(total_candidates=len(candidates),seconds=time.monotonic()-started)),flush=True)

if __name__=='__main__':main()
